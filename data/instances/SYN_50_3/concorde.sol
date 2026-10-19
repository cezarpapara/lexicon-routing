Using Concorde/CPLEX
Input in TSPLIB format
Using fixed seed of 99
Executing on prod-exec-1.neos-server.org
concorde -f -s 99 -o results.txt concorde.dat
Host: prod-exec-1.neos-server.org  Current process id: 478947
Using random seed 99
Problem Name: SYN_50_3
Problem Type: TSP
edge weights = road metres / 1
Number of Nodes: 51
Explicit Lengths (CC_MATRIXNORM)
Set initial upperbound to 288141 (from tour)
  LP Value  1: 253692.500000  (0.01 seconds)
  LP Value  2: 286869.500000  (0.01 seconds)
  LP Value  3: 288015.000000  (0.03 seconds)
  LP Value  4: 288141.000000  (0.04 seconds)
New lower bound: 288141.000000
Final lower bound 288141.000000, upper bound 288141.000000
Exact lower bound: 288141.000000
DIFF: 0.000000
Final LP has 77 rows, 279 columns, 1095 nonzeros
Optimal Solution: 288141.00
Number of bbnodes: 1
Total Running Time: 0.14 (seconds)


Solution file output:
51 51
0 31 6637
31 28 6665
28 35 1020
35 6 721
6 21 171
21 12 228
12 34 5556
34 50 634
50 22 5573
22 9 6262
9 36 8057
36 5 11278
5 11 5888
11 49 22319
49 48 10547
48 44 11329
44 37 3396
37 17 9074
17 15 1879
15 30 32845
30 42 13625
42 38 15299
38 7 26279
7 43 18676
43 13 500
13 14 448
14 16 13091
16 32 17002
32 23 112
23 10 582
10 20 2027
20 25 2556
25 8 4704
8 18 1343
18 41 127
41 19 2004
19 39 1013
39 1 559
1 3 622
3 4 433
4 40 246
40 45 887
45 47 1010
47 2 168
2 46 1198
46 26 1399
26 29 3778
29 24 2634
24 33 700
33 27 1171
27 0 3869

