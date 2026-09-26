# run_014_v3-balanced

Created 2026-09-26 14:42 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 6991 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, GrassGIS, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 6991 rows (one per recording: its segments averaged).

**Labels.** `csv:labels/labels_v3.csv`. One label per recording, and one row per recording, so the row and the label describe the same thing.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): one row per recording, so a recording is on one side by construction. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| configure_option | 1480 | 1480 |
| navigate_view | 1266 | 1266 |
| format_style | 908 | 908 |
| edit_content | 830 | 830 |
| create_item | 770 | 770 |
| other | 399 | 399 |
| insert_element | 352 | 352 |
| file_manage | 290 | 290 |
| delete_remove | 174 | 174 |
| search_filter | 157 | 157 |
| organize_items | 150 | 150 |
| communicate | 127 | 127 |
| media_control | 54 | 54 |
| run_command | 34 | 34 |

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.001 | 0.071 | 0.212 | 0.212 | 0.00 | 0.000 |
| xgboost | tier1 | 0.318 | 0.015 | 0.301 | 0.405 | 0.405 | 3.82 | 0.004 |
| stacking | tier3 | 0.315 | 0.006 | 0.300 | 0.399 | 0.399 | 21.15 | 0.904 |
| voting | tier3 | 0.312 | 0.017 | 0.325 | 0.395 | 0.395 | 15.46 | 0.926 |
| lightgbm | tier1 | 0.300 | 0.009 | 0.278 | 0.398 | 0.398 | 2.18 | 0.012 |
| mlp | tier2 | 0.292 | 0.013 | 0.317 | 0.361 | 0.361 | 6.04 | 0.001 |
| svm | tier1 | 0.286 | 0.011 | 0.298 | 0.379 | 0.379 | 9.71 | 0.799 |
| late_fusion | tier3 | 0.284 | 0.010 | 0.262 | 0.385 | 0.385 | 12.58 | 0.703 |
| random_forest | tier1 | 0.282 | 0.009 | 0.264 | 0.390 | 0.390 | 0.29 | 0.040 |
| transformer | tier2 | 0.259 | 0.013 | 0.293 | 0.333 | 0.333 | 29.84 | 0.003 |
| lstm | tier2 | 0.249 | 0.009 | 0.279 | 0.331 | 0.331 | 16.78 | 0.002 |
| knn | tier1 | 0.240 | 0.010 | 0.268 | 0.318 | 0.318 | 0.00 | 0.038 |
| decision_tree | tier1 | 0.210 | 0.013 | 0.209 | 0.288 | 0.288 | 0.49 | 0.001 |
| cnn1d | tier2 | 0.137 | 0.015 | 0.186 | 0.270 | 0.270 | 15.09 | 0.019 |
| naive_bayes | tier1 | 0.073 | 0.005 | 0.214 | 0.062 | 0.062 | 0.00 | 0.023 |

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/native150__svm.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__naive_bayes.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__decision_tree.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__random_forest.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__knn.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__xgboost.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__lightgbm.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__mlp.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__cnn1d.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__lstm.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__transformer.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__voting.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__stacking.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__late_fusion.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
