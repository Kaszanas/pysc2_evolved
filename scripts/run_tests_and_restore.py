#!/usr/bin/env python3
"""Run pytest then restore the editable install regardless of test outcome.

Usage: python scripts/run_tests_and_restore.py [pytest-args...]

Runs:
  uv run --no-project python -m pytest <pytest-args>
  uv sync --frozen          (always, even if tests fail)

Exits with the pytest exit code so make propagates failures correctly.
"""
import subprocess
import sys


def run(*cmd: str) -> int:
    return subprocess.run(cmd).returncode


pytest_status = run(
    "uv", "run", "--no-project", "python", "-m", "pytest", *sys.argv[1:]
)

# Always restore the editable dev install. Re-resolves from pyproject.toml so
# [tool.uv.sources] entries (e.g. s2protocol from git) are honoured correctly.
run("uv", "sync")

sys.exit(pytest_status)
