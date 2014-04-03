import os.path
import time
import shutil
import copy
import glob
import sys

from  itertools import product, groupby

from numpy import array

import scipy
from scipy.stats import chi2, t
from scipy.stats.mstats import rankdata

from xml_runner import *
from utils import *
from parameters import *

# Helper classes to hold settings: maybe only need one class?
class IFraceSettings(object):
    def __init__(self, is_iterative=False, interval=10, regenerator=regen_minmax_sobol(64)):
        self.is_iterative = is_iterative
        self.interval = interval
        self.regenerator = regenerator


class FRaceSettings(object):
    def __init__(self, generator, min_probs=1, min_solutions=2, alpha=0.05, iterations=100):
        self.min_probs = min_probs
        self.min_solutions = min_solutions
        self.alpha = alpha
        self.iterations = iterations
        self.generator = generator


class GeneralSettings(object):
    def __init__(self, algorithm, problems, measure, samples, resolution, maximising, user, job, base_location, jar_path, cmd):
        self.algorithm = algorithm
        self.problems = problems
        self.measurement = measure
        self.samples = samples
        self.resolution = resolution

        self.maximising = maximising

        self.user = user
        self.job = job

        self.jar_path = jar_path
        if not os.path.exists(jar_path):
            print "Could not find JAR file"
            sys.exit(1)

        self.base_location = base_location
        self.results_location = os.path.join(base_location, user + '_' + job)

        self.cmd = cmd


# Statistical functions
def friedman(results, alpha=0.05):
    '''
    Performs the Friedman test on the given results determining if there is a difference between configurations

    results: list of list of numbers representing results for parameters for a number of problems
    alpha: 1 - confidence of outcome
    '''

    ranks = rankdata(array(results), axis=1)
    (k,n) = ranks.shape
    T = (n-1)*sum((sum(ranks) - k*(n+1)/2.)**2) / sum(sum(ranks ** 2 - (n+1)*(n+1) / 4.))
    return T, chi2.ppf(1-alpha, n-1)


def post_hoc(results, alpha, stat):
    '''
    Performs a post-hoc test on the given results to determine the index configurations which are not 
    statistically worse than the best configuration

    results: list of list of numbers representing results for parameters for a number of problems
    alpha: 1 - confidence of outcome
    stat: statistic obtained from friedman test
    '''

    ranks = rankdata(array(results), axis=1)
    (k,n) = ranks.shape
    rank_sum = list(sum(ranks))
    best = min(rank_sum)
    rhs = ((2*k*(1-stat/(k*(n-1)))*sum(sum(ranks**2 - (n+1)*(n+1) / 4.)))/((k-1)*(n-1)))**0.5 * t.ppf(1-alpha/2, n-1)
    return [rank_sum.index(i) for i in rank_sum if abs(best - i) < rhs]


def generate_results(settings):
    '''
    Function to generate a results table and a list of parameters given from a directory
    It is assumed that there are an equal number results for each parameter
    '''

    def by_iter(x):
        return int(os.path.basename(x).split('_')[0])

    def file_mean(x, obj=1):
        return obj * scipy.mean([float(i) for i in open(x, 'r').readlines()[-1].split(' ')[1:]])

    results = []
    pars = []
    path = settings.results_location
    files = sorted(os.listdir(path), key=by_iter)

    groups = groupby(files, by_iter)
    for k in groups:
        ps = sorted([v for v in k[1]])

        if not pars:
            pars = [ p[p.find('_')+1:].replace('.txt', '') for p in ps ]

        results.append([file_mean(os.path.join(path, p), 1 if not settings.maximising else -1) for p in ps])

    return results, pars


