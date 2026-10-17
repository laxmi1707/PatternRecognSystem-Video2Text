# Evaluation report — generating an SOP from a bare screen recording

Video2Knowledge · evaluation workstream · 2026-10-17 · v7

The bare-video SOP detector: how it recovers typed text and, new in this version, clicks
from the mouse pointer; how each scores on recordings it never saw; and how the two
together compare with the SOP written from the action log.

---

## Executive summary

| | |
|---|---|
| **Application named from pixels alone** | **94.5%** of 6,991 recordings, 70 applications (1.4% by chance) |
| **Typed steps** | **50.6%** of the steps shown are real; **26.4%** of 1,690 typed strings recovered — 61 applications, out of fold |
| **Clicks — new in v7** | **50.5%** of 204 clicks found by following the mouse pointer, a median **8 px** from the true point; **51.5%** of click steps are real clicks — 59 held-out recordings of 5 applications |
| **The whole SOP** | typing and clicks together recover **45.2%** of every step the log-based SOP writes for those recordings, against **2.1%** with typing alone; **50.7%** of the 213 steps shown are real |
| **Click names** | **32.8%** of clicks are recovered with the same name the log-based SOP gives them, e.g. "Click 'Apply and Close'" |
| **On the team's frontend** | a local demo serves the detector's steps to the unmodified frontend as its SOP and runbook (section 15) |
| **On real uploads** | the typing figures use frames timed by the action log; processed as a real upload, typing recall held (50% on both, 12 recordings) while precision fell (78% → 27%) until the filter is retrained on upload-style frames (section 8.1). The click figures already read the video as an upload is read. |
| Not recovered | Enter and other keys, shortcuts, drags; clicks are measured on 5 applications so far |

**What changed since v6, in one line.** v6 recovered only what the user typed — about 2%
of the steps in these recordings. The mouse pointer is drawn in the recordings, so v7
follows it: where it comes to rest and the screen answers, the text under it names a
click. On the recordings it was measured on, that lifts coverage of the log-based SOP
from 2.1% to 45.2%.

**Also from this work:** the application-identification model was scored against
unnormalised labels. The dataset spells 70 applications 107 ways (`ATOM` / `Atom`,
`krtia`, `morzillafirefox`); scoring against canonical names lifts the best model from
87.63% to **94.49%**, and every model by 5.3 to 9.1 points, with no retraining.

---

## 1 · Background

### 1.1 What the system is for

Video2Knowledge takes a screen recording of someone performing a task and produces two
things: a **classification** of the activity, and a **standard operating procedure
(SOP)** — the steps the person performed, in a form a colleague could follow:

```
1.  Type "sudo adduser priya"
2.  Press Enter
3.  Click "Application of Funds (Assets)"
4.  Type "Nabil Bank"
5.  Click "Save"
```

This report evaluates the SOP half. The classification half is evaluated in
`evaluation_report_en_v3`.

### 1.2 What the dataset provides, and what a real user does not

The training data is **VideoCUA** (`ServiceNow/VideoCUA`): screen recordings of tasks in
70 desktop applications. Each ships with an **`action_log.json`**, a timestamped record
of everything the person did:

```json
{"action_type": "TYPING",  "action_params": {"text": "sudo adduser priya"}, "t": 1.4}
{"action_type": "CLICK",   "action_params": {"x": 744, "y": 427},           "t": 17.2}
{"action_type": "HOTKEY",  "action_params": {"keys": ["ctrl", "s"]},        "t": 22.8}
```

The SOP generator already in the repository (`v2k/sop.py`) transcribes this file. **A
user who uploads a recording has no such file**, and the backend has no fallback: with
no actions, `extract_segments` returns the whole video as one segment and the step list
is empty.

### 1.3 The question this report answers

> **From the video alone — no action log, no keystroke capture, no accessibility tree —
> can the system recover the steps the user performed?**

Everything measured below reads only the video's frames. The action log is used to train
the models and to score them, never at inference. Sections 3-11 cover typed text, as in
v6; section 12 adds clicks, and section 13 scores the two together.

---

## 2 · Glossary

| term | meaning |
|---|---|
| **SOP** | standard operating procedure: the numbered steps that are the system's output |
| **`action_log.json`** | the dataset's ground truth: every click, keystroke and mouse move, timestamped |
| **bare video** | a recording with no action log — what a real user uploads |
| **frame cache** | precomputed per-frame data: OCR text with positions, and feature vectors; 478 MB for all 6,991 recordings |
| **keyframe** | a frame selected for full-resolution OCR; not every frame gets it |
| **candidate** | a screen region the extractor proposes as possibly typed text |
| **ranker** | the filter that decides, for each candidate, whether it is **text the user typed** or **text the screen showed by itself** — program output, labels, menus. It does not decide what kind of action happened: every step it keeps is a "Type" step. It gives each candidate a score from 0 to 1 and keeps those at 0.5 or above. |
| **stage 1 / stage 2** | name the application / find and filter the typed steps |
| **routing** | using stage 1's answer to choose which application's ranker scores the candidates |
| **oracle routing** | routing by the *true* application — a diagnostic, not deployable |
| **fold** | one part of a 5-way cross-validation; every model is scored on recordings it never trained on |
| **precision / recall** | of the steps the SOP shows, the share that are real / of what the user did, the share the SOP shows |
| **pointer stop** | a moment where the mouse pointer is seen moving in one frame and not in the next: a candidate click at that point |
| **self-match** | recognising the pointer by its own movement: the picture at its new place equals the picture at its old place one frame earlier, so shapes with no template (a hand, an I-beam) are seen too |
| **reaction filter** | a small model that keeps the pointer stops after which the screen changes the way it does after a click |
| **held-out recording** | for clicks, one of the 59 recordings (30% of 215, by task id) that no click model was fitted on |

---

## 3 · The architecture

