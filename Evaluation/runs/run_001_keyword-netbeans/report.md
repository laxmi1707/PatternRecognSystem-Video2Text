# run_001_keyword-netbeans

Created 2026-09-23 11:47 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 26 tasks from NetBeans; 103 segments (the backend's segmentation: actions more than 2 s apart start a new segment).

**Labels.** `keyword` - the backend's derive_activity_label, a keyword match on the task instruction. One label per task, copied to all of its segments.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): all segments of a recording are on the same side. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| coding_editing | 22 | 85 |
| other | 4 | 18 |

Left out (fewer than 2 tasks): git_operations (1)

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### main150 (150 dims: ocr + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.452 | 0.336 | 0.500 | 0.825 | 0.846 | 0.00 | 0.000 |
| transformer | tier2 | 0.449 | 0.285 | 0.457 | 0.718 | 0.808 | 0.30 | 0.036 |
| decision_tree | tier1 | 0.445 | 0.276 | 0.451 | 0.709 | 0.808 | 0.00 | 0.006 |
| svm | tier1 | 0.431 | 0.319 | 0.459 | 0.757 | 0.808 | 0.00 | 0.015 |
| random_forest | tier1 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.07 | 2.205 |
| knn | tier1 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.00 | 1.532 |
| xgboost | tier1 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.08 | 0.089 |
| lightgbm | tier1 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 1.01 | 0.078 |
| cnn1d | tier2 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.18 | 0.052 |
| lstm | tier2 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.14 | 0.039 |
| late_fusion | tier3 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.17 | 2.389 |
| mlp | tier2 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.31 | 0.007 |
| voting | tier3 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.18 | 2.757 |
| stacking | tier3 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.23 | 2.655 |
| naive_bayes | tier1 | 0.394 | 0.263 | 0.394 | 0.650 | 0.731 | 0.00 | 0.014 |

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.452 | 0.336 | 0.500 | 0.825 | 0.846 | 0.00 | 0.000 |
| decision_tree | tier1 | 0.437 | 0.215 | 0.432 | 0.641 | 0.692 | 0.00 | 0.005 |
| svm | tier1 | 0.431 | 0.319 | 0.459 | 0.757 | 0.808 | 0.00 | 0.014 |
| random_forest | tier1 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.07 | 1.903 |
| xgboost | tier1 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.02 | 0.053 |
| mlp | tier2 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.10 | 0.009 |
| lstm | tier2 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.16 | 0.021 |
| voting | tier3 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.17 | 2.881 |
| stacking | tier3 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.25 | 2.615 |
| late_fusion | tier3 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.17 | 2.401 |
| knn | tier1 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.00 | 0.642 |
| lightgbm | tier1 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.02 | 0.082 |
| cnn1d | tier2 | 0.415 | 0.313 | 0.429 | 0.709 | 0.808 | 0.18 | 0.032 |
| transformer | tier2 | 0.411 | 0.317 | 0.423 | 0.699 | 0.808 | 0.32 | 0.034 |
| naive_bayes | tier1 | 0.408 | 0.299 | 0.418 | 0.689 | 0.654 | 0.00 | 0.013 |

### cnn (512 dims: cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.452 | 0.336 | 0.500 | 0.825 | 0.846 | 0.00 | 0.000 |
| decision_tree | tier1 | 0.442 | 0.205 | 0.438 | 0.650 | 0.731 | 0.01 | 0.007 |
| lightgbm | tier1 | 0.425 | 0.311 | 0.447 | 0.738 | 0.808 | 0.03 | 0.085 |
| svm | tier1 | 0.418 | 0.307 | 0.435 | 0.718 | 0.808 | 0.00 | 0.022 |
| random_forest | tier1 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.07 | 1.907 |
| lstm | tier2 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.18 | 0.043 |
| voting | tier3 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.19 | 2.761 |
| stacking | tier3 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.25 | 3.146 |
| late_fusion | tier3 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.17 | 2.328 |
| knn | tier1 | 0.411 | 0.300 | 0.423 | 0.699 | 0.769 | 0.00 | 1.284 |
| xgboost | tier1 | 0.411 | 0.309 | 0.423 | 0.699 | 0.808 | 0.03 | 0.051 |
| naive_bayes | tier1 | 0.408 | 0.329 | 0.418 | 0.689 | 0.769 | 0.00 | 0.016 |
| mlp | tier2 | 0.408 | 0.292 | 0.418 | 0.689 | 0.769 | 0.11 | 0.008 |
| transformer | tier2 | 0.401 | 0.304 | 0.406 | 0.670 | 0.769 | 0.33 | 0.028 |
| cnn1d | tier2 | 0.394 | 0.293 | 0.394 | 0.650 | 0.731 | 0.30 | 0.074 |

### native150+cnn (662 dims: ocr_native + ui + visual + interaction + cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.452 | 0.336 | 0.500 | 0.825 | 0.846 | 0.00 | 0.000 |
| decision_tree | tier1 | 0.442 | 0.232 | 0.438 | 0.650 | 0.731 | 0.01 | 0.008 |
| svm | tier1 | 0.425 | 0.315 | 0.447 | 0.738 | 0.808 | 0.00 | 0.027 |
| naive_bayes | tier1 | 0.421 | 0.318 | 0.441 | 0.728 | 0.731 | 0.00 | 0.018 |
| random_forest | tier1 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.07 | 1.911 |
| lightgbm | tier1 | 0.418 | 0.307 | 0.435 | 0.718 | 0.808 | 0.03 | 0.087 |
| lstm | tier2 | 0.418 | 0.311 | 0.435 | 0.718 | 0.808 | 0.17 | 0.040 |
| voting | tier3 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.19 | 2.787 |
| stacking | tier3 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.25 | 2.739 |
| late_fusion | tier3 | 0.415 | 0.306 | 0.429 | 0.709 | 0.808 | 0.18 | 2.530 |
| knn | tier1 | 0.411 | 0.300 | 0.423 | 0.699 | 0.769 | 0.00 | 1.497 |
| xgboost | tier1 | 0.411 | 0.309 | 0.423 | 0.699 | 0.808 | 0.04 | 0.053 |
| mlp | tier2 | 0.411 | 0.300 | 0.423 | 0.699 | 0.769 | 0.11 | 0.007 |
| transformer | tier2 | 0.408 | 0.307 | 0.418 | 0.689 | 0.808 | 0.31 | 0.028 |
| cnn1d | tier2 | 0.401 | 0.275 | 0.406 | 0.670 | 0.769 | 0.35 | 0.078 |

## Read before quoting a number

- Only 26 tasks, about 5 per test fold: one task more or less right moves a fold's task accuracy by ~19 points. Treat differences of a few points between models as noise.
- Classes with fewer than 5 tasks: other (4). Their per-class scores rest on a handful of recordings.
- Left out for having fewer than 2 tasks: git_operations (1).
- main150: the best model (transformer, macro-F1 0.45) is within 0.05 of always answering the majority class (0.45). These features do not separate these labels yet.
- native150: the best model (decision_tree, macro-F1 0.44) is within 0.05 of always answering the majority class (0.45). These features do not separate these labels yet.
- cnn: the best model (decision_tree, macro-F1 0.44) is within 0.05 of always answering the majority class (0.45). These features do not separate these labels yet.
- native150+cnn: the best model (decision_tree, macro-F1 0.44) is within 0.05 of always answering the majority class (0.45). These features do not separate these labels yet.

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/main150__transformer.joblib` - main150, refitted on all 103 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__decision_tree.joblib` - native150, refitted on all 103 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__decision_tree.joblib` - cnn, refitted on all 103 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__decision_tree.joblib` - native150+cnn, refitted on all 103 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