def iteration(pars, settings, frace_settings, iteration):
    while not all(os.path.exists(p) for p in par_filenames(iteration, pars, settings)):
        # for p in par_filenames(iteration, pars, settings):
        #     print p, os.path.exists(p)
        #     # wait for results
        # print "sleepy time"
        print '\r', sum([os.path.exists(p) for p in par_filenames(iteration, pars, settings)]), '/', float(len(pars)), 'Completed results',
        time.sleep(5)
    print

    results, pars = generate_results(settings)

    if len(results) >= frace_settings.min_probs and len(pars) > 1:
        print 'Consulting Milton'
        f_stat, p_val = friedman(results, frace_settings.alpha)

        if f_stat > p_val:
            print 'Difference detected'
            indexes = set(post_hoc(results, frace_settings.alpha, f_stat))

            if indexes:
                if len(indexes) >= frace_settings.min_solutions:
                    print '== Reducing by index'
                    print 'Keeping:', indexes
                    pars = [pars[i] for i in indexes]
                    print 'Parameter count:', len(pars)
                    print '=='
                else:
                    # if not enough surviving configs, get best min_solutions
                    print '== Reducing by min_solutions'
                    pars = sort_pars(results, pars)[:frace_settings.min_solutions]
                    print 'Parameter count:', len(pars)
                    print '=='
            else:
                print 'Could not find difference'

    return pars


def frace_runner(settings, frace_settings, ifrace_settings):

    path = os.path.join(settings.base_location, settings.user)
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)

    if os.path.exists(settings.results_location):
        shutil.rmtree(settings.results_location)
    os.makedirs(settings.results_location)

    print '** Generating parameters'
    pars = [p for p in frace_settings.generator()]

    print '** Preparing output file'
    result_filename = os.path.join(settings.base_location, settings.user, settings.user + '_' + settings.job + '.txt')

    results_file = open(result_filename, 'w+')
    results_file.write('0 ' + ' '.join([par_to_result(p) for p in pars]) + '\n')

    i = 0
    while i < frace_settings.iterations:

        print '\nStarting iteration', i

        # regenerate parameters if needed
        if ifrace_settings.is_iterative and i % ifrace_settings.interval == 0 and not i == 0:
            print 'Regenerating parameters...'
            pars = ifrace_settings.regenerator(pars)
            # delete all result files for this frace run since they're not used anymore
            shutil.rmtree(os.path.join(settings.results_location))
            os.makedirs(os.path.join(settings.results_location))

        # get list of current result files
        toRemove = copy.deepcopy(pars)

        # determine start, middle and end iterations of current cycle
        if not ifrace_settings.is_iterative:
            e_iter = frace_settings.iterations
            m_iter = frace_settings.min_probs
            s_iter = 0
        else:
            s_iter = i / ifrace_settings.interval * ifrace_settings.interval
            m_iter = s_iter + frace_settings.min_probs
            e_iter = s_iter + ifrace_settings.interval

        # if at beginning of a cylce generate all sims from now until discarding iteration
        if i == s_iter:
            run_script(generate_script(pars, range(s_iter, min(frace_settings.iterations, m_iter)), settings), settings.jar_path, settings.cmd)
            i = min(m_iter - 1, frace_settings.iterations)
        elif i >= m_iter: # if discarding iteration 
            run_script(generate_script(pars, [i], settings), settings.jar_path, settings.cmd)

        # frace iteration
        print '-- Iteration'
        pars = iteration(pars, settings, frace_settings, i)

        # delete unused results
        print '-- Deleting removed parameters'
        toRemove = [ p for p in toRemove if not p in pars ]
        for p in toRemove:
            for j in glob.glob(os.path.join(settings.results_location, '*' + p + '*')):
                os.remove(j)
        print '       Removed', len(toRemove), 'parameters'

        # sort parameters
        print '-- Sorting parameters'
        pars = sort_pars(*generate_results(settings))

        i += 1

        # write pars to result file
        results_file.write(str(i) + ' ' + ' '.join([par_to_result(p) for p in pars]) + '\n')

        # this is so we don't waste time tuning when there is no chance of reducing the no. of parameters
        if ifrace_settings.is_iterative and len(pars) == frace_settings.min_solutions:
            old_i = i
            print '-- Recalculating iteration'
            i = (i / ifrace_settings.interval + 1) * ifrace_settings.interval

            for j in range(i - old_i):
                p = settings.problems.pop(0)
                settings.problems.append(p)

            print i

        print '-- Remaining parameter count: ', len(pars)
        print 'Ending iteration\n'

    results_file.close()

    # clear results folder, TODO: not sure if this is needed for ciclops
    shutil.rmtree(os.path.join(settings.results_location))

    print '** Done'
    return result_filename

