# run_013_v3-tasklevel

Created 2026-09-26 13:41 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

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
| stacking | tier3 | 0.316 | 0.009 | 0.294 | 0.410 | 0.410 | 15.45 | 0.759 |
| xgboost | tier1 | 0.304 | 0.017 | 0.283 | 0.403 | 0.403 | 3.50 | 0.005 |
| voting | tier3 | 0.292 | 0.009 | 0.279 | 0.403 | 0.403 | 11.73 | 0.797 |
| lightgbm | tier1 | 0.291 | 0.010 | 0.270 | 0.398 | 0.398 | 2.50 | 0.011 |
| mlp | tier2 | 0.284 | 0.011 | 0.278 | 0.375 | 0.375 | 4.09 | 0.001 |
| random_forest | tier1 | 0.282 | 0.010 | 0.256 | 0.396 | 0.396 | 0.26 | 0.043 |
| late_fusion | tier3 | 0.259 | 0.009 | 0.239 | 0.380 | 0.380 | 9.98 | 0.623 |
| transformer | tier2 | 0.249 | 0.008 | 0.247 | 0.349 | 0.349 | 17.30 | 0.004 |
| svm | tier1 | 0.243 | 0.009 | 0.229 | 0.381 | 0.381 | 8.06 | 0.702 |
| knn | tier1 | 0.231 | 0.007 | 0.223 | 0.338 | 0.338 | 0.00 | 0.031 |
| lstm | tier2 | 0.224 | 0.011 | 0.226 | 0.352 | 0.352 | 6.01 | 0.003 |
| decision_tree | tier1 | 0.223 | 0.008 | 0.218 | 0.291 | 0.291 | 0.42 | 0.001 |
| cnn1d | tier2 | 0.110 | 0.015 | 0.119 | 0.271 | 0.271 | 9.62 | 0.020 |
| naive_bayes | tier1 | 0.073 | 0.006 | 0.210 | 0.061 | 0.061 | 0.00 | 0.025 |

### cnn (512 dims: cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.001 | 0.071 | 0.212 | 0.212 | 0.00 | 0.000 |
| stacking | tier3 | 0.246 | 0.013 | 0.229 | 0.358 | 0.358 | 35.34 | 1.954 |
| voting | tier3 | 0.231 | 0.008 | 0.220 | 0.358 | 0.358 | 24.66 | 1.984 |
| late_fusion | tier3 | 0.228 | 0.017 | 0.210 | 0.346 | 0.346 | 17.93 | 0.960 |
| mlp | tier2 | 0.225 | 0.013 | 0.224 | 0.331 | 0.331 | 3.57 | 0.001 |
| xgboost | tier1 | 0.220 | 0.007 | 0.204 | 0.347 | 0.347 | 21.82 | 0.007 |
| lightgbm | tier1 | 0.217 | 0.013 | 0.200 | 0.346 | 0.346 | 4.47 | 0.014 |
| random_forest | tier1 | 0.213 | 0.019 | 0.196 | 0.342 | 0.342 | 0.72 | 0.043 |
| knn | tier1 | 0.198 | 0.006 | 0.198 | 0.309 | 0.309 | 0.00 | 0.064 |
| lstm | tier2 | 0.197 | 0.010 | 0.197 | 0.305 | 0.305 | 8.36 | 0.031 |
| svm | tier1 | 0.196 | 0.007 | 0.192 | 0.346 | 0.346 | 20.59 | 1.994 |
| transformer | tier2 | 0.193 | 0.011 | 0.193 | 0.293 | 0.293 | 18.50 | 0.004 |
| decision_tree | tier1 | 0.154 | 0.009 | 0.154 | 0.230 | 0.230 | 3.01 | 0.001 |
| naive_bayes | tier1 | 0.116 | 0.008 | 0.245 | 0.127 | 0.127 | 0.01 | 0.076 |
| cnn1d | tier2 | 0.066 | 0.005 | 0.092 | 0.238 | 0.238 | 22.06 | 0.093 |

### native150+cnn (662 dims: ocr_native + ui + visual + interaction + cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.001 | 0.071 | 0.212 | 0.212 | 0.00 | 0.000 |
| stacking | tier3 | 0.303 | 0.010 | 0.283 | 0.404 | 0.404 | 47.99 | 2.940 |
| mlp | tier2 | 0.295 | 0.015 | 0.286 | 0.376 | 0.376 | 3.60 | 0.001 |
| voting | tier3 | 0.294 | 0.005 | 0.278 | 0.402 | 0.402 | 32.16 | 2.910 |
| xgboost | tier1 | 0.285 | 0.008 | 0.261 | 0.397 | 0.397 | 28.21 | 0.007 |
| lightgbm | tier1 | 0.274 | 0.012 | 0.249 | 0.391 | 0.391 | 6.12 | 0.014 |
| late_fusion | tier3 | 0.257 | 0.008 | 0.235 | 0.368 | 0.368 | 23.21 | 1.213 |
| transformer | tier2 | 0.257 | 0.008 | 0.257 | 0.353 | 0.353 | 19.09 | 0.005 |
| random_forest | tier1 | 0.251 | 0.004 | 0.229 | 0.383 | 0.383 | 0.72 | 0.044 |
| svm | tier1 | 0.238 | 0.013 | 0.224 | 0.381 | 0.381 | 27.36 | 2.880 |
| knn | tier1 | 0.224 | 0.012 | 0.219 | 0.333 | 0.333 | 0.00 | 0.078 |
| lstm | tier2 | 0.219 | 0.014 | 0.216 | 0.328 | 0.328 | 8.41 | 0.044 |
| decision_tree | tier1 | 0.179 | 0.007 | 0.177 | 0.266 | 0.266 | 3.43 | 0.001 |
| naive_bayes | tier1 | 0.107 | 0.005 | 0.250 | 0.101 | 0.101 | 0.01 | 0.096 |
| cnn1d | tier2 | 0.077 | 0.009 | 0.101 | 0.253 | 0.253 | 27.41 | 0.132 |

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
- `models/cnn__svm.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__naive_bayes.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__decision_tree.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__random_forest.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__knn.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__xgboost.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__lightgbm.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__mlp.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__cnn1d.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__lstm.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__transformer.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__voting.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__stacking.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__late_fusion.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__svm.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__naive_bayes.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__decision_tree.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__random_forest.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__knn.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__xgboost.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__lightgbm.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__mlp.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__cnn1d.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__lstm.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__transformer.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__voting.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__stacking.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__late_fusion.joblib` - native150+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
