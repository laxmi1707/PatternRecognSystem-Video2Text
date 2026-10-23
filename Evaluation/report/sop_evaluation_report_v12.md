# SOP detector — evaluation for the team

Video2Knowledge · Joshua · 2026-10-23 · v12

## 1 · What it does

A user uploads a screen recording. The SOP detector writes the steps they performed —
**from the video alone, with no action log**:

```
Eclipse, a recording no model saw (6 of the 10 steps it wrote)
 1.  0:01  Click 'Package Explorer'
 2.  0:09  Click 'Modulepath'
 3.  0:13  Click 'Add JARS'
 4.  0:24  Click 'Module Dependencies'
 5.  0:30  Click 'facebook-messenger-1.0.0.jar'
 6.  0:35  Click 'Apply and Close'
```

Our proposal promises an "end-to-end pipeline from **raw screen recording** to
searchable knowledge base — no manual annotation required". A recording a user makes
has no action log. So this is the step our product needs for real uploads.

| | Needs an action log? | Concrete actions? |
|---|---|---|
| Backend SOP (`main`) | No | No — phases named from activity labels |
| Log-based SOP (`feat/action-classifier`) | **Yes** | Yes, with what the screen showed |
| **SOP detector** (`feat/frontend`) | **No** | **Yes** — clicks and typing |

The log-based SOP is the better choice when a log exists, as in the dataset. The
detector covers every upload that has none. The two complement each other.

## 2 · How it works

1. **Name the application** from the screen (94.5% correct over 70 applications).
2. **Typing:** read the screen once a second; text that grows at one spot is a field
   being typed into; a filter trained per application keeps what the user typed.
3. **Clicks:** a small neural network finds the mouse pointer in any shape (arrow,
   hand, text cursor) five times a second. Where it stops, a learned filter (LightGBM)
   checks whether the screen reacted as it does after a click. OCR then reads the
   control under the pointer.
4. Both are merged in time order.

## 3 · How it was tested

- **Only recordings the models never saw**, split by recording, sampled across all 87
  applications of the dataset.
- **Reference:** the SOP written from each recording's action log.
- **Scoring is strict and one-to-one:**
  - a click counts only within 2 s before or 0.3 s after the logged click, and within
    40 px of it;
  - a typed step counts only if its text matches the logged text;
  - a duplicate step counts as wrong.

## 4 · Results

**The whole SOP, 720 unseen recordings from 61 applications:**

| | Steps that are real | Steps found |
|---|---|---|
| Clicks | 55.4% | 29.6% |
| Typing | 47.4% | 27.4% |
| **Whole SOP** | **54.7%** | **29.4%** |

- **More than half of the steps it writes are real.**
- Without the click branch, the detector found 1.7% of all logged steps; with it, 23.8%.
  About a fifth of logged steps are key presses, shortcuts and drags, which it does not
  look for.
- A found click carries the right control name in about seven of ten cases.

**Against chance.** Two baselines write exactly as many click and typing steps as the
detector does in each recording. They use the same recordings and the same scoring,
averaged over 20 runs:

| | Steps that are real | Steps found |
|---|---|---|
| Random guesses (random time and screen position) | 0.1% | 0.1% |
| Random picks from the detector's own candidates (every pointer stop, every growing text), with no learned filter | 26.2% | 14.1% |
| **SOP detector** | **54.7%** | **29.4%** |

- The steps are far from luck: a random click almost never lands within 2 s and 40 px
  of a real one.
- Finding the pointer and growing text alone gets a quarter of steps right. The learned
  parts — the screen-reaction filter, the OCR naming and the typing filter — double both
  numbers. For typing alone they lift the real share from 12.2% to 47.4%.

**Clicks, 974 unseen recordings from all 87 applications**, step by step:

| | Steps that are real | Clicks found | Right name |
|---|---|---|---|
| v1 — pointer templates, logistic filter | 40.8% | 27.1% | 70% |
| v2 — pointer network, logistic filter | 46.5% | 29.9% | 75% |
| **v2 — pointer network, LightGBM filter (now)** | **54.0%** | **29.6%** | **77%** |

The filter was chosen out of four models (logistic regression, LightGBM, random forest,
gradient boosting), each fitted and thresholded the same way on training recordings
only. The tree models separate clicks from other pointer stops better (held-out AUC
0.82 against 0.76).

**It varies by application.** Lemmy finds 61% of steps, NetBeans 52% and OpenToonz 50%.
draw.io, Veusz and OnlyOffice PDF Forms find between one in ten and one in seven.

## 5 · Ready to use

- **In the frontend:** the results page shows "Steps read from the video". Selecting a
  step plays the recording from that moment. Each SOP phase lists the actions found in
  it. It runs beside the backend, which is unchanged.
- **Tested with the team backend:** run locally, frontend + backend + detector work
  together in the browser.
- **Deployable:** a Docker image, tested at 4 CPUs / 8 GB, and a Terraform package that
  adds `/sop-detector/*` to the existing load balancer without changing the backend
  stack. Steps are in `Evaluation/deploy/sop-detector/README.md`.
- **Speed:** clicks take under 40 s for a 40 s video. With typing, the whole video takes
  4–8 minutes on 4 CPUs. Stored demo videos are answered at once.
- **Code:** one package, `Evaluation/detector/`, separate from the research scripts.

## 6 · Limits

- **Just over half the steps it shows are real, and it finds about three in ten.** It
  suits a draft SOP that a person checks.
- **A third of logged clicks are on icons with no text.** The detector names clicks by
  the text under the pointer, so it does not report these.
- **Not detected:** key presses, shortcuts and drags.
- **A new video takes minutes**, mostly reading the screen once a second for typing.

## 7 · Comparing SOP detectors fairly

Scores on a few applications are not comparable with scores on many. Across the 61
applications above, the share of steps found runs from 61% (Lemmy) down to 10%
(OnlyOffice PDF Forms). A test on a handful of chosen applications can land anywhere in
that range.

**I propose one shared test** for any SOP detector:

- the same unseen recordings (the 720 above, or any agreed set);
- the same reference (the log-based SOP);
- the same scoring rules (section 3).

Send the steps your detector writes for those recordings as `[{t, action, text}]`
(with the click position `x, y` if it has one), and I will score them under the same
rules as ours (`combined_sop_v3.py`). Then the team can pick on evidence.
