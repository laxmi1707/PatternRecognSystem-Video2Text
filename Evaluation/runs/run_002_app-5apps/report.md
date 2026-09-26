# run_002_app-5apps

Created 2026-09-23 13:23 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 288 tasks from Bash, Eclipse, KDevelop, NetBeans, VSCode; 836 segments (the backend's segmentation: actions more than 2 s apart start a new segment).

**Labels.** `app` - the application being used (ground truth, not the project's activity classes). One label per task, copied to all of its segments.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): all segments of a recording are on the same side. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| VSCode | 106 | 255 |
| Bash | 71 | 169 |
| Eclipse | 46 | 218 |
| Kdevelop | 38 | 89 |
| NetBeans | 27 | 105 |

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### main150 (150 dims: ocr + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.093 | 0.003 | 0.200 | 0.305 | 0.368 | 0.00 | 0.000 |
| lightgbm | tier1 | 0.901 | 0.028 | 0.895 | 0.919 | 0.938 | 1.46 | 0.016 |
| xgboost | tier1 | 0.880 | 0.059 | 0.871 | 0.901 | 0.927 | 0.47 | 0.016 |
| random_forest | tier1 | 0.877 | 0.032 | 0.866 | 0.898 | 0.913 | 0.09 | 0.269 |
| late_fusion | tier3 | 0.871 | 0.043 | 0.861 | 0.895 | 0.917 | 0.35 | 0.290 |
| stacking | tier3 | 0.797 | 0.039 | 0.793 | 0.842 | 0.892 | 1.02 | 0.593 |
| voting | tier3 | 0.788 | 0.045 | 0.786 | 0.833 | 0.882 | 0.83 | 0.563 |
| decision_tree | tier1 | 0.765 | 0.013 | 0.765 | 0.801 | 0.872 | 0.01 | 0.001 |
| transformer | tier2 | 0.765 | 0.047 | 0.763 | 0.803 | 0.865 | 3.16 | 0.010 |
| mlp | tier2 | 0.755 | 0.023 | 0.755 | 0.800 | 0.858 | 1.08 | 0.002 |
| svm | tier1 | 0.723 | 0.041 | 0.716 | 0.782 | 0.847 | 0.07 | 0.057 |
| lstm | tier2 | 0.706 | 0.055 | 0.712 | 0.763 | 0.840 | 1.34 | 0.011 |
| knn | tier1 | 0.701 | 0.045 | 0.705 | 0.755 | 0.844 | 0.00 | 0.218 |
| cnn1d | tier2 | 0.629 | 0.056 | 0.626 | 0.720 | 0.750 | 1.75 | 0.017 |
| naive_bayes | tier1 | 0.586 | 0.036 | 0.603 | 0.615 | 0.674 | 0.00 | 0.005 |

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.093 | 0.003 | 0.200 | 0.305 | 0.368 | 0.00 | 0.000 |
| random_forest | tier1 | 0.985 | 0.012 | 0.984 | 0.984 | 0.979 | 0.08 | 0.221 |
| voting | tier3 | 0.971 | 0.019 | 0.971 | 0.977 | 0.990 | 0.85 | 0.526 |
| stacking | tier3 | 0.969 | 0.020 | 0.969 | 0.976 | 0.990 | 0.99 | 0.505 |
| xgboost | tier1 | 0.968 | 0.023 | 0.966 | 0.971 | 0.979 | 0.28 | 0.011 |
| late_fusion | tier3 | 0.968 | 0.024 | 0.958 | 0.970 | 0.986 | 0.30 | 0.256 |
| lightgbm | tier1 | 0.965 | 0.017 | 0.964 | 0.975 | 0.979 | 0.21 | 0.015 |
| mlp | tier2 | 0.957 | 0.019 | 0.960 | 0.965 | 0.986 | 0.64 | 0.001 |
| decision_tree | tier1 | 0.955 | 0.007 | 0.956 | 0.959 | 0.965 | 0.01 | 0.001 |
| svm | tier1 | 0.949 | 0.020 | 0.939 | 0.953 | 0.976 | 0.05 | 0.043 |
| transformer | tier2 | 0.938 | 0.029 | 0.936 | 0.941 | 0.969 | 3.04 | 0.009 |
| lstm | tier2 | 0.922 | 0.029 | 0.921 | 0.929 | 0.979 | 1.58 | 0.006 |
| knn | tier1 | 0.915 | 0.017 | 0.916 | 0.923 | 0.958 | 0.00 | 0.097 |
| naive_bayes | tier1 | 0.881 | 0.018 | 0.878 | 0.896 | 0.938 | 0.00 | 0.005 |
| cnn1d | tier2 | 0.703 | 0.055 | 0.695 | 0.766 | 0.816 | 1.60 | 0.012 |

### cnn (512 dims: cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.093 | 0.003 | 0.200 | 0.305 | 0.368 | 0.00 | 0.000 |
| mlp | tier2 | 0.937 | 0.048 | 0.929 | 0.945 | 0.976 | 0.68 | 0.002 |
| voting | tier3 | 0.929 | 0.048 | 0.918 | 0.940 | 0.972 | 0.96 | 0.600 |
| stacking | tier3 | 0.929 | 0.048 | 0.918 | 0.940 | 0.972 | 1.19 | 0.623 |
| late_fusion | tier3 | 0.899 | 0.054 | 0.881 | 0.916 | 0.955 | 0.38 | 0.336 |
| svm | tier1 | 0.894 | 0.042 | 0.874 | 0.913 | 0.955 | 0.10 | 0.095 |
| lightgbm | tier1 | 0.869 | 0.052 | 0.858 | 0.896 | 0.924 | 0.68 | 0.018 |
| lstm | tier2 | 0.866 | 0.050 | 0.856 | 0.888 | 0.941 | 1.72 | 0.010 |
| random_forest | tier1 | 0.862 | 0.057 | 0.842 | 0.890 | 0.938 | 0.10 | 0.281 |
| transformer | tier2 | 0.859 | 0.046 | 0.845 | 0.876 | 0.927 | 3.18 | 0.009 |
| knn | tier1 | 0.856 | 0.035 | 0.846 | 0.879 | 0.941 | 0.00 | 0.206 |
| xgboost | tier1 | 0.832 | 0.066 | 0.817 | 0.866 | 0.910 | 2.02 | 0.015 |
| naive_bayes | tier1 | 0.785 | 0.072 | 0.787 | 0.824 | 0.872 | 0.00 | 0.010 |
| decision_tree | tier1 | 0.726 | 0.046 | 0.724 | 0.767 | 0.816 | 0.12 | 0.002 |
| cnn1d | tier2 | 0.474 | 0.061 | 0.485 | 0.566 | 0.611 | 3.00 | 0.059 |

### native150+cnn (662 dims: ocr_native + ui + visual + interaction + cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.093 | 0.003 | 0.200 | 0.305 | 0.368 | 0.00 | 0.000 |
| lightgbm | tier1 | 0.976 | 0.014 | 0.974 | 0.981 | 0.986 | 1.06 | 0.019 |
| random_forest | tier1 | 0.973 | 0.015 | 0.968 | 0.975 | 0.983 | 0.14 | 0.374 |
| voting | tier3 | 0.970 | 0.025 | 0.966 | 0.975 | 0.993 | 1.09 | 0.716 |
| stacking | tier3 | 0.968 | 0.027 | 0.964 | 0.974 | 0.993 | 1.40 | 0.728 |
| xgboost | tier1 | 0.966 | 0.019 | 0.963 | 0.971 | 0.986 | 1.78 | 0.014 |
| mlp | tier2 | 0.965 | 0.027 | 0.964 | 0.970 | 0.986 | 0.76 | 0.002 |
| late_fusion | tier3 | 0.951 | 0.026 | 0.938 | 0.959 | 0.972 | 0.56 | 0.547 |
| transformer | tier2 | 0.947 | 0.007 | 0.950 | 0.951 | 0.965 | 3.53 | 0.010 |
| svm | tier1 | 0.941 | 0.032 | 0.926 | 0.953 | 0.976 | 0.23 | 0.221 |
| decision_tree | tier1 | 0.937 | 0.031 | 0.930 | 0.949 | 0.948 | 0.12 | 0.002 |
| knn | tier1 | 0.914 | 0.032 | 0.905 | 0.923 | 0.976 | 0.00 | 0.274 |
| lstm | tier2 | 0.893 | 0.017 | 0.880 | 0.910 | 0.951 | 1.82 | 0.011 |
| naive_bayes | tier1 | 0.868 | 0.025 | 0.859 | 0.889 | 0.931 | 0.00 | 0.027 |
| cnn1d | tier2 | 0.468 | 0.033 | 0.484 | 0.578 | 0.608 | 4.04 | 0.108 |

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/main150__lightgbm.joblib` - main150, refitted on all 836 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__random_forest.joblib` - native150, refitted on all 836 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__mlp.joblib` - cnn, refitted on all 836 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__lightgbm.joblib` - native150+cnn, refitted on all 836 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
