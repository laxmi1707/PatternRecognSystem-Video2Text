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

## Bare-video SOP detector

`v2k/sop.py` writes an SOP by reading `action_log.json`, which a user uploading a
recording does not have. `v2k/sop_detector.py` reads only the frames:

1. **Stage 1** names the application with run_029's best classifier
   (OCR + UI + visual + CNN, MLP).
2. **Stage 2** tracks OCR regions by screen position and keeps any whose text
   extends between keyframes, which is a field being typed into. The ranker for
   the application stage 1 named scores each candidate, and repeated reads of one
   string are merged into a single "Type ..." step.

The ranker reads 32 features: 13 from the frames (position, length, OCR
confidence, how long the text grew), 13 on the shape of the string (spaces,
`=` `(` `/` `-`, a known command first), one text score from a character n-gram
model trained across every application, and 5 on the recording around it (other
lines on the same row, vertical rank, how often the string was read). Each
application's ranker is trained conservatively - shallow trees, large leaves,
subsampling - because some applications have only a few dozen typed strings.

Out of fold over the 61 applications with at least five logged typed strings
(6,716 recordings, 1,690 typed strings of three or more characters), threshold 0.5,
from `runs/run_037_sop-detector`:

| | precision | recall |
|---|---|---|
| **routed by stage 1, as delivered** | **50.6%** | **26.4%** |
| routed by the true application | 50.6% | 26.6% |
| one pooled ranker, no routing | 51.2% | 18.3% |

How the ranker got there, routed, as delivered, threshold 0.5. The feature rows
come from `sop_ranker_experiments_v1.py` (`runs/run_033`); the training rows from
`sop_ranker_experiments_v2.py` (`runs/run_036`):

| ranker | precision | recall | recall, applications never seen in training |
|---|---|---|---|
| 13 frame features (the first version, run_032) | 38.1% | 26.6% | 3.1% |
| + shape of the string | 39.5% | 28.3% | |
| + cross-application text score | 42.3% | 26.1% | 6.1% |
| + recording context | 47.9% | 26.3% | 10.9% |
| **+ conservative per-application training (shipped)** | **50.6%** | **26.4%** | |

The frame features alone made position the strongest clue, and position means
nothing outside the application it was learned on: a ranker that had never seen an
application recovered 3.1% of its typed strings. Text and context carry over, which
is why the pooled ranker and unseen applications both improved most.

Round 2 also tried one pooled ranker told the application (worse: 43.6% precision
at the same recall) and the mean of pooled and per-application scores (higher
precision but lower recall in four of five folds). Conservative training raised
precision in all five folds, by 0.7 to 4.2 points, while recall moved by -0.9 to +1.5;
its settings were fixed before scoring, not tuned on the test folds.

Stage 1 is 94.49% correct once application labels are normalised; the dataset
spells 70 applications 107 ways (`ATOM`/`Atom`, `krtia`), which costs 6.87 points
when scored on raw strings. 90.1% of typed strings are present among the
candidates, so the ranker, not extraction, is where recall is lost. Only typing is
recovered: it is 4.3% of logged actions, and clicks (41.3%) are not detected, so a
task done entirely by clicking yields an empty SOP.

"As delivered" means repeated reads are merged and scoring is one-to-one, so a
duplicate is a false positive and a string typed twice needs two steps. Crediting
every copy instead gives 69.3% / 27.6%; `runs/run_037_sop-detector/report.md` has
both. A picture of the mechanism and every result: `viz/sop_detector_viz_v3.html`
(`_v1` and `_v2` are the earlier rankers, kept for comparison).

```
python -m v2k.sop_detector train                      # cache, evaluate out of fold, fit, save
python -m v2k.sop_detector detect --bundle runs/<run>/sop_detector.joblib \
    --video path/to/recording.mp4 --out sop.md        # a bare video, nothing else read
python -m v2k.sop_detector detect --bundle runs/<run>/sop_detector.joblib --cached Bash 111478
python sop_ranker_experiments_v1.py                   # the feature comparison above
python sop_ranker_experiments_v2.py                   # the training comparison above
python viz/build_sop_viz_v3.py runs/<detector run> runs/<experiments run> \
    runs/<experiments-2 run> viz/<page>.html
```

Bundles from run_032 (frame features only) still load: `detect` adds the text and
context features only when the bundle carries a text model.

`train` needs the frame cache and run_029's saved stage-1 bundle, neither of which
is committed. The fitted rankers (`sop_detector.joblib`, 15 MB) and out-of-fold
scores (`oof_scores.npz`) stay local; the scores the numbers above come from are
in `results.json`.

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

13 tests. Several exist only to catch leakage: one fails if a fold ever splits a
recording, one if a test task's own token reaches the TF-IDF vocabulary, one if
the scaler sees a test row. The oversampling test asserts no synthetic point is
invented, and the sampling test asserts whole recordings are kept.

## Layout

| Path | What is in it |
|---|---|
| `report/` | the evaluation report, Markdown and Word |
| `v2k/` | the harness: one module per stage |
| `tests/` | 13 tests, mostly leakage guards |
| `labels/` | the three label sets and the taxonomy each was derived with |
| `runs/` | one folder per run: settings, scores, predictions, confusion matrices |
| `scripts/` | the shell drivers that chain the stages unattended |
| `examples/` | three generated SOPs (one pair shows the effect of merging repeated step headings), and the encoding-bug reproduction script |
| `viz/` | the SOP detector's visual explainer, its template, and the script that fills it from a run folder |

## Commands

| Command | What it does |
|---|---|
| `apps` | list the dataset's applications and what is cached locally |
| `download` | fetch and unpack an application's recordings |
| `frames` | decode video, run the backend's extractors, cache the vectors |
| `train` | cross-validate the 14 classifiers, write a run folder |
| `tune` | grid-search the hyperparameters the backend's classes accept |
| `predict` | classify one recording with a saved bundle |
| `sop` | step-by-step procedure with timestamps for one cached recording, read from its action log |
| `v2k.sop_detector` | the same from frames alone; run as `python -m v2k.sop_detector` (see above) |
| `taxonomy` | propose a label set from the instructions, write a labels CSV |
| `survey` | label coverage and extraction cost of a dataset folder |
| `parity` | check the cache reproduces the backend's live vectors |

## CPU

`V2K_MAX_THREADS` caps the thread count (default 16) and the process drops to
below-normal priority. It also sets `LOKY_MAX_CPU_COUNT`, which is what
constrains the two classifiers that pass `n_jobs=-1`.