```
                    bare video (mp4, no action log)
                                 |
    ===========  STAGE 1  ===============================================
                                 |
              per-frame visual features from the cache
              (ResNet-18 embedding, colour and layout, OCR text)
                                 |
                      classifier over 70 applications
                                 |
                   "this is OnlyOffice Spreadsheet"   (94.5% correct)
                                 |
    ===========  STAGE 2  ===============================================
                                 |
      2a  CANDIDATES - every screen region whose text GREW between
          consecutive keyframes at the same position:
                frame 2:  =textjoin("
                frame 3:  =textjoin(" ",,A1
                frame 5:  =textjoin(" ",A1,B1
                frame 6:  =textjoin(" ", A1,B1,C1     -> one candidate
                                 |
                  515,941 candidates; 90.1% of typed strings are among
                  them, but only 1.1% of candidates are typed text
                                 |
      2b  RANKER - that application's model scores each candidate
          from 32 features; keep 0.5 or above
                                 |
      2c  MERGE - repeated readings of one string become one step
                                 |
                      steps:  Type "..."
```

### 3.1 Why extraction watches text grow

The first extractor looked for a shell prompt — a region ending in `$` — and took the
rest of the line. It reached 43.5% recall at 77.1% precision on terminals and **zero** on
Anki, LibreOffice Writer and Frappe Books, which have no prompt. A field being typed into
grows wherever it is — a shell, a spreadsheet's formula bar, a search box — so growth
works in GUI applications too. The prompt rule survives only as a measured terminal
baseline.

### 3.2 What the ranker reads

Growth also fires on things nobody typed. Program output appears line by line; OCR
re-reads a label slightly differently between frames. Only about one candidate in ninety
is typed text. The ranker separates them, reading 32 features computed from the
candidates alone:

| group | features | what it tells the ranker |
|---|---|---|
| **frame** (13) | position x and y, length, characters gained, frames spent growing, OCR confidence, digit and letter fractions, word count, prompt adjacency, time on screen, distinct readings | where and how the text appeared |
| **shape of the string** (13) | contains a space; `=` or `(`; `/`; ` -` flag; `.`; ends in `:`; share of capitals and punctuation; starts lowercase; title-case words; longest word; first word a common shell command; starts with `=` | whether it *looks* like a command or a formula rather than a label |
| **text content** (1) | a character n-gram model trained across every application on the training folds, scoring "does this look typed" | evidence that does not depend on screen position |
| **recording context** (5) | other candidates on the same row; vertical rank; how many times the string was read; time on screen relative to the rest; whether it is the lowest line | program output arrives as a block of lines; typed input sits on one line on its own |

The text model is a hashed character n-gram linear classifier: nothing to fit at
inference, saved inside the detector's bundle. To keep it honest, every training row's
text score comes from a model that never saw that row (three inner folds by recording).

One LightGBM ranker is trained per application, deliberately conservative — shallow
trees, large leaves, row and feature subsampling — because some applications have only a
few dozen typed strings.

### 3.3 Why identify the application first

**The objection a reader will raise.** Commercial tools that write step-by-step guides —
UiPath, Scribe, Tango — never *classify* the application: they run on the user's machine
and the operating system tells them which window is in front. Large vision-language
models take the opposite route and absorb application identity into one model.

**Why this design needs the stage.** Its input is a finished `.mp4`. No window handle, no
process name, no accessibility tree was recorded, so the application must be inferred
from pixels.

**What the stage buys, measured.** One pooled ranker for all applications recovers 18.3%
of typed strings at 51.2% precision; routing to per-application rankers recovers 26.4% at
50.6% — about **1.4×** the recall at the same precision. Screen position is still the
single most-used feature, and position only means something within one application.

**And how that changed.** With frame features alone the gap was 2.7×. Text and context
evidence work across applications, so the pooled ranker caught up part of the way. The
claim must always carry the feature set it was measured with.

**Stage 1's mistakes cost almost nothing.** Routing on stage 1's guess scores 50.6% /
26.4%; routing on the true application scores 50.6% / 26.6%. A misidentified recording
lands on a similar application's ranker or on none, and none emits nothing — the
detector fails quietly rather than inventing steps.

### 3.4 The click branch

Typing is found in the OCR text; clicks are found from the mouse pointer, in a second
branch that reads the same video at five frames per second. Section 12 explains each
part and how it was arrived at.

```
                    bare video (mp4, no action log)
                                 |
            5 frames per second; what changed between frames
                                 |
   1  POINTER  small changed regions that match a pointer template,
               or that match themselves one frame earlier (any shape)
                                 |
   2  STOP     seen moving in this frame, not in the next
               -> a candidate click at that point
                                 |
   3  FILTER   keep the stops that look like clicks: how long the pointer
               rests; how much of the screen changes 1-3 s later, anywhere
               and within 200 px; how busy the screen was just before
                                 |
   4  NAME     OCR around the stop; the text under the pointer, or the
               nearest within 70 px; no text -> dropped
                                 |
   5  MERGE    the same name twice within 2 s is one click
                                 |
                       steps:  Click "Apply and Close"
```

Click steps and typed steps are then put in time order as one SOP.

---

## 4 · Three worked examples

### 4.1 A typed formula, seen without a keystroke log

**OnlyOffice Spreadsheet, recording 70039**, "Use the TEXTJOIN function to concatenate
text with a delimiter." The OCR readings at one screen position (x 0.124, y 0.221 of the
frame) as the formula was typed:

| keyframe | time | OCR reading |
|---|---|---|
| 2 | 0:18.7 | `=textjoin("` |
| 3 | 0:19.6 | `=textjoin(" ",,A1` |
| 5 | 0:21.9 | `=textjoin(" ",A1,B1` |
| 6 | 0:23.1 | `=textjoin(" ", A1,B1,C1` |

OCR reads `",,"` as `","` at frame 5; the extractor tolerates it because the new reading's
start still matches the previous one closely. The candidate: 6 letters and digits gained,
tracked over 7 frames, mean OCR confidence 0.70. **Ranker score 0.858, kept.** Only
afterwards, for scoring: the log records `=TEXTJOIN(" ",,`, so this is a correct step.

### 4.2 One recording, every decision

