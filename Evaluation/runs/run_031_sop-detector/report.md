# SOP detector — 2026-10-14

Stage 1 accuracy: raw labels 0.8763, normalised 0.9449 (107 raw spellings -> 70 applications).

61 applications, 6716 recordings, 515941 candidates, 1690 logged strings of >= 3 chars. Rankers per fold: [60, 59, 57, 58, 59].

Strict columns: one-to-one matching, so a duplicate read of one typed string is a false positive and a string typed twice needs two steps.

| variant | threshold | emitted | precision | recall | precision (strict) | recall (strict) |
|---|---|---|---|---|---|---|
| predicted | 0.3 | 2627 | 49.8% | 31.9% | 20.0% | 31.1% |
| predicted | 0.5 | 1847 | 59.1% | 28.1% | 24.8% | 27.1% |
| oracle | 0.3 | 2595 | 50.1% | 31.6% | 20.1% | 30.9% |
| oracle | 0.5 | 1814 | 59.3% | 27.6% | 24.9% | 26.7% |
| no_routing | 0.3 | 825 | 60.8% | 14.3% | 28.2% | 13.8% |
| no_routing | 0.5 | 478 | 72.2% | 10.3% | 35.4% | 10.0% |
| ceiling | - | 515941 | 1.1% | 90.1% | | |

## Per application, stage 1 routing, threshold 0.5

| application | targets | emitted | correct | precision | recall |
|---|---|---|---|---|---|
| Ubuntu Terminal | 106 | 155 | 127 | 81.9% | 71.7% |
| Bash | 78 | 108 | 80 | 74.1% | 66.7% |
| OnlyOffice Spreadsheet | 59 | 68 | 55 | 80.9% | 64.4% |
| Chromium | 40 | 245 | 211 | 86.1% | 90.0% |
| Bitwarden | 91 | 61 | 37 | 60.7% | 38.5% |
| DuckDuckGo | 52 | 221 | 142 | 64.3% | 61.5% |
| Zotero | 59 | 36 | 29 | 80.6% | 49.2% |
| Lemmy | 48 | 210 | 136 | 64.8% | 43.8% |
| Frappe Books | 122 | 115 | 57 | 49.6% | 16.4% |
| Anki | 100 | 35 | 18 | 51.4% | 18.0% |
| Veusz | 27 | 89 | 51 | 57.3% | 66.7% |
| LibreOffice Calc | 60 | 41 | 26 | 63.4% | 25.0% |
| LibreOffice Writer | 46 | 17 | 14 | 82.4% | 23.9% |
| Cryptomator | 28 | 19 | 13 | 68.4% | 32.1% |
| OnlyOffice PDF Forms | 50 | 23 | 13 | 56.5% | 18.0% |
| Shotcut | 33 | 28 | 10 | 35.7% | 27.3% |
| Zulip | 54 | 10 | 6 | 60.0% | 11.1% |
| GnuCash | 25 | 28 | 14 | 50.0% | 20.0% |
| Atom | 15 | 15 | 8 | 53.3% | 26.7% |
| Bluefish | 34 | 24 | 6 | 25.0% | 11.8% |
| GNU Octave | 19 | 17 | 5 | 29.4% | 21.1% |
| WeKan | 37 | 25 | 4 | 16.0% | 10.8% |
| Brackets | 29 | 32 | 7 | 21.9% | 10.3% |
| Affine | 27 | 8 | 2 | 25.0% | 7.4% |
| IntelliJ IDEA | 6 | 10 | 2 | 20.0% | 33.3% |

Feature importance (pooled ranker): x_norm 2090, y_norm 1913, final_len 1105, frac_alpha 842, conf_mean 823, conf_min 640, frames_growing 596, frac_digit 416
