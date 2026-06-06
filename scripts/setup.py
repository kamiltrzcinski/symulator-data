#!/usr/bin/env python3
"""Run once after cloning: python3 scripts/setup.py
Configures git to use tracked hooks from .githooks/.
Works on Linux, macOS, and Windows.
"""
import subprocess
import sys

subprocess.run(
    ["git", "config", "core.hooksPath", ".githooks"],
    check=True,
)
print("Git hooks installed. Pre-commit validation is now active.")
