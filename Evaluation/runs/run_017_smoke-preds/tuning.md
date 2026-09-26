# Hyperparameter search - run_017_smoke-preds

155 recordings, 11 classes, 5 folds, feature set `native150`, level `task`, balance `none`, labels `csv:labels/labels_v3.csv`.

4 configurations, 0 failed. Selection is on the pooled out-of-fold macro-F1 of the same split `train` uses - no held-out set is involved, so nothing is chosen on data a reported score is computed from.

## What tuning bought

| model | default macro-F1 | best macro-F1 | gain | best configuration |
|---|---|---|---|---|
| lightgbm | 0.2745 | 0.2745 | +0.0000 | n_estimators=100, max_depth=6, learning_rate=0.1 |
| stacking | nan | 0.1965 | - | bases=svm+random_forest+mlp+lightgbm, meta_C=0.1 |

## Top 15 overall

| rank | model | macro-F1 | fold sd | balanced acc | task acc | fit s | configuration |
|---|---|---|---|---|---|---|---|
| 1 | lightgbm | 0.2745 | 0.0573 | 0.2669 | 0.3613 | 0.1 | n_estimators=100, max_depth=6, learning_rate=0.1 |
| 2 | lightgbm | 0.2583 | 0.0452 | 0.2560 | 0.3613 | 0.1 | n_estimators=100, max_depth=4, learning_rate=0.03 |
| 3 | stacking | 0.1965 | 0.0633 | 0.2077 | 0.3419 | 0.3 | bases=svm+random_forest+mlp+lightgbm, meta_C=0.1 |
| 4 | stacking | 0.1681 | 0.0557 | 0.1936 | 0.3484 | 0.5 | bases=svm+random_forest+mlp, meta_C=0.1 |

## Per-class F1 of each model's best configuration

| class | recordings | lightgbm | stacking |
|---|---|---|---|
| configure_option | 31 | 0.329 | 0.315 |
| navigate_view | 26 | 0.431 | 0.441 |
| insert_element | 23 | 0.444 | 0.458 |
| create_item | 21 | 0.474 | 0.432 |
| format_style | 14 | 0.370 | 0.333 |
| edit_content | 10 | 0.000 | 0.000 |
| file_manage | 9 | 0.286 | 0.182 |
| organize_items | 7 | 0.400 | 0.000 |
| delete_remove | 5 | 0.000 | 0.000 |
| other | 5 | 0.000 | 0.000 |
| media_control | 4 | 0.286 | 0.000 |
