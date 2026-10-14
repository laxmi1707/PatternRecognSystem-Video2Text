# run_029_appid70

Created 2026-10-02 13:16 · backend main-d866716 (`d866716`) · frame cache `frames_v1_main-d866716`

**Data.** 6991 tasks from 7-Zip, Affine, Anki, Arduino IDE, Atom, Audacity, Bash, Bitwarden, Blender, Bluefish, Brackets, Brave, Chromium, Code__Blocks, Conky, Cryptomator, DuckDuckGo, Eclipse, Flameshot, Frappe Books, FreeCAD, GIMP, GNU Octave, Geany, Gedit, GnuCash, GrassGIS, Inkscape, IntelliJ IDEA, Jitsi, KDevelop, Komodo Edit, Krita, Lemmy, LibreOffice Calc, LibreOffice Draw, LibreOffice Impress, LibreOffice Writer, Matrix, Metabase, Mozilla Firefox, MuseScore, Natron, Nemo, NetBeans, OnlyOffice Calendar, OnlyOffice Document Editor, OnlyOffice Forms, OnlyOffice PDF Forms, OnlyOffice Presentation, OnlyOffice Spreadsheet, OpenBoard, OpenProject, OpenShot, OpenToonz, PDFedit, PyCharm, QGIS, Scribus, Shotcut, Signal, Spyder, Ubuntu Terminal, VSCode, Veusz, WeKan, WordPress, Zotero, Zulip, draw.io; 6991 rows (one per recording: its segments averaged).

