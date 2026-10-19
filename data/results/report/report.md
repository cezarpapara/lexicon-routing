# Results

## Real trips: mean over instances, change relative to the dispatcher's plan

| configuration | instances | distance_km | duration_h | waiting_h | monetary_cost_ron | penalty_h | composite_cost_ron | satisfaction_pct | binding_missed | runtime_s | dC_m_pct | dC_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Dispatcher | 18 | 110.09 | 4.09 | 0.0 | 865.89 | 0.0 | 865.89 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Nearest neighbour | 18 | 108.99 | 5.69 | 1.61 | 1065.15 | 1.28 | 1227.14 | 64.61 | 0.0 | 0.0 | 13.3 | 26.2 |
| Concorde | 18 | 99.53 | 5.58 | 1.58 | 1021.61 | 1.22 | 1175.51 | 73.13 | 0.0 | 0.0 | 9.4 | 21.3 |
| OR-Tools (windows) | 18 | 100.16 | 3.98 | 0.0 | 821.73 | 0.74 | 914.94 | 73.28 | 0.0 | 30.01 | -4.9 | 3.2 |
| Adaptive heuristic (2025) | 18 | 118.38 | 4.72 | 0.45 | 972.0 | 1.2 | 1123.69 | 65.66 | 0.0 | 0.0 | 6.3 | 18.6 |
| Proposed | 18 | 102.54 | 4.02 | 0.0 | 833.68 | 0.08 | 843.91 | 86.32 | 0.0 | 0.0 | -4.2 | -2.1 |

## Real trips: preference satisfaction by band (% of stated intervals met)

| configuration | flexible | mild | strong | binding |
|---|---|---|---|---|
| Dispatcher | - | 100.0 (30/30) | 100.0 (33/33) | 100.0 (29/29) |
| Nearest neighbour | - | 26.7 (8/30) | 54.5 (18/33) | 100.0 (29/29) |
| Concorde | - | 50.0 (15/30) | 60.6 (20/33) | 100.0 (29/29) |
| OR-Tools (windows) | - | 53.3 (16/30) | 66.7 (22/33) | 100.0 (29/29) |
| Adaptive heuristic (2025) | - | 30.0 (9/30) | 54.5 (18/33) | 100.0 (29/29) |
| Proposed | - | 86.7 (26/30) | 78.8 (26/33) | 100.0 (29/29) |

## Synthetic instances: mean over seeds per size, change relative to OR-Tools

### 25 stops (3 instances)

| configuration | instances | distance_km | duration_h | waiting_h | monetary_cost_ron | penalty_h | composite_cost_ron | satisfaction_pct | binding_missed | runtime_s | dC_m_pct | dC_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nearest neighbour | 3 | 278.87 | 25.43 | 12.98 | 4101.2 | 3.96 | 4601.94 | 61.1 | 0.0 | 0.0 | 71.5 | 45.5 |
| Concorde | 3 | 223.59 | 19.78 | 8.56 | 3211.23 | 4.92 | 3833.72 | 64.27 | 0.0 | 0.0 | 35.4 | 21.9 |
| OR-Tools (windows) | 3 | 249.13 | 12.42 | 0.63 | 2361.34 | 6.38 | 3168.6 | 58.87 | 0.0 | 30.02 | 0.0 | 0.0 |
| Adaptive heuristic (2025) | 3 | 323.3 | 18.5 | 5.07 | 3365.54 | 8.92 | 4494.48 | 50.6 | 0.0 | 0.0 | 43.6 | 42.7 |
| Proposed | 3 | 279.02 | 13.04 | 0.59 | 2534.97 | 1.19 | 2685.04 | 80.33 | 0.0 | 0.01 | 8.2 | -15.4 |

### 50 stops (3 instances)

