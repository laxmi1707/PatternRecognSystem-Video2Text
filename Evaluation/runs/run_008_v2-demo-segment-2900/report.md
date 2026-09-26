# run_008_v2-demo-segment-2900

Created 2026-09-24 14:52 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 2987 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, GrassGIS, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 9778 rows (one per segment - the backend's segmentation: actions more than 2 s apart start a new segment).

**Labels.** `csv:labels/labels_v2.csv`. One label per task, copied to all of its segments - so a segment showing a password prompt still carries the label of the recording around it.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): all segments of a recording are on the same side. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| configure_option | 606 | 1980 |
| navigate_view | 589 | 1386 |
| format_style | 397 | 1383 |
| edit_content | 365 | 1258 |
| create_item | 329 | 1424 |
| other | 148 | 411 |
| insert_element | 134 | 578 |
| file_manage | 114 | 461 |
| delete_remove | 77 | 234 |
| communicate | 64 | 209 |
| search_filter | 59 | 158 |
| organize_items | 57 | 169 |
| media_control | 26 | 74 |
| run_command | 22 | 53 |

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.024 | 0.002 | 0.071 | 0.203 | 0.203 | 0.00 | 0.000 |
| xgboost | tier1 | 0.242 | 0.008 | 0.226 | 0.344 | 0.348 | 111.13 | 0.037 |
| lightgbm | tier1 | 0.231 | 0.015 | 0.216 | 0.340 | 0.341 | 96.97 | 0.033 |
| mlp | tier2 | 0.227 | 0.015 | 0.216 | 0.321 | 0.328 | 75.68 | 0.006 |
| random_forest | tier1 | 0.215 | 0.012 | 0.204 | 0.331 | 0.339 | 1.03 | 0.172 |

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/native150__xgboost.joblib` - native150, refitted on all 9778 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__lightgbm.joblib` - native150, refitted on all 9778 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__random_forest.joblib` - native150, refitted on all 9778 segments; load it with `python -m v2k predict --bundle ...`
- `models/native150__mlp.joblib` - native150, refitted on all 9778 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
