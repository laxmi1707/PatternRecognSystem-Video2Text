# Hyperparameter search - run_016_v3-tuned

6991 recordings, 14 classes, 5 folds, feature set `native150`, level `task`, balance `none`, labels `csv:labels/labels_v3.csv`.

75 configurations, 0 failed. Selection is on the pooled out-of-fold macro-F1 of the same split `train` uses - no held-out set is involved, so nothing is chosen on data a reported score is computed from.

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
| 1 | xgboost | 0.3271 | 0.0182 | 0.3138 | 0.4112 | 44.1 | n_estimators=600, max_depth=10, learning_rate=0.2 |
| 2 | xgboost | 0.3243 | 0.0192 | 0.3091 | 0.4084 | 35.2 | n_estimators=300, max_depth=10, learning_rate=0.2 |
| 3 | xgboost | 0.3217 | 0.0099 | 0.3063 | 0.4105 | 65.9 | n_estimators=600, max_depth=10, learning_rate=0.1 |
| 4 | xgboost | 0.3211 | 0.0125 | 0.3022 | 0.4111 | 49.7 | n_estimators=300, max_depth=10, learning_rate=0.1 |
| 5 | xgboost | 0.3186 | 0.0141 | 0.2962 | 0.4098 | 113.9 | n_estimators=600, max_depth=10, learning_rate=0.03 |
| 6 | stacking | 0.3170 | 0.0064 | 0.2995 | 0.4042 | 33.8 | bases=svm+random_forest+mlp, meta_C=10.0 |
| 7 | stacking | 0.3164 | 0.0062 | 0.2931 | 0.4095 | 33.5 | bases=svm+random_forest+mlp, meta_C=1.0 |
| 8 | xgboost | 0.3159 | 0.0102 | 0.2960 | 0.4038 | 41.8 | n_estimators=600, max_depth=6, learning_rate=0.2 |
| 9 | xgboost | 0.3136 | 0.0206 | 0.2931 | 0.4041 | 20.2 | n_estimators=100, max_depth=10, learning_rate=0.2 |
| 10 | xgboost | 0.3100 | 0.0156 | 0.2884 | 0.4031 | 25.5 | n_estimators=100, max_depth=10, learning_rate=0.1 |
| 11 | xgboost | 0.3091 | 0.0201 | 0.2878 | 0.4052 | 33.2 | n_estimators=300, max_depth=6, learning_rate=0.03 |
| 12 | xgboost | 0.3087 | 0.0082 | 0.2854 | 0.4047 | 51.6 | n_estimators=600, max_depth=6, learning_rate=0.1 |
| 13 | lightgbm | 0.3052 | 0.0159 | 0.2832 | 0.4060 | 6.0 | n_estimators=100, max_depth=10, learning_rate=0.03 |
| 14 | xgboost | 0.3052 | 0.0153 | 0.2815 | 0.4081 | 61.8 | n_estimators=600, max_depth=6, learning_rate=0.03 |
| 15 | xgboost | 0.3051 | 0.0128 | 0.2839 | 0.4052 | 76.7 | n_estimators=300, max_depth=10, learning_rate=0.03 |
