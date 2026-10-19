Using Concorde/CPLEX
Input in TSPLIB format
Using fixed seed of 99
Executing on prod-exec-7.neos-server.org
concorde -f -s 99 -o results.txt concorde.dat
Host: prod-exec-7.neos-server.org  Current process id: 3064046
Using random seed 99
Problem Name: DAY_1_TRUCK_4_TRIP_1
Problem Type: TSP
Number of Nodes: 14
Explicit Lengths (CC_MATRIXNORM)
Set initial upperbound to 176228 (from tour)
  LP Value  1: 128259.000000  (0.00 seconds)
  LP Value  2: 174775.000000  (0.00 seconds)
  LP Value  3: 176228.000000  (0.00 seconds)
New lower bound: 176228.000000
Final lower bound 176228.000000, upper bound 176228.000000
Exact lower bound: 176228.000000
DIFF: 0.000000
Final LP has 21 rows, 58 columns, 158 nonzeros
Optimal Solution: 176228.00
Number of bbnodes: 1
Total Running Time: 0.01 (seconds)


Solution file output:
14 14
0 13 3932
13 12 6377
12 3 28772
3 1 26508
1 2 1849
2 4 38758
4 5 334
5 7 16376
7 6 2065
6 11 4342
11 10 6930
10 8 4427
8 9 3698
9 0 31860

