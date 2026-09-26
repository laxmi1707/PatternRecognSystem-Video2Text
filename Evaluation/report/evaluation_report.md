# Activity Classifier Evaluation

2026-09-26 · Yuan Zilin (A0283899Y) · 6,991 recordings, 14 classes, task-grouped 5-fold cross-validation

---

## Summary

The best configuration reaches **macro-F1 0.3271** over 14 activity classes, against a majority-class baseline of 0.0250 — a 13.1x improvement. Accuracy on the same predictions is 0.4112 and weighted-F1 is 0.3999.

Recommended configuration:

| | value |
|---|---|
| Model | XGBoost |
| Hyperparameters | `n_estimators=600, max_depth=10, learning_rate=0.2` |
| Feature set | `native150` — the 150 backend dimensions, with OCR run at full resolution rather than 640x480 |
| Granularity | one row per recording (segments averaged) |
| Labels | `labels_v3.csv`, after the `run_command` rule correction described below |
| Class balancing | off — it lowers the score once the model is tuned |

The numbers come from 6,991 recordings across 87 applications, evaluated with 5-fold cross-validation grouped by recording. Nothing in the backend's classifier or feature code was modified: the hyperparameters are passed to the existing constructors, which already accept them.

---

## How it is evaluated

Four design decisions, each chosen so the reported number is not inflated.

**1. Folds are grouped by recording.** All segments of one recording stay on the same side of the split. Two frames a second apart are near-identical images, so a recording that appears in both the training and the test fold means the model is scored on copies of what it was trained on. The section on split leakage measures what that is worth.

**2. Everything fitted is fitted inside the training fold.** The TF-IDF vocabulary, the StandardScaler, the LabelEncoder and any oversampling are fitted after the split, on training rows only. No test-fold word enters the vocabulary. The harness carries 12 tests, several of which assert these boundaries — one fails if a test task's own token reaches the TF-IDF vocabulary, another if a fold ever splits a recording.

**3. Rows are pooled to one per recording.** The labels exist per recording, derived from the task instruction; the backend classifies per segment. Averaging a recording's segment vectors aligns the row with the granularity the label actually has, and is worth +23% on its own (segment level 0.243 vs recording level 0.300, under the earlier label set).

**4. Hyperparameters are selected on out-of-fold scores.** All 75 configurations are evaluated on the same folds, and the winner is chosen on the pooled out-of-fold macro-F1. There is no held-out set that selection could contaminate.

**Why macro-F1 is the headline.** The class distribution is heavily skewed — 1,480 recordings in the largest class, 34 in the smallest. Macro-F1 weights all 14 classes equally, so a model that ignores the rare classes cannot hide behind the large ones. Accuracy and weighted-F1 are reported alongside it, and both are higher.

---

## Results, stage by stage

| Stage | What changed | Best model | macro-F1 | Net gain |
|---|---|---|---|---|
| Baseline | earlier labels, library default hyperparameters | stacking | 0.2999 | — |
| B | corrected the `run_command` labelling rule | stacking | 0.3164 | +0.0165 |
| C | B plus oversampling of rare classes in the training fold | xgboost | 0.3179 | +0.0015 |
| A | B plus a 75-configuration hyperparameter search | **xgboost** | **0.3271** | **+0.0107** |
| A+C | tuning and balancing together | xgboost | 0.3238 | −0.0033 |

### B: a labelling rule was catching GUI actions

The earlier rule assigned `run_command` whenever an instruction began with `stop`, `start`, `run` or `count`. 19 of its 40 recordings were ordinary GUI actions — "stop the video", "start a new document".

The corrected rule requires one of: a terminal application (Ubuntu Terminal, Bash, GNU Octave), a real command token in the instruction (`sudo`, `chmod`, `grep`, `systemctl` and 30 others), or a code object being acted on inside an IDE. `run_command` went from 40 recordings to 34 — 24 genuine terminal sessions plus 10 IDE code executions.

