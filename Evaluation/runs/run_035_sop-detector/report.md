# SOP detector — 2026-10-14

Stage 1 accuracy: raw labels 0.8763, normalised 0.9449 (107 raw spellings -> 70 applications).

61 applications, 6716 recordings, 515941 candidates, 1690 logged strings of >= 3 chars. Rankers per fold: [60, 59, 57, 58, 59].

**SOP as delivered**: repeated reads of one string collapsed into one step, then scored one-to-one, so a duplicate is a false positive and a string typed twice needs two steps. **Per candidate**: every emitted candidate credited if it matches any logged string - the earlier convention, kept for comparison.

| variant | threshold | steps | precision | recall | candidates | precision | recall |
|---|---|---|---|---|---|---|---|
| | | *SOP as delivered* | | | *per candidate* | | |
| predicted | 0.3 | 1185 | 42.2% | 29.6% | 2286 | 60.7% | 31.4% |
| predicted | 0.5 | 926 | 48.1% | 26.3% | 1801 | 66.9% | 28.0% |
| oracle | 0.3 | 1189 | 42.1% | 29.6% | 2283 | 60.3% | 31.1% |
| oracle | 0.5 | 926 | 47.8% | 26.2% | 1787 | 66.6% | 27.6% |
| no_routing | 0.3 | 1063 | 37.1% | 23.3% | 1726 | 54.1% | 24.8% |
| no_routing | 0.5 | 603 | 51.1% | 18.2% | 961 | 66.6% | 19.1% |
| ceiling | - | | | | 515941 | 1.1% | 90.1% |

## Per application, stage 1 routing, threshold 0.5

| application | targets | emitted | correct | precision | recall |
|---|---|---|---|---|---|
| Ubuntu Terminal | 106 | 119 | 70 | 58.8% | 66.0% |
| Bash | 78 | 90 | 52 | 57.8% | 66.7% |
| Chromium | 40 | 50 | 37 | 74.0% | 92.5% |
| OnlyOffice Spreadsheet | 59 | 48 | 36 | 75.0% | 61.0% |
| DuckDuckGo | 52 | 74 | 33 | 44.6% | 63.5% |
| Zotero | 59 | 38 | 30 | 78.9% | 50.8% |
| Bitwarden | 91 | 32 | 25 | 78.1% | 27.5% |
| Anki | 100 | 31 | 24 | 77.4% | 24.0% |
| LibreOffice Calc | 60 | 32 | 21 | 65.6% | 35.0% |
| Frappe Books | 122 | 52 | 20 | 38.5% | 16.4% |
| Lemmy | 48 | 117 | 20 | 17.1% | 41.7% |
| Cryptomator | 28 | 27 | 14 | 51.9% | 50.0% |
| Shotcut | 33 | 22 | 10 | 45.5% | 30.3% |
| Veusz | 27 | 21 | 10 | 47.6% | 37.0% |
| LibreOffice Writer | 46 | 12 | 8 | 66.7% | 17.4% |
| OnlyOffice PDF Forms | 50 | 11 | 7 | 63.6% | 14.0% |
| GNU Octave | 19 | 13 | 6 | 46.2% | 31.6% |
| GnuCash | 25 | 7 | 3 | 42.9% | 12.0% |
| Zulip | 54 | 8 | 3 | 37.5% | 5.6% |
| Metabase | 13 | 9 | 2 | 22.2% | 15.4% |
| VSCode | 23 | 6 | 2 | 33.3% | 8.7% |
| Atom | 15 | 2 | 1 | 50.0% | 6.7% |
| Eclipse | 9 | 4 | 1 | 25.0% | 11.1% |
| FreeCAD | 8 | 1 | 1 | 100.0% | 12.5% |
| Geany | 7 | 7 | 1 | 14.3% | 14.3% |

Feature importance (pooled ranker): x_norm 1139, text_score 862, n_reads 852, rel_life 849, y_norm 746, y_rank 604, n_same_row 483, frames_growing 399
