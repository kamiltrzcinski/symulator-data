#!/usr/bin/env python3
"""scripts/check-changelog.py

Cross-platform manual pre-commit check for symulator-data.
Run this before committing if your Git client does not fire shell hooks:

    python scripts/check-changelog.py

Returns exit code 0 on success, 1 on failure.
"""
import re
import subprocess
import sys


def staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.splitlines()


def first_version_in_changelog() -> str | None:
    try:
        with open("CHANGELOG.md", encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^## \[(\d+\.\d+\.\d+)\]", line)
                if m:
                    return m.group(1)
    except FileNotFoundError:
        pass
    return None


def main() -> int:
    errors: list[str] = []

    if "CHANGELOG.md" not in staged_files():
        errors.append(
            "CHANGELOG.md is not staged.\n"
            "  Run:  git add CHANGELOG.md\n"
            "  Then commit again."
        )

    ver = first_version_in_changelog()
    if ver is None:
        errors.append(
            "No valid '## [X.Y.Z]' version entry found in CHANGELOG.md.\n"
            "  Add a line like:  ## [0.1.1] - (today's date)"
        )

    if errors:
        for err in errors:
            print(f"[check-changelog] ERROR: {err}", file=sys.stderr)
        return 1

    print(f"[check-changelog] OK — CHANGELOG.md staged, version {ver} present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