The side effect is the more interesting result: **`media_control` F1 doubled, 0.069 to 0.136**, without that class being touched. The misfiled "stop the video" recordings belonged to it. One bad rule was degrading two classes.

### C: balancing trades large classes for small ones

Rare classes are oversampled inside each training fold until no class holds fewer than a fifth of the largest. Oversampling rather than class weights, because none of the 14 classifiers exposes `class_weight` and `fit(X, y)` takes no `sample_weight` — weighting would mean changing the models, and then the scores would no longer describe the backend.

| Improved | Degraded |
|---|---|
| `delete_remove` +0.085 | `other` −0.044 |
| `file_manage` +0.042 | `format_style` −0.008 |
| `run_command` +0.030 | `configure_option` −0.003 |

Balanced accuracy rises from 0.2940 to 0.3011, plain accuracy falls from 0.4100 to 0.4052. The net macro-F1 gain is 0.0015, so this is not worth enabling by default; it is worth enabling if every class has to be usable.

### A: what tuning bought

75 configurations, five processes in parallel, 28 minutes. Each model's library default sits inside its own grid, so the gain is measured rather than asserted.

| Model | Default | Best | Gain | Best configuration |
|---|---|---|---|---|
| **xgboost** | 0.3040 | **0.3271** | **+0.0231** | `n_estimators=600, max_depth=10, lr=0.2` |
| lightgbm | 0.2912 | 0.3052 | +0.0140 | `n_estimators=100, max_depth=10, lr=0.03` |
| random_forest | 0.2816 | 0.2910 | +0.0094 | `n_estimators=100, max_depth=40` |
| stacking | 0.3164 | 0.3170 | +0.0006 | `bases=svm+rf+mlp, meta_C=10.0` |

Two findings worth carrying into the report:

1. **Tuning changed which model wins.** On defaults, stacking led. Tuned, xgboost overtakes it, and stacking barely moves (+0.0006).
2. **The default `max_depth=6` underfits these 150 dimensions.** All five top xgboost configurations use `max_depth=10`, and the fold-to-fold standard deviation falls rather than rises (0.0206 to 0.0182). The problem was underfitting, not overfitting.

And one negative result: **tuning and balancing do not add up.** Separately they gave xgboost +0.0231 and +0.0139. Together the score is 0.3238, below tuning alone. `max_depth=10` already does what the oversampling was doing.

---

## Per-class F1

Each model's best configuration, over the same out-of-fold predictions.

| Class | Recordings | xgboost | stacking | lightgbm | random_forest |
|---|---|---|---|---|---|
| configure_option | 1480 | 0.475 | 0.458 | 0.454 | 0.443 |
| navigate_view | 1266 | 0.525 | 0.520 | 0.523 | 0.516 |
| format_style | 908 | 0.382 | 0.371 | 0.373 | 0.368 |
| edit_content | 830 | 0.301 | 0.298 | 0.263 | 0.267 |
| create_item | 770 | 0.405 | 0.408 | 0.424 | 0.403 |
| other | 399 | 0.180 | 0.220 | 0.174 | 0.211 |
| insert_element | 352 | 0.344 | 0.356 | 0.351 | 0.311 |
| file_manage | 290 | 0.468 | 0.413 | 0.480 | 0.317 |
| delete_remove | 174 | 0.161 | 0.102 | 0.134 | 0.094 |
| search_filter | 157 | 0.434 | 0.454 | 0.421 | 0.444 |
| organize_items | 150 | 0.182 | 0.137 | 0.110 | 0.112 |
| communicate | 127 | 0.442 | 0.428 | 0.359 | 0.292 |
| media_control | 54 | 0.103 | 0.203 | 0.098 | 0.215 |
| run_command | 34 | 0.179 | 0.071 | 0.107 | 0.080 |

`run_command` scored **0.000** under the earlier label set — not one recording recognised. With the corrected rule and tuning it reaches **0.179**. The split by class size:

| Class group | macro-F1 |
|---|---|
| The 7 classes with 300 or more recordings | 0.3730 |
| The 7 classes with fewer than 300 | 0.2811 |

---

