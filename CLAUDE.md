# CLAUDE.md — Project Context

Video2Knowledge: NUS M.Tech AIS, ISY5002 Pattern Recognition Systems, Group 21 (Semester 2, 2026).
This file is the project and domain context: what we are building, why, and what the data looks like.
For repo and harness conventions (agents, skills, commands, rules), see `SourceCode/CLAUDE.md`.
For the implemented pipeline, see `Architecture/PIPELINE.md`. For the target AWS design, see `Architecture/README.md`.

## Source documents

- Proposal (authoritative, submitted 15-Sep-2026): `ProjectReport/ISY5002-PRS-Project_Proposal_Group-21.docx`
  (Markdown drafts: `ProjectReport/PROPOSAL_FULL.md`, `PROPOSAL_TEMPLATE_CONTENT.md`)
- Dataset description: `ProjectReport/DataSetDescription.txt`. It is **partly out of date**; see "Dataset" below.
- `ReadMe.md` is **stale on scope**: it lists 10 DevOps target classes (git_operations, docker_workflow, ...) and an older team list.
  The proposal replaces both. Follow the proposal.

## Problem and aim

Screen recordings of software/operational work (development, deployment, debugging, troubleshooting) hold reusable
knowledge that can't be searched. A single signal is not enough to say what happened. For example, OCR sees a command
but can't tell whether it was only typed, or executed and whether it succeeded. The core pattern-recognition problem
is to **fuse multimodal evidence to recognize activities, then model activity sequences to recognize workflows.**
The recognized workflows then become SOPs, runbooks and searchable knowledge.

Three-level recognition hierarchy:

1. **Level 1 — Interaction evidence**: pointer movement, click, keyboard input, drag (from action logs). This level supplies input evidence and is not the main target.
2. **Level 2 — Activity recognition (primary classification task)**: combines six modalities: visual, OCR/text, UI/application, command/log, interaction and temporal.
3. **Level 3 — Workflow recognition**: Activity₁ → … → Activityₙ ⇒ workflow pattern (LSTM / Transformer).

OCR, YOLO/UI detection, feature extraction and LLM generation are *supporting* technologies. They are not the pattern-recognition
techniques under evaluation.

## Research questions → experiments

| RQ | Question | Experiment |
|----|----------|------------|
| RQ1 | Classical ML vs deep learning for activity recognition from multimodal features? | Tier 1 vs Tier 2 |
| RQ2 | Does multimodal fusion beat individual modalities? | Tier 3 (voting, stacking, late fusion) + modality ablation (each modality alone → progressively fused) |
| RQ3 | Can LSTM/Transformer identify higher-level workflows from activity sequences? | Temporal workflow recognition |

## Multi-tier classifier

- **Tier 1 (classical)**: SVM, Naive Bayes, Decision Tree, Random Forest, KNN, XGBoost, LightGBM (scikit-learn)
- **Tier 2 (deep, PyTorch)**: MLP, CNN1D (on sequential multimodal *feature* representations, not raw frames), LSTM, Transformer
- **Tier 3 (ensemble)**: hard and soft voting, stacking (base models → meta-learner), multimodal late fusion

**Evaluation** (required by the proposal): accuracy; macro- and weighted-averaged precision, recall and F1; per-class metrics; confusion matrices;
multiclass ROC-AUC where applicable; cross-validation; feature importance where supported; modality ablation.

**Leakage rule (non-negotiable):** split and cross-validate at the **task/video level**, never at the frame or segment level.
Frames or segments from one recording must never appear in both train and eval.

## Labeling scheme (from the proposal)

- **Task-level (Level 2) labels**: map each *application* to a broader activity category (for example software development,
  document editing, web browsing). The dataset does **not** provide this mapping. The `activity` field is `null` in
  every labels row, so the project must define it (see `app/data_pipeline/labeling/`).
- **Segment-level (Level 1) labels**: come straight from action logs, grouped into 4 interaction types:
  pointer movement (`MOVE_TO`), click (`CLICK`, `MOUSE_DOWN/UP`), keyboard (`TYPING`, `PRESS`, `HOTKEY`, `KEY_DOWN/UP`), drag (`DRAG_TO`).
  `SCROLL` and `AFTER_LAST_ACTION` also appear rarely. Decide how to bucket them explicitly.
