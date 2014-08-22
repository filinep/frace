import os
import re
import sys

from subprocess import *
from utils import *

header_section = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE simulator [
<!ATTLIST algorithm id ID #IMPLIED>
<!ATTLIST problem id ID #IMPLIED>
<!ATTLIST measurements id ID #IMPLIED>
]>
<simulator>
'''

simulation = '''
<simulation samples="$4">
    <algorithm idref="$1"/>
    <problem idref="$2"/>
    <measurements idref="m_frace" />
    <output format="TXT" file="$3"/>
</simulation>
'''

def generate_script(pars, iterations, settings):
    '''
    Function to generate a script file given certain elements
    NOTE: Change this as needed
    '''

    script_filename = os.path.join(settings.base_location, settings.user, settings.user + '_' + settings.job + '.xml')
    script = open(script_filename, 'w')

    algorithms = ''
    problems = ''
    sims = ''

    for p in pars:
        algorithm = settings.algorithm

        config = par_to_num(p)
        for i in range(len(config)):
            algorithm = algorithm.replace(
                'tuning.TuningControlParameter" index="%d"' % i, 
                'controlparameter.ConstantControlParameter" parameter="%f"' % config[i]
            ).replace(
                '$int_index=%d$' % i, str(int(config[i]))
            ).replace(
                '$double_index=%d$' % i, str(config[i])
            )

        algorithms += algorithm.replace(id_name(settings.algorithm), 'alg_' + p, 1) + '\n'

    for iteration in iterations:
        problem = settings.problems.pop(0)
        settings.problems.append(problem)

        if not problem in problems:
            problems += problem

        for p in pars:
            sims += simulation.replace('$1', 'alg_' + p).replace('$2', id_name(problem)) \
                                                        .replace('$3', par_filename(iteration, p, settings)) \
                                                        .replace('$4', str(settings.samples))

    script.write(header_section + '\n')
    script.write('<measurements id="m_frace" class="simulator.MeasurementSuite" resolution="%i">\n' % (settings.resolution) + \
                 settings.measurement + '</measurements>\n')
    script.write('<problems>' + problems + '</problems>\n')
    script.write('<algorithms>' + algorithms + '</algorithms>\n')
    script.write('<simulations>' + sims + '</simulations>')
    script.write('</simulator>')

    script.close()
    return script_filename


def run_script(script, jar_path, cmd, run=True):
    '''
    Function to run a given script
    '''
    if not run: return
    print "~~~ Starting process ~~~"
    process = Popen((cmd % (jar_path, script)).split(' '))
    process.wait()
    if process.returncode:
        print "Error running process: Exiting"
        sys.exit(1)
    print "~~~ Process complete ~~~"
