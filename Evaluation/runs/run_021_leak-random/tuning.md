# Hyperparameter search - run_021_leak-random

6991 recordings, 14 classes, 5 folds, feature set `native150`, level `segment`, balance `none`, labels `csv:labels/labels_v3.csv`, split `random`.

2 configurations, 0 failed. Selection is on the pooled out-of-fold macro-F1 of the same split `train` uses - no held-out set is involved, so nothing is chosen on data a reported score is computed from.

## What tuning bought

| model | default macro-F1 | best macro-F1 | gain | best configuration |
|---|---|---|---|---|
| xgboost | 0.4374 | 0.5547 | +0.1173 | n_estimators=600, max_depth=10, learning_rate=0.2 |

## Top 15 overall

| rank | model | macro-F1 | fold sd | balanced acc | task acc | fit s | configuration |
|---|---|---|---|---|---|---|---|
| 1 | xgboost | 0.5547 | 0.0168 | 0.5168 | 0.5969 | 43.5 | n_estimators=600, max_depth=10, learning_rate=0.2 |
| 2 | xgboost | 0.4374 | 0.0173 | 0.4008 | 0.4750 | 5.1 | n_estimators=100, max_depth=6, learning_rate=0.1 |

## Per-class F1 of each model's best configuration

| class | recordings | xgboost |
|---|---|---|
| configure_option | 4935 | 0.653 |
| create_item | 3404 | 0.687 |
| format_style | 3224 | 0.652 |
| edit_content | 3060 | 0.617 |
| navigate_view | 2859 | 0.553 |
| insert_element | 1400 | 0.691 |
| other | 1230 | 0.545 |
| file_manage | 1171 | 0.621 |
| delete_remove | 501 | 0.334 |
| communicate | 420 | 0.643 |
| search_filter | 416 | 0.470 |
| organize_items | 415 | 0.504 |
| media_control | 151 | 0.434 |
| run_command | 70 | 0.362 |
