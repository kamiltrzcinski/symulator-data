# Getting Started

## Prerequisites

- Git
- Python 3.12+

## Setup

1. Clone the repository:
   ```
   git clone git@github.com:kamiltrzcinski/symulator-data.git
   cd symulator-data
   ```

2. Install git hooks (one-time, required):
   ```
   python3 scripts/setup.py
   ```
   This configures git to run the pre-commit validator before every commit.
   **Without this step your commits will not be validated locally** — the CI
   pipeline will still catch errors, but you will waste a round-trip to GitHub.

## Making a contribution

1. Create a branch off `main`:
   ```
   git checkout -b my-feature
   ```

2. Make your changes.

3. Generate a UID for any new file (see [uid-guide-en.md](uid-guide-en.md)):
   ```
   python3 tools/uid-generator/main.py --domain ROLLING_STOCK --kind TRAIN_CONSIST
   ```

4. Commit — the pre-commit hook runs `scripts/precommit_validate.py` automatically.
   A commit with a duplicate or invalid UID will be rejected immediately.

5. Open a Pull Request targeting `main`.
   CI must pass (`validate` + `build-tools`) before the PR can be merged.
   A review from `@kamiltrzcinski` is required.

## Running validation manually

```
python3 scripts/precommit_validate.py
```

Exit code `0` — all UIDs valid. Exit code `1` — errors printed to stderr.

## Tools

| Tool | How to run |
|------|------------|
| UID generator | `python3 tools/uid-generator/main.py` |
| Vehicle browser (GUI) | `python3 tools/vehicle-browser/main.py` |

Pre-built binaries for Linux / Windows / macOS are available on the
[Releases](https://github.com/kamiltrzcinski/symulator-data/releases) page.
