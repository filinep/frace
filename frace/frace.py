import os.path
import time
import shutil
import copy
import glob
import sys

from  itertools import product, groupby, combinations

from numpy import array

import scipy
from scipy.stats import chi2, t
from scipy.stats.mstats import rankdata
from scipy.stats import tiecorrect
from scipy.stats import distributions
from scipy.stats import rankdata as rank
import numpy as np

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


def mann_whitney_u(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    n1 = len(x)
    n2 = len(y)
    ranked = rank(np.concatenate((x,y)))
    rankx = ranked[0:n1]       # get the x-ranks
    u1 = n1*n2 + (n1*(n1+1))/2.0 - np.sum(rankx,axis=0)  # calc U for x
    u2 = n1*n2 - u1                            # remainder is U for y
    T = tiecorrect(ranked)
    if T == 0:
        #raise ValueError('All numbers are identical in amannwhitneyu')
        z = 0
    else:
        sd = np.sqrt(T*n1*n2*(n1+n2+1)/12.0)
        z = (min(u1,u2)-n1*n2/2.0) / sd  # normal approximation for prob calc

    return u1, u2, z, distributions.norm.sf(abs(z))  # (1.0 - zprob(z))


def generate_results(settings, frace_settings, iteration):
    def by_iter(x):
        return int(os.path.basename(x).split('_')[0])

    path = settings.results_location
    files = sorted([i for i in os.listdir(path) if by_iter(i) <= iteration and os.path.isfile(os.path.join(path, i))], key=by_iter)
    groups = [(i[0], [j for j in i[1]]) for i in groupby(files, by_iter)]

    pars = [ p[p.find('_')+1:].replace('.txt', '') for p in groups[0][1] ]
    with open(os.path.join(path, files[0]), 'r') as tmp:
        header = [i for i in tmp.readlines() if i[0] == '#']
        ms = int(header[-1].split(' ')[-1].translate(None, '()')) + 1
        single = len(set([i.split(' ')[3] for i in header[1:]])) == 1

    if single:
        return generate_results_single(
            1 if not settings.maximising else -1,
            groups, path
        ), pars
    else:
        return generate_results_multiple(
            [ 1 if not o else -1 for o in settings.maximising],
            groups, path, ms, frace_settings.alpha
        ), pars


def generate_results_single(obj, groups, path):
    '''
    Function to generate a results table and a list of parameters given from a directory
    It is assumed that there are an equal number results for each parameter
    '''

    def file_mean(x):
        return obj * scipy.mean([float('inf') if float(i) is float('nan') else float(i) for i in open(x, 'r').readlines()[-1].split(' ')[1:]])

    return [ [file_mean(os.path.join(path, p)) for p in sorted([v for v in k[1]])] for k in groups ]


def generate_results_multiple(obj, groups, path, ms, alpha):
    def chunks(l, n):
        for i in xrange(0, len(l), n):
            yield l[i:i+n]

    def measurements(x):
        rs = [float('inf') if float(i) is float('nan') else float(i) for i in open(x, 'r').readlines()[-1].split(' ')[1:]]
        return [o * i for o, r in zip(obj, list(chunks(rs, ms))) for i in r]

    results = []
    for k in groups:
        ps = sorted([v for v in k[1]])
        one = zip(*[measurements(os.path.join(path, p)) for p in ps])
        results.extend(one)

    return results


def iteration(pars, settings, frace_settings, iteration):
    print 'Waiting for results...'

    while not all(os.path.exists(p) for p in par_filenames(iteration, pars, settings)):
        not_done = [p for p in par_filenames(iteration, pars, settings) if not os.path.exists(p)]
        if not_done:
            print 'Waiting for\n\t', '\n\t'.join(not_done)
        time.sleep(10)

    results, pars = generate_results(settings, frace_settings, iteration)

    while not all([len(i) == len(pars) for i in results]):
        results, pars = generate_results(settings, frace_settings, iteration)
        print 'Results not ready...'
        time.sleep(10)

    if len(results) >= frace_settings.min_probs * (len(settings.maximising) if type(settings.maximising) is list else 1) and len(pars) > 1:
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


def frace_runner(settings, frace_settings, ifrace_settings, skip=None):

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

        def run(i):
            return skip is None or (not skip is None and not i in skip)

        # if at beginning of a cylce generate all sims from now until discarding iteration
        if i == s_iter:
            for j in range(s_iter, min(frace_settings.iterations, m_iter)):
                run_script(generate_script(pars, [j], settings), settings.jar_path, settings.cmd, run(j))
                time.sleep(1)
        elif i >= m_iter: # if discarding iteration 
            run_script(generate_script(pars, [i], settings), settings.jar_path, settings.cmd, run(i))

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
        pars = sort_pars(*generate_results(settings, frace_settings, i))

        i += 1

        # write pars to result file
        results_file.write(str(i) + ' ' + ' '.join([par_to_result(p) for p in pars]) + '\n')
        results_file.flush()

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

