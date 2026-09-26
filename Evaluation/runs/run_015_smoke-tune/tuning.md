# Hyperparameter search - run_015_smoke-tune

155 recordings, 11 classes, 5 folds, feature set `native150`, level `task`, balance `none`, labels `csv:labels/labels_v3.csv`.

39 configurations, 0 failed. Selection is on the pooled out-of-fold macro-F1 of the same split `train` uses - no held-out set is involved, so nothing is chosen on data a reported score is computed from.

## What tuning bought

| model | default macro-F1 | best macro-F1 | gain | best configuration |
|---|---|---|---|---|
| lightgbm | 0.2745 | 0.2920 | +0.0175 | n_estimators=600, max_depth=6, learning_rate=0.1 |
| stacking | 0.2226 | 0.2459 | +0.0233 | bases=random_forest+mlp+lightgbm, meta_C=1.0 |

## Top 15 overall

| rank | model | macro-F1 | fold sd | balanced acc | task acc | fit s | configuration |
|---|---|---|---|---|---|---|---|
| 1 | lightgbm | 0.2920 | 0.0489 | 0.2888 | 0.3935 | 0.6 | n_estimators=600, max_depth=6, learning_rate=0.1 |
| 2 | lightgbm | 0.2895 | 0.0551 | 0.2824 | 0.3806 | 0.2 | n_estimators=300, max_depth=6, learning_rate=0.1 |
| 3 | lightgbm | 0.2880 | 0.0608 | 0.2811 | 0.3806 | 0.4 | n_estimators=300, max_depth=10, learning_rate=0.1 |
| 4 | lightgbm | 0.2858 | 0.0627 | 0.2800 | 0.3806 | 0.4 | n_estimators=600, max_depth=10, learning_rate=0.1 |
| 5 | lightgbm | 0.2801 | 0.0419 | 0.2775 | 0.3742 | 1.0 | n_estimators=600, max_depth=4, learning_rate=0.03 |
| 6 | lightgbm | 0.2798 | 0.0450 | 0.2765 | 0.3742 | 0.4 | n_estimators=300, max_depth=4, learning_rate=0.1 |
| 7 | lightgbm | 0.2785 | 0.0455 | 0.2771 | 0.3742 | 0.6 | n_estimators=600, max_depth=4, learning_rate=0.1 |
| 8 | lightgbm | 0.2745 | 0.0573 | 0.2669 | 0.3613 | 0.2 | n_estimators=100, max_depth=6, learning_rate=0.1 |
| 9 | lightgbm | 0.2734 | 0.0407 | 0.2674 | 0.3613 | 0.1 | n_estimators=100, max_depth=4, learning_rate=0.1 |
| 10 | lightgbm | 0.2713 | 0.0490 | 0.2597 | 0.3484 | 0.4 | n_estimators=300, max_depth=4, learning_rate=0.03 |
| 11 | lightgbm | 0.2711 | 0.0628 | 0.2597 | 0.3484 | 0.1 | n_estimators=100, max_depth=10, learning_rate=0.1 |
| 12 | lightgbm | 0.2697 | 0.0402 | 0.2631 | 0.3548 | 0.6 | n_estimators=300, max_depth=10, learning_rate=0.03 |
| 13 | lightgbm | 0.2672 | 0.0471 | 0.2636 | 0.3548 | 0.2 | n_estimators=300, max_depth=4, learning_rate=0.2 |
| 14 | lightgbm | 0.2670 | 0.0471 | 0.2636 | 0.3548 | 0.4 | n_estimators=600, max_depth=4, learning_rate=0.2 |
| 15 | lightgbm | 0.2645 | 0.0575 | 0.2667 | 0.3871 | 0.3 | n_estimators=300, max_depth=6, learning_rate=0.2 |