| configuration | instances | distance_km | duration_h | waiting_h | monetary_cost_ron | penalty_h | composite_cost_ron | satisfaction_pct | binding_missed | runtime_s | dC_m_pct | dC_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nearest neighbour | 3 | 411.65 | 34.66 | 13.01 | 5689.87 | 13.35 | 7379.37 | 65.27 | 0.0 | 0.0 | 56.8 | 38.2 |
| Concorde | 3 | 324.26 | 38.49 | 18.78 | 5897.29 | 10.46 | 7220.57 | 59.93 | 0.0 | 0.0 | 62.5 | 35.7 |
| OR-Tools (windows) | 3 | 344.63 | 20.16 | 0.0 | 3642.88 | 13.44 | 5343.44 | 59.3 | 0.0 | 30.03 | 0.0 | 0.0 |
| Adaptive heuristic (2025) | 3 | 492.94 | 24.61 | 1.16 | 4676.79 | 14.35 | 6492.38 | 54.03 | 0.0 | 0.0 | 28.2 | 21.9 |
| Proposed | 3 | 362.28 | 20.55 | 0.0 | 3748.42 | 7.74 | 4727.75 | 72.73 | 0.0 | 0.05 | 3.0 | -10.8 |

### 100 stops (3 instances)

| configuration | instances | distance_km | duration_h | waiting_h | monetary_cost_ron | penalty_h | composite_cost_ron | satisfaction_pct | binding_missed | runtime_s | dC_m_pct | dC_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nearest neighbour | 3 | 528.27 | 73.92 | 37.19 | 11027.52 | 24.51 | 14129.22 | 63.37 | 0.0 | 0.0 | 74.6 | 53.6 |
| Concorde | 3 | 409.74 | 71.99 | 37.89 | 10407.27 | 28.18 | 13972.78 | 57.8 | 0.0 | 0.0 | 64.3 | 52.1 |
| OR-Tools (windows) | 3 | 486.14 | 37.53 | 1.73 | 6289.86 | 23.09 | 9210.95 | 60.87 | 0.67 | 30.11 | 0.0 | 0.0 |
| Adaptive heuristic (2025) | 3 | 657.17 | 45.91 | 6.31 | 7892.36 | 23.71 | 10891.8 | 62.77 | 0.33 | 0.0 | 25.2 | 18.4 |
| Proposed | 3 | 596.17 | 38.8 | 0.55 | 6798.69 | 6.16 | 7578.64 | 78.8 | 0.67 | 1.31 | 8.2 | -17.7 |

### 250 stops (3 instances)

| configuration | instances | distance_km | duration_h | waiting_h | monetary_cost_ron | penalty_h | composite_cost_ron | satisfaction_pct | binding_missed | runtime_s | dC_m_pct | dC_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nearest neighbour | 3 | 687.94 | 173.41 | 95.62 | 24120.42 | 74.41 | 33533.93 | 56.47 | 2.0 | 0.0 | 68.3 | 43.5 |
| Concorde | 3 | 547.69 | 173.86 | 99.19 | 23732.57 | 74.34 | 33138.45 | 55.47 | 1.67 | 0.0 | 66.0 | 41.6 |
| OR-Tools (windows) | 3 | 917.85 | 90.06 | 7.16 | 14303.65 | 71.99 | 23411.33 | 56.17 | 1.67 | 30.41 | 0.0 | 0.0 |
| Adaptive heuristic (2025) | 3 | 1007.46 | 93.06 | 8.17 | 14967.28 | 72.57 | 24149.11 | 57.33 | 1.67 | 0.0 | 4.5 | 3.3 |
| Proposed | 3 | 1113.26 | 90.17 | 2.93 | 14937.62 | 23.76 | 17944.36 | 81.03 | 2.0 | 15.56 | 4.5 | -23.3 |

### 500 stops (3 instances)

| configuration | instances | distance_km | duration_h | waiting_h | monetary_cost_ron | penalty_h | composite_cost_ron | satisfaction_pct | binding_missed | runtime_s | dC_m_pct | dC_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nearest neighbour | 3 | 792.35 | 313.76 | 171.15 | 42208.62 | 135.09 | 59300.18 | 59.17 | 0.33 | 0.01 | 76.5 | 49.8 |
| Concorde | 3 | 634.57 | 314.95 | 175.85 | 41858.78 | 131.33 | 58474.25 | 59.17 | 0.67 | 0.0 | 75.0 | 47.6 |
| OR-Tools (windows) | 3 | 1194.0 | 159.15 | 7.61 | 23920.08 | 124.11 | 39623.32 | 60.5 | 1.33 | 31.38 | 0.0 | 0.0 |
| Adaptive heuristic (2025) | 3 | 1240.56 | 159.15 | 6.57 | 24067.67 | 124.61 | 39832.48 | 60.53 | 1.67 | 0.01 | 0.6 | 0.5 |
| Proposed | 3 | 1331.42 | 157.17 | 2.59 | 24105.8 | 52.86 | 30794.08 | 77.8 | 1.67 | 129.26 | 0.7 | -22.2 |

