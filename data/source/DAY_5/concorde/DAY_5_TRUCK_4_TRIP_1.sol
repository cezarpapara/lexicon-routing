Using Concorde/CPLEX
Input in TSPLIB format
Using fixed seed of 99
Executing on prod-exec-1.neos-server.org
concorde -f -s 99 -o results.txt concorde.dat
Host: prod-exec-1.neos-server.org  Current process id: 3354056
Using random seed 99
Problem Name: DAY_5_TRUCK_4_TRIP_1
Problem Type: TSP
Number of Nodes: 16
Explicit Lengths (CC_MATRIXNORM)
Set initial upperbound to 183807 (from tour)
  LP Value  1: 180210.000000  (0.00 seconds)
  LP Value  2: 183807.000000  (0.00 seconds)
New lower bound: 183807.000000
Final lower bound 183807.000000, upper bound 183807.000000
Exact lower bound: 183807.000000
DIFF: 0.000000
Final LP has 20 rows, 69 columns, 172 nonzeros
Optimal Solution: 183807.00
Number of bbnodes: 1
Total Running Time: 0.01 (seconds)


Solution file output:
16 16
0 13 14358
13 14 648
14 1 17716
1 2 28098
2 3 43938
3 4 11548
4 6 9003
6 5 8636
5 7 3185
7 8 429
8 10 6916
10 9 1947
9 11 16480
11 12 9264
12 15 5165
15 0 6476

