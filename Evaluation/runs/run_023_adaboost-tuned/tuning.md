# Hyperparameter search - run_023_adaboost-tuned

6991 recordings, 14 classes, 5 folds, feature set `native150`, level `task`, balance `none`, labels `csv:labels/labels_v3.csv`, split `grouped`.

18 configurations, 0 failed. Selection is on the pooled out-of-fold macro-F1 of the same split `train` uses - no held-out set is involved, so nothing is chosen on data a reported score is computed from.

## What tuning bought

| model | default macro-F1 | best macro-F1 | gain | best configuration |
|---|---|---|---|---|
| adaboost | 0.1198 | 0.2596 | +0.1398 | n_estimators=600, max_depth=10, learning_rate=0.5 |

## Top 15 overall

| rank | model | macro-F1 | fold sd | balanced acc | task acc | fit s | configuration |
|---|---|---|---|---|---|---|---|
| 1 | adaboost | 0.2596 | 0.0155 | 0.2340 | 0.3885 | 216.0 | n_estimators=600, max_depth=10, learning_rate=0.5 |
| 2 | adaboost | 0.2523 | 0.0199 | 0.2274 | 0.3806 | 111.7 | n_estimators=300, max_depth=10, learning_rate=0.5 |
| 3 | adaboost | 0.2429 | 0.0119 | 0.2193 | 0.3832 | 208.4 | n_estimators=600, max_depth=10, learning_rate=1.0 |
| 4 | adaboost | 0.2409 | 0.0113 | 0.2166 | 0.3582 | 35.3 | n_estimators=100, max_depth=10, learning_rate=0.5 |
| 5 | adaboost | 0.2388 | 0.0076 | 0.2327 | 0.3320 | 70.9 | n_estimators=600, max_depth=3, learning_rate=0.5 |
| 6 | adaboost | 0.2301 | 0.0076 | 0.2085 | 0.3659 | 113.1 | n_estimators=300, max_depth=10, learning_rate=1.0 |
| 7 | adaboost | 0.2154 | 0.0095 | 0.1966 | 0.3433 | 35.0 | n_estimators=100, max_depth=10, learning_rate=1.0 |
| 8 | adaboost | 0.2134 | 0.0080 | 0.2044 | 0.3208 | 35.5 | n_estimators=300, max_depth=3, learning_rate=0.5 |
| 9 | adaboost | 0.2078 | 0.0159 | 0.2044 | 0.2808 | 70.6 | n_estimators=600, max_depth=3, learning_rate=1.0 |
| 10 | adaboost | 0.2049 | 0.0207 | 0.1986 | 0.2819 | 36.4 | n_estimators=300, max_depth=3, learning_rate=1.0 |
| 11 | adaboost | 0.1873 | 0.0058 | 0.1836 | 0.3103 | 11.4 | n_estimators=100, max_depth=3, learning_rate=0.5 |
| 12 | adaboost | 0.1788 | 0.0147 | 0.1707 | 0.2749 | 10.9 | n_estimators=100, max_depth=3, learning_rate=1.0 |
| 13 | adaboost | 0.1719 | 0.0138 | 0.1814 | 0.2816 | 25.6 | n_estimators=600, max_depth=1, learning_rate=1.0 |
| 14 | adaboost | 0.1620 | 0.0100 | 0.1666 | 0.2772 | 11.4 | n_estimators=300, max_depth=1, learning_rate=1.0 |
| 15 | adaboost | 0.1602 | 0.0039 | 0.1646 | 0.2905 | 26.6 | n_estimators=600, max_depth=1, learning_rate=0.5 |

## Per-class F1 of each model's best configuration

| class | recordings | adaboost |
|---|---|---|
| configure_option | 1480 | 0.442 |
| navigate_view | 1266 | 0.511 |
| format_style | 908 | 0.383 |
| edit_content | 830 | 0.270 |
| create_item | 770 | 0.385 |
| other | 399 | 0.141 |
| insert_element | 352 | 0.281 |
| file_manage | 290 | 0.334 |
| delete_remove | 174 | 0.033 |
| search_filter | 157 | 0.374 |
| organize_items | 150 | 0.098 |
| communicate | 127 | 0.252 |
| media_control | 54 | 0.036 |
| run_command | 34 | 0.095 |
