# run_003_keyword-5apps

Created 2026-09-23 13:28 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 287 tasks from Bash, Eclipse, KDevelop, NetBeans, VSCode; 831 segments (the backend's segmentation: actions more than 2 s apart start a new segment).

**Labels.** `keyword` - the backend's derive_activity_label, a keyword match on the task instruction. One label per task, copied to all of its segments.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): all segments of a recording are on the same side. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| coding_editing | 175 | 544 |
| other | 95 | 237 |
| git_operations | 8 | 24 |
| aws_console | 4 | 11 |
| documentation | 3 | 7 |
| debugging | 2 | 8 |

Left out (fewer than 2 tasks): docker_workflow (1)

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### main150 (150 dims: ocr + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.132 | 0.044 | 0.167 | 0.655 | 0.610 | 0.00 | 0.000 |
| lightgbm | tier1 | 0.332 | 0.076 | 0.319 | 0.780 | 0.794 | 1.76 | 0.023 |
| xgboost | tier1 | 0.324 | 0.080 | 0.312 | 0.780 | 0.773 | 0.55 | 0.015 |
| random_forest | tier1 | 0.309 | 0.075 | 0.298 | 0.793 | 0.791 | 0.17 | 0.554 |
| mlp | tier2 | 0.299 | 0.085 | 0.289 | 0.782 | 0.805 | 1.35 | 0.002 |
| decision_tree | tier1 | 0.296 | 0.089 | 0.294 | 0.735 | 0.742 | 0.05 | 0.003 |
| late_fusion | tier3 | 0.296 | 0.070 | 0.286 | 0.794 | 0.794 | 0.46 | 0.608 |
| stacking | tier3 | 0.296 | 0.067 | 0.286 | 0.797 | 0.794 | 1.14 | 0.561 |
| voting | tier3 | 0.288 | 0.078 | 0.280 | 0.801 | 0.805 | 1.00 | 0.559 |
| svm | tier1 | 0.271 | 0.082 | 0.270 | 0.820 | 0.822 | 0.18 | 0.140 |
| knn | tier1 | 0.271 | 0.058 | 0.270 | 0.780 | 0.784 | 0.00 | 0.390 |
| transformer | tier2 | 0.269 | 0.059 | 0.269 | 0.779 | 0.808 | 3.63 | 0.011 |
| lstm | tier2 | 0.257 | 0.071 | 0.264 | 0.779 | 0.798 | 1.53 | 0.011 |
| cnn1d | tier2 | 0.252 | 0.075 | 0.253 | 0.774 | 0.770 | 2.02 | 0.022 |
| naive_bayes | tier1 | 0.190 | 0.065 | 0.230 | 0.414 | 0.443 | 0.00 | 0.015 |

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.132 | 0.044 | 0.167 | 0.655 | 0.610 | 0.00 | 0.000 |
| xgboost | tier1 | 0.360 | 0.094 | 0.339 | 0.803 | 0.805 | 0.52 | 0.014 |
| lightgbm | tier1 | 0.352 | 0.091 | 0.335 | 0.791 | 0.798 | 1.09 | 0.020 |
| mlp | tier2 | 0.333 | 0.063 | 0.320 | 0.792 | 0.822 | 0.75 | 0.002 |
| stacking | tier3 | 0.327 | 0.076 | 0.308 | 0.805 | 0.826 | 1.17 | 0.564 |
| voting | tier3 | 0.326 | 0.082 | 0.307 | 0.800 | 0.819 | 1.00 | 0.601 |
| random_forest | tier1 | 0.326 | 0.085 | 0.309 | 0.806 | 0.808 | 0.17 | 0.467 |
| decision_tree | tier1 | 0.308 | 0.098 | 0.315 | 0.741 | 0.735 | 0.06 | 0.002 |
| late_fusion | tier3 | 0.307 | 0.085 | 0.293 | 0.798 | 0.798 | 0.43 | 0.583 |
| knn | tier1 | 0.300 | 0.063 | 0.289 | 0.775 | 0.805 | 0.00 | 0.148 |
| transformer | tier2 | 0.300 | 0.107 | 0.295 | 0.766 | 0.794 | 3.80 | 0.013 |
| lstm | tier2 | 0.299 | 0.077 | 0.288 | 0.776 | 0.805 | 1.61 | 0.006 |
| svm | tier1 | 0.288 | 0.087 | 0.274 | 0.803 | 0.815 | 0.17 | 0.130 |
| cnn1d | tier2 | 0.263 | 0.081 | 0.263 | 0.800 | 0.805 | 1.94 | 0.018 |
| naive_bayes | tier1 | 0.150 | 0.045 | 0.198 | 0.326 | 0.293 | 0.00 | 0.015 |

### cnn (512 dims: cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.132 | 0.044 | 0.167 | 0.655 | 0.610 | 0.00 | 0.000 |
| voting | tier3 | 0.356 | 0.074 | 0.342 | 0.822 | 0.829 | 1.38 | 0.765 |
| svm | tier1 | 0.350 | 0.105 | 0.330 | 0.835 | 0.840 | 0.39 | 0.269 |
| stacking | tier3 | 0.349 | 0.097 | 0.332 | 0.818 | 0.829 | 1.81 | 0.801 |
| xgboost | tier1 | 0.348 | 0.094 | 0.329 | 0.816 | 0.812 | 2.97 | 0.017 |
| knn | tier1 | 0.345 | 0.081 | 0.346 | 0.781 | 0.794 | 0.00 | 0.286 |
| mlp | tier2 | 0.344 | 0.076 | 0.337 | 0.807 | 0.812 | 0.93 | 0.003 |
| random_forest | tier1 | 0.339 | 0.090 | 0.317 | 0.823 | 0.826 | 0.22 | 0.527 |
| transformer | tier2 | 0.338 | 0.080 | 0.330 | 0.788 | 0.812 | 4.19 | 0.013 |
| late_fusion | tier3 | 0.336 | 0.090 | 0.314 | 0.830 | 0.833 | 0.62 | 0.799 |
| lightgbm | tier1 | 0.335 | 0.106 | 0.321 | 0.806 | 0.805 | 2.16 | 0.022 |
| lstm | tier2 | 0.334 | 0.076 | 0.333 | 0.795 | 0.812 | 1.83 | 0.014 |
| naive_bayes | tier1 | 0.331 | 0.058 | 0.364 | 0.753 | 0.760 | 0.00 | 0.042 |
| decision_tree | tier1 | 0.308 | 0.067 | 0.309 | 0.737 | 0.777 | 0.36 | 0.003 |
| cnn1d | tier2 | 0.267 | 0.076 | 0.267 | 0.812 | 0.815 | 4.59 | 0.097 |

### native150+cnn (662 dims: ocr_native + ui + visual + interaction + cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.132 | 0.044 | 0.167 | 0.655 | 0.610 | 0.00 | 0.000 |
| voting | tier3 | 0.368 | 0.081 | 0.349 | 0.826 | 0.826 | 1.46 | 0.776 |
| stacking | tier3 | 0.363 | 0.087 | 0.345 | 0.817 | 0.815 | 1.77 | 0.767 |
| late_fusion | tier3 | 0.354 | 0.099 | 0.330 | 0.838 | 0.843 | 0.68 | 0.685 |
| mlp | tier2 | 0.354 | 0.091 | 0.341 | 0.798 | 0.801 | 0.89 | 0.003 |
| knn | tier1 | 0.348 | 0.076 | 0.347 | 0.788 | 0.791 | 0.00 | 0.299 |
| svm | tier1 | 0.348 | 0.125 | 0.323 | 0.836 | 0.843 | 0.45 | 0.308 |
| lightgbm | tier1 | 0.347 | 0.090 | 0.334 | 0.805 | 0.805 | 2.76 | 0.024 |
| xgboost | tier1 | 0.342 | 0.105 | 0.327 | 0.805 | 0.805 | 3.92 | 0.019 |
| random_forest | tier1 | 0.339 | 0.087 | 0.319 | 0.822 | 0.819 | 0.20 | 0.470 |
| transformer | tier2 | 0.337 | 0.063 | 0.343 | 0.787 | 0.780 | 4.12 | 0.013 |
| lstm | tier2 | 0.323 | 0.087 | 0.316 | 0.795 | 0.794 | 1.98 | 0.015 |
| naive_bayes | tier1 | 0.301 | 0.059 | 0.326 | 0.670 | 0.652 | 0.00 | 0.045 |
| decision_tree | tier1 | 0.299 | 0.094 | 0.305 | 0.722 | 0.767 | 0.36 | 0.003 |
| cnn1d | tier2 | 0.270 | 0.078 | 0.270 | 0.818 | 0.822 | 5.35 | 0.136 |

## Read before quoting a number

- Classes with fewer than 5 tasks: debugging (2), documentation (3), aws_console (4). Their per-class scores rest on a handful of recordings.
- Left out for having fewer than 2 tasks: docker_workflow (1).

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/main150__lightgbm.joblib` - main150, refitted on all 831 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__xgboost.joblib` - native150, refitted on all 831 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__voting.joblib` - cnn, refitted on all 831 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__voting.joblib` - native150+cnn, refitted on all 831 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
