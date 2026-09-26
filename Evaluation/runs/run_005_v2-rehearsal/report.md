# run_005_v2-rehearsal

Created 2026-09-23 19:54 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 482 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, GrassGIS, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 1443 segments (the backend's segmentation: actions more than 2 s apart start a new segment).

**Labels.** `csv:labels/labels_v2.csv`. One label per task, copied to all of its segments.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): all segments of a recording are on the same side. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| navigate_view | 126 | 299 |
| configure_option | 119 | 386 |
| edit_content | 47 | 138 |
| create_item | 46 | 177 |
| format_style | 35 | 116 |
| other | 27 | 77 |
| search_filter | 18 | 49 |
| file_manage | 15 | 62 |
| run_command | 13 | 25 |
| insert_element | 12 | 38 |
| delete_remove | 11 | 33 |
| organize_items | 8 | 28 |
| communicate | 5 | 15 |

Left out (fewer than 3 tasks): media_control (1)

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.033 | 0.003 | 0.077 | 0.268 | 0.247 | 0.00 | 0.000 |
| mlp | tier2 | 0.173 | 0.033 | 0.165 | 0.290 | 0.299 | 4.06 | 0.004 |
| voting | tier3 | 0.173 | 0.029 | 0.167 | 0.308 | 0.307 | 3.28 | 1.043 |
| random_forest | tier1 | 0.156 | 0.027 | 0.151 | 0.282 | 0.274 | 0.24 | 0.497 |
| stacking | tier3 | 0.155 | 0.024 | 0.149 | 0.297 | 0.305 | 3.85 | 0.943 |
| lightgbm | tier1 | 0.152 | 0.018 | 0.144 | 0.277 | 0.284 | 18.48 | 0.034 |
| xgboost | tier1 | 0.145 | 0.030 | 0.138 | 0.277 | 0.272 | 12.28 | 0.045 |
| knn | tier1 | 0.145 | 0.019 | 0.149 | 0.273 | 0.297 | 0.00 | 0.219 |
| late_fusion | tier3 | 0.131 | 0.012 | 0.128 | 0.272 | 0.290 | 1.68 | 0.991 |
| decision_tree | tier1 | 0.130 | 0.038 | 0.128 | 0.205 | 0.228 | 0.11 | 0.002 |
| svm | tier1 | 0.123 | 0.019 | 0.131 | 0.314 | 0.322 | 0.99 | 0.379 |
| transformer | tier2 | 0.115 | 0.023 | 0.126 | 0.257 | 0.261 | 11.98 | 0.033 |
| lstm | tier2 | 0.091 | 0.019 | 0.098 | 0.228 | 0.226 | 4.32 | 0.023 |
| naive_bayes | tier1 | 0.082 | 0.018 | 0.163 | 0.082 | 0.085 | 0.00 | 0.028 |
| cnn1d | tier2 | 0.058 | 0.009 | 0.083 | 0.261 | 0.255 | 10.52 | 0.104 |

### cnn (512 dims: cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.033 | 0.003 | 0.077 | 0.268 | 0.247 | 0.00 | 0.000 |
| lstm | tier2 | 0.163 | 0.023 | 0.159 | 0.262 | 0.280 | 4.22 | 0.025 |
| stacking | tier3 | 0.157 | 0.019 | 0.156 | 0.276 | 0.280 | 5.31 | 1.147 |
| voting | tier3 | 0.155 | 0.026 | 0.154 | 0.274 | 0.268 | 7.03 | 1.095 |
| mlp | tier2 | 0.152 | 0.025 | 0.149 | 0.253 | 0.272 | 1.86 | 0.004 |
| transformer | tier2 | 0.151 | 0.024 | 0.150 | 0.240 | 0.255 | 10.29 | 0.030 |
| late_fusion | tier3 | 0.150 | 0.021 | 0.148 | 0.285 | 0.288 | 2.70 | 0.855 |
| svm | tier1 | 0.145 | 0.035 | 0.150 | 0.302 | 0.301 | 2.01 | 0.714 |
| random_forest | tier1 | 0.144 | 0.023 | 0.142 | 0.279 | 0.276 | 0.39 | 0.508 |
| knn | tier1 | 0.142 | 0.020 | 0.149 | 0.254 | 0.284 | 0.00 | 0.113 |
| naive_bayes | tier1 | 0.141 | 0.034 | 0.149 | 0.165 | 0.153 | 0.01 | 0.136 |
| xgboost | tier1 | 0.141 | 0.024 | 0.139 | 0.275 | 0.284 | 34.43 | 0.041 |
| lightgbm | tier1 | 0.128 | 0.013 | 0.124 | 0.263 | 0.270 | 14.66 | 0.029 |
| decision_tree | tier1 | 0.128 | 0.022 | 0.127 | 0.196 | 0.195 | 0.89 | 0.003 |
| cnn1d | tier2 | 0.054 | 0.010 | 0.085 | 0.276 | 0.268 | 23.36 | 0.329 |

## Read before quoting a number

- Left out for having fewer than 3 tasks: media_control (1).

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/native150__mlp.joblib` - native150, refitted on all 1443 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__lstm.joblib` - cnn, refitted on all 1443 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
