frace
=====
1) Dependencies:
- scipy

2) TODO
- split samples thingy
- maximisation/minimisation (sort of done, but can't mix max/min problems e.g. for fitness measurement)
- other regenerators
- close ranks/no removals stopping condition

3) Before running a job
- Make sure the run_script method at the end of xml_runner.py has the correct run command.
- Make sure the correct locations for the jar file and base location are set:
    If the job is being uploaded to the cluster the location should be "/SAN/pleiades/results/frace"
- Double check the settings!!!
