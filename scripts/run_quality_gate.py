#!/usr/bin/env python3
"""Run the complete local/CI quality gate in a deterministic order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(label: str, command: list[str]) -> None:
    print(f"\n[QUALITY] {label}", flush=True)
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if result.returncode:
        raise SystemExit(result.returncode)


def main() -> None:
    python = sys.executable
    run(
        "Python syntax compilation",
        [
            python,
            "-m",
            "py_compile",
            "test_vocab_apps.py",
            "scripts/validate_project_contract.py",
            "scripts/run_quality_gate.py",
        ],
    )
    run("Executable project-contract validation", [python, "scripts/validate_project_contract.py"])
    run("Git whitespace validation", ["git", "diff", "--check"])
    run("Static and Selenium regression suite", [python, "test_vocab_apps.py"])
    print("\n[QUALITY] All required checks passed.", flush=True)


if __name__ == "__main__":
    main()
