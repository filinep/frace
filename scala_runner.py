import os
import re
import subprocess

from utils import *

import_section = '''import net.cilib.simulator.Simulation._
import net.sourceforge.cilib._
'''

measurement_section = '''def m_frace = new simulator.MeasurementSuite() {
  addMeasurement($1)
}
'''


def generate_script(pars, iteration, simulation_settings, user_settings, location_settings):
    '''
    Function to generate a script file given certain elements
    NOTE: Change this as needed
    '''

    script_filename = os.path.join(location_settings.base_location, user_settings.user, user_settings.job + '.scala')
    script = open(script_filename, 'w')

    problem = simulation_settings.problems.pop(0)
    simulation_settings.problems.append(problem)

    algorithms = ''
    runners = ''

    # TODO: it kinda sucks doing it this way, jython? :)
    for p in pars:
        algorithm = simulation_settings.algorithm

        config = par_to_num(p)
        for i in range(len(config)):
            algorithm = algorithm.replace(
                'new tuning.TuningControlParameter() { setIndex(%d) }' % i, 
                'controlparameter.ConstantControlParameter.of(%f)' % config[i]
            )

        algorithms += algorithm.replace(def_name(simulation_settings.algorithm), 'alg_' + p, 1) + '\n'

        runners += 'runner(simulation(alg_' + p + ', ' + def_name(problem) + '), m_frace, "' + \
            parameter_filename(user_settings.user, user_settings.job, iteration, p, location_settings.results_location) + \
            '" ,' + str(simulation_settings.samples) + ', 5000)' + '\n'
        # XXX: 'alg' and 'prob' must be used

    script.write(import_section + '\n')
    script.write(measurement_section.replace('$1', simulation_settings.measurement) + '\n')
    script.write(problem + '\n')
    script.write(algorithms + '\n')
    script.write(runners)

    script.close()
    return script_filename


def run_script(script):
    '''
    Function to run a given script
    '''

    subprocess.call(['cilib', script])
