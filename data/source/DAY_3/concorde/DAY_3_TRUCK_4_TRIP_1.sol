Using Concorde/CPLEX
Input in TSPLIB format
Using fixed seed of 99
Executing on prod-exec-1.neos-server.org
concorde -f -s 99 -o results.txt concorde.dat
Host: prod-exec-1.neos-server.org  Current process id: 3356048
Using random seed 99
Problem Name: DAY_3_TRUCK_4_TRIP_1
Problem Type: TSP
Number of Nodes: 16
Explicit Lengths (CC_MATRIXNORM)
Set initial upperbound to 190599 (from tour)
  LP Value  1: 140571.000000  (0.00 seconds)
  LP Value  2: 181872.000000  (0.00 seconds)
  LP Value  3: 185740.000000  (0.00 seconds)
  LP Value  4: 190599.000000  (0.01 seconds)
New lower bound: 190599.000000
Final lower bound 190599.000000, upper bound 190599.000000
Exact lower bound: 190599.000000
DIFF: 0.000000
Final LP has 29 rows, 59 columns, 233 nonzeros
Optimal Solution: 190599.00
Number of bbnodes: 1
Total Running Time: 0.01 (seconds)


Solution file output:
16 16
0 15 3455
15 13 6468
13 11 141
11 12 2273
12 10 16051
10 8 7889
8 1 11104
1 2 4399
2 3 4456
3 4 35078
4 5 29990
5 7 4508
7 6 1275
6 9 25696
9 14 29890
14 0 7926