**Bash, recording 111478**, "Add a new user." 77 candidates; all 7 typed strings of three
characters or more are among them. Scores from the ranker stage 1 chose, out of fold:

| score | typed by the user? | candidate | outcome |
|---|---|---|---|
| 0.987 | yes | `sudo adduser priya` | **step** |
| 0.969 | yes | `sudo adduser priyal` | merged into the step above |
| 0.933 | yes | `priya` | merged |
| 0.820 | no | `new password:` | step — wrong |
| 0.757 | no | `for` | step — wrong |
| 0.676 | no | `the` | step — wrong |
| 0.645 | no | `password` | merged |
| 0.591 | yes | `priyanka` | **step** |
| 0.453 | yes | `1234567890` | dropped, just under 0.5 |
| 0.388 | yes | `priyankal` | dropped |

Twenty candidates pass 0.5; merging repeats leaves six steps, two of them real. Two of
the seven typed strings are recovered although all seven were candidates. **This is the
typing half's central finding on one page:** extraction finds the text, and the loss is
in the filter.

### 4.3 A task done by clicking, recovered from the pointer

**Eclipse, recording 52918** — adding an external JAR to a project's module path. No
click model was fitted on this recording. Left, the steps v7 writes from the video alone;
right, the steps `v2k/sop.py` writes from the action log (an empty name means the log-based
generator found no text near the click either). ✓ marks a step that lands on a logged
click.

| from the video alone | from the action log |
|---|---|
| 1.8 s Click 'Package Explorer' ✓ | 2.0 s Click 'Package Explorer' |
| 9.2 s Click 'Modulepath' ✓ | 5.0 s Click '' |
| 13.6 s Click 'Ndd External' ✓ | 10.6 s Click 'Modulepath' |
| 14.6 s Click 'Add Variablo ..' | 14.0 s Click 'Add JARS ..' |
| 17.8 s Click '~logging-1.2.jar' ✓ | 17.9 s Click '' |
| 20.4 s Click 'Open' ✓ | 20.8 s Click 'Open' |
| 21.2 s Click 'Onen' | 24.2 s Click 'Module Dependencies' |
| 24.2 s Click 'Module Dependencies' ✓ | 27.4 s Click 'Add Externab' |
| 27.0 s Click 'Add JARS' ✓ | 30.4 s Click 'facebook-messenger-1.0.0.jar' |
| 27.8 s Click 'Add External JJARs:' | 32.9 s Click '' |
| 30.4 s Click 'facebook-messenger-1.0.0.jar' ✓ | 36.5 s Click 'Apply and Closo' |
| 32.0 s Click 'Cancel' | |
| 35.8 s Click 'Apply and Close' ✓ | |

The procedure can be followed from the left column: the panel, the module path, the
external JAR, the file, Apply and Close. Its faults are typical too — an OCR misreading
(`Ndd` for `Add`), one press read twice (`Open`, `Onen`), and stops where the user paused
over a neighbouring control (`Add Variablo`, `Cancel`).

---

## 5 · Method

### 5.1 Data

| | |
|---|---|
| Recordings in the frame cache | 6,991 |
| Applications | 70 |
| Recordings with full-resolution OCR | 6,991 (all) |
| Logged actions | 50,429 |
| Logged typed strings | 2,104 (**4.2%** of actions) |

### 5.2 Scope

The ranker needs logged typing to learn from and be scored against, so an application is
in scope if it has at least five logged typed strings: **61 of the 70**, with 6,716
recordings, 2,085 typed strings and 48,708 of the 50,429 actions. Every figure below is a
61-application figure.

### 5.3 Cross-validation

Five folds from `v2k.evaluate.make_folds` (`StratifiedGroupKFold`, seed 42), **grouped by
recording**, so no recording's frames appear on both sides. **Both stages share the same
folds**: a recording's application guess and the ranker applied to it both come from
models that never saw it.

### 5.4 What counts as a correct step

| | definition |
|---|---|
| **a step worth recovering** | a logged typed string of at least **three** letters or digits |
| **a match** | lowercase letters and digits only; one contains the other, or `difflib` similarity ≥ 0.80 |
| **the delivered SOP** | candidates scoring ≥ 0.5, with repeated readings merged (each group shown as its best-scored reading) |
| **precision** | SOP steps that claim a logged string ÷ all SOP steps |
| **recall** | logged strings claimed by a step ÷ all logged strings in scope (1,690) |

Claims are **one-to-one**: a step claims at most one logged string and a string is claimed
at most once, by maximum bipartite matching per recording. A duplicate step is therefore a
false positive, and a string typed twice needs two steps — how a detection benchmark
scores.

**Two precision figures.** Counting every reading the ranker keeps that matches typed
text gives **69.3%**; merging repeated readings of one string and scoring one-to-one gives
**50.6%**. Both are in `runs/run_037_sop-detector/report.md`. The second is the headline
throughout because it describes the document a reader receives, where one typed command
appears once.

### 5.5 Why three characters

395 logged strings (18.9%) are one or two characters — `1` ×35, `2` ×18, `10` ×16,
`hi` ×15, `ok` ×10. They are not instructions a reader can follow, and under the lenient
match a one-character string is "contained" in almost any candidate. Measured with the
first ranker: excluding them **raised** both precision and recall, because the ranker
stopped training against one-character targets; the extraction ceiling also rose rather
than fell. Three rather than six was chosen on substance — six would exclude real commands
such as `ls` and `git`.

| minimum length | typed strings | precision change | recall change |
|---|---|---|---|
| 1 | 2,054 | — | — |
| **3** | **1,690** | **+7.6 points** | **+2.1 points** |
| 4 | 1,558 | +8.2 points | +1.8 points |
| 6 | 1,156 | +10.8 points | +3.0 points |

*Changes against a one-character floor, measured with the first ranker.*

### 5.6 How clicks and the whole SOP are scored

