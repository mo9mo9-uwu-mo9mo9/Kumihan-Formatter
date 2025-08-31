#!/usr/bin/env python3
"""
Document Consistency Checker (minimal)
- Issue #1315: Makefile 'doc-consistency' target alignment

Commands:
  - check:   run lightweight checks and write a JSON report
  - summary: print a short human-readable summary from the report

Design notes:
- Never fail the pipeline: always exit code 0
- Write report to tmp/automation-logs/doc_consistency.json
- Keep implementation minimal and side‑effect free
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = REPO_ROOT / "tmp" / "automation-logs"
REPORT_PATH = LOG_DIR / "doc_consistency.json"

AGENTS_MD = REPO_ROOT / "AGENTS.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"

MISSING_SCRIPTS = [
    REPO_ROOT / "scripts" / "run_quality_check.sh",
    REPO_ROOT / "scripts" / "set_issue_priorities.sh",
    REPO_ROOT / "scripts" / "create_minimal_pr.sh",
    REPO_ROOT / "scripts" / "pr_merge_and_cleanup.sh",
]


@dataclass
class Finding:
    kind: str  # "warning" | "info"
    message: str
    path: str | None = None


@dataclass
class Report:
    status: str  # "ok" | "warnings"
    findings: List[Finding]

    def to_json(self) -> str:
        return json.dumps(
            {
                "status": self.status,
                "findings": [asdict(f) for f in self.findings],
            },
            ensure_ascii=False,
            indent=2,
        )


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def check_cov_threshold(findings: List[Finding]) -> None:
    agents = read_text(AGENTS_MD)
    pyproject = read_text(PYPROJECT)

    # Find AGENTS mention like --cov-fail-under=6
    m_agents = re.search(r"--cov-fail-under\s*=\s*(\d+)", agents)
    agents_val = int(m_agents.group(1)) if m_agents else None

    # Find pytest addopts --cov-fail-under=20 in pyproject.toml
    m_py = re.search(r"--cov-fail-under=(\d+)", pyproject)
    py_val = int(m_py.group(1)) if m_py else None

    if agents_val is not None and py_val is not None and agents_val != py_val:
        findings.append(
            Finding(
                kind="warning",
                message=f"Coverage threshold mismatch: AGENTS.md={agents_val}% vs pyproject={py_val}%",
                path=str(AGENTS_MD),
            )
        )
    elif agents_val is None or py_val is None:
        findings.append(
            Finding(
                kind="info",
                message="Coverage threshold not found in one of the sources (AGENTS.md/pyproject).",
            )
        )


def check_script_existence(findings: List[Finding]) -> None:
    for p in MISSING_SCRIPTS:
        if not p.exists():
            findings.append(
                Finding(
                    kind="warning",
                    message=f"Referenced automation script is missing: {p.name}",
                    path=str(p),
                )
            )


def run_check() -> Report:
    findings: List[Finding] = []
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    check_cov_threshold(findings)
    check_script_existence(findings)

    status = "warnings" if any(f.kind == "warning" for f in findings) else "ok"
    report = Report(status=status, findings=findings)
    REPORT_PATH.write_text(report.to_json(), encoding="utf-8")
    return report


def print_summary() -> None:
    if REPORT_PATH.exists():
        data: Dict[str, Any] = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        warnings = [f for f in data.get("findings", []) if f.get("kind") == "warning"]
        infos = [f for f in data.get("findings", []) if f.get("kind") == "info"]
        print("📚 Doc Consistency Summary")
        print(
            f"  Status   : {data.get('status')}\n  Warnings : {len(warnings)}\n  Infos    : {len(infos)}"
        )
        for f in warnings:
            print(f"  - WARN: {f.get('message')}")
        for f in infos:
            print(f"  - INFO: {f.get('message')}")
    else:
        print("No report found. Run 'check' first.")


def main(argv: List[str] | None = None) -> int:
    import sys

    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "summary"

    if cmd == "check":
        run_check()
        return 0
    elif cmd == "summary":
        print_summary()
        return 0
    else:
        print(f"Unknown command: {cmd}. Use 'check' or 'summary'.")
        return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

