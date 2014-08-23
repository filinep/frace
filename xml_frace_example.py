from frace import frace, parameters
from frace.frace import *
from frace.parameters import *

# The order here corresponds to the tuning parameters below
parameter_bounds = [
(0.01,0.99),
(0.0,4.0),
(0.0,4.0),
(10,50)
]

algorithm = """<algorithm id="pso" class="pso.PSO">
    <initialisationStrategy class="algorithm.initialisation.ClonedPopulationInitialisationStrategy">
        <entityType class="pso.particle.StandardParticle">
            <behaviour class="pso.behaviour.StandardParticleBehaviour">
                <velocityProvider class="pso.velocityprovider.StandardVelocityProvider">
                    <inertiaWeight class="tuning.TuningControlParameter" index="0"/>
                    <cognitiveAcceleration class="tuning.TuningControlParameter" index="1"/>
                    <socialAcceleration class="tuning.TuningControlParameter" index="2"/>
                </velocityProvider>
            </behaviour>
        </entityType>
        <entityNumber value="$int_index=3$"/>
    </initialisationStrategy>
    <addStoppingCondition class="stoppingcondition.MeasuredStoppingCondition" target="100"/>
</algorithm>"""

problems = [
'''<problem id="f1" class="problem.FunctionOptimisationProblem" domain="R(-100:100)^10">
    <function class="functions.continuous.unconstrained.Spherical"/>
</problem>''',

'''<problem id="f2" class="problem.FunctionOptimisationProblem" domain="R(-100:100)^10">
    <function class="functions.continuous.unconstrained.Rosenbrock"/>
</problem>''',

'''<problem id="f3" class="problem.FunctionOptimisationProblem" domain="R(0:600)^10">
    <function class="functions.continuous.unconstrained.Griewank"/>
</problem>''',

'''<problem id="f4" class="problem.FunctionOptimisationProblem" domain="R(-32:32)^10">
    <function class="functions.continuous.unconstrained.Ackley"/>
</problem>''',

'''<problem id="f5" class="problem.FunctionOptimisationProblem" domain="R(-5:5)^10">
    <function class="functions.continuous.unconstrained.Rastrigin"/>
</problem>'''
]

measurement = '''
<addMeasurement class="measurement.single.Fitness"/>
<addMeasurement class="measurement.single.diversity.Diversity"/>
'''

samples = 1

ifrace_settings = IFraceSettings(
    is_iterative=True, 
    interval=10, 
    regenerator=regen_minmax_sobol(32)
)

frace_settings = FRaceSettings(
    generator=initial_sobol(parameter_bounds, 32), 
    min_probs=5, 
    min_solutions=2, 
    alpha=0.05, 
    iterations=30
)

#use this to run locally
settings = GeneralSettings(
    algorithm=algorithm,
    problems=problems,
    measure=measurement,
    samples=samples,
    resolution=5000,
    maximising=[False,False],
    user='USER_NAME',
    job='JOB',
    base_location='./test',
    jar_path='./cilib-simulator-assembly-0.9-SNAPSHOT.jar',
    cmd='java -jar %s %s' # add extra jvm options if needed
)

#use this to upload to cluster
#settings = GeneralSettings(
#    algorithm=algorithm,
#    problems=problems,
#    measure=measurement,
#    samples=samples,
#    resolution=5000,
#    maximising=[False,False],
#    user='filinep',
#    job='gbest_test',
#    base_location='/SAN/pleiades/results/filinep',
#    jar_path='./cilib-simulator-assembly-0.9-SNAPSHOT.jar',
#    cmd='/home/pleiades/NewPleiades/upload.py -u filinep -j %s -i %s -t custom'
#)

frace_runner(settings, frace_settings, ifrace_settings)

