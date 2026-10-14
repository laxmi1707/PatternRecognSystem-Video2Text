# SOP detector — 2026-10-14

Stage 1 accuracy: raw labels 0.8763, normalised 0.9449 (107 raw spellings -> 70 applications).

61 applications, 6716 recordings, 515941 candidates, 1690 logged strings of >= 3 chars. Rankers per fold: [60, 59, 57, 58, 59].

**SOP as delivered**: repeated reads of one string collapsed into one step, then scored one-to-one, so a duplicate is a false positive and a string typed twice needs two steps. **Per candidate**: every emitted candidate credited if it matches any logged string - the earlier convention, kept for comparison.

| variant | threshold | steps | precision | recall | candidates | precision | recall |
|---|---|---|---|---|---|---|---|
| | | *SOP as delivered* | | | *per candidate* | | |
| predicted | 0.3 | 1696 | 30.0% | 30.1% | 2627 | 49.8% | 31.9% |
| predicted | 0.5 | 1177 | 38.1% | 26.6% | 1847 | 59.1% | 28.1% |
| oracle | 0.3 | 1692 | 30.0% | 30.0% | 2595 | 50.1% | 31.6% |
| oracle | 0.5 | 1169 | 37.8% | 26.2% | 1814 | 59.3% | 27.6% |
| no_routing | 0.3 | 549 | 41.9% | 13.6% | 825 | 60.8% | 14.3% |
| no_routing | 0.5 | 311 | 53.4% | 9.8% | 478 | 72.2% | 10.3% |
| ceiling | - | | | | 515941 | 1.1% | 90.1% |

## Per application, stage 1 routing, threshold 0.5

| application | targets | emitted | correct | precision | recall |
|---|---|---|---|---|---|
| Ubuntu Terminal | 106 | 119 | 69 | 58.0% | 65.1% |
| Bash | 78 | 100 | 52 | 52.0% | 66.7% |
| OnlyOffice Spreadsheet | 59 | 49 | 37 | 75.5% | 62.7% |
| Chromium | 40 | 57 | 36 | 63.2% | 90.0% |
| DuckDuckGo | 52 | 115 | 32 | 27.8% | 61.5% |
| Zotero | 59 | 36 | 29 | 80.6% | 49.2% |
| Bitwarden | 91 | 45 | 25 | 55.6% | 27.5% |
| Lemmy | 48 | 137 | 21 | 15.3% | 43.8% |
| Frappe Books | 122 | 54 | 19 | 35.2% | 15.6% |
| Anki | 100 | 33 | 17 | 51.5% | 17.0% |
| Veusz | 27 | 41 | 17 | 41.5% | 63.0% |
| LibreOffice Calc | 60 | 31 | 14 | 45.2% | 23.3% |
| LibreOffice Writer | 46 | 14 | 11 | 78.6% | 23.9% |
| Cryptomator | 28 | 19 | 9 | 47.4% | 32.1% |
| Shotcut | 33 | 26 | 9 | 34.6% | 27.3% |
| OnlyOffice PDF Forms | 50 | 15 | 7 | 46.7% | 14.0% |
| GnuCash | 25 | 22 | 5 | 22.7% | 20.0% |
| Zulip | 54 | 9 | 5 | 55.6% | 9.3% |
| Atom | 15 | 9 | 4 | 44.4% | 26.7% |
| Bluefish | 34 | 17 | 4 | 23.5% | 11.8% |
| GNU Octave | 19 | 14 | 4 | 28.6% | 21.1% |
| Brackets | 29 | 20 | 3 | 15.0% | 10.3% |
| WeKan | 37 | 22 | 3 | 13.6% | 8.1% |
| Affine | 27 | 8 | 2 | 25.0% | 7.4% |
| IntelliJ IDEA | 6 | 8 | 2 | 25.0% | 33.3% |

Feature importance (pooled ranker): x_norm 2090, y_norm 1913, final_len 1105, frac_alpha 842, conf_mean 823, conf_min 640, frames_growing 596, frac_digit 416
