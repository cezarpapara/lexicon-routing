Using Concorde/CPLEX
Input in TSPLIB format
Using fixed seed of 99
Executing on prod-exec-7.neos-server.org
concorde -f -s 99 -o results.txt concorde.dat
Host: prod-exec-7.neos-server.org  Current process id: 3065297
Using random seed 99
Problem Name: DAY_5_TRUCK_2_TRIP_1
Problem Type: TSP
Number of Nodes: 10
Explicit Lengths (CC_MATRIXNORM)
Set initial upperbound to 164398 (from tour)
  LP Value  1: 145055.000000  (0.00 seconds)
  LP Value  2: 164398.000000  (0.00 seconds)
New lower bound: 164398.000000
Final lower bound 164398.000000, upper bound 164398.000000
Exact lower bound: 164398.000000
DIFF: 0.000000
Final LP has 15 rows, 27 columns, 72 nonzeros
Optimal Solution: 164398.00
Number of bbnodes: 1
Total Running Time: 0.01 (seconds)


Solution file output:
10 10
0 8 18418
8 7 13994
7 6 7487
6 5 900
5 2 29950
2 1 18061
1 3 14431
3 4 28064
4 9 23115
9 0 9978

