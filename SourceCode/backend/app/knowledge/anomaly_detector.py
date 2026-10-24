from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Anomaly:
    category: str
    pattern: str
    matched_text: str
    severity: str  # "critical" | "warning" | "info"
    description: str


# Each entry: (category, severity, description, [regex_patterns])
_RULES: list[tuple[str, str, str, list[str]]] = [
    (
        "Destructive File Operation",
        "critical",
        "Command may permanently delete files or directories",
        [
            r"\brm\s+-[rRfF]*[fF][rRfF]*\b",   # rm -rf, rm -fr, rm -f
            r"\brm\s+--force\b",
            r"\bdd\s+.*if=",                     # dd overwrite
            r"\bshred\b",
            r"\btruncate\s+-s\s+0\b",
            r"\bwipe\b",
        ],
    ),
    (
        "Database Destruction",
        "critical",
        "SQL command may destroy database objects or data",
        [
            r"\bDROP\s+TABLE\b",
            r"\bDROP\s+DATABASE\b",
            r"\bDROP\s+SCHEMA\b",
            r"\bTRUNCATE\s+TABLE\b",
            r"\bTRUNCATE\b",
            r"\bDELETE\s+FROM\b.*WHERE\s+1\s*=\s*1",  # DELETE without filter
        ],
    ),
    (
        "Privilege Escalation",
        "critical",
        "Command grants excessive privileges",
        [
            r"\bsudo\b",                   # exact
            # EasyOCR misreads of "sudo" observed in CUA dataset
            r"\bsuco\b",                   # [suco ] → [sudo]
            r"\*[Uu]dv\b",                # *Udv → sudo
            r"\b[Uu]dv\s+tt\b",           # Udv tt → sudo apt
            r"\bsudo\s+su\b",
            r"\bsudo\s+-i\b",
            r"\bchmod\s+777\b",
            r"\bchmod\s+-R\s+777\b",
            r"\bchown\s+root\b",
            r"\bpasswd\s+root\b",
            r"\busermod\s+.*-G\s+sudo\b",
        ],
    ),
    (
        "Remote Code Execution",
        "critical",
        "Command downloads and executes code from the network",
        [
            r"\bcurl\b.*\|\s*(ba)?sh\b",
            r"\bwget\b.*\|\s*(ba)?sh\b",
            r"\bcurl\b.*\|\s*python\b",
            r"\bpython\b.*<\s*\(\s*curl\b",
            r"\beval\s*\(\s*curl\b",
        ],
    ),
    (
        "Network Security Bypass",
        "warning",
        "Command disables firewall or network security rules",
        [
            r"\baptables\s+-F\b",
            r"\bufw\s+disable\b",
            r"\bsystemctl\s+stop\s+firewall\b",
            r"\bfirewall-cmd\s+.*--remove\b",
            r"\bsetenforce\s+0\b",
        ],
    ),
    (
        "Sensitive Data Access",
        "warning",
        "Command accesses credential files or private keys",
        [
            r"\bcat\s+.*\.pem\b",
            r"\bcat\s+.*\.key\b",
            r"\bcat\s+.*id_rsa\b",
            r"\bcat\s+.*\.env\b",
            r"\bcat\s+.*/etc/passwd\b",
            r"\bcat\s+.*/etc/shadow\b",
            r"\bcp\s+.*\.pem\b",
        ],
    ),
    (
        "Process Termination",
        "warning",
        "Command forcefully terminates processes",
        [
            r"\bkill\s+-9\b",
            r"\bkillall\b",
            r"\bpkill\s+-9\b",
        ],
    ),
    (
        "Disk Wipe / Format",
        "critical",
        "Command may wipe or format a disk",
        [
            r"\bmkfs\b",
            r"\bfdisk\b.*-l",
            r"\bwipefs\b",
            r"\bdd\b.*of=/dev/(sd|nvme|hd)",
        ],
    ),
]


def detect(ocr_text: str) -> list[Anomaly]:
    """Scan OCR text and return list of detected anomalies."""
    if not ocr_text:
        return []
    anomalies: list[Anomaly] = []
    text_lower = ocr_text  # keep case for SQL; patterns use \b
    for category, severity, description, patterns in _RULES:
        for pattern in patterns:
            m = re.search(pattern, text_lower, re.IGNORECASE)
            if m:
                anomalies.append(Anomaly(
                    category=category,
                    pattern=pattern,
                    matched_text=m.group(0).strip(),
                    severity=severity,
                    description=description,
                ))
                break  # one anomaly per category per segment
    return anomalies
