# Proposed label set

7021 tasks, 70 applications. Each label is assigned by the leading verb of the task instruction; `labels_v1.csv` has one row per task and can be fed straight to `python -m v2k train --labels csv:labels_v1.csv`.

## What the recordings actually contain

| category | tasks | share | apps | example instructions |
|---|---:|---:|---:|---|
| `configure_option` | 1436 | 20.5% | 66 | *Set status to busy*; *Turn off invisble mode* |
| `navigate_view` | 1288 | 18.3% | 68 | *Go to go invisible mode.*; *Display usage statistics from the profile menu* |
| `format_style` | 920 | 13.1% | 65 | *Change the user list style to "Compact"*; *Change time format to 24 hour format* |
| `edit_content` | 788 | 11.2% | 66 | *Add a video call in a moving messages channel.*; *add a voice call link from the compose message window and send it to "welcome to zulip" to* |
| `create_item` | 761 | 10.8% | 65 | *create "abczxb"*; *create "hi."* |
| `other` | 653 | 9.3% | 64 | *Reactivate an inactive bot named "abczxb"*; *Pin a topic '#Zulip' for quick access* |
| `insert_element` | 336 | 4.8% | 36 | *Embed the YouTube video “Sidemen abandoned in Europe 2” in the post "Writing: How to be co*; *Insert a table in a post or page.* |
| `file_manage` | 305 | 4.3% | 65 | *upload "musashi"*; *Save a message as draft and view the same* |
| `delete_remove` | 179 | 2.5% | 49 | *Remove custom css*; *Delete the message* |
| `search_filter` | 157 | 2.2% | 39 | *Search for text - 'Hi' in the conversations*; *Filter your messages by starred messages.* |
| `communicate` | 136 | 1.9% | 21 | *send a gif in a message*; *Send a reply message stating, "Thanks for the greetings," to the recent conversation with * |
| `media_control` | 62 | 0.9% | 16 | *Mark the "General" stream as read.*; *Bring the clip to the timeline and duplicate it* |

## The same tasks under the current DevOps labels

| category | tasks | share |
|---|---:|---:|
| `git_operations` | 58 | 0.8% |
| `docker_workflow` | 190 | 2.7% |
| `kubernetes_ops` | 5 | 0.1% |
| `terraform_iac` | 0 | 0.0% |
| `aws_console` | 39 | 0.6% |
| `jenkins_ci_cd` | 0 | 0.0% |
| `coding_editing` | 2251 | 32.1% |
| `debugging` | 35 | 0.5% |
| `documentation` | 197 | 2.8% |
| `other` | 4246 | 60.5% |

## Why this one is trainable and that one is not

- Largest class: `configure_option` at 20.5%. Always answering it scores 20.5% accuracy, so a model has room to beat the baseline.
  Under the DevOps labels the largest class is `other` at 60.5%.
- Smallest named class: `media_control` with 62 tasks - enough for five-fold cross-validation, which needs a handful of tasks per fold.
- Unmatched: 653 tasks (9.3%) fall in `other`; under the DevOps labels it is 4246 (60.5%).
- Empty classes: 2 of 10 DevOps labels match nothing, against 0 here.

These labels come from the instruction text, so they are still weak supervision: they say what the task was asked to do, not what the pixels show. They are a starting point for hand-checking, not ground truth.