### 1000 stops (3 instances)

| configuration | instances | distance_km | duration_h | waiting_h | monetary_cost_ron | penalty_h | composite_cost_ron | satisfaction_pct | binding_missed | runtime_s | dC_m_pct | dC_pct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nearest neighbour | 3 | 966.9 | 613.95 | 342.46 | 80742.06 | 278.13 | 115931.47 | 60.0 | 3.67 | 0.03 | 83.3 | 49.1 |
| Concorde | 3 | 737.99 | 649.37 | 382.97 | 84497.49 | 284.16 | 120449.43 | 60.43 | 3.33 | 0.0 | 92.0 | 54.9 |
| OR-Tools (windows) | 3 | 1728.75 | 304.56 | 16.14 | 44012.85 | 266.55 | 77736.4 | 58.6 | 5.33 | 35.08 | 0.0 | 0.0 |
| Adaptive heuristic (2025) | 3 | 1752.58 | 304.56 | 15.61 | 44088.37 | 267.58 | 77942.62 | 58.33 | 6.33 | 0.1 | 0.2 | 0.3 |
| Proposed | 3 | 2025.63 | 310.56 | 15.54 | 45713.07 | 127.09 | 61793.16 | 73.1 | 5.67 | 600.58 | 3.8 | -20.5 |

## Ablation: mean over instances

| variant | instances | composite_cost_ron | monetary_cost_ron | penalty_h | satisfaction_pct | binding_missed | runtime_s |
|---|---|---|---|---|---|---|---|
| OR-Tools baseline (no refinement) | 22 | 2047.28 | 1550.16 | 3.93 | 70.7 | 0.09 | 30.02 |
| Proposed, full | 22 | 1757.1 | 1615.97 | 1.12 | 86.01 | 0.09 | 0.2 |
| Start from OR-Tools only | 22 | 1769.67 | 1621.57 | 1.17 | 84.49 | 0.09 | 0.2 |
| Start from the dispatcher's sequence only | 19 | 841.73 | 834.57 | 0.06 | 89.92 | 0.0 | 0.0 |
| Start from nearest neighbour only | 22 | 2172.17 | 2031.03 | 1.12 | 84.7 | 0.05 | 0.17 |
| No 2-opt phase | 22 | 1812.08 | 1660.1 | 1.2 | 87.99 | 0.09 | 0.01 |
| Relocate and 2-opt only (no swap) | 22 | 1772.16 | 1634.18 | 1.09 | 86.54 | 0.09 | 0.14 |
| Swap and 2-opt only (no relocate) | 22 | 1849.98 | 1611.75 | 1.88 | 85.68 | 0.14 | 0.07 |
| 2-opt only (no preference moves) | 22 | 1809.43 | 1641.71 | 1.33 | 86.09 | 0.05 | 0.14 |
| Unranked candidates | 22 | 1778.63 | 1635.27 | 1.13 | 86.38 | 0.09 | 0.18 |
| Unweighted violations (u_i = 1) | 22 | 1867.97 | 1827.22 | 0.32 | 92.7 | 0.05 | 0.15 |
| Penalty rate lambda = 0.5 c_t in the search | 22 | 1733.93 | 1605.0 | 1.02 | 86.23 | 0.09 | 0.07 |
| Penalty rate lambda = 2 c_t in the search | 22 | 1789.75 | 1669.78 | 0.95 | 91.56 | 0.09 | 0.17 |
| Oracle extraction (reference labels) | 22 | 1714.7 | 1652.23 | 0.49 | 88.78 | 0.0 | 0.11 |
| LLM extraction (gemini-3.8-flash) | 22 | 1757.66 | 1600.72 | 1.24 | 90.79 | 0.0 | 0.06 |

## Extraction quality on the corpus

| extractor | messages | reference | precision | recall | f1 | boundary_mae_min | spearman | band_accuracy |
|---|---|---|---|---|---|---|---|---|
| lexicon | 250 | annotation | 0.994 | 0.994 | 0.994 | 10.4 | 0.962 | 0.944 |
| llm | 250 | annotation | 1.0 | 0.994 | 0.997 | 0.0 | 0.979 | 0.928 |
