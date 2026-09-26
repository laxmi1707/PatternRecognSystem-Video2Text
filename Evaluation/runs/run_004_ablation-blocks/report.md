# run_004_ablation-blocks

Created 2026-09-23 13:36 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

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

### ocr (50 dims: ocr)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.132 | 0.044 | 0.167 | 0.655 | 0.610 | 0.00 | 0.000 |
| lightgbm | tier1 | 0.231 | 0.067 | 0.225 | 0.738 | 0.704 | 1.02 | 0.017 |
| svm | tier1 | 0.230 | 0.077 | 0.229 | 0.737 | 0.721 | 0.10 | 0.087 |
| random_forest | tier1 | 0.222 | 0.088 | 0.221 | 0.738 | 0.714 | 0.15 | 0.458 |

### ocr_native (50 dims: ocr_native)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.132 | 0.044 | 0.167 | 0.655 | 0.610 | 0.00 | 0.000 |
| random_forest | tier1 | 0.368 | 0.080 | 0.351 | 0.800 | 0.829 | 0.15 | 0.463 |
| svm | tier1 | 0.343 | 0.099 | 0.318 | 0.810 | 0.819 | 0.09 | 0.072 |
| lightgbm | tier1 | 0.325 | 0.092 | 0.317 | 0.771 | 0.805 | 0.90 | 0.020 |

### ui (30 dims: ui)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.132 | 0.044 | 0.167 | 0.655 | 0.610 | 0.00 | 0.000 |
| random_forest | tier1 | 0.198 | 0.033 | 0.205 | 0.669 | 0.638 | 0.16 | 0.532 |
| lightgbm | tier1 | 0.162 | 0.032 | 0.178 | 0.661 | 0.645 | 0.58 | 0.017 |
| svm | tier1 | 0.132 | 0.044 | 0.167 | 0.655 | 0.610 | 0.10 | 0.096 |

### visual (40 dims: visual)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.132 | 0.044 | 0.167 | 0.655 | 0.610 | 0.00 | 0.000 |
| lightgbm | tier1 | 0.336 | 0.091 | 0.325 | 0.776 | 0.794 | 0.83 | 0.023 |
| random_forest | tier1 | 0.336 | 0.097 | 0.329 | 0.783 | 0.794 | 0.16 | 0.468 |
| svm | tier1 | 0.255 | 0.073 | 0.259 | 0.782 | 0.794 | 0.08 | 0.069 |

### interaction (30 dims: interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.132 | 0.044 | 0.167 | 0.655 | 0.610 | 0.00 | 0.000 |
| svm | tier1 | 0.253 | 0.083 | 0.255 | 0.775 | 0.794 | 0.12 | 0.077 |
| lightgbm | tier1 | 0.244 | 0.078 | 0.249 | 0.745 | 0.770 | 0.95 | 0.024 |
| random_forest | tier1 | 0.237 | 0.074 | 0.240 | 0.729 | 0.742 | 0.16 | 0.469 |

### cnn (512 dims: cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.132 | 0.044 | 0.167 | 0.655 | 0.610 | 0.00 | 0.000 |
| svm | tier1 | 0.350 | 0.105 | 0.330 | 0.835 | 0.840 | 0.35 | 0.261 |
| random_forest | tier1 | 0.339 | 0.090 | 0.317 | 0.823 | 0.826 | 0.18 | 0.466 |
| lightgbm | tier1 | 0.335 | 0.106 | 0.321 | 0.806 | 0.805 | 1.97 | 0.021 |

## Read before quoting a number

- Classes with fewer than 5 tasks: debugging (2), documentation (3), aws_console (4). Their per-class scores rest on a handful of recordings.
- Left out for having fewer than 2 tasks: docker_workflow (1).

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/ocr__lightgbm.joblib` - ocr, refitted on all 831 segments; load it with `python -m v2k predict --bundle ...`
- `models/ocr_native__random_forest.joblib` - ocr_native, refitted on all 831 segments; load it with `python -m v2k predict --bundle ...`
- `models/ui__random_forest.joblib` - ui, refitted on all 831 segments; load it with `python -m v2k predict --bundle ...`
- `models/visual__lightgbm.joblib` - visual, refitted on all 831 segments; load it with `python -m v2k predict --bundle ...`
- `models/interaction__svm.joblib` - interaction, refitted on all 831 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__svm.joblib` - cnn, refitted on all 831 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