| | definition |
|---|---|
| **data** | the 215 recordings of Bash, VSCode, Eclipse, KDevelop and NetBeans whose videos were on disk, split 70 / 30 by task id with a fixed hash |
| **what is fitted on the 156 training recordings** | the pointer templates, the reaction filter, its threshold (0.16, keeping 90% of training recall) and the stop rule; nothing is chosen on the 59 held-out recordings |
| **a found click** | a click step whose stop lies between 2 s before and 0.3 s after a logged click and within 40 logged pixels of it, one to one — people stop the pointer, then press about a second later |
| **a correct name** | the step's name matches the name `v2k/sop.py` gives that logged click (the same lenient text match as typing), or neither has one |
| **the reference SOP** | every step `v2k/sop.py` writes from the log, mouse moves excluded: 204 clicks, 18 typed strings of three or more characters, and 17 others (key presses, shortcuts, drags, shorter typing) — **239 steps** |
| **typed steps in the combined figures** | run_037's out-of-fold ranker scores for these recordings, threshold 0.5, merged as in 5.4 |

The log-based SOP is not a perfect reference for names: it names only 151 of the 204
clicks (74%), finding no text near the rest (icons), and its own OCR misreads some labels
(section 12.5).

---

## 6 · Stage 1 — naming the application

### 6.1 A label defect worth 6.87 points

The training labels are read from a free-text field that VideoCUA fills inconsistently:
**107 distinct strings for 70 applications.**

| kind | examples |
|---|---|
| case | `ATOM`/`Atom`, `7-ZIP`/`7-Zip`, `GIMP`/`Gimp`, `gedit`/`Gedit` |
| typos in the dataset | `Arduino iDE`, `Code: :Blocks`, `krtia`, `morzillafirefox`, `OnlyOffice Calender` |
| naming | `Brave Browser`/`Brave`, `Chromium Browser`/`Chromium`, `Spyder IDE`/`Spyder` |

The classifier was asked to tell apart spellings that look identical on screen, and each
application's examples were split across its spellings. Lowercasing and stripping
punctuation collapses 107 to 77; seven aliases finish 77 to 70.

### 6.2 Results

Recording-level accuracy over 70 applications; majority-class baseline 0.0346.

| features : model | raw labels | canonical labels | gain (points) |
|---|---|---|---|
| **OCR + UI + visual + CNN : MLP** | **0.8763** | **0.9449** | **+6.86** |
| OCR + UI + visual + CNN : SVM | 0.8640 | 0.9311 | +6.71 |
| OCR + UI + visual : random forest | 0.8584 | 0.9298 | +7.14 |
| OCR + UI + visual + CNN : random forest | 0.8668 | 0.9289 | +6.21 |
| CNN : MLP | 0.8561 | 0.9242 | +6.81 |
| OCR + UI + visual : MLP | 0.8198 | 0.9107 | **+9.09** |
| CNN : SVM | 0.8389 | 0.9029 | +6.40 |
| OCR + UI + visual : SVM | 0.8148 | 0.8992 | +8.44 |
| CNN : random forest | 0.8032 | 0.8561 | +5.29 |

Every model gains 5.3 to 9.1 points, so the ranking of models barely moves. The fix costs
no retraining. **macro-F1 after the fix has not been re-measured**; any macro-F1 quoted for
stage 1 must be re-run first.

---

## 7 · Stage 2 — candidates

| | |
|---|---|
| Candidates over 61 applications | 515,941 |
| That match a typed string | 1.1% |
| Typed strings carried by at least one candidate | **1,522 of 1,690 = 90.1%** |

**90.1% is the ceiling**: no ranker can recover more. The missing 9.9% are typed strings
no candidate carries. One cause is text typed and cleared between two keyframes, where
full-resolution OCR never looked; how much of the 9.9% that explains has not been
measured.

---

## 8 · Results — typed steps

Out of fold, 61 applications, 6,716 recordings, 1,690 typed strings; `runs/run_037`.

| variant | threshold | steps | precision | recall |
|---|---|---|---|---|
| **routed by stage 1 — the detector** | **0.5** | **882** | **50.6%** | **26.4%** |
| routed by stage 1 | 0.3 | 1,352 | 39.4% | 31.5% |
| routed by the true application | 0.5 | 887 | 50.6% | 26.6% |
| one pooled ranker, no routing | 0.5 | 603 | 51.2% | 18.3% |
| every candidate kept — the ceiling | — | 515,941 candidates | 1.1% | 90.1% |

The threshold trades one for the other along this curve (routed by stage 1):

| threshold | 0.10 | 0.20 | 0.30 | 0.40 | **0.50** | 0.60 | 0.70 | 0.80 | 0.90 |
|---|---|---|---|---|---|---|---|---|---|
| steps | 3,274 | 1,904 | 1,352 | 1,079 | **882** | 710 | 590 | 482 | 313 |
| precision | 21.8% | 31.4% | 39.4% | 44.9% | **50.6%** | 55.2% | 60.2% | 63.9% | 73.8% |
| recall | 42.3% | 35.4% | 31.5% | 28.7% | **26.4%** | 23.2% | 21.0% | 18.2% | 13.7% |

0.5 is the reported operating point. A team that prefers fewer, surer steps can choose 0.8
(63.9% / 18.2%); one that prefers coverage can choose 0.3.

### 8.1 Checked on real uploads

The frame cache behind every figure above was built with each recording's action log:
`v2k/frames.py` takes a keyframe at every logged action, and full-resolution OCR runs only
on keyframes. A user's upload has no log, so its keyframes are a plain one-per-second grid.
The evaluation therefore read the screen at moments only the log knew.

`bare_vs_cached_v1.py` measures the effect. Twelve recordings whose videos are on disk (6
Bash, 6 VSCode; 14 typed strings) were re-extracted exactly as `detect --video` would
process an upload, a detector was trained without them, and both versions of each
recording were scored against the same log, routed by the true application:

| keyframes | candidates | steps | precision | recall | ceiling |
|---|---|---|---|---|---|
| at logged actions (all figures above) | 492 | 9 | 77.8% | 50.0% | 85.7% |
| **one per second, no log (a real upload)** | 930 | 26 | **26.9%** | **50.0%** | **92.9%** |

