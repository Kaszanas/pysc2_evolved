#!/usr/bin/env python3
"""Cross-platform wheel installer: python scripts/install_wheel.py [--force-reinstall]

Finds dist/*.whl and installs it via uv pip install.  Replaces the glob
expansion that cmd.exe (chocolatey make on Windows) cannot perform.
"""
import glob
import subprocess
import sys

wheels = glob.glob("dist/*.whl")
if not wheels:
    print("error: no wheel found in dist/", file=sys.stderr)
    sys.exit(1)

cmd = ["uv", "pip", "install"] + sys.argv[1:] + wheels
subprocess.run(cmd, check=True)
