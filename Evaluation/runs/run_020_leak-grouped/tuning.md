# Hyperparameter search - run_020_leak-grouped

6991 recordings, 14 classes, 5 folds, feature set `native150`, level `segment`, balance `none`, labels `csv:labels/labels_v3.csv`, split `grouped`.

2 configurations, 0 failed. Selection is on the pooled out-of-fold macro-F1 of the same split `train` uses - no held-out set is involved, so nothing is chosen on data a reported score is computed from.

## What tuning bought

| model | default macro-F1 | best macro-F1 | gain | best configuration |
|---|---|---|---|---|
| xgboost | 0.2415 | 0.2540 | +0.0125 | n_estimators=600, max_depth=10, learning_rate=0.2 |

## Top 15 overall

| rank | model | macro-F1 | fold sd | balanced acc | task acc | fit s | configuration |
|---|---|---|---|---|---|---|---|
| 1 | xgboost | 0.2540 | 0.0093 | 0.2384 | 0.3510 | 42.0 | n_estimators=600, max_depth=10, learning_rate=0.2 |
| 2 | xgboost | 0.2415 | 0.0138 | 0.2266 | 0.3502 | 4.8 | n_estimators=100, max_depth=6, learning_rate=0.1 |

## Per-class F1 of each model's best configuration

| class | recordings | xgboost |
|---|---|---|
| configure_option | 4935 | 0.437 |
| create_item | 3404 | 0.361 |
| format_style | 3224 | 0.341 |
| edit_content | 3060 | 0.247 |
| navigate_view | 2859 | 0.362 |
| insert_element | 1400 | 0.299 |
| other | 1230 | 0.146 |
| file_manage | 1171 | 0.358 |
| delete_remove | 501 | 0.083 |
| communicate | 420 | 0.312 |
| search_filter | 416 | 0.270 |
| organize_items | 415 | 0.100 |
| media_control | 151 | 0.058 |
| run_command | 70 | 0.182 |
