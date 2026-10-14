# run_028_segmentlevel

Created 2026-09-30 11:12 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 6991 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, GrassGIS, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 23256 rows (one per segment - the backend's segmentation: actions more than 2 s apart start a new segment).

**Labels.** `keyword` - the backend's derive_activity_label, a keyword match on the task instruction. One label per task, copied to all of its segments - so a segment showing a password prompt still carries the label of the recording around it.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): all segments of a recording are on the same side. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| other | 3868 | 13118 |
| coding_editing | 2586 | 8274 |
| docker_workflow | 214 | 846 |
| documentation | 192 | 631 |
| git_operations | 60 | 199 |
| aws_console | 41 | 84 |
| debugging | 25 | 79 |
| kubernetes_ops | 5 | 25 |

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### native150 (150 dims: ocr_native + ui + visual + interaction)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.090 | 0.006 | 0.125 | 0.564 | 0.553 | 0.00 | 0.000 |
| stacking | tier3 | 0.288 | 0.039 | 0.260 | 0.701 | 0.718 | 142.73 | 2.089 |
| mlp | tier2 | 0.275 | 0.026 | 0.246 | 0.720 | 0.732 | 14.79 | 0.000 |
| xgboost | tier1 | 0.262 | 0.030 | 0.239 | 0.730 | 0.737 | 2.36 | 0.002 |
| random_forest | tier1 | 0.258 | 0.038 | 0.232 | 0.734 | 0.743 | 0.83 | 0.011 |
| lightgbm | tier1 | 0.244 | 0.038 | 0.236 | 0.711 | 0.728 | 1.35 | 0.007 |
| svm | tier1 | 0.214 | 0.019 | 0.207 | 0.728 | 0.737 | 80.84 | 1.729 |

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/native150__stacking.joblib` - native150, refitted on all 23256 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
