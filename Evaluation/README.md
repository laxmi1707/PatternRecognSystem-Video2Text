# Evaluation harness

Cross-validated evaluation of the backend's 14 classifiers on the full VideoCUA
set: 6,991 recordings, 14 activity classes, folds grouped by recording. A
fifteenth, AdaBoost, is added here for the boosting comparison and is marked as
ours wherever it appears — it is not part of `MLService`.

**Results and how to read them: [report/evaluation_report.md](report/evaluation_report.md)**
(same text as `report/evaluation_report.docx`, if you prefer Word).
Headline: macro-F1 **0.3271** against a majority-class baseline of 0.0250.

This directory imports the backend's own feature extractors and classifier
classes rather than reimplementing them, so the scores describe `SourceCode/backend`
as it stands. Nothing under `SourceCode/` is modified by anything here.

## What is committed and what is not

Committed: the harness code, the label sets, the run configurations, and every
score (`runs/*/config.json`, `results.csv`, `tuning.csv`, `predictions.csv`,
`confusion/`). About 38 MB.

Not committed, because it is large and regenerable (see `.gitignore`): the 26 GB
dataset, the frame-vector cache, the model weights, and the fitted model bundles
(150-270 MB per run).

## Reproducing a number

Each `runs/<run>/config.json` records every setting used, including the backend
commit the features came from. To re-run one:

```
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt

# The backend, at the commit the cache was built against, importable as `app`:
#   Evaluation/vendor/<snapshot>/SourceCode/backend
# Set V2K_BACKEND_SNAPSHOT to that folder's name; the cache path includes it, so
# a different snapshot starts a fresh cache rather than mixing feature versions.

python -m v2k download NetBeans          # or the apps you want
python -m v2k frames --workers 4 --threads 4
python -m v2k train --labels csv:labels/labels_v3.csv --features native150 \
    --models all --level task --folds 5 --min-tasks 10
```

Stage A (the hyperparameter search) runs in three steps so the three-minute
cache load happens once rather than once per configuration:

```
python -m v2k tune --prepare --labels csv:labels/labels_v3.csv \
    --features native150 --models lightgbm xgboost random_forest stacking --level task
python -m v2k tune --shard 0/5 --run-dir runs/<run>    # x5, in parallel
python -m v2k tune --collect --run-dir runs/<run>
```

`scripts/run_tuning_A_v1.sh` and `scripts/run_leakage_check_v1.sh` drive those steps end to end.

## Checks

```
.venv/Scripts/python.exe tests/test_harness.py
```

12 tests. Several exist only to catch leakage: one fails if a fold ever splits a
recording, one if a test task's own token reaches the TF-IDF vocabulary, one if
the scaler sees a test row. The oversampling test asserts no synthetic point is
invented, and the sampling test asserts whole recordings are kept.

## Layout

| Path | What is in it |
|---|---|
| `report/` | the evaluation report, Markdown and Word |
| `v2k/` | the harness: one module per stage |
| `tests/` | 12 tests, mostly leakage guards |
| `labels/` | the three label sets and the taxonomy each was derived with |
| `runs/` | one folder per run: settings, scores, predictions, confusion matrices |
| `scripts/` | the shell drivers that chain the stages unattended |
| `examples/` | three generated SOPs (one pair shows the effect of merging repeated step headings), and the encoding-bug reproduction script |

## Commands

| Command | What it does |
|---|---|
| `apps` | list the dataset's applications and what is cached locally |
| `download` | fetch and unpack an application's recordings |
| `frames` | decode video, run the backend's extractors, cache the vectors |
| `train` | cross-validate the 14 classifiers, write a run folder |
| `tune` | grid-search the hyperparameters the backend's classes accept |
| `predict` | classify one recording with a saved bundle |
| `sop` | step-by-step procedure with timestamps for one cached recording |
| `taxonomy` | propose a label set from the instructions, write a labels CSV |
| `survey` | label coverage and extraction cost of a dataset folder |
| `parity` | check the cache reproduces the backend's live vectors |

## CPU

`V2K_MAX_THREADS` caps the thread count (default 16) and the process drops to
below-normal priority. It also sets `LOKY_MAX_CPU_COUNT`, which is what
constrains the two classifiers that pass `n_jobs=-1`.
