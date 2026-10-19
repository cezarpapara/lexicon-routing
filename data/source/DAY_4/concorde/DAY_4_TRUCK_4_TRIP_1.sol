Using Concorde/CPLEX
Input in TSPLIB format
Using fixed seed of 99
Executing on prod-exec-1.neos-server.org
concorde -f -s 99 -o results.txt concorde.dat
Host: prod-exec-1.neos-server.org  Current process id: 3356505
Using random seed 99
Problem Name: DAY_4_TRUCK_4_TRIP_1
Problem Type: TSP
Number of Nodes: 13
Explicit Lengths (CC_MATRIXNORM)
Set initial upperbound to 174511 (from tour)
  LP Value  1: 173468.000000  (0.00 seconds)
  LP Value  2: 174511.000000  (0.00 seconds)
New lower bound: 174511.000000
Final lower bound 174511.000000, upper bound 174511.000000
Exact lower bound: 174511.000000
DIFF: 0.000000
Final LP has 14 rows, 49 columns, 103 nonzeros
Optimal Solution: 174511.00
Number of bbnodes: 1
Total Running Time: 0.00 (seconds)


Solution file output:
13 13
0 10 25502
10 11 967
11 9 13475
9 8 3509
8 6 15922
6 7 3523
7 5 30938
5 4 15270
4 3 10254
3 2 15422
2 1 8428
1 12 16337
12 0 14964

