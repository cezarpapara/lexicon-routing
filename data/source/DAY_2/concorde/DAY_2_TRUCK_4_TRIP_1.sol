Using Concorde/CPLEX
Input in TSPLIB format
Using fixed seed of 99
Executing on prod-exec-7.neos-server.org
concorde -f -s 99 -o results.txt concorde.dat
Host: prod-exec-7.neos-server.org  Current process id: 3066900
Using random seed 99
Problem Name: DAY_2_TRUCK_4_TRIP_1
Problem Type: TSP
Number of Nodes: 13
Explicit Lengths (CC_MATRIXNORM)
Set initial upperbound to 173987 (from tour)
  LP Value  1: 153542.000000  (0.00 seconds)
  LP Value  2: 173890.000000  (0.00 seconds)
  LP Value  3: 173987.000000  (0.00 seconds)
New lower bound: 173987.000000
Final lower bound 173987.000000, upper bound 173987.000000
Exact lower bound: 173987.000000
DIFF: 0.000000
Final LP has 21 rows, 39 columns, 120 nonzeros
Optimal Solution: 173987.00
Number of bbnodes: 1
Total Running Time: 0.01 (seconds)


Solution file output:
13 13
0 5 22730
5 2 29083
2 1 8274
1 4 37393
4 3 13249
3 6 22664
6 11 13566
11 8 4833
8 7 1960
7 9 5846
9 10 6157
10 12 4212
12 0 4020

