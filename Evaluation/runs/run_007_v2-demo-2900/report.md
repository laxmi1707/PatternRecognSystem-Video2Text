# run_007_v2-demo-2900

Created 2026-09-24 14:23 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 2968 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, GrassGIS, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 2968 rows (one per recording: its segments averaged).

**Labels.** `csv:labels/labels_v2.csv`. One label per recording, and one row per recording, so the row and the label describe the same thing.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): one row per recording, so a recording is on one side by construction. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| configure_option | 604 | 604 |
| navigate_view | 585 | 585 |
| format_style | 395 | 395 |
| edit_content | 364 | 364 |
| create_item | 323 | 323 |
| other | 146 | 146 |
| insert_element | 134 | 134 |
| file_manage | 114 | 114 |
| delete_remove | 77 | 77 |
| communicate | 63 | 63 |
| search_filter | 58 | 58 |
| organize_items | 57 | 57 |
| media_control | 26 | 26 |
| run_command | 22 | 22 |

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.036 | 0.002 | 0.070 | 0.197 | 0.197 | 0.00 | 0.000 |
| xgboost | tier1 | 0.277 | 0.017 | 0.251 | 0.373 | 0.373 | 13.20 | 0.027 |
| lightgbm | tier1 | 0.255 | 0.024 | 0.234 | 0.379 | 0.379 | 13.81 | 0.030 |
| mlp | tier2 | 0.250 | 0.011 | 0.245 | 0.365 | 0.365 | 5.11 | 0.002 |
| random_forest | tier1 | 0.249 | 0.012 | 0.229 | 0.376 | 0.376 | 0.28 | 0.212 |

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/native150__xgboost.joblib` - native150, refitted on all 2968 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__lightgbm.joblib` - native150, refitted on all 2968 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__random_forest.joblib` - native150, refitted on all 2968 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__mlp.joblib` - native150, refitted on all 2968 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
