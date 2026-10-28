# TRACE — Demo Video Script
**NUS M.Tech AIS · ISY5002 Pattern Recognition Systems · Group 21**
Target duration: 10–12 minutes

---

## Setup before recording
- Browser open at `http://54.255.213.206:5173` (full-screen, zoom 100%)
- All 7 demo videos ready in `dataset/demo-videos/`
- Mic tested, screen recorder running (OBS / QuickTime / Loom)

---

## Section 1 — Introduction (1 min)

**Narrate:**
> "Welcome to TRACE — a Multimodal Pattern Recognition Framework for Screen Activity
> Understanding and Knowledge Extraction. This system was built as part of ISY5002
> Pattern Recognition Systems at NUS ISS by Group 21."

**Show:** Front page — point out:
- NUS ISS badge and course name
- "Pattern Recognition System" badge
- TRACE title
- The subtitle with yellow highlights: *Screen Activity Understanding* and *Knowledge Extraction*
- The amber callout: "⚠ with real-time risk & anomaly detection"
- Processing Pipeline sidebar (5 stages)
- Recognised Activities (9 categories)

---

## Section 2 — Normal workflow: safe coding (2 min)

**Narrate:**
> "Let's start with a normal developer workflow — no risky operations. We upload a
> screen recording of someone editing Python code and making a git commit."

**Do:**
1. Drag and drop `demo_safe_coding_workflow.mp4` into the dropzone
2. Wait for processing — point out the progress states
3. Results appear — show:
   - Video filename at top, duration, steps
   - "Viewing: Stacking" model toggle
   - Screen View tab — video plays on the left
   - Right side: **"No anomalies detected in this recording."**
   - Narrate: *"The system correctly classifies this as coding and editing activity with no risk flags — no false positives."*
4. Click **Show Model Comparison** — show all 13 classifiers agreed on `coding_editing`

---

## Section 3 — SOP & Runbook generation (2 min)

**Narrate:**
> "Beyond classification, TRACE automatically generates structured documentation."

**Do (still on safe coding result):**
1. Scroll down to Knowledge Generation
2. Click **Generate SOP** — wait, then show the SOP
   - Point out: Procedure steps with timestamps
   - Activity labels per step
3. Click **Generate Runbook** — show merged steps with commands extracted
4. Click **Download Report** — show the PDF/HTML report briefly

---

## Section 4 — Risk detection: Docker destructive ops (2 min)

**Narrate:**
> "Now let's demonstrate the anomaly detection system. We upload a recording
> where a developer runs destructive Docker and Kubernetes commands."

**Do:**
1. Click "Analyze another video"
2. Upload `demo_docker_risk.mp4`
3. Results appear — Screen View:
   - Left: video plays
   - Right: **"3 anomalies detected"** (red/amber badges)
   - Point out each step:
     - `docker rmi --force` → **HIGH RISK** badge: "Destructive command"
     - `kubectl delete namespace production` → **HIGH RISK**: "Irreversible infrastructure change"
4. Narrate: *"The multimodal fusion of OCR text and activity classification surfaces these risks automatically."*

---

## Section 5 — Credential leak detection (1.5 min)

**Narrate:**
> "The system also detects exposed credentials — a critical security scenario."

**Do:**
1. Upload `demo_git_credential_leak.mp4`
2. Show anomaly panel:
   - `AWS_SECRET_ACCESS_KEY=...` → **HIGH RISK**: "Sensitive credential visible on screen"
   - `git push --force` → **HIGH RISK**: "Sensitive operation"
3. Narrate: *"OCR extracts the text from each frame and rule-based risk assessment fires immediately — no ML model needed for these patterns."*

---

## Section 6 — Infrastructure destruction: Terraform (1.5 min)

**Narrate:**
> "Here's a DevOps scenario — terraform destroy targeting live infrastructure."

**Do:**
1. Upload `demo_terraform_destroy.mp4`
2. Show anomalies:
   - `terraform destroy -auto-approve` → **HIGH RISK**: "Irreversible infrastructure change"
   - `aws ec2 terminate-instances` → **HIGH RISK**
3. Generate SOP — show the risk badge appearing inside the SOP procedure steps

---

## Section 7 — Multi-tier classifier explained (1.5 min)

**Narrate:**
> "Under the hood, TRACE uses a three-tier classifier ensemble.
> Tier 1 is classical ML — SVM, Random Forest, XGBoost. Tier 2 is deep learning —
> MLP, CNN1D, LSTM, Transformer. Tier 3 fuses them via voting and stacking."

**Do:**
1. Go back to any result, click **Show Model Comparison**
2. Scroll through the 13 classifiers — point out:
   - Classical (SVM, NB, DT, RF, KNN, XGBoost, LightGBM)
   - Deep (MLP, CNN1D, LSTM, Transformer)
   - Ensemble (Voting, Stacking)
3. Narrate: *"Stacking is the default — a meta-learner that learns which base models to trust per activity type."*

---

## Section 8 — History & wrap-up (30 sec)

**Do:**
1. Click **History** in nav — show all uploaded videos with timestamps
2. Click View on one to re-open results without re-running

**Narrate:**
> "TRACE converts unstructured screen recordings into searchable, structured
> knowledge — SOPs, runbooks, and risk-flagged activity timelines.
> Thank you."

---

## Recording tips
- Use 1920×1080, 30fps
- Zoom browser to 125% for readability
- Pause 2 seconds after each major UI state change
- Edit out the processing wait times (30–60 s per video) in post
- Add slide overlays for section titles if desired
