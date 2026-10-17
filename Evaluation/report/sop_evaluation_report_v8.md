# SOP detector — evaluation report

Video2Knowledge · Joshua · 2026-10-17 · v8

## 1 · What it does

A user uploads a screen recording. The SOP detector writes the steps they performed —
from the video alone, with no action log:

```
SOP: Eclipse procedure
 1.  Click 'Package Explorer'                 [1.8 s]
 2.  Click 'Modulepath'                       [9.2 s]
 3.  Click 'Open'                            [20.4 s]
 4.  Click 'Module Dependencies'             [24.2 s]
 5.  Click 'facebook-messenger-1.0.0.jar'    [30.4 s]
 6.  Click 'Apply and Close'                 [35.8 s]
```

It finds two kinds of step: **Click** (73% of the steps in an SOP) and **Type** (7%).

## 2 · How it works

**First, name the application** from the screen (94.5% correct over 70 applications).
Then two branches read the video:

**Typing**

1. Read the screen with OCR, one frame per second.
2. Keep text that **grows** at the same spot from frame to frame — that is a field being
   typed into: `=textjoin(` → `=textjoin(" ", A1,B1,C1`.
3. A filter trained for that application decides whether the user typed it or the screen
   showed it by itself (program output, labels).
4. Write "Type …" steps.

**Clicks**

1. Follow the **mouse pointer**, five frames per second.
2. Where the pointer **stops**, there may be a click.
3. Keep the stops after which **the screen reacts** — a menu opens, a dialog appears.
4. Read the text under the pointer with OCR and write "Click '…'".

Both kinds of step are put in time order as one SOP.

## 3 · Results

Scored on recordings the models never saw, against the SOP written from the action log.

| | steps that are real | steps found |
|---|---|---|
| **Typing** (61 applications) | **50.6%** | **26.4%** |
| **Clicks** (5 applications) | **51.5%** | **50.5%** |
| **The whole SOP** (5 applications) | **50.7%** | **45.2%** of all steps |

- Before clicks were added, the detector found **2.1%** of the steps; now **45.2%**.
- A found click is a median **8 px** from the true click point.
- The click's name matches the log-based SOP's name in about three of four cases.

## 4 · An example

Eclipse, a recording no model saw; selected steps. Left: from the video alone. Right:
from the action log. ✓ = lands on a real click.

| from the video alone | from the action log |
|---|---|
| Click 'Package Explorer' ✓ | Click 'Package Explorer' |
| Click 'Modulepath' ✓ | Click 'Modulepath' |
| Click 'Open' ✓ | Click 'Open' |
| Click 'Module Dependencies' ✓ | Click 'Module Dependencies' |
| Click 'facebook-messenger-1.0.0.jar' ✓ | Click 'facebook-messenger-1.0.0.jar' |
| Click 'Apply and Close' ✓ | Click 'Apply and Closo' |
| Click 'Onen' (the same press read twice) | |
| Click 'Cancel' (the user only paused there) | |

## 5 · Limitations

- **About half the steps it shows are real, and about half the steps are missed.**
- **Clicks are tested on 5 applications** (Eclipse, VSCode, NetBeans, KDevelop, Bash).
- **The pointer is sometimes not recognised** — a hand or I-beam pointer on a busy
  background. This is the largest source of missed clicks.
- **Not detected:** Enter and other keys, shortcuts, drags.

## 6 · Next steps

1. Test clicks on all 87 applications (the full dataset is now downloaded).
2. Train a small model to recognise the pointer in any shape.
3. Retrain the typing filter on one-frame-per-second frames, as a real upload is read.
4. Connect the detector to the SOP endpoint, so the website shows these steps.

## 7 · Code and demo

- Code: `Evaluation/` on the `feat/frontend` branch. `bare_sop_v1.py video.mp4` runs the
  whole detector on one video.
- Demo: `demo_server_v1.py` serves the detector's steps to the team's frontend, unmodified.
- Full details, every number and its method: `sop_evaluation_report_v7.docx`.
