#!/usr/bin/env python3
"""
Lightweight local eval harness (no external calls required).

Loads YAML cases under scripts/evals/cases/*.yaml and prints a summary.
This is a scaffold: if OPENAI_API_KEY is set and you choose to integrate
API calls later, plug them under `run_case()`.
"""

from __future__ import annotations

import sys
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:
    print("YAML not installed: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


@dataclass
class EvalCase:
    name: str
    objective: str
    evaluator: dict[str, Any]


def load_cases(root: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    for p in sorted((root / "cases").glob("*.yaml")):
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
        cases.append(EvalCase(**data))
    return cases


def run_case(case: EvalCase) -> dict[str, Any]:
    # Scaffold evaluator: just check static criteria field presence
    crit = case.evaluator.get("criteria", {})
    result = {
        "name": case.name,
        "status": "passed" if crit else "skipped",
        "details": "criteria stub check",
    }
    return result


def main() -> int:
    root = Path(__file__).parent
    cases = load_cases(root)
    results = [run_case(c) for c in cases]
    passed = sum(1 for r in results if r["status"] == "passed")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    print(json.dumps({"passed": passed, "skipped": skipped, "cases": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

