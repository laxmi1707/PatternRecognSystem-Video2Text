# Proposed label set

7021 tasks, 70 applications. Each label is assigned by the leading verb of the task instruction; `labels_v2.csv` has one row per task and can be fed straight to `python -m v2k train --labels csv:labels_v2.csv`.

## What the recordings actually contain

| category | tasks | share | apps | example instructions |
|---|---:|---:|---:|---|
| `configure_option` | 1482 | 21.1% | 67 | *Set status to busy*; *Turn off invisble mode* |
| `navigate_view` | 1268 | 18.1% | 68 | *Go to go invisible mode.*; *Display usage statistics from the profile menu* |
| `format_style` | 913 | 13.0% | 65 | *Change the user list style to "Compact"*; *Change time format to 24 hour format* |
| `edit_content` | 832 | 11.9% | 65 | *Add a video call in a moving messages channel.*; *add a voice call link from the compose message window and send it to "welcome to zulip" to* |
| `create_item` | 771 | 11.0% | 65 | *create "abczxb"*; *create "hi."* |
| `other` | 399 | 5.7% | 59 | *Reactivate an inactive bot named "abczxb"*; *Sign out of your account and log in with google again.* |
| `insert_element` | 361 | 5.1% | 43 | *Link the cat file to a website 'https://labeling-s.turing.com/conversations/49706/view'.*; *Link a PDF to an "acrobat-refernce" item.* |
| `file_manage` | 291 | 4.1% | 64 | *upload "musashi"*; *Save a message as draft and view the same* |
| `delete_remove` | 175 | 2.5% | 49 | *Remove custom css*; *Delete the message* |
| `search_filter` | 157 | 2.2% | 39 | *Search for text - 'Hi' in the conversations*; *Filter your messages by starred messages.* |
| `organize_items` | 151 | 2.2% | 41 | *Pin a topic '#Zulip' for quick access*; *mark messages in moving messages channel as read* |
| `communicate` | 127 | 1.8% | 21 | *send a gif in a message*; *Send a reply message stating, "Thanks for the greetings," to the recent conversation with * |
| `media_control` | 54 | 0.8% | 20 | *Mute all sounds from zulip*; *Mute a specific channel - '#sandbox' to stop recieving notifications* |
| `run_command` | 40 | 0.6% | 14 | *run through the "Getting Started" guide in the Walkthrough section.*; *Run a task defined in a tasks.json file.* |

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

- Largest class: `configure_option` at 21.1%. Always answering it scores 21.1% accuracy, so a model has room to beat the baseline.
  Under the DevOps labels the largest class is `other` at 60.5%.
- Smallest named class: `run_command` with 40 tasks - enough for five-fold cross-validation, which needs a handful of tasks per fold.
- Unmatched: 399 tasks (5.7%) fall in `other`; under the DevOps labels it is 4246 (60.5%).
- Empty classes: 2 of 10 DevOps labels match nothing, against 0 here.

These labels come from the instruction text, so they are still weak supervision: they say what the task was asked to do, not what the pixels show. They are a starting point for hand-checking, not ground truth.

