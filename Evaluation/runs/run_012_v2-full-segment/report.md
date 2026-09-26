# run_012_v2-full-segment

Created 2026-09-25 18:03 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 6991 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, GrassGIS, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 23256 rows (one per segment - the backend's segmentation: actions more than 2 s apart start a new segment).

**Labels.** `csv:labels/labels_v2.csv`. One label per task, copied to all of its segments - so a segment showing a password prompt still carries the label of the recording around it.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): all segments of a recording are on the same side. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| configure_option | 1477 | 4920 |
| navigate_view | 1265 | 2855 |
| format_style | 908 | 3224 |
| edit_content | 830 | 3060 |
| create_item | 769 | 3399 |
| other | 398 | 1222 |
| insert_element | 352 | 1400 |
| file_manage | 290 | 1171 |
| delete_remove | 174 | 501 |
| search_filter | 157 | 416 |
| organize_items | 150 | 415 |
| communicate | 127 | 420 |
| media_control | 54 | 151 |
| run_command | 40 | 102 |

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.002 | 0.071 | 0.212 | 0.211 | 0.00 | 0.000 |
| voting | tier3 | 0.243 | 0.012 | 0.230 | 0.351 | 0.360 | 109.37 | 2.874 |
| lightgbm | tier1 | 0.241 | 0.012 | 0.226 | 0.336 | 0.346 | 3.19 | 0.010 |
| xgboost | tier1 | 0.239 | 0.012 | 0.225 | 0.344 | 0.354 | 4.75 | 0.005 |
| random_forest | tier1 | 0.227 | 0.011 | 0.211 | 0.341 | 0.348 | 0.66 | 0.013 |
| mlp | tier2 | 0.227 | 0.008 | 0.218 | 0.325 | 0.343 | 15.10 | 0.000 |
| transformer | tier2 | 0.205 | 0.005 | 0.202 | 0.299 | 0.307 | 79.40 | 0.009 |
| svm | tier1 | 0.205 | 0.018 | 0.194 | 0.331 | 0.343 | 94.86 | 2.797 |
| knn | tier1 | 0.201 | 0.004 | 0.195 | 0.293 | 0.306 | 0.00 | 0.059 |
| lstm | tier2 | 0.192 | 0.013 | 0.189 | 0.297 | 0.315 | 23.75 | 0.006 |
| decision_tree | tier1 | 0.173 | 0.002 | 0.167 | 0.266 | 0.281 | 1.35 | 0.000 |
| cnn1d | tier2 | 0.126 | 0.012 | 0.131 | 0.259 | 0.273 | 43.47 | 0.028 |
| naive_bayes | tier1 | 0.046 | 0.004 | 0.154 | 0.035 | 0.034 | 0.01 | 0.022 |

### native150+cnn (662 dims: ocr_native + ui + visual + interaction + cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.002 | 0.071 | 0.212 | 0.211 | 0.00 | 0.000 |
| voting | tier3 | 0.242 | 0.014 | 0.231 | 0.343 | 0.358 | 370.59 | 12.210 |
| xgboost | tier1 | 0.233 | 0.010 | 0.217 | 0.342 | 0.354 | 40.38 | 0.006 |
| mlp | tier2 | 0.232 | 0.010 | 0.225 | 0.317 | 0.337 | 13.81 | 0.001 |
| lightgbm | tier1 | 0.228 | 0.010 | 0.212 | 0.335 | 0.345 | 7.98 | 0.012 |
| svm | tier1 | 0.223 | 0.010 | 0.211 | 0.342 | 0.352 | 359.33 | 13.957 |
| knn | tier1 | 0.214 | 0.005 | 0.209 | 0.309 | 0.322 | 0.01 | 0.205 |
| random_forest | tier1 | 0.210 | 0.014 | 0.195 | 0.333 | 0.342 | 2.58 | 0.013 |
| transformer | tier2 | 0.206 | 0.006 | 0.203 | 0.300 | 0.314 | 70.11 | 0.004 |
| lstm | tier2 | 0.194 | 0.009 | 0.189 | 0.284 | 0.301 | 28.72 | 0.003 |
| decision_tree | tier1 | 0.158 | 0.007 | 0.155 | 0.247 | 0.262 | 12.97 | 0.001 |
| naive_bayes | tier1 | 0.090 | 0.007 | 0.200 | 0.082 | 0.075 | 0.05 | 0.105 |
| cnn1d | tier2 | 0.081 | 0.013 | 0.099 | 0.235 | 0.224 | 98.20 | 0.101 |

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/native150__svm.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__naive_bayes.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__decision_tree.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__random_forest.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__knn.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__xgboost.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__lightgbm.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__mlp.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__cnn1d.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__lstm.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__transformer.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__voting.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__svm.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__naive_bayes.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__decision_tree.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__random_forest.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__knn.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__xgboost.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__lightgbm.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__mlp.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__cnn1d.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__lstm.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__transformer.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__voting.joblib` - native150+cnn, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