## Which features carry the signal

Each block trained alone, on the full dataset, so the numbers say what each part of the 150-dimension vector is worth.

| Block | Dimensions | macro-F1 alone |
|---|---|---|
| `ocr_native` — OCR at full resolution | 50 | 0.280 |
| `cnn` — ResNet-18 frame embedding | 512 | 0.230 |
| `visual` | 40 | 0.223 |
| `interaction` | 30 | 0.183 |
| **`ui` — YOLOv8n with COCO weights** | **30** | **0.099** |

Two consequences for the pipeline:

**The `ui` block contributes close to nothing.** YOLOv8n on COCO weights detects people, cars and chairs; run against a screenshot it has almost nothing to say about screen content. 30 of the 150 dimensions are near-noise. A UI-element detector in its place is the single largest available feature improvement.

**OCR resolution matters more than the model does.** `VideoProcessor` resizes frames to 640x480 before `OCRExtractor` runs, and text recognised from the downscaled copy is frequently garbled. `native150` — the same 150 dimensions with OCR run on the full-resolution keyframe — is what every number in this report uses, and it is why `ocr_native` leads the ablation. Adding the 512-dimension ResNet embedding on top does not help (0.290 with, 0.300 without, under the earlier label set), so image embeddings are not where the remaining headroom is.

---

## What bounds the score

Four limits, ordered by how much each costs. The first two are properties of the data, not of the classifiers, and no amount of modelling removes them.

**1. The labels are derived by rule, so the reference itself carries error.** `labels_v3.csv` comes from keyword matching on the task instruction. A manual audit of one class found **9 of 40 assignments wrong** — a 22% error rate in that class. Where the reference is wrong the model is penalised for being right, which puts a ceiling on any achievable F1.

**2. 38% of all errors fall on ten symmetric class pairs.** 4,116 of 6,991 recordings are misclassified, and the errors are not spread evenly:

| Confusion pair | Errors | Share of all errors |
|---|---|---|
| configure_option ↔ navigate_view | 506 | 12.3% |
| format_style ↔ configure_option | 368 | 9.0% |
| edit_content ↔ format_style | 250 | 6.1% |

These are pairs an annotator reading the same instruction would also confuse — "change a setting" and "move around the interface" are not cleanly separable from the instruction text. This is taxonomy ambiguity rather than model error.

**3. Roughly 30 of the 150 dimensions are near-noise.** See the ablation above: the `ui` block scores 0.099 alone.

**4. One label per recording, several activities inside it.** The label describes the instruction, not what is on screen second by second. Pooling to recording level recovers part of this (+23%), but a recording that opens a file, edits it and saves it still carries one class.

### A consequence for the SOP output

The recommended model is trained at recording level, and `sop.py` needs a per-segment prediction to name each step, which a recording-level bundle cannot give. The SOP path therefore runs on a segment-level model, whose best macro-F1 is 0.2540 rather than 0.3271. The two numbers should not be reported as one, and the SOP figures should say which model produced them.

---

## What an ungrouped split is worth

**An ungrouped split inflates macro-F1 by 81% to 118%.** Same recordings, same `native150` features, same labels, same seed, same XGBoost — only the fold split differs. Segment level, because pooling to one row per recording leaves nothing to leak.

| Configuration | Grouped by recording | Segments shuffled | Inflation |
|---|---|---|---|
| `n_estimators=100, max_depth=6, lr=0.1` | 0.2415 | 0.4374 | **+81%** |
| `n_estimators=600, max_depth=10, lr=0.2` | 0.2540 | 0.5547 | **+118%** |

Accuracy moves the same way: 0.3383 grouped, 0.6242 shuffled.

The mechanism is that segments of one recording are near-identical, so a shuffled split scores the model on copies of its own training rows. The stronger configuration gains more from the leak, which is the signature of the effect: extra capacity goes into memorising rows that then reappear on the test side.

Two places in our own code do the shuffled split:

