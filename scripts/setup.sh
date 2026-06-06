#!/usr/bin/env bash
set -e
git config core.hooksPath .githooks
echo "Git hooks installed. Pre-commit validation is now active."
