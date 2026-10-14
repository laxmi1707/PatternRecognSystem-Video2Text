# SOP detector — 2026-10-14

Stage 1 accuracy: raw labels 0.8763, normalised 0.9449 (107 raw spellings -> 70 applications).

61 applications, 6716 recordings, 515941 candidates, 1690 logged strings of >= 3 chars. Rankers per fold: [60, 59, 57, 58, 59].

**SOP as delivered**: repeated reads of one string collapsed into one step, then scored one-to-one, so a duplicate is a false positive and a string typed twice needs two steps. **Per candidate**: every emitted candidate credited if it matches any logged string - the earlier convention, kept for comparison.

| variant | threshold | steps | precision | recall | candidates | precision | recall |
|---|---|---|---|---|---|---|---|
| | | *SOP as delivered* | | | *per candidate* | | |
| predicted | 0.3 | 1352 | 39.4% | 31.5% | 2612 | 58.2% | 33.6% |
| predicted | 0.5 | 882 | 50.6% | 26.4% | 1716 | 69.3% | 27.6% |
| oracle | 0.3 | 1358 | 39.1% | 31.4% | 2602 | 57.8% | 33.2% |
| oracle | 0.5 | 887 | 50.6% | 26.6% | 1708 | 69.3% | 27.6% |
| no_routing | 0.3 | 1063 | 37.2% | 23.4% | 1726 | 54.1% | 24.8% |
| no_routing | 0.5 | 603 | 51.2% | 18.3% | 961 | 66.6% | 19.1% |
| ceiling | - | | | | 515941 | 1.1% | 90.1% |

## Per application, stage 1 routing, threshold 0.5

| application | targets | emitted | correct | precision | recall |
|---|---|---|---|---|---|
| Ubuntu Terminal | 106 | 115 | 66 | 57.4% | 62.3% |
| Bash | 78 | 92 | 53 | 57.6% | 67.9% |
| OnlyOffice Spreadsheet | 59 | 49 | 39 | 79.6% | 66.1% |
| Chromium | 40 | 56 | 37 | 66.1% | 92.5% |
| DuckDuckGo | 52 | 72 | 33 | 45.8% | 63.5% |
| Zotero | 59 | 39 | 33 | 84.6% | 55.9% |
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
| Zulip | 54 | 7 | 3 | 42.9% | 5.6% |
| Atom | 15 | 4 | 2 | 50.0% | 13.3% |
| Metabase | 13 | 6 | 2 | 33.3% | 15.4% |
| Arduino IDE | 10 | 1 | 1 | 100.0% | 10.0% |
| Brackets | 29 | 2 | 1 | 50.0% | 3.4% |

Feature importance (pooled ranker): x_norm 1139, text_score 862, n_reads 852, rel_life 849, y_norm 746, y_rank 604, n_same_row 483, frames_growing 399
