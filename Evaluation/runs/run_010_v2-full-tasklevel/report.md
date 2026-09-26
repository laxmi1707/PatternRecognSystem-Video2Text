# run_010_v2-full-tasklevel

Created 2026-09-25 16:55 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 6991 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, GrassGIS, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 6991 rows (one per recording: its segments averaged).

**Labels.** `csv:labels/labels_v2.csv`. One label per recording, and one row per recording, so the row and the label describe the same thing.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): one row per recording, so a recording is on one side by construction. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| configure_option | 1477 | 1477 |
| navigate_view | 1265 | 1265 |
| format_style | 908 | 908 |
| edit_content | 830 | 830 |
| create_item | 769 | 769 |
| other | 398 | 398 |
| insert_element | 352 | 352 |
| file_manage | 290 | 290 |
| delete_remove | 174 | 174 |
| search_filter | 157 | 157 |
| organize_items | 150 | 150 |
| communicate | 127 | 127 |
| media_control | 54 | 54 |
| run_command | 40 | 40 |

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.000 | 0.071 | 0.211 | 0.211 | 0.00 | 0.000 |
| stacking | tier3 | 0.300 | 0.017 | 0.282 | 0.409 | 0.409 | 16.25 | 0.768 |
| lightgbm | tier1 | 0.299 | 0.022 | 0.271 | 0.398 | 0.398 | 2.01 | 0.011 |
| voting | tier3 | 0.294 | 0.018 | 0.278 | 0.404 | 0.404 | 12.20 | 0.806 |
| xgboost | tier1 | 0.292 | 0.025 | 0.271 | 0.400 | 0.400 | 3.77 | 0.005 |
| mlp | tier2 | 0.292 | 0.007 | 0.281 | 0.382 | 0.382 | 4.50 | 0.001 |
| random_forest | tier1 | 0.269 | 0.018 | 0.248 | 0.400 | 0.400 | 0.25 | 0.045 |
| late_fusion | tier3 | 0.269 | 0.013 | 0.245 | 0.379 | 0.379 | 9.90 | 0.615 |
| transformer | tier2 | 0.241 | 0.012 | 0.243 | 0.358 | 0.358 | 23.37 | 0.004 |
| svm | tier1 | 0.239 | 0.019 | 0.226 | 0.379 | 0.379 | 7.94 | 0.697 |
| lstm | tier2 | 0.239 | 0.012 | 0.242 | 0.357 | 0.357 | 7.07 | 0.003 |
| knn | tier1 | 0.227 | 0.004 | 0.220 | 0.336 | 0.336 | 0.00 | 0.032 |
| decision_tree | tier1 | 0.200 | 0.010 | 0.196 | 0.280 | 0.280 | 0.42 | 0.001 |
| cnn1d | tier2 | 0.108 | 0.006 | 0.121 | 0.279 | 0.279 | 13.27 | 0.024 |
| naive_bayes | tier1 | 0.067 | 0.008 | 0.197 | 0.057 | 0.057 | 0.00 | 0.023 |

### cnn (512 dims: cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.000 | 0.071 | 0.211 | 0.211 | 0.00 | 0.000 |
| stacking | tier3 | 0.232 | 0.018 | 0.221 | 0.354 | 0.354 | 35.22 | 1.830 |
| mlp | tier2 | 0.230 | 0.008 | 0.226 | 0.333 | 0.333 | 5.02 | 0.001 |
| voting | tier3 | 0.226 | 0.018 | 0.217 | 0.354 | 0.354 | 25.67 | 1.909 |
| late_fusion | tier3 | 0.220 | 0.017 | 0.206 | 0.347 | 0.347 | 17.42 | 0.957 |
| xgboost | tier1 | 0.214 | 0.023 | 0.199 | 0.346 | 0.346 | 22.26 | 0.007 |
| random_forest | tier1 | 0.212 | 0.022 | 0.195 | 0.340 | 0.340 | 0.70 | 0.036 |
| lightgbm | tier1 | 0.211 | 0.020 | 0.194 | 0.337 | 0.337 | 4.70 | 0.014 |
| knn | tier1 | 0.204 | 0.011 | 0.202 | 0.316 | 0.316 | 0.00 | 0.065 |
| lstm | tier2 | 0.196 | 0.009 | 0.200 | 0.310 | 0.310 | 7.82 | 0.028 |
| svm | tier1 | 0.196 | 0.014 | 0.192 | 0.346 | 0.346 | 20.01 | 1.817 |
| transformer | tier2 | 0.186 | 0.011 | 0.186 | 0.305 | 0.305 | 24.18 | 0.005 |
| decision_tree | tier1 | 0.152 | 0.008 | 0.150 | 0.234 | 0.234 | 2.88 | 0.001 |
| naive_bayes | tier1 | 0.110 | 0.006 | 0.225 | 0.125 | 0.125 | 0.01 | 0.075 |
| cnn1d | tier2 | 0.071 | 0.007 | 0.095 | 0.243 | 0.243 | 25.96 | 0.094 |

### native150+cnn (662 dims: ocr_native + ui + visual + interaction + cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.000 | 0.071 | 0.211 | 0.211 | 0.00 | 0.000 |
| stacking | tier3 | 0.290 | 0.016 | 0.272 | 0.400 | 0.400 | 48.54 | 2.818 |
| mlp | tier2 | 0.289 | 0.014 | 0.277 | 0.372 | 0.372 | 4.97 | 0.001 |
| voting | tier3 | 0.285 | 0.013 | 0.270 | 0.400 | 0.400 | 33.06 | 2.904 |
| lightgbm | tier1 | 0.278 | 0.017 | 0.251 | 0.391 | 0.391 | 6.40 | 0.014 |
| xgboost | tier1 | 0.276 | 0.018 | 0.255 | 0.394 | 0.394 | 28.80 | 0.007 |
| late_fusion | tier3 | 0.250 | 0.021 | 0.230 | 0.366 | 0.366 | 23.09 | 1.220 |
| transformer | tier2 | 0.244 | 0.008 | 0.240 | 0.348 | 0.348 | 23.55 | 0.005 |
| svm | tier1 | 0.240 | 0.016 | 0.226 | 0.384 | 0.384 | 27.28 | 2.827 |
| random_forest | tier1 | 0.237 | 0.018 | 0.219 | 0.379 | 0.379 | 0.69 | 0.035 |
| lstm | tier2 | 0.230 | 0.007 | 0.225 | 0.340 | 0.340 | 7.72 | 0.045 |
| knn | tier1 | 0.218 | 0.010 | 0.216 | 0.331 | 0.331 | 0.00 | 0.073 |
| decision_tree | tier1 | 0.182 | 0.017 | 0.180 | 0.267 | 0.267 | 3.43 | 0.001 |
| naive_bayes | tier1 | 0.109 | 0.006 | 0.243 | 0.105 | 0.105 | 0.01 | 0.099 |
| cnn1d | tier2 | 0.077 | 0.002 | 0.100 | 0.249 | 0.249 | 31.24 | 0.118 |

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
