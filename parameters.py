import random

from sobol import i4_sobol_generate
from utils import *

# Parameter generators for FFD
def parameter_specific(values):
    '''
    Returns the given values - used when specific values are needed for parameters

    values: list of numbers
    '''

    return lambda: values


def parameter_random(bounds, count):
    '''
    Returns count values randomly generated within bounds
    NOTE: upper bound is never reached

    bounds: tuple or list containing a lower and upper bound (l, u)
    count: number of parameters to generate
    '''

    return lambda: [random.random() * (bounds[1] - bounds[0]) + bounds[0] for i in range(count)]


def parameter_uniform(bounds, count):
    '''
    Returns count equallyspaced values within the bounds
    NOTE: upper bound is never reached

    bounds: tuple or list containing a lower and upper bound (l, u)
    count: number of parameters to generate
    '''

    return lambda: [float(i) * (bounds[1] - bounds[0])/count + bounds[0] for i in range(count)]


# Configuration generators for initial parameters
# NOTE: these dunctions return parameter *names*, i.e. one string made from a configuration because 
#       it is a bad idea to keep converting from strings to values and back due to representation errors
def initial_ffd(par_gens):
    '''
    Generates all combinations of parameters created with the given generators
    NOTE: the above generators create different values for one parameter

    par_gens: list of parameter generators
    '''

    return lambda: [parameter_name(i) for i in product(*[p() for p in par_gens])]


def initial_sobol(bounds, count):
    '''
    Generates count parameter configurations using a sobol sequence
    NOTE: the upper bounds are never reached

    bounds: list of tuples (or lists) containing lower and upper bounds [(l1,u1), ..., (ln,un)]
    count: number of configurations to generate
    '''
    print bounds, count
    return lambda: [parameter_name([i[j] * (bounds[j][1] - bounds[j][0]) + bounds[j][0] for j in range(len(bounds))]) 
        for i in i4_sobol_generate(len(bounds), int(count), 2).T]


# Configuration regenerators for iterated F-Race
def regen_minmax_sobol(count):
    '''
    Gets the min and max for each parameter from the surviving configurations 
    and generates count parameter configurations using a sobol sequence within the min/max bounds

    count: number of new configurations to generate
    '''

    def regen(pars):
        fPars = [par_to_num(p) for p in pars]
        return initial_sobol([(min(p[i] for p in fPars), max(p[i] for p in fPars)) for i in range(len(fPars[0]))], count)()

    return regen
