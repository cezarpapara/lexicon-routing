Using Concorde/CPLEX
Input in TSPLIB format
Using fixed seed of 99
Executing on prod-exec-6.neos-server.org
concorde -f -s 99 -o results.txt concorde.dat
Host: prod-exec-6.neos-server.org  Current process id: 2855231
Using random seed 99
Problem Name: SYN_50_2
Problem Type: TSP
edge weights = road metres / 1
Number of Nodes: 51
Explicit Lengths (CC_MATRIXNORM)
Set initial upperbound to 338776 (from tour)
  LP Value  1: 320600.500000  (0.01 seconds)
  LP Value  2: 333307.250000  (0.02 seconds)
  LP Value  3: 338051.714286  (0.04 seconds)
  LP Value  4: 338621.500000  (0.05 seconds)
  LP Value  5: 338776.000000  (0.05 seconds)
New lower bound: 338776.000000
Final lower bound 338776.000000, upper bound 338776.000000
Exact lower bound: 338776.000000
DIFF: 0.000000
Final LP has 86 rows, 184 columns, 976 nonzeros
Optimal Solution: 338776.00
Number of bbnodes: 1
Total Running Time: 0.14 (seconds)


Solution file output:
51 51
0 4 3533
4 39 915
39 38 1401
38 11 400
11 41 394
41 36 267
36 8 266
8 29 3425
29 35 1949
35 31 1448
31 49 739
49 18 1294
18 45 5226
45 26 1011
26 9 13284
9 46 9706
46 33 10745
33 14 9138
14 40 20361
40 34 37236
34 1 16937
1 25 8818
25 47 15787
47 6 16166
6 12 1881
12 3 14333
3 44 630
44 16 16165
16 7 11117
7 42 21433
42 50 1844
50 21 8270
21 20 3481
20 17 777
17 13 2992
13 30 4993
30 32 668
32 19 7203
19 43 7395
43 2 12440
2 28 6035
28 37 706
37 10 3929
10 23 705
23 24 7359
24 27 1211
27 15 10558
15 48 683
48 22 7043
22 5 3675
5 0 804

