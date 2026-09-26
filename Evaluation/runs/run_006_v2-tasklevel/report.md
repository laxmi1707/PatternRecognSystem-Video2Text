# run_006_v2-tasklevel

Created 2026-09-23 20:13 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 530 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, GrassGIS, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 530 segments (the backend's segmentation: actions more than 2 s apart start a new segment).

**Labels.** `csv:labels/labels_v2.csv`. One label per task, copied to all of its segments.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): all segments of a recording are on the same side. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| navigate_view | 142 | 142 |
| configure_option | 126 | 126 |
| edit_content | 52 | 52 |
| create_item | 50 | 50 |
| format_style | 37 | 37 |
| other | 29 | 29 |
| search_filter | 20 | 20 |
| file_manage | 17 | 17 |
| insert_element | 15 | 15 |
| delete_remove | 15 | 15 |
| run_command | 13 | 13 |
| organize_items | 9 | 9 |
| communicate | 5 | 5 |

Left out (fewer than 3 tasks): media_control (1)

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.033 | 0.004 | 0.077 | 0.268 | 0.268 | 0.00 | 0.000 |
| xgboost | tier1 | 0.201 | 0.044 | 0.185 | 0.342 | 0.342 | 9.81 | 0.077 |
| mlp | tier2 | 0.195 | 0.050 | 0.187 | 0.340 | 0.340 | 2.01 | 0.014 |
| lightgbm | tier1 | 0.184 | 0.048 | 0.172 | 0.343 | 0.343 | 8.67 | 0.047 |
| stacking | tier3 | 0.180 | 0.041 | 0.174 | 0.364 | 0.364 | 2.15 | 1.144 |
| random_forest | tier1 | 0.169 | 0.033 | 0.164 | 0.360 | 0.360 | 0.26 | 0.907 |
| voting | tier3 | 0.169 | 0.045 | 0.163 | 0.357 | 0.357 | 2.19 | 1.147 |
| late_fusion | tier3 | 0.147 | 0.020 | 0.146 | 0.349 | 0.349 | 0.51 | 1.086 |
| knn | tier1 | 0.146 | 0.028 | 0.148 | 0.330 | 0.330 | 0.00 | 0.445 |
| svm | tier1 | 0.126 | 0.025 | 0.134 | 0.345 | 0.345 | 0.21 | 0.161 |
| decision_tree | tier1 | 0.125 | 0.021 | 0.126 | 0.249 | 0.249 | 0.05 | 0.008 |
| transformer | tier2 | 0.120 | 0.013 | 0.126 | 0.307 | 0.307 | 5.96 | 0.098 |
| naive_bayes | tier1 | 0.104 | 0.010 | 0.181 | 0.111 | 0.111 | 0.00 | 0.048 |
| lstm | tier2 | 0.068 | 0.015 | 0.090 | 0.287 | 0.287 | 2.43 | 0.031 |
| cnn1d | tier2 | 0.057 | 0.011 | 0.084 | 0.279 | 0.279 | 5.37 | 0.117 |

### cnn (512 dims: cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.033 | 0.004 | 0.077 | 0.268 | 0.268 | 0.00 | 0.000 |
| lightgbm | tier1 | 0.182 | 0.032 | 0.166 | 0.313 | 0.313 | 10.49 | 0.048 |
| xgboost | tier1 | 0.175 | 0.047 | 0.162 | 0.285 | 0.285 | 24.07 | 0.070 |
| mlp | tier2 | 0.171 | 0.030 | 0.166 | 0.309 | 0.309 | 1.75 | 0.026 |
| naive_bayes | tier1 | 0.156 | 0.031 | 0.172 | 0.198 | 0.198 | 0.00 | 0.100 |
| voting | tier3 | 0.146 | 0.021 | 0.141 | 0.321 | 0.321 | 1.95 | 1.251 |
| stacking | tier3 | 0.145 | 0.022 | 0.143 | 0.315 | 0.315 | 2.12 | 1.344 |
| random_forest | tier1 | 0.145 | 0.038 | 0.140 | 0.315 | 0.315 | 0.20 | 0.853 |
| late_fusion | tier3 | 0.126 | 0.022 | 0.129 | 0.332 | 0.332 | 0.61 | 1.047 |
| knn | tier1 | 0.113 | 0.015 | 0.122 | 0.291 | 0.291 | 0.00 | 0.167 |
| lstm | tier2 | 0.111 | 0.020 | 0.121 | 0.323 | 0.323 | 2.46 | 0.059 |
| transformer | tier2 | 0.103 | 0.018 | 0.111 | 0.287 | 0.287 | 5.14 | 0.092 |
| decision_tree | tier1 | 0.096 | 0.022 | 0.095 | 0.170 | 0.170 | 0.26 | 0.005 |
| cnn1d | tier2 | 0.070 | 0.013 | 0.097 | 0.304 | 0.304 | 10.78 | 0.386 |
| svm | tier1 | 0.069 | 0.010 | 0.098 | 0.319 | 0.319 | 0.40 | 0.321 |

## Read before quoting a number

- Left out for having fewer than 3 tasks: media_control (1).

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/native150__xgboost.joblib` - native150, refitted on all 530 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__lightgbm.joblib` - cnn, refitted on all 530 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