**Labels.** `app` - the application being used (ground truth, not the project's activity classes). One label per recording, and one row per recording, so the row and the label describe the same thing.

**Evaluation.** 5-fold cross-validation grouped by task (StratifiedGroupKFold, seed 42): one row per recording, so a recording is on one side by construction. The OCR TF-IDF vocabulary, the scaler and the label encoding are fitted on each training fold only. No augmentation.

## Classes

| class | tasks | segments |
|---|---:|---:|
| SPYDER IDE | 242 | 242 |
| Zulip | 176 | 176 |
| Anki | 163 | 163 |
| Draw.io | 154 | 154 |
| Shotcut | 151 | 151 |
| FreeCAD | 150 | 150 |
| Audacity | 148 | 148 |
| OnlyOffice Presentation | 148 | 148 |
| BRACKETS | 145 | 145 |
| OnlyOffice Document Editor | 140 | 140 |
| OnlyOffice Spreadsheet Editor | 137 | 137 |
| Bitwarden | 127 | 127 |
| Jitsi | 126 | 126 |
| Scribus | 119 | 119 |
| Frappe Books | 118 | 118 |
| LibreOffice Calc | 115 | 115 |
| Zotero | 114 | 114 |
| LibreOffice Draw | 107 | 107 |
| VSCode | 106 | 106 |
| Matrix | 103 | 103 |
| Krita | 102 | 102 |
| Inkscape | 97 | 97 |
| DuckDuckGo | 97 | 97 |
| OnlyOffice PDF Forms | 97 | 97 |
| LibreOffice Impress | 95 | 95 |
| BLUEFISH | 94 | 94 |
| GNU Octave | 91 | 91 |
| LibreOffice Writer | 90 | 90 |
| Lemmy | 90 | 90 |
| Code: :Blocks | 90 | 90 |
| Ubuntu Terminal | 89 | 89 |
| WordPress | 86 | 86 |
| 7-ZIP | 86 | 86 |
| ZOTERO | 85 | 85 |
| Blender | 83 | 83 |
| Atom | 81 | 81 |
| SIGNAL | 81 | 81 |
| GnuCash | 80 | 80 |
| Nemo | 79 | 79 |
| Wekan | 78 | 78 |
| Chromium | 76 | 76 |
| Spyder | 74 | 74 |
| QGIS | 73 | 73 |
| PyCharm | 73 | 73 |
| OpenProject | 72 | 72 |
| Metabase | 72 | 72 |
| Mozilla Firefox | 71 | 71 |
| Bash | 71 | 71 |
| AFFINE | 66 | 66 |
| Gedit | 66 | 66 |
| MuseScore | 64 | 64 |
| OpenToonz | 60 | 60 |
| Komodo Edit | 57 | 57 |
| Code::Blocks | 57 | 57 |
| Signal | 55 | 55 |
| Arduino iDE | 51 | 51 |
| MATRIX | 47 | 47 |
| Eclipse | 46 | 46 |
| IntelliJ IDEA | 46 | 46 |
| GIMP | 45 | 45 |
| Libreoffice Draw | 44 | 44 |
| WeKan | 44 | 44 |
| GEANY | 43 | 43 |
| MUSESCORE | 42 | 42 |
| Libreoffice Impress | 42 | 42 |
| Bluefish | 42 | 42 |
| Brave Browser | 41 | 41 |
| Chromium Browser | 41 | 41 |
| draw.io | 39 | 39 |
| Libreoffice Calc | 38 | 38 |
| Kdevelop | 38 | 38 |
| Brackets | 38 | 38 |
| OpenBoard | 36 | 36 |
| ATOM | 35 | 35 |
| 7-Zip | 32 | 32 |
| OnlyOffice Calender | 32 | 32 |
| OPENSHOT | 32 | 32 |
| Veusz | 31 | 31 |
| OpenShot | 29 | 29 |
| Flameshot | 29 | 29 |
| NetBeans | 27 | 27 |
| CRYPTOMATOR | 27 | 27 |
| MOZILLA FIREFOX | 27 | 27 |
| OnlyOffice calendar | 27 | 27 |
| Gimp | 25 | 25 |
| Libreoffice Writer | 25 | 25 |
| Mozilla FireFox | 25 | 25 |
| gnucash | 24 | 24 |
| Musescore | 23 | 23 |
| Affine | 21 | 21 |
| Libreoffice writer | 20 | 20 |
| Natron | 18 | 18 |
| OnlyOffice Spreadsheet | 17 | 17 |
| GNUCASH | 17 | 17 |
| Morzilla Firefox | 17 | 17 |
| inkscape | 17 | 17 |
| Cryptomator | 15 | 15 |
| PDFedit | 15 | 15 |
| Openshot | 14 | 14 |
| Brave | 13 | 13 |
| OnlyOffice Calendar | 7 | 7 |
| GrassGis | 4 | 4 |
| Conky | 4 | 4 |
| Arduino IDE | 4 | 4 |
| Krtia | 3 | 3 |
| gedit | 3 | 3 |
| OnlyOffice Forms | 2 | 2 |

## Results

Scores are computed on the pooled out-of-fold predictions. Macro-F1 weights every class equally, so it is the one to rank by when classes are unbalanced; ± is the spread across folds. Task accuracy takes a majority vote over each task's segments. `majority` always answers the training fold's most common class - a model has to beat it to be learning anything.

### ocr_native+ui+visual+cnn (632 dims: ocr_native + ui + visual + cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.001 | 0.000 | 0.009 | 0.035 | 0.035 | 0.00 | 0.000 |
| mlp | tier2 | 0.779 | 0.016 | 0.768 | 0.876 | 0.876 | 5.24 | 0.001 |
| random_forest | tier1 | 0.762 | 0.017 | 0.739 | 0.867 | 0.867 | 2.06 | 0.043 |
| svm | tier1 | 0.737 | 0.018 | 0.722 | 0.864 | 0.864 | 18.50 | 3.945 |
| lightgbm | tier1 | 0.148 | 0.072 | 0.133 | 0.177 | 0.177 | 8.11 | 0.026 |

### cnn (512 dims: cnn)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.001 | 0.000 | 0.009 | 0.035 | 0.035 | 0.00 | 0.000 |
| mlp | tier2 | 0.758 | 0.010 | 0.750 | 0.856 | 0.856 | 4.98 | 0.001 |
| svm | tier1 | 0.713 | 0.014 | 0.696 | 0.839 | 0.839 | 17.26 | 3.301 |
| random_forest | tier1 | 0.689 | 0.011 | 0.662 | 0.803 | 0.803 | 2.26 | 0.070 |
| lightgbm | tier1 | 0.144 | 0.027 | 0.143 | 0.184 | 0.184 | 6.45 | 0.029 |

### ocr_native+ui+visual (120 dims: ocr_native + ui + visual)

| model | tier | macro-F1 | ± | balanced acc | segment acc | task acc | fit s/fold | ms/segment |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **majority** | baseline | 0.001 | 0.000 | 0.009 | 0.035 | 0.035 | 0.00 | 0.000 |
| random_forest | tier1 | 0.751 | 0.004 | 0.737 | 0.858 | 0.858 | 0.58 | 0.076 |
| mlp | tier2 | 0.695 | 0.006 | 0.694 | 0.820 | 0.820 | 4.95 | 0.001 |
| svm | tier1 | 0.659 | 0.007 | 0.655 | 0.815 | 0.815 | 10.13 | 2.269 |
| lightgbm | tier1 | 0.106 | 0.045 | 0.097 | 0.133 | 0.133 | 2.90 | 0.019 |

## Read before quoting a number

- Classes with fewer than 5 tasks: OnlyOffice Forms (2), Krtia (3), gedit (3), GrassGis (4), Conky (4), Arduino IDE (4). Their per-class scores rest on a handful of recordings.

## Files

- `results.csv` - the tables above, plus any error messages
- `predictions.csv` - every segment's true label and each model's out-of-fold prediction
- `confusion/` - a confusion matrix per model (CSV), and a picture for each feature set's best model
- `models/ocr_native+ui+visual+cnn__mlp.joblib` - ocr_native+ui+visual+cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/cnn__mlp.joblib` - cnn, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `models/ocr_native+ui+visual__random_forest.joblib` - ocr_native+ui+visual, refitted on all 6991 segments; load it with `python -m v2k predict --bundle ...`
- `config.json` - the exact command-line settings
