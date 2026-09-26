# Hyperparameter search - run_019_v3-tuned-balanced

6991 recordings, 14 classes, 5 folds, feature set `native150`, level `task`, balance `5.0`, labels `csv:labels/labels_v3.csv`, split `grouped`.

75 configurations, 0 failed. Selection is on the pooled out-of-fold macro-F1 of the same split `train` uses - no held-out set is involved, so nothing is chosen on data a reported score is computed from.

## What tuning bought

| model | default macro-F1 | best macro-F1 | gain | best configuration |
|---|---|---|---|---|
| lightgbm | 0.3001 | 0.3177 | +0.0176 | n_estimators=300, max_depth=4, learning_rate=0.03 |
| random_forest | 0.2821 | 0.2964 | +0.0143 | n_estimators=600, max_depth=40 |
| stacking | 0.3154 | 0.3208 | +0.0054 | bases=svm+random_forest+mlp+lightgbm, meta_C=10.0 |
| xgboost | 0.3179 | 0.3238 | +0.0059 | n_estimators=600, max_depth=10, learning_rate=0.1 |

## Top 15 overall

| rank | model | macro-F1 | fold sd | balanced acc | task acc | fit s | configuration |
|---|---|---|---|---|---|---|---|
| 1 | xgboost | 0.3238 | 0.0108 | 0.3081 | 0.4104 | 69.4 | n_estimators=600, max_depth=10, learning_rate=0.1 |
| 2 | xgboost | 0.3221 | 0.0089 | 0.3041 | 0.4098 | 52.2 | n_estimators=300, max_depth=10, learning_rate=0.1 |
| 3 | xgboost | 0.3208 | 0.0072 | 0.3011 | 0.4107 | 119.9 | n_estimators=600, max_depth=10, learning_rate=0.03 |
| 4 | stacking | 0.3208 | 0.0106 | 0.2970 | 0.4035 | 29.8 | bases=svm+random_forest+mlp+lightgbm, meta_C=10.0 |
| 5 | xgboost | 0.3201 | 0.0172 | 0.3089 | 0.4034 | 46.4 | n_estimators=600, max_depth=10, learning_rate=0.2 |
| 6 | xgboost | 0.3191 | 0.0116 | 0.2945 | 0.4074 | 10.8 | n_estimators=100, max_depth=6, learning_rate=0.2 |
| 7 | stacking | 0.3180 | 0.0139 | 0.2925 | 0.4032 | 8.8 | bases=random_forest+mlp+lightgbm, meta_C=10.0 |
| 8 | xgboost | 0.3179 | 0.0147 | 0.3011 | 0.4052 | 11.7 | n_estimators=100, max_depth=6, learning_rate=0.1 |
| 9 | xgboost | 0.3178 | 0.0123 | 0.3025 | 0.4057 | 35.0 | n_estimators=300, max_depth=6, learning_rate=0.03 |
| 10 | lightgbm | 0.3177 | 0.0134 | 0.3081 | 0.4005 | 6.8 | n_estimators=300, max_depth=4, learning_rate=0.03 |
| 11 | xgboost | 0.3172 | 0.0110 | 0.2948 | 0.4080 | 64.8 | n_estimators=600, max_depth=6, learning_rate=0.03 |
| 12 | lightgbm | 0.3165 | 0.0086 | 0.2994 | 0.4045 | 20.8 | n_estimators=600, max_depth=10, learning_rate=0.2 |
| 13 | xgboost | 0.3163 | 0.0151 | 0.3037 | 0.4009 | 35.0 | n_estimators=600, max_depth=4, learning_rate=0.03 |
| 14 | xgboost | 0.3163 | 0.0154 | 0.2962 | 0.4041 | 80.7 | n_estimators=300, max_depth=10, learning_rate=0.03 |
| 15 | stacking | 0.3163 | 0.0070 | 0.2964 | 0.4058 | 30.4 | bases=svm+random_forest+mlp, meta_C=0.1 |

## Per-class F1 of each model's best configuration

| class | recordings | xgboost | stacking | lightgbm | random_forest |
|---|---|---|---|---|---|
| configure_option | 1480 | 0.467 | 0.455 | 0.459 | 0.459 |
| navigate_view | 1266 | 0.525 | 0.504 | 0.510 | 0.522 |
| format_style | 908 | 0.375 | 0.384 | 0.376 | 0.379 |
| edit_content | 830 | 0.305 | 0.291 | 0.239 | 0.272 |
| create_item | 770 | 0.406 | 0.415 | 0.410 | 0.411 |
| other | 399 | 0.179 | 0.204 | 0.171 | 0.225 |
| insert_element | 352 | 0.361 | 0.362 | 0.378 | 0.317 |
| file_manage | 290 | 0.472 | 0.432 | 0.454 | 0.328 |
| delete_remove | 174 | 0.159 | 0.136 | 0.150 | 0.120 |
| search_filter | 157 | 0.419 | 0.466 | 0.446 | 0.420 |
| organize_items | 150 | 0.171 | 0.119 | 0.104 | 0.119 |
| communicate | 127 | 0.432 | 0.461 | 0.428 | 0.333 |
| media_control | 54 | 0.148 | 0.167 | 0.168 | 0.165 |
| run_command | 34 | 0.114 | 0.095 | 0.156 | 0.081 |