**Recall holds and the ceiling rises:** a one-per-second grid sees the typed text as well as
log-timed frames do. **Precision does not hold:** the grid yields nearly twice the
candidates, and a filter trained on log-timed frames lets about three times as many steps
through, the extra ones nearly all screen text. The sample is small — twelve recordings —
so the size of the drop is uncertain, but its direction is not.

**The remedy is to train on upload-style frames**, so that the filter learns the
candidates it will actually see. The full dataset (87 applications, 26 GB) was downloaded
again on 17 October; what remains is full-resolution OCR at one frame per second for every
recording.

---

## 9 · Improving the ranker

Both rounds use the same folds, the same candidates and the same delivered-SOP scoring,
so every row is comparable. Where two versions emit different numbers of steps, the fair
comparison is precision at the same recall.

### 9.1 Round 1 — what the ranker reads

`sop_ranker_experiments_v1.py`, `runs/run_033`. Default per-application LightGBM.

| ranker reads | precision @0.5 | recall @0.5 | precision at the first version's recall | recall, applications never trained on |
|---|---|---|---|---|
| 13 frame features (first version) | 38.1% | 26.6% | 38.1% | 3.1% |
| + shape of the string | 39.5% | 28.3% | 40.6% | |
| + text content model | 42.3% | 26.1% | 40.2% | 6.1% |
| **+ recording context** | **47.9%** | **26.3%** | **46.3%** | **10.9%** |

Context does the most: program output arrives as a block of lines on neighbouring rows,
typed input as one line on its own, and a typed string is read again and again while it
stays on screen. Feature importance in the pooled ranker now reads: x position, text
score, times read, relative time on screen, y position, vertical rank, lines on the same
row — position is still first, but no longer alone.

The last column is the more surprising result. The earlier conclusion that unseen
applications were a dead end held for position-only features; with text and context the
pooled ranker recovers **3.5×** as much on applications it never trained on. 10.9% is
still weak, but it is no longer the floor.

### 9.2 Round 2 — how the ranker is trained

`sop_ranker_experiments_v2.py`, `runs/run_036`. Same 32 features.

| training | precision @0.5 | recall @0.5 | precision at 26.3% recall | recall at 47.9% precision |
|---|---|---|---|---|
| D — per-application, default settings | 47.9% | 26.3% | 47.9% | 26.3% |
| E — one pooled ranker told the application | 48.1% | 23.8% | 43.6% | 23.8% |
| **F — per-application, conservative** | **50.6%** | **26.4%** | **50.6%** | **26.4%** |
| G — mean of D and E | 52.8% | 24.1% | 49.1% | 27.6% |

F's settings (300 trees at learning rate 0.03, 15 leaves, at least 40 rows per leaf, 80%
row and feature subsampling) were fixed before scoring, not tuned on the test folds.
**Fold by fold**, at threshold 0.5:

| fold | typed strings | D precision | D recall | F precision | F recall |
|---|---|---|---|---|---|
| 0 | 348 | 53.9% | 27.9% | **58.0%** | 27.0% |
| 1 | 358 | 43.4% | 22.9% | **44.1%** | 23.2% |
| 2 | 342 | 47.4% | 26.6% | **49.7%** | 26.0% |
| 3 | 310 | 47.6% | 28.4% | **50.0%** | 28.7% |
| 4 | 332 | 47.8% | 25.9% | **52.0%** | 27.4% |

F raises precision in **all five folds**, by 0.7 to 4.2 points, while recall moves by −0.9
to +1.5 points. G also raises precision everywhere but loses 2 to 3 points of recall in four
folds: it moves along the curve rather than improving it. E is worse — applications differ
enough that a shared model, even one told the application, does not replace separate ones.

A full retrain with F (`runs/run_037`) reproduces 50.6% / 26.4% exactly.

### 9.3 A change measured and rejected

Merging shows each group of repeated readings as its best-scored member. Showing the
**longest** member instead seemed better for a reader — `sudo adduser priya` rather than a
fragment `priya` — and scored 0.2 points higher (48.1% against 47.9%). It was rejected:
the gain came from replacing a correct `priyanka` with the shell prompt line
`user@workstation-priyankaj:~$`, which the lenient match credits because it contains the
name. Grouping only readings of similar length avoided that but cost 6.6 points of
precision. The rejection is recorded in `dedupe()`'s docstring.

### 9.4 Diminishing returns

Round 1 gained 9.8 points; round 2 gained 2.7. These 32 features are close to their limit.
The next gain needs a new kind of evidence — section 16.

---

## 10 · Applications never seen in training

Two experiments answer two different questions.

**Does more training data help?** No — with frame features. Fifteen applications held out;
a frame-features-only pooled ranker trained on 8, 16 and 32 others (`ranker_scope_v1.py`,
threshold 0.3, earlier per-candidate scoring):

| training applications | precision | recall |
|---|---|---|
| 8 | 1.3% | 1.7% |
| 16 | 2.9% | 1.3% |
| 32 | 3.2% | 0.9% |
| keeping every candidate | 1.2% | 77.8% |
| *same ranker on applications it trained on* | *56.4%* | *10.7%* |

Position, the dominant feature then, does not transfer between applications however much
data is added.

**Do better features help?** Yes — section 9.1: with text and context, recall on
held-out applications rises from 3.1% to 10.9%. The detector still works best, by a wide
margin, on applications it was trained on, which is also how a deployment would know which
tools its staff use.

What *does* generalise within an application: the dataset spans 39 resolutions across 163
Anki recordings and 42 across 135 LibreOffice Writer recordings, and positions are
normalised by frame size. Holding out whole resolutions cost 0.8 points of precision in the
8-application evaluation.

---

## 11 · Results by application

Routed by stage 1, threshold 0.5, `runs/run_037`; the 20 applications with the most
recovered steps.

