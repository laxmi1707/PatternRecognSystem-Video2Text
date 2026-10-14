# run_027_augment5

Created 2026-09-29 19:58 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 6991 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, GrassGIS, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 6991 rows (one per recording: its segments averaged).

**Labels.** `keyword` - the backend's derive_activity_label, a keyword match on the task instruction. One label per recording, and one row per recording, so the row and the label describe the same thing.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): one row per recording, so a recording is on one side by construction. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. Noise augmentation x5 on training folds only.

## Classes

| class | tasks | segments |
|---|---:|---:|
| other | 3868 | 3868 |
| coding_editing | 2586 | 2586 |
| docker_workflow | 214 | 214 |
| documentation | 192 | 192 |
| git_operations | 60 | 60 |
| aws_console | 41 | 41 |
| debugging | 25 | 25 |
| kubernetes_ops | 5 | 5 |

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.089 | 0.005 | 0.125 | 0.553 | 0.553 | 0.00 | 0.000 |
| stacking | tier3 | 0.304 | 0.055 | 0.277 | 0.731 | 0.731 | 876.74 | 4.632 |
| svm | tier1 | 0.295 | 0.039 | 0.265 | 0.736 | 0.736 | 687.01 | 5.450 |
| xgboost | tier1 | 0.287 | 0.040 | 0.259 | 0.745 | 0.745 | 4.90 | 0.004 |
| lightgbm | tier1 | 0.271 | 0.024 | 0.258 | 0.724 | 0.724 | 1.57 | 0.008 |
| random_forest | tier1 | 0.268 | 0.039 | 0.242 | 0.752 | 0.752 | 3.70 | 0.054 |

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/native150__stacking.joblib` - native150, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
