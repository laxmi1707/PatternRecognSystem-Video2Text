# run_009_v2-full-modelpick

Created 2026-09-25 15:53 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 2499 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 8329 rows (one per segment - the backend's segmentation: actions more than 2 s apart start a new segment). Sampled from the 6991 cached recordings that have a label, drawn per class so the balance is unchanged; whole recordings, never single rows.

**Labels.** `csv:labels/labels_v2.csv`. One label per task, copied to all of its segments - so a segment showing a password prompt still carries the label of the recording around it.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): all segments of a recording are on the same side. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| configure_option | 528 | 1785 |
| navigate_view | 452 | 1014 |
| format_style | 325 | 1137 |
| edit_content | 297 | 1064 |
| create_item | 275 | 1183 |
| other | 142 | 441 |
| insert_element | 126 | 546 |
| file_manage | 104 | 442 |
| delete_remove | 62 | 189 |
| search_filter | 56 | 152 |
| organize_items | 54 | 133 |
| communicate | 45 | 155 |
| media_control | 19 | 49 |
| run_command | 14 | 39 |

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.001 | 0.071 | 0.214 | 0.211 | 0.00 | 0.000 |
| stacking | tier3 | 0.205 | 0.023 | 0.199 | 0.316 | 0.324 | 22.45 | 0.935 |
| lightgbm | tier1 | 0.204 | 0.023 | 0.192 | 0.307 | 0.315 | 2.14 | 0.011 |
| voting | tier3 | 0.204 | 0.028 | 0.197 | 0.315 | 0.323 | 16.66 | 0.956 |
| mlp | tier2 | 0.196 | 0.022 | 0.192 | 0.298 | 0.304 | 5.75 | 0.001 |
| xgboost | tier1 | 0.195 | 0.029 | 0.186 | 0.307 | 0.316 | 3.65 | 0.006 |
| random_forest | tier1 | 0.184 | 0.015 | 0.176 | 0.304 | 0.310 | 0.28 | 0.038 |
| late_fusion | tier3 | 0.184 | 0.018 | 0.175 | 0.291 | 0.293 | 13.40 | 0.742 |
| svm | tier1 | 0.174 | 0.023 | 0.170 | 0.311 | 0.313 | 11.47 | 0.877 |
| transformer | tier2 | 0.172 | 0.014 | 0.171 | 0.271 | 0.279 | 28.39 | 0.004 |
| knn | tier1 | 0.170 | 0.011 | 0.167 | 0.268 | 0.271 | 0.00 | 0.037 |
| lstm | tier2 | 0.161 | 0.014 | 0.163 | 0.262 | 0.273 | 9.70 | 0.010 |
| decision_tree | tier1 | 0.149 | 0.009 | 0.144 | 0.235 | 0.240 | 0.46 | 0.001 |
| cnn1d | tier2 | 0.105 | 0.015 | 0.116 | 0.244 | 0.235 | 16.55 | 0.031 |
| naive_bayes | tier1 | 0.052 | 0.008 | 0.151 | 0.049 | 0.044 | 0.00 | 0.024 |

### cnn (512 dims: cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.001 | 0.071 | 0.214 | 0.211 | 0.00 | 0.000 |
| voting | tier3 | 0.188 | 0.008 | 0.182 | 0.283 | 0.291 | 31.66 | 2.531 |
| stacking | tier3 | 0.183 | 0.007 | 0.177 | 0.285 | 0.291 | 47.85 | 2.549 |
| knn | tier1 | 0.179 | 0.008 | 0.178 | 0.269 | 0.273 | 0.00 | 0.072 |
| mlp | tier2 | 0.178 | 0.009 | 0.175 | 0.261 | 0.271 | 5.60 | 0.001 |
| late_fusion | tier3 | 0.172 | 0.012 | 0.167 | 0.285 | 0.287 | 22.84 | 1.132 |
| svm | tier1 | 0.172 | 0.014 | 0.166 | 0.299 | 0.298 | 25.62 | 2.387 |
| lightgbm | tier1 | 0.158 | 0.017 | 0.153 | 0.276 | 0.282 | 4.88 | 0.013 |
| lstm | tier2 | 0.157 | 0.011 | 0.155 | 0.253 | 0.263 | 8.72 | 0.035 |
| xgboost | tier1 | 0.154 | 0.012 | 0.152 | 0.284 | 0.291 | 23.11 | 0.008 |
| transformer | tier2 | 0.150 | 0.013 | 0.147 | 0.243 | 0.269 | 27.89 | 0.005 |
| random_forest | tier1 | 0.142 | 0.008 | 0.143 | 0.280 | 0.282 | 0.81 | 0.032 |
| decision_tree | tier1 | 0.129 | 0.015 | 0.128 | 0.199 | 0.204 | 3.40 | 0.001 |
| naive_bayes | tier1 | 0.120 | 0.009 | 0.188 | 0.154 | 0.133 | 0.01 | 0.075 |
| cnn1d | tier2 | 0.066 | 0.012 | 0.092 | 0.228 | 0.216 | 30.66 | 0.083 |

### native150+cnn (662 dims: ocr_native + ui + visual + interaction + cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.001 | 0.071 | 0.214 | 0.211 | 0.00 | 0.000 |
| mlp | tier2 | 0.208 | 0.015 | 0.202 | 0.292 | 0.303 | 5.56 | 0.001 |
| voting | tier3 | 0.203 | 0.010 | 0.198 | 0.309 | 0.313 | 42.32 | 3.730 |
| stacking | tier3 | 0.197 | 0.015 | 0.193 | 0.304 | 0.311 | 65.75 | 3.704 |
| late_fusion | tier3 | 0.193 | 0.014 | 0.186 | 0.307 | 0.311 | 31.12 | 1.446 |
| svm | tier1 | 0.188 | 0.015 | 0.180 | 0.316 | 0.314 | 35.58 | 3.643 |
| knn | tier1 | 0.184 | 0.019 | 0.183 | 0.283 | 0.284 | 0.00 | 0.093 |
| transformer | tier2 | 0.183 | 0.023 | 0.183 | 0.261 | 0.274 | 28.25 | 0.004 |
| xgboost | tier1 | 0.175 | 0.016 | 0.169 | 0.299 | 0.300 | 28.62 | 0.008 |
| lstm | tier2 | 0.167 | 0.006 | 0.164 | 0.250 | 0.258 | 8.96 | 0.004 |
| random_forest | tier1 | 0.166 | 0.012 | 0.163 | 0.301 | 0.306 | 0.81 | 0.036 |
| lightgbm | tier1 | 0.155 | 0.029 | 0.151 | 0.272 | 0.267 | 6.42 | 0.013 |
| decision_tree | tier1 | 0.132 | 0.014 | 0.131 | 0.227 | 0.239 | 4.13 | 0.001 |
| naive_bayes | tier1 | 0.101 | 0.005 | 0.192 | 0.103 | 0.093 | 0.02 | 0.099 |
| cnn1d | tier2 | 0.065 | 0.011 | 0.094 | 0.234 | 0.223 | 36.69 | 0.120 |

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/native150__stacking.joblib` - native150, refitted on all 8329 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__voting.joblib` - cnn, refitted on all 8329 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150+cnn__mlp.joblib` - native150+cnn, refitted on all 8329 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