| application | typed strings | steps | correct | precision | recall |
|---|---|---|---|---|---|
| Ubuntu Terminal | 106 | 115 | 66 | 57.4% | 62.3% |
| Bash | 78 | 92 | 53 | 57.6% | 67.9% |
| OnlyOffice Spreadsheet | 59 | 49 | 39 | **79.6%** | 66.1% |
| Chromium | 40 | 56 | 37 | 66.1% | **92.5%** |
| DuckDuckGo | 52 | 72 | 33 | 45.8% | 63.5% |
| Zotero | 59 | 39 | 33 | **84.6%** | 55.9% |
| LibreOffice Calc | 60 | 35 | 23 | 65.7% | 38.3% |
| Anki | 100 | 30 | 22 | 73.3% | 22.0% |
| Frappe Books | 122 | 47 | 21 | 44.7% | 17.2% |
| Bitwarden | 91 | 29 | 20 | 69.0% | 22.0% |
| Lemmy | 48 | 111 | 17 | 15.3% | 35.4% |
| Cryptomator | 28 | 29 | 16 | 55.2% | 57.1% |
| Shotcut | 33 | 24 | 11 | 45.8% | 33.3% |
| Veusz | 27 | 20 | 9 | 45.0% | 33.3% |
| LibreOffice Writer | 46 | 13 | 8 | 61.5% | 17.4% |
| OnlyOffice PDF Forms | 50 | 12 | 7 | 58.3% | 14.0% |
| GNU Octave | 19 | 7 | 5 | 71.4% | 26.3% |
| GnuCash | 25 | 4 | 3 | 75.0% | 12.0% |
| OnlyOffice Document Editor | 36 | 8 | 3 | 37.5% | 8.3% |
| VSCode | 23 | 13 | 3 | 23.1% | 13.0% |

**The top 8 applications carry 68.6% of recovered steps.** The result is concentrated but
not degenerate; "covers 61 applications" should be quoted with that share.

The pattern is interpretable. Browsers and terminals lead: one unambiguous input region,
an address bar or a prompt. Chat applications trail: a message is typed and sent, so the
region vanishes instead of settling. **OnlyOffice Spreadsheet, at 79.6% precision and 66.1%
recall, answers "it only works on terminals"** — an ordinary GUI application with a formula
bar. Lemmy's 15.3% precision is the clearest remaining failure: a forum page full of text
that looks typed.

---

## 12 · Clicks — reading the mouse pointer

### 12.1 Why the pointer

Clicks are 41.3% of all logged actions, and **73.4%** of the actions an SOP would list
once mouse moves are set aside (typing is 7.4%, key presses 4.9%, shortcuts 3.4%, drags
3.3%). A detector that sees only typing therefore misses most of every procedure.

A press leaves no mark of its own in a video. What the video does show is the pointer: a
person moves it to a control, it comes to rest, they press, and the screen answers — a
menu opens, a dialog appears, a panel changes. The click branch reads exactly those three
things: where the pointer stops, whether the screen answers, and what text is under it.

### 12.2 How the design was arrived at

| attempt | result | kept |
|---|---|---|
| the largest change in an 8×8 tile grid, 4 fps (v6) | AUC **0.512** for "a click happened here" — chance: cursor blink and scrolling outweigh a click | no |
| is the pointer in the recordings at all? (`cursor_probe_v1.py`) | yes, visible at the logged click points | — |
| "the logged pointer moved here" (`cursor_click_probe_v1.py`) | AUC 0.927 — **withdrawn**: the log records a mouse move at the click itself (median gap 0.00 s, 84% within 0.25 s), so it restated the click | no |
| track the pointer in every frame with harvested templates (`pointer_tracker_v1.py`) | 42.7% of resting pointers placed within 25 px; arrow-shaped icons win too often | no |
| match templates only inside small regions that changed (`pointer_motion_v1.py`) | a stop near **57.8%** of clicks, a median 7.1 px away; 33.5% of stops are clicks | yes |
| + reaction filter (`pointer_reaction_v1.py`) | 44.0% of stops are clicks, at 52.5% of clicks found | yes |
| + a name from OCR, unnamed stops dropped (`click_labels_v1.py`) | 50.3% of steps are clicks | yes |
| + self-match, for pointer shapes the templates lack (`pointer_selfmatch_v1.py`, `_v2.py`) | a stop near **66.2%** of clicks, before filtering | yes |

The templates are harvested without any labelling: a frame with the pointer resting at a
logged point, minus a frame where it has moved elsewhere, leaves the pointer's picture.
Only the training recordings are used.

### 12.3 What each part contributes

Held-out recordings, 204 clicks; from `pointer_selfmatch_v2.py` and `click_sop_v3.py`.

| stage | click steps | clicks found | steps that are real clicks |
|---|---|---|---|
| every pointer stop | 442 | 66.2% | 30.5% |
| + reaction filter | 307 | 60.8% | 40.4% |
| **+ named, repeats merged — delivered** | **200** | **50.5%** | **51.5%** |

The reaction filter is a logistic model on eight features. It separates stops followed by
a click from the others at AUC **0.740** on held-out recordings. The most telling features:
how much of the screen changes two to three seconds after the stop (AUC 0.65 alone), how
long the pointer rests (0.65), and — counting against a click — how much changed in the
second *before* the stop (0.44): a person who stops while the screen is still scrolling is
usually reading.

### 12.4 Where the other clicks go

Measured one step before delivery (filter threshold 0.19; the delivered 0.16 finds 103
rather than 94), `missed_steps_v1.py`:

| what happened to the click | clicks | share |
|---|---|---|
| no pointer seen within 40 px of it | 66 | 32.4% |
| clicked again in the same place, so the pointer did not move | 3 | 1.5% |
| a stop was found; the reaction filter dropped it | 21 | 10.3% |
| a stop was found; no text under the pointer (an icon) | 16 | 7.8% |
| merged with a neighbouring click | 4 | 2.0% |
| **found** | **94** | **46.1%** |

**The largest loss is not seeing the pointer.** A contact sheet of the misses
(`pointer_miss_diag_v1.py`) shows why: over buttons and links the pointer is a hand, over
text an I-beam, and the harvested templates are almost all arrows. Self-match, which needs
no template, cut the clicks with no pointer seen near them from 77 to 66. The rest are
thought to be the pointer changing shape as it arrives — an arrow becoming a hand, so the
two frames no longer show the same picture — which is untested.