- The task's natural-language instruction and its action sequence are the **reference** for evaluating generated SOP/summary text and retrieval.

## Dataset

Source: ServiceNow **VideoCUA** (part of CUA-Suite, MIT license). These are expert human demos of desktop tasks, 30/60 fps video
with millisecond-level action logs. The proposal cites a 70-app subset (7,021 tasks, ~48 GB). **The local copy is much smaller:**

- Location: `dataset/` (gitignored; mounted read-only at `/app/dataset` in `docker-compose.yml`; `dataset_root` in `app/config.py`)
- **277 task videos across 8 apps** (~2.3 GB), plus an unextracted `NetBeans-…zip`:

  | App | Tasks |  | App | Tasks |
  |-----|------:|--|-----|------:|
  | VSCode | 106 | | Bash | 10 |
  | OpenShot | 75 | | Chromium | 10 |
  | IntelliJ IDEA | 46 | | Eclipse | 10 |
  | draw.io | 10 | | Mozilla Firefox | 10 |

  The classes are heavily imbalanced. VSCode and OpenShot make up ~65% of the tasks. Use macro-F1 and stratify at the task level.

**Actual layout** (this differs from `DataSetDescription.txt`, which names `action.json` and `label.json`):

```
dataset/<App>-<exportTimestamp>-1-001/<App>/
├── video2knowledge_labels.jsonl        # one row per action segment, all tasks of this app
└── <task_id>/                          # e.g. 111433
    ├── action_log.json                 # {task_id, task_instruction, platform, action_log:[{action_type, timestamp, action_params, groundcua_id}]}
    ├── label.txt                       # NL task instruction (workflow-level label); sometimes a 2nd "instruction: ..." line
    └── video/
        ├── video.mp4
        └── video_metadata.json         # {can_be_loaded, can_be_played, total_frames, fps, duration_seconds, width, height, error}
```

`video2knowledge_labels.jsonl` row fields: `t_start`, `t_end`, `action` (lowercase action type), `params` (`text`/coords, `groundcua_id`),
`nl` (the task instruction), `activity` (**always null**), `workflow` (the task instruction), `app`, `task_id`, `source` (`"videocua"`). There are 4,963 rows in total.

**Data quirks to handle:**

- Resolution and fps vary. `DataSetDescription.txt` says 1920×1008 @ 30 fps, but the files contain 1920×1080 / 1920×1020 / 1920×1008 / 1920×1006 / 1920×1014 @ 30 fps,
  2940×1912 and 2880×1800 @ 60 fps (Retina captures), 29.97 fps, and 1908×808. Normalize before extracting features.
- Duration ranges from 3.7 s to 117 s (mean ~18 s), not the "8–30 s" stated in the description.
- Platform names are inconsistent in `action_log.json`: `OpenShot` / `OPENSHOT` / `Openshot`, and `Draw.io` vs folder `draw.io`. Canonicalize them.
- Each task has one short instruction ("List files in the current directory"). Most tasks contain only a few actions.
- `SourceCode/backend/localDataset/109539` is a single sample task used for local dev/tests.

## Team (per proposal)

| Member | Scope |
|--------|-------|
| Lakshmi Barthwal Chamoli | AWS infra, video upload, OCR, SVM, Naive Bayes, temporal sequence dataset + workflow-sequence analysis, CI/CD |
| Yuan Zilin | React dashboard, workflow visualization, ground-truth collection, evaluation, MLP, CNN1D, Voting |
| Stalin Sagayaraj | Docker, video ingestion, YOLO, LSTM/Transformer |
| Muthaiah Muneeswaran | FastAPI, multi-tier classifier, Decision Tree, Random Forest, multimodal late fusion, CI/CD, monitoring |

## Tech stack

Python 3.11 · OpenCV · Tesseract/EasyOCR · YOLO · Albumentations · scikit-learn / XGBoost / LightGBM · PyTorch · MLflow ·
FastAPI · PostgreSQL + pgvector · LLM (SOP/runbook generation) · React + Vite + TS · Docker · GitHub Actions · AWS (ECS Fargate, SageMaker, S3).

## Key dates

- 15-Sep-2026: proposal submitted
- **30-Sep-2026: first presentation** (Zoom, 6:30–10:30 pm)
- 31-Oct-2026: final deliverables (code, dataset doc, trained models, report, presentation, README, demo video)
