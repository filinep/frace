from frace import *
from parameters import *

# The order here coresponds to the tuning parameters below
parameter_bounds = [
(0.01,0.99),
(0.0,4.0),
(0.0,4.0)
]

algorithm = """def alg = new pso.PSO() {
  addStoppingCondition(new stoppingcondition.MeasuredStoppingCondition() { setTarget(100) })
  setInitialisationStrategy {
    new algorithm.initialisation.ClonedPopulationInitialisationStrategy() {
      setEntityType {
        new pso.particle.StandardParticle() {
          setVelocityProvider {
            new pso.velocityprovider.StandardVelocityProvider(
              new tuning.TuningControlParameter() { setIndex(0) },
              new tuning.TuningControlParameter() { setIndex(1) },
              new tuning.TuningControlParameter() { setIndex(2) }
            )
          }
        }
      }
    }
  }
}"""

problems = [
"""
def p = new problem.FunctionOptimisationProblem() {
  setDomain("R(-1:1)^10")
  setFunction(new functions.continuous.unconstrained.Spherical())
}
""",
"""
def p = new problem.FunctionOptimisationProblem() {
  setDomain("R(-1:1)^10")
  setFunction(new functions.continuous.unconstrained.Rosenbrock())
}
""",
"""
def p = new problem.FunctionOptimisationProblem() {
  setDomain("R(-1:1)^10")
  setFunction(new functions.continuous.unconstrained.Ackley())
}
""",
"""
def p = new problem.FunctionOptimisationProblem() {
  setDomain("R(-1:1)^10")
  setFunction(new functions.continuous.unconstrained.Rastrigin())
}
""",
"""
def p = new problem.FunctionOptimisationProblem() {
  setDomain("R(-1:1)^10")
  setFunction(new functions.continuous.unconstrained.Griewank())
}
"""
]

measurement = "new measurement.single.Fitness()"

ifrace_settings = IFraceSettings(is_iterative=True, interval=10, regenerator=regen_minmax_sobol(32))
frace_settings = FRaceSettings(generator=initial_sobol(parameter_bounds, 32), min_probs=5, min_solutions=2, alpha=0.05, iterations=100)
user_settings = UserSettings('user_name', 'job_name')
location_settings = LocationSettings('/home/filipe/tmp', '/home/filipe/tmp')
simulation = SimulationSettings(algorithm, problems, measurement, samples=30)
runner(user_settings, simulation, frace_settings, ifrace_settings, location_settings)

