Using Concorde/CPLEX
Input in TSPLIB format
Using fixed seed of 99
Executing on prod-exec-6.neos-server.org
concorde -f -s 99 -o results.txt concorde.dat
Host: prod-exec-6.neos-server.org  Current process id: 2854224
Using random seed 99
Problem Name: SYN_50_1
Problem Type: TSP
edge weights = road metres / 1
Number of Nodes: 51
Explicit Lengths (CC_MATRIXNORM)
Set initial upperbound to 345857 (from tour)
  LP Value  1: 331117.000000  (0.00 seconds)
  LP Value  2: 342808.000000  (0.01 seconds)
  LP Value  3: 345428.000000  (0.02 seconds)
  LP Value  4: 345857.000000  (0.03 seconds)
New lower bound: 345857.000000
Final lower bound 345857.000000, upper bound 345857.000000
Exact lower bound: 345857.000000
DIFF: 0.000000
Final LP has 83 rows, 270 columns, 1402 nonzeros
Optimal Solution: 345857.00
Number of bbnodes: 1
Total Running Time: 0.10 (seconds)


Solution file output:
51 51
0 27 4160
27 36 2045
36 12 970
12 48 3908
48 43 1170
43 14 1038
14 49 4198
49 19 557
19 7 2522
7 45 830
45 29 173
29 6 27855
6 1 17685
1 46 17144
46 11 1505
11 21 3996
21 2 7710
2 34 8506
34 17 12786
17 8 11591
8 16 18837
16 22 17584
22 32 989
32 30 1018
30 3 26851
3 15 26887
15 47 1826
47 40 1004
40 41 13449
41 18 17839
18 24 5089
24 5 1242
5 25 253
25 31 1308
31 35 4042
35 50 9380
50 42 4779
42 38 9361
38 26 4224
26 28 6792
28 44 628
44 33 3604
33 4 7429
4 37 6849
37 10 5646
10 23 466
23 20 6986
20 13 5922
13 39 471
39 9 1259
9 0 3494

