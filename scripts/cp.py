#!/usr/bin/env python3
"""Cross-platform file copy: python scripts/cp.py <src> <dst>

Replaces `cp src dst` in Makefile targets so they work on Windows with
chocolatey make (which uses cmd.exe and has no `cp` built-in).
"""
import os
import shutil
import stat
import sys

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <src> <dst>", file=sys.stderr)
    sys.exit(1)

src, dst = sys.argv[1], sys.argv[2]

# Remove destination first — on Windows, compiled extensions (.pyd) are often
# marked read-only after a previous copy, which causes PermissionError on overwrite.
if os.path.exists(dst):
    os.chmod(dst, stat.S_IWRITE)
    os.remove(dst)

shutil.copy(src, dst)
