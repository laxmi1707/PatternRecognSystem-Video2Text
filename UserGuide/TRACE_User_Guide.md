# TRACE — User Guide

**Task Recognition & Activity Capture Engine**
NUS M.Tech AIS — ISY5002 Pattern Recognition Systems | Group 21

---

## Live Application

**URL:** [https://main.d2tjfo3h4t5uox.amplifyapp.com](https://main.d2tjfo3h4t5uox.amplifyapp.com)

No installation required. Open the URL in any modern browser (Chrome, Firefox, Edge, Safari).

---

## Sample Video for Testing

A ready-to-use screen recording is available in the repository:

**File:** `dataset/demo-videos/risk_test_video.mp4`
**Direct link:** [risk_test_video.mp4](https://github.com/laxmi1707/PatternRecognSystem-Video2Text/blob/main/dataset/demo-videos/risk_test_video.mp4)

Download it by clicking **Raw** on the GitHub page, then use it in the steps below.

---

## Step-by-Step Guide

### Step 1 — Open the Application

1. Navigate to [https://main.d2tjfo3h4t5uox.amplifyapp.com](https://main.d2tjfo3h4t5uox.amplifyapp.com)
2. The TRACE upload page loads. You will see a drag-and-drop zone in the centre.

---

### Step 2 — Upload a Screen Recording

1. Click the upload area, or drag and drop your video file onto it.
   - Supported formats: `.mp4`, `.mov`, `.webm`, `.avi`
   - Use `risk_test_video.mp4` from the link above if you do not have a recording of your own.
2. The filename appears in the upload zone once selected.
3. Click **Analyse** (or the equivalent submit button) to start processing.

---

### Step 3 — Wait for Analysis

1. A progress bar appears showing the pipeline stages:
   - Uploading video
   - Extracting frames and features
   - Running classifiers (Tier 1 → Tier 2 → Tier 3 ensemble)
   - Generating workflow steps
2. Analysis typically completes in **30–90 seconds** depending on video length.

---

### Step 4 — Review the Results

Once analysis is complete, the results page shows:

| Section | What it shows |
|---------|--------------|
| **Activity Classification** | Predicted activity class (e.g. `Coding and Editing`) with confidence score |
| **Model Comparison** | Per-model predictions across all 6 classifiers (SVM, Random Forest, Decision Tree, MLP, LSTM, Voting Ensemble) |
| **Workflow Steps** | Timestamped SOP extracted from the recording (e.g. "0:03 — Opened terminal") |
| **Anomaly Alerts** | Any destructive commands or privilege escalation detected by the OCR rule engine |

Click **Show Model Comparison** to expand the per-model breakdown.

---

### Step 5 — View the History

1. Click **History** in the top navigation bar.
2. All previously analysed sessions are listed with filename, date, duration, step count, and status.
3. Click **View** on any row to re-open its results page.

---

### Step 6 — Switch UI Mode (Optional)

The application has two UI modes:

- **Classic** — default view on first load
- **New Look** — click the toggle button (top right, labelled **New Look** or **✦**) for the updated interface

Both modes show the same results; the New Look mode has an updated layout and colour scheme.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Upload fails or times out | Check that the file is under 500 MB. Try a shorter clip. |
| Analysis stuck at 0 % | Refresh the page and re-upload. The backend may have restarted. |
| History shows no entries | The backend database may be empty. Upload a video first. |
| Page does not load | Check your internet connection. The app is hosted on AWS Amplify (region: ap-southeast-1). |

---

## API Access (Advanced)

The REST API is available at:

```
https://d3aev25xtfpx7z.cloudfront.net/api/v1
```

Interactive documentation (Swagger UI):

```
https://d3aev25xtfpx7z.cloudfront.net/api/v1/docs
```

---

*NUS-ISS M.Tech in Artificial Intelligence Systems — ISY5002 Pattern Recognition Systems*