Two other ideas were measured and gave nothing: deciding a stop from motion near the
pointer rather than anywhere on screen (60 to 500 px, all worse on the training
recordings), and discarding self-matches that recur at one spot (an animation). The
global rule was kept.

### 12.5 How accurate a found click is

| | |
|---|---|
| **time** | a median 0.4 s before the press (half within 0.2-0.8 s): the stop comes before the press |
| **position** | a median 8.1 px from the logged point; 90% within 25 px |
| **name** | agrees with the log-based name for **74%** of found clicks where both have one (63 of 85). Of the 22 disagreements, at least four are the log side misreading: `Save` / `Sake`, `Project` / `Prciect`, `Window` / `Nvindow`, `Run and Debug` / `83` |
| **typical wrong name** | the neighbouring control — `Cancel` for `Add`, `File` for `Debug` — when the pointer rests between two controls or a menu is still opening |

---

## 13 · The whole SOP — typing and clicks together

The 59 held-out recordings, against all 239 steps the log-based SOP writes for them.
"Click and typed steps found" counts the 222 steps the detector attempts; "all logged
steps" counts every one, key presses and drags included.

| version | steps shown | real | click and typed steps found | … with the same name | all logged steps found |
|---|---|---|---|---|---|
| typing only (the v6 detector) | 13 | 38.5% | 2.3% | 2.3% | 2.1% |
| + clicks, template pointer (`combined_sop_v1.py`) | 190 | 49.5% | 42.3% | 30.6% | 39.3% |
| + one press read twice merged (`combined_sop_v2.py`) | 168 | 53.6% | 40.5% | 28.8% | 37.7% |
| + self-match pointer (`pointer_selfmatch_v2.py`) | 195 | 50.8% | 44.6% | 30.6% | 41.4% |
| **+ filter threshold chosen on training recordings, wider OCR crop, typed steps timed correctly (`click_sop_v3.py`) — delivered** | **213** | **50.7%** | **48.6%** | **32.4%** | **45.2%** |
| *variant:* unnamed stops kept as "Click (icon)" | 295 | 42.0% | 55.9% | 37.8% | 51.9% |
| *variant:* nearest text within 120 px instead of 70 | 255 | 45.5% | 52.3% | 32.0% | 48.5% |

The delivered version keeps roughly the precision of the typing detector (50.7% against
50.6%) while finding about twenty times as many of the steps. The "Click (icon)" variant
is the choice for a reader who prefers completeness: it finds over half of all logged
steps, at 42% precision.

**Typed steps are now timed correctly.** A typed step was timed at the first keyframe
showing its text. On log-timed keyframes that is the *next* action's frame — a median
11.2 s after the typing — which placed typed steps after the clicks that followed them.
It is now timed at the frame before the text appeared (it was typed between the two): a
median 0.0 s from the log. On a one-frame-per-second upload the two differ by at most a
second.

---

## 14 · What the detector does not recover

All 48,708 logged actions in the 61 typing applications:

| action type | count | share | recovered |
|---|---|---|---|
| mouse move | 21,310 | 43.8% | not a step |
| **click** | **20,118** | **41.3%** | **yes, from the pointer** — measured on 5 applications |
| **typing** | **2,085** | **4.3%** | **yes** |
| key press | 1,365 | 2.8% | no — Enter is about two-thirds of these |
| shortcut | 944 | 1.9% | no — paste is about a fifth |
| other (drags, mouse down / up, …) | 2,886 | 5.9% | no |

Keys, shortcuts and drags were left out by choice, to concentrate on clicks and typing,
which together are 80.8% of the actions an SOP lists. Drags matter mainly in drawing and
video-editing tools (LibreOffice Draw, Krita, Shotcut, Inkscape).

**The click figures cover 5 applications** — the programming tools whose videos were on
disk. Office suites and browsers, where clicking dominates even more, are not yet
measured; the whole dataset is now downloaded, so this is the next run (section 16).

---

## 15 · Demo on the team's frontend

`bare_sop_v1.py` runs the whole detector on one video file — application, typed steps,
click steps — reading nothing but the video. `demo_server_v1.py` answers the endpoints
the team's frontend calls (`SourceCode/frontend` on `main`, unmodified), with the response
shapes of `app/routers/knowledge.py`, so the frontend shows the detector's steps as its
SOP and its runbook:

```
python demo_server_v1.py          # port 8000
npm run dev                       # in SourceCode/frontend, port 5173
```

Nothing in `SourceCode/` is changed; the demo is local. Its one classification row is
stage 1's application mapped by hand to an activity label (Bash to terminal operations,
the IDEs to coding), not the team's activity classifier.

| video | length | detector time on CPU |
|---|---|---|
| Bash 111479 | 21 s | 157 s |
| Eclipse 52918 | 38 s | 469 s |
| Eclipse 52907 | 44 s | 448 s |
| VSCode 46738 | 44 s | 536 s |

Most of the time is full-resolution OCR at one frame per second.

**How it would fit the team's SOP.** The SOP endpoint writes one step per run of segments
with the same predicted activity — a phase such as "Execute terminal command". The
detector's Click and Type actions are the detail inside each phase, so they fit into each
step's description by time range, with no change to the response schema or the frontend.

---

## 16 · Recommendations

1. **Retrain the typing filter on upload-style frames before deploying it** (8.1). The
   dataset is on disk again; what remains is full-resolution OCR at one frame per second.
2. **Measure clicks on every application.** Harvest pointer templates and fit the reaction
   filter on the full dataset; today's figures are 5 programming tools.
3. **Learn the pointer instead of matching templates.** Not seeing the pointer loses a
   third of clicks. Crops at logged pointer positions, against crops elsewhere in the same
   frame, are free and exact labels for a small image classifier that would learn the
   hand, the I-beam and the arrow on any background.
4. **Integrate as detail inside the SOP endpoint's phases** (section 15): a
   `detect(video) → steps` function and the model files, called from the SOP endpoint.
   That endpoint's action-log fallback looks for `TYPE` and `KEY`, while the dataset
   writes `TYPING` and `PRESS`, and a click's `text` field is the mouse button (`Left`);
   worth fixing at the same time.
