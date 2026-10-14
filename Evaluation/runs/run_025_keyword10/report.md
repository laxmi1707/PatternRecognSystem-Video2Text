# run_025_keyword10

Created 2026-09-29 19:36 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 6991 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, GrassGIS, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 6991 rows (one per recording: its segments averaged).

**Labels.** `keyword` - the backend's derive_activity_label, a keyword match on the task instruction. One label per recording, and one row per recording, so the row and the label describe the same thing.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): one row per recording, so a recording is on one side by construction. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| other | 3868 | 3868 |
| coding_editing | 2586 | 2586 |
| docker_workflow | 214 | 214 |
| documentation | 192 | 192 |
| git_operations | 60 | 60 |
| aws_console | 41 | 41 |
| debugging | 25 | 25 |
| kubernetes_ops | 5 | 5 |

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.089 | 0.005 | 0.125 | 0.553 | 0.553 | 0.00 | 0.000 |
| stacking | tier3 | 0.296 | 0.045 | 0.263 | 0.740 | 0.740 | 17.08 | 0.811 |
| xgboost | tier1 | 0.281 | 0.038 | 0.253 | 0.745 | 0.745 | 1.78 | 0.003 |
| lightgbm | tier1 | 0.276 | 0.047 | 0.250 | 0.743 | 0.743 | 0.94 | 0.008 |
| mlp | tier2 | 0.270 | 0.051 | 0.246 | 0.734 | 0.734 | 5.48 | 0.001 |
| knn | tier1 | 0.263 | 0.016 | 0.240 | 0.719 | 0.719 | 0.00 | 0.035 |
| voting | tier3 | 0.260 | 0.034 | 0.238 | 0.745 | 0.745 | 12.96 | 0.787 |
| late_fusion | tier3 | 0.251 | 0.030 | 0.227 | 0.713 | 0.713 | 8.37 | 0.456 |
| decision_tree | tier1 | 0.250 | 0.033 | 0.241 | 0.680 | 0.680 | 0.54 | 0.001 |
| random_forest | tier1 | 0.249 | 0.020 | 0.228 | 0.748 | 0.748 | 0.29 | 0.039 |
| transformer | tier2 | 0.241 | 0.015 | 0.225 | 0.710 | 0.710 | 23.61 | 0.004 |
| lstm | tier2 | 0.224 | 0.016 | 0.225 | 0.719 | 0.719 | 9.20 | 0.003 |
| svm | tier1 | 0.216 | 0.015 | 0.210 | 0.735 | 0.735 | 8.81 | 0.745 |
| cnn1d | tier2 | 0.161 | 0.009 | 0.166 | 0.649 | 0.649 | 11.95 | 0.022 |
| adaboost | tier1 | 0.140 | 0.008 | 0.143 | 0.557 | 0.557 | 3.43 | 0.015 |
| naive_bayes | tier1 | 0.066 | 0.011 | 0.253 | 0.083 | 0.083 | 0.01 | 0.016 |

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/native150__stacking.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
