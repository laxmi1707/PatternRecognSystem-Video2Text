# run_011_v2-full-ablation

Created 2026-09-25 17:59 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

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

### ocr_native (50 dims: ocr_native)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.000 | 0.071 | 0.211 | 0.211 | 0.00 | 0.000 |
| lightgbm | tier1 | 0.280 | 0.026 | 0.259 | 0.367 | 0.367 | 1.34 | 0.009 |
| random_forest | tier1 | 0.252 | 0.025 | 0.236 | 0.383 | 0.383 | 0.15 | 0.042 |
| mlp | tier2 | 0.240 | 0.018 | 0.232 | 0.355 | 0.355 | 4.15 | 0.001 |

### ui (30 dims: ui)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.000 | 0.071 | 0.211 | 0.211 | 0.00 | 0.000 |
| lightgbm | tier1 | 0.099 | 0.011 | 0.108 | 0.234 | 0.234 | 0.73 | 0.010 |
| random_forest | tier1 | 0.086 | 0.004 | 0.100 | 0.229 | 0.229 | 0.16 | 0.049 |
| mlp | tier2 | 0.063 | 0.006 | 0.092 | 0.237 | 0.237 | 3.92 | 0.001 |

### visual (40 dims: visual)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.000 | 0.071 | 0.211 | 0.211 | 0.00 | 0.000 |
| random_forest | tier1 | 0.223 | 0.020 | 0.204 | 0.340 | 0.340 | 0.30 | 0.050 |
| lightgbm | tier1 | 0.195 | 0.018 | 0.182 | 0.316 | 0.316 | 0.77 | 0.012 |
| mlp | tier2 | 0.121 | 0.005 | 0.128 | 0.271 | 0.271 | 4.00 | 0.001 |

### interaction (30 dims: interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.000 | 0.071 | 0.211 | 0.211 | 0.00 | 0.000 |
| random_forest | tier1 | 0.183 | 0.013 | 0.177 | 0.304 | 0.304 | 0.18 | 0.050 |
| lightgbm | tier1 | 0.176 | 0.005 | 0.168 | 0.294 | 0.294 | 0.85 | 0.011 |
| mlp | tier2 | 0.131 | 0.005 | 0.142 | 0.286 | 0.286 | 3.73 | 0.001 |

### cnn (512 dims: cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.025 | 0.000 | 0.071 | 0.211 | 0.211 | 0.00 | 0.000 |
| mlp | tier2 | 0.230 | 0.008 | 0.226 | 0.333 | 0.333 | 4.39 | 0.001 |
| random_forest | tier1 | 0.212 | 0.022 | 0.195 | 0.340 | 0.340 | 0.83 | 0.044 |
| lightgbm | tier1 | 0.211 | 0.020 | 0.194 | 0.337 | 0.337 | 4.55 | 0.013 |

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/ocr_native__lightgbm.joblib` - ocr_native, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/ui__lightgbm.joblib` - ui, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/visual__random_forest.joblib` - visual, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/interaction__random_forest.joblib` - interaction, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__mlp.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