5. **Apply the stage-1 label normalisation.** +6.86 points on the best model for a one-line
   change; re-run macro-F1 before quoting it.
6. **Quote each figure with its scope**: typing 50.6% / 26.4% over 61 applications, out of
   fold; clicks 51.5% / 50.5% and the whole SOP 45.2% of logged steps, on 59 held-out
   recordings of 5 applications.
7. **The next typing gain needs new evidence, not more tuning**: a typed command is usually
   followed, within a second or two, by new output below it, and no feature looks at what
   happens after a candidate.

---

## 17 · Threats to validity

| # | threat | effect |
|---|---|---|
| 1 | **The text match is lenient**: one string containing the other counts (section 9.3 shows a case). Typing precision and click-name agreement are upper bounds. | optimistic |
| 2 | **The typing ceiling uses the same match**, so 90.1% carries the same bias. | unquantified |
| 3 | **Typing keyframes were taken at logged action times**, which a real upload cannot do. Measured in 8.1 on twelve recordings: recall unchanged, precision 77.8% → 26.9%. The typed share of the combined figures inherits this; the click branch reads the video as an upload is read. | typing precision optimistic |
| 4 | **Click figures come from 59 recordings of 5 programming applications.** How they spread across other applications is unknown. | scope, stated |
| 5 | **Click names are scored against the log-based SOP's own OCR**, which misreads labels and names only 74% of clicks (12.5). | names under-credited and over-credited |
| 6 | **Click designs were compared on the same 59 recordings.** Thresholds and rules were chosen on the training recordings, but the delivered version is the best of several shown on these 59. | mildly optimistic |
| 7 | **The metric is match-to-log, not usefulness.** No person has judged whether a step reads as a usable instruction or appears in the right order. | unmeasured |
| 8 | **9 of 70 applications are out of typing scope** for having fewer than five typed strings. | scope, stated |
| 9 | **The three-character floor is a judgement**, justified in 5.5 and checked against 1, 4 and 6. | stated |
| 10 | **Several typing variants were compared on the same folds.** F's settings were fixed beforehand and its gain held in every fold. | minor |
| 11 | **Untested**: other themes, rearranged panels, other application versions, other screen recorders (some do not draw the pointer). | scope, stated |

---

## 18 · How the conclusions evolved

All figures in this report are re-measured with the current detector; where they differ
from an earlier draft, this report's figures supersede it.

| earlier conclusion | now |
|---|---|
| "Clicks cannot be detected from the pixels" (tile grid, AUC 0.512) | **superseded**: following the pointer finds half of them |
| "Pointer movement predicts clicks at AUC 0.93" | **withdrawn**: the log restated the click (12.2) |
| "Spurious self-matches elsewhere on screen break stop detection" | **tested and wrong**: local stop rules changed nothing (12.4) |
| "Typed steps arrive about 11 s late" | **a keyframe-timing artefact**, fixed (13) |
| "Whole-workflow coverage is about 1.1%" | **typing only**; with clicks, 45.2% of logged steps on the measured recordings |
| "Routing doubles recall" | **depends on the features**: 2.7× with frame features, 1.4× now |
| "Applications never seen in training are a dead end" | **revised**: typing recall 3.1% → 10.9% with text and context |
| "Showing the longest reading improves the SOP" | **rejected**: its gain came from a scoring loophole (9.3) |
| "37.9% is the extraction ceiling" | **superseded**: the ceiling is 90.1% |

---

## 19 · Verdict

**The claim is supported within a measured boundary, and the boundary has moved.** From a
bare video, the detector names the application at 94.5% accuracy, recovers 26.4% of typed
text at 50.6% precision across 61 applications, and now recovers clicks from the mouse
pointer — half of them, with half of its click steps real, on recordings no click model
saw. Together, typing and clicks recover **45.2%** of every step the log-based SOP writes
for those recordings, up from 2.1%, at about the typing detector's precision.

**It does not yet reproduce workflows reliably.** About half the steps it shows are real
and about half the steps are missed; key presses, shortcuts and drags are not detected;
and clicks are measured on five applications. The two largest next gains are known:
seeing the pointer where templates fail, and training on frames as an upload produces them.

---

## 20 · Reproduction

Code: the evaluation harness, `Evaluation/` on the `feat/frontend` branch (commit
`54154e5`). Use the project's virtual environment; `lightgbm` is not installed system-wide.

```
python -m v2k.sop_detector train                       # typing: candidates, out-of-fold evaluation, fit
python sop_ranker_experiments_v1.py                    # section 9.1
python sop_ranker_experiments_v2.py                    # section 9.2
python pointer_tracker_v1.py harvest <sheet.png>       # pointer templates, training recordings only
python pointer_selfmatch_v2.py extract                 # pointer moves and screen changes, 5 fps
python pointer_selfmatch_v2.py eval                    # stop rule, reaction filter, sections 12.3-12.4
python click_sop_v3.py                                 # the merged SOP, section 13
python bare_sop_v1.py path/to/recording.mp4            # the whole detector on one video
python demo_server_v1.py                               # section 15
```

| measured cost | |
|---|---|
| Typing: candidate extraction from the frame cache, 6,716 recordings, 8 workers | 10-12 s |
| Clicks: pointer extraction at 5 fps, 215 recordings, 6 workers | 166 s |
| A new video, mp4 to SOP with typing and clicks | 7-12 times its length on CPU |
| Full-resolution OCR of one frame | 3.0 s |

| run or script | what it holds |
|---|---|
| `run_029_appid70` | stage 1, the 70-application classifier |
| `run_033`, `run_036` | typing ranker rounds 1 and 2 |
| `run_037_sop-detector` | **the typing detector this report describes** |
| `click_sop_v3.py` | **the click branch and the merged SOP this report describes** |
| `examples/sop_clicks_and_typing_heldout.md` | side-by-side SOPs for six held-out recordings |
