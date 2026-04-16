#!/usr/bin/env python3
"""Cross-platform mkdir -p: python scripts/mkdir_p.py <dir>

Replaces `mkdir -p dir` in Makefile targets so they work on Windows with
chocolatey make (which uses cmd.exe and has no `mkdir -p` built-in).
"""
import os
import sys

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <directory>", file=sys.stderr)
    sys.exit(1)

os.makedirs(sys.argv[1], exist_ok=True)
