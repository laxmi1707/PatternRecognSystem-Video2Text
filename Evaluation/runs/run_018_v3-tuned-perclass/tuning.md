# Hyperparameter search - run_018_v3-tuned-perclass

6991 recordings, 14 classes, 5 folds, feature set `native150`, level `task`, balance `none`, labels `csv:labels/labels_v3.csv`.

8 configurations, 0 failed. Selection is on the pooled out-of-fold macro-F1 of the same split `train` uses - no held-out set is involved, so nothing is chosen on data a reported score is computed from.

## What tuning bought

| model | default macro-F1 | best macro-F1 | gain | best configuration |
|---|---|---|---|---|
| lightgbm | 0.2912 | 0.3052 | +0.0140 | n_estimators=100, max_depth=10, learning_rate=0.03 |
| random_forest | 0.2816 | 0.2910 | +0.0094 | n_estimators=100, max_depth=40 |
| stacking | 0.3164 | 0.3170 | +0.0006 | bases=svm+random_forest+mlp, meta_C=10.0 |
| xgboost | 0.3040 | 0.3271 | +0.0231 | n_estimators=600, max_depth=10, learning_rate=0.2 |

## Top 15 overall

| rank | model | macro-F1 | fold sd | balanced acc | task acc | fit s | configuration |
|---|---|---|---|---|---|---|---|
| 1 | xgboost | 0.3271 | 0.0182 | 0.3138 | 0.4112 | 32.2 | n_estimators=600, max_depth=10, learning_rate=0.2 |
| 2 | stacking | 0.3170 | 0.0064 | 0.2995 | 0.4042 | 25.9 | bases=svm+random_forest+mlp, meta_C=10.0 |
| 3 | stacking | 0.3164 | 0.0062 | 0.2931 | 0.4095 | 25.3 | bases=svm+random_forest+mlp, meta_C=1.0 |
| 4 | lightgbm | 0.3052 | 0.0159 | 0.2832 | 0.4060 | 5.6 | n_estimators=100, max_depth=10, learning_rate=0.03 |
| 5 | xgboost | 0.3040 | 0.0173 | 0.2832 | 0.4031 | 8.9 | n_estimators=100, max_depth=6, learning_rate=0.1 |
| 6 | lightgbm | 0.2912 | 0.0103 | 0.2702 | 0.3977 | 3.5 | n_estimators=100, max_depth=6, learning_rate=0.1 |
| 7 | random_forest | 0.2910 | 0.0121 | 0.2621 | 0.3935 | 1.2 | n_estimators=100, max_depth=40 |
| 8 | random_forest | 0.2816 | 0.0097 | 0.2555 | 0.3962 | 1.2 | n_estimators=100, max_depth=20 |

## Per-class F1 of each model's best configuration

| class | recordings | xgboost | stacking | lightgbm | random_forest |
|---|---|---|---|---|---|
| configure_option | 1480 | 0.475 | 0.458 | 0.454 | 0.443 |
| navigate_view | 1266 | 0.525 | 0.520 | 0.523 | 0.516 |
| format_style | 908 | 0.382 | 0.371 | 0.373 | 0.368 |
| edit_content | 830 | 0.301 | 0.298 | 0.263 | 0.267 |
| create_item | 770 | 0.405 | 0.408 | 0.424 | 0.403 |
| other | 399 | 0.180 | 0.220 | 0.174 | 0.211 |
| insert_element | 352 | 0.344 | 0.356 | 0.351 | 0.311 |
| file_manage | 290 | 0.468 | 0.413 | 0.480 | 0.317 |
| delete_remove | 174 | 0.161 | 0.102 | 0.134 | 0.094 |
| search_filter | 157 | 0.434 | 0.454 | 0.421 | 0.444 |
| organize_items | 150 | 0.182 | 0.137 | 0.110 | 0.112 |
| communicate | 127 | 0.442 | 0.428 | 0.359 | 0.292 |
| media_control | 54 | 0.103 | 0.203 | 0.098 | 0.215 |
| run_command | 34 | 0.179 | 0.071 | 0.107 | 0.080 |
