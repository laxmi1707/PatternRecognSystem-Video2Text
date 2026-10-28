# SOP Detector

Writes the steps of a standard operating procedure (SOP) from a screen recording alone -
which control was clicked and what was typed, and when - with no action log. It is the
SOP detector of **TRACE** (ISY5002 Pattern Recognition Systems, Group 21, NUS-ISS), and
runs as a small HTTP service beside the TRACE backend.

```
Eclipse, a recording no model saw in training
 1.  0:01  Click 'Package Explorer'
 2.  0:09  Click 'Modulepath'
 3.  0:13  Click 'Add JARS'
 4.  0:24  Click 'Module Dependencies'
 5.  0:30  Click 'facebook-messenger-1.0.0.jar'
 6.  0:35  Click 'Apply and Close'
```

## How it works

| Part | Model | What it decides |
|---|---|---|
| Application | MLP on frame features | which of 70 applications is on screen (94.5% correct) |
| Pointer | small CNN, 5 frames a second | where the mouse pointer is, in any shape |
| Clicks | LightGBM, 17 features | whether a pointer stop was a click - from how the screen reacted and how the pointer moved |
| Click names | OCR under the pointer | the control's label; icons are written as "Click (icon)" |
| Typing | LightGBM ranker, per application + pooled | which new on-screen text the user typed - from the text and how it arrived |

Clicks and typed text are merged in time order. All four fitted models are in one file,
`models/sop_detector.pkl`. It runs on CPU; no GPU is needed.

## Results

Tested only on recordings the models never saw, against the SOP written from each
recording's action log. A click counts only within 2 s and 40 px of the logged click; typed
text only if it matches the logged text.

| 720 unseen recordings, 61 applications | Steps that are real | Steps found |
|---|---|---|
| Random guesses (same number of steps) | 0.2% | 0.1% |
| Random picks from the detector's own candidates | 28.7% | 16.7% |
| **SOP detector** | **77.5%** | **45.2%** |

The full evaluation is in [reports/sop_evaluation_report_v16.md](reports/sop_evaluation_report_v16.md).

## Test it in 3 steps

You need Docker with at least 8 GB of memory. No GPU is needed.

1. **Start it.** From the team repository:

   ```bash
   git fetch origin
   git checkout SOP-detector
   cd SOP-detector
   docker compose up --build
   ```

   The first build takes about 15-20 minutes (it downloads the OCR and vision models).
   It is ready when the log shows `Uvicorn running`.

2. **Upload a video.** Open <http://localhost:8100/docs> in a browser, then:
   - open **POST /sop-detector/jobs**;
   - click **Try it out**;
   - choose a video from [`samples/`](samples), for example `samples/Eclipse_52918.mp4`;
   - click **Execute**.

   The response gives a `job_id`.

3. **Read the steps.** Open **GET /sop-detector/jobs/{job_id}**, then:
   - click **Try it out**;
   - paste the `job_id`;
   - click **Execute**.

   When `status` is `completed`, `result.steps` lists each step as `{"t": seconds, "action": "Click" or "Type", "text": ...}`.

The four sample recordings are answered at once from stored results. Any other recording is processed live and takes a few minutes; while it runs, `status` is `running` and `progress_pct` rises, so run step 3 again until it finishes. The detector needs a real recording with a visible mouse pointer. A screen capture made by a browser automation tool has no pointer and gives no clicks.

## Run it

**Docker** (about 4.5 GB image; the first build downloads the OCR and vision weights):

```bash
docker compose up --build
curl http://localhost:8100/sop-detector/health
```

**Python 3.14**, from the repository root:

```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.10.0 torchvision==0.25.0
pip install -r requirements.txt
python -m detector path/to/video.mp4 --out steps.json     # one video, steps as JSON
python sop_detector_service.py                            # the service on port 8100
```

## API

```
GET  /sop-detector/health
POST /sop-detector/jobs          multipart "file"  -> {"job_id": ...}
GET  /sop-detector/jobs/{id}     {"status": running | completed | failed, "progress_pct",
                                  "stage", "result": {"app", "app_confidence", "duration",
                                  "steps": [{"t", "action", "text"}, ...]}}
```

One video is processed at a time: clicks take under 40 s for a 40 s video, the whole video
4-8 minutes on 4 CPUs (reading the screen once a second for typing). The four recordings in
`samples/` are answered at once (their results are stored in `cache/demo_v6/`).

Settings: `SOP_DETECTOR_HOST` (127.0.0.1), `SOP_DETECTOR_PORT` (8100),
`SOP_DETECTOR_THREADS`, `SOP_DETECTOR_UPLOADS`, `ALLOWED_ORIGINS` (JSON list of frontend
origins), `SOP_DETECTOR_PKL` (model file; `models/sop_detector.pkl` by default).

## Layout

| Path | Content |
|---|---|
| `detector/` | the detector: clicks, typing, the one-file model loader, the command line |
| `v2k/` | shared feature and model code the detector builds on |
| `sop_detector_service.py` | the HTTP service |
| `models/sop_detector.pkl` | the four fitted models |
| `vendor/main-d866716/` | the TRACE backend at commit d866716, whose OCR and frame features the models were trained on |
| `cache/demo_v6/` | stored results for the four sample recordings |
| `samples/` | four sample recordings from VideoCUA (Bash, Eclipse x2, VS Code; MIT licence) |
| `deploy/aws/` | Terraform for AWS Fargate behind the TRACE load balancer ([deploy/aws/README.md](deploy/aws/README.md)) |
| `reports/` | the evaluation report |

## Data

Trained and evaluated on [ServiceNow VideoCUA](https://huggingface.co/datasets/ServiceNow/VideoCUA)
(MIT licence), with recordings split so that no recording is in both training and test data.