- `app/ml/dataset.py:80-88` — `train_test_split_data` cuts a random permutation. A correct `task_level_split` already exists at `dataset.py:91`, but is only ever called from tests. Separately, `dataset.py:63-66` augments before the split, so augmented copies cross the boundary too.
- `data_pipeline/dataset/splits.py` — shuffles `LabeledExample` records 70/15/15. Each record is one frame, so frames from one video land on both sides. `Frame` already carries `video_id`, so grouping by it is a few lines.

Any score produced through either path should be read as roughly double what the model earned. This is the reason every number in this report uses `StratifiedGroupKFold` grouped by recording.

---

## Findings in the shared code

Four things that came up while running the full VideoCUA set, in the order they affect the numbers we report. Each has a one-line or few-line fix.

### 1. `label.txt` is read with the platform's default encoding

`app/ml/dataset_loader.py:147`

```
instruction = label_file.read_text().strip() or instruction
```

`read_text()` with no `encoding` uses the machine's default rather than the file's. That is UTF-8 on Linux and cp1252 on Windows. **111 of the 7,021 `label.txt` files are UTF-8 and raise `UnicodeDecodeError`** on a cp1252 machine — typographic quotes are the usual trigger.

The fix:

```
instruction = label_file.read_text(encoding="utf-8").strip() or instruction
```

Still present after the `_scan_directory` / `_load_task` refactor on `feat/model-training-comparison-ui` (`a16be03`) — the restructure did not touch that line. A standalone reproduction script exists; it only reads and changes nothing.

### 2. That exception turns into silent training on synthetic data

`app/services/ml_service.py:90-94`

```
try:
    return self._get_real_data()
except Exception as e:
    logger.warning(f"Failed to load real dataset, falling back to synthetic: {e}")
    return self._get_synth_data()
```

`_ensure_trained` calls this with `prefer_real=True`, so the intended path is the real dataset. Any exception from loading it — including the `UnicodeDecodeError` above — is caught, logged at warning level, and replaced with randomly generated data. Training then completes without error on noise, and the only trace is one log line.

**This is very likely why the demo numbers never moved regardless of what was changed.** The same fallback exists at inference in `app/services/classification_service.py:37-40`.

Beyond the encoding fix, worth making that fallback opt-in rather than automatic: a crash gets investigated, while silently training on noise just looks like a model that does not work.

### 3. The train/test split ignores recordings

Covered above with the measured cost: `app/ml/dataset.py:80-88` and `data_pipeline/dataset/splits.py`. `task_level_split` already exists at `dataset.py:91` and is simply never called outside tests, so this is a wiring change rather than a rewrite.

### 4. Two classifiers bypass the thread cap

`app/ml/classifiers/tier1/random_forest.py:18` and `knn.py:15` pass `n_jobs=-1`, which asks joblib for every core and so ignores `OMP_NUM_THREADS`. On a shared machine that means one model saturates all 32 threads. Setting `LOKY_MAX_CPU_COUNT` alongside the OMP variables caps them; joblib reads it.

### Already correct on the new branch

Two things adopted on `feat/model-training-comparison-ui` that were on our list and need no further action: `task_level_split` for the split, and remapping labels to contiguous `0..N-1`.

### Open item with no code behind it

Layer 6 of the proposal — retrieval over the extracted content — has no implementation. A keyword search over the OCR text already extracted would satisfy it for the demo, and the extracted text can be handed over as a CSV.

---

## Reproducing these numbers

| Run | What it is |
|---|---|
| `run_010` | baseline, earlier labels, recording level |
| `run_011` | feature ablation |
| `run_012` | segment level, earlier labels |
| `run_013` | stage B, corrected labels |
| `run_014` | stage C, corrected labels plus balancing |
| `run_016` | stage A, 75-configuration grid |
| `run_018` | stage A winners with stored predictions, for per-class F1 |
| `run_019` | stage A grid with balancing |
| `run_020` / `run_021` | the grouped and shuffled split comparison |

Each run folder holds `config.json` (every setting and the backend commit), `results.csv` or `tuning.csv`, `predictions.csv`, and per-model confusion matrices.
