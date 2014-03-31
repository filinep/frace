frace
=====
1) Dependencies:
- scipy
- python 2.7

2) Installation:
- run:
    [sudo] python2 setup/py install
- It is possible to run a job without installing the files. In that case place the xml file on the same
  level as the frace folder, e.g. xml_frace_example.py

3) TODO:
- split samples thingy
- maximisation/minimisation (sort of done, but can't mix max/min problems e.g. for fitness measurement)
- other regenerators
- close ranks/no removals stopping condition

4) Before running a job:
- Make sure the correct locations for the jar file and base location are set:
    If the job is being uploaded to the cluster the location should be "/SAN/pleiades/results/frace"
- Double check the settings!!!
