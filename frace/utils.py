import os
import re

from numpy import array
from scipy.stats.mstats import rankdata

def par_to_num(a):
    '''
    Converts a parameter configuration string into a list of numbers
    '''

    return [float(i) for i in a.replace('___', '.').split('_')]


def par_to_result(a):
    '''
    Converts a parameter configuration string into a result measurement
    '''

    return '[' + a.replace('___', '.').replace('_', ',') + ']'


def num_to_par(p):
    '''
    Converts a list of numbers into a parameter configuration string
    '''

    return '_'.join([str(j) for j in p]).replace('.', '___')


def par_filename(iteration, p, location):
    '''
    Creates a file path for a given parameter/iteration combination
    '''
    
    return os.path.join(location.results_location, str(iteration) + '_' + p + '.txt')


def par_filenames(iteration, pars, location):
    '''
    Creates a list of file paths for the given parameters
    '''

    return [ par_filename(iteration, p, location) for p in pars ]


def sort_pars(results, pars):
    '''
    Sorts the parameters in order of performance according to results
    '''

    return [i[1] for i in sorted(zip(list(sum(rankdata(array(results), axis=1))),pars))]


def def_name(s):
    '''
    Retrieves the scala def name for a given scala def
    '''

    return re.search(r'def(.*?)=', s).group(1).strip()


def id_name(s):
    try:
        return re.search(r'class=".*?" id="(.*?)"', s).group(1).strip()
    except:
        return re.search(r'id="(.*?)" class', s).group(1).strip()


def get_algorithm_string(algorithm_path):
    with open(algorithm_path) as f:
        s = f.read().replace('\n', '')

    return re.findall(r'<algorithm\s.*</algorithm>', s)[0]

def get_problem_strings(problems_path):
    with open(problems_path) as f:
        s = f.read().replace('\n', '')

    return [i + '</problem>' for i in re.findall(r'<problem\s.*</problem>', s)[0].split('</problem>')[:-1]]
