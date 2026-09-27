# run_022_v3-all15

Created 2026-09-26 21:40 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

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
| stacking | tier3 | 0.316 | 0.009 | 0.293 | 0.409 | 0.409 | 17.17 | 0.789 |
| xgboost | tier1 | 0.304 | 0.017 | 0.283 | 0.403 | 0.403 | 3.34 | 0.004 |
| lightgbm | tier1 | 0.291 | 0.010 | 0.270 | 0.398 | 0.398 | 1.58 | 0.012 |
| mlp | tier2 | 0.289 | 0.014 | 0.281 | 0.378 | 0.378 | 4.81 | 0.000 |
| voting | tier3 | 0.288 | 0.010 | 0.276 | 0.402 | 0.402 | 13.14 | 0.826 |
| random_forest | tier1 | 0.282 | 0.010 | 0.256 | 0.396 | 0.396 | 0.27 | 0.033 |
| late_fusion | tier3 | 0.259 | 0.009 | 0.239 | 0.380 | 0.380 | 10.13 | 0.622 |
| transformer | tier2 | 0.246 | 0.007 | 0.248 | 0.344 | 0.344 | 27.18 | 0.004 |
| svm | tier1 | 0.243 | 0.009 | 0.229 | 0.381 | 0.381 | 8.15 | 0.705 |
| knn | tier1 | 0.231 | 0.007 | 0.223 | 0.338 | 0.338 | 0.00 | 0.030 |
| lstm | tier2 | 0.224 | 0.011 | 0.226 | 0.352 | 0.352 | 13.32 | 0.004 |
| decision_tree | tier1 | 0.223 | 0.008 | 0.218 | 0.291 | 0.291 | 0.42 | 0.001 |
| adaboost | tier1 | 0.120 | 0.010 | 0.127 | 0.258 | 0.258 | 3.60 | 0.017 |
| cnn1d | tier2 | 0.113 | 0.018 | 0.122 | 0.272 | 0.272 | 13.72 | 0.021 |
| naive_bayes | tier1 | 0.073 | 0.006 | 0.210 | 0.061 | 0.061 | 0.00 | 0.023 |

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/native150__stacking.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
