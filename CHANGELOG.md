# Changelog

All notable changes are documented here.

## [Unreleased]

### Added
- `scripts`: Added `enrich_connections.py` script to bake exact segment speeds and line classifications directly from PLK registries into connection topology data.
- `scripts`: Added `find_path.py` for routing railway paths with route distance calculation and CLI options (`--via`, `--exclude`, `--traction`).
- `scripts`: Added unit tests (`tests/test_find_path.py`) for pathfinding cost strategies (`BaseTractionStrategy`, `ElectricTractionStrategy`).
- `data`: Added `TIMETABLE_POINT` and `TIMETABLE_CONNECTION` topology data packages extracted from SKRJ Kalkulacja.
- `cd`: Added `timetable-points` and `timetable-connections` to the CD packaging matrix (`.github/workflows/cd.yml`) for automated release artifact builds.

### Changed
- `scripts`: Refactored `find_path.py` pathfinding algorithm to apply SOLID principles (Strategy Pattern: `CostStrategy`, `BaseTractionStrategy`, `ElectricTractionStrategy`) with Dependency Injection for edge cost calculations.
- `scripts`: Replaced arithmetic mean speed calculation in `enrich_connections.py` with harmonic mean (time-based: `total_length / total_time`) for physically accurate travel time estimation.
- `scripts`: Enhanced `enrich_connections.py` segment lookup to support Track 2 and multi-track fallbacks when primary tracks (1/N) are unavailable.
- `scripts`: Transitioned topology specification from legacy `operating_points` to `timetable_points`.
- `scripts`: Restored and enhanced `precommit_validate.py` to validate UID ranges, timetable points, connections, and vehicle UID references.

### Fixed
- `scripts`: Fixed electric traction routing in `find_path.py` to strictly forbid unelectrified tracks (`float('inf')` / skip edge) instead of applying a soft penalty multiplier.
- `scripts`: Fixed pandas float line number parsing in `enrich_connections.py` (`safe_line_no`) and added column name decoding fallbacks for PLK Excel registry files.
- `scripts`: Optimized Dijkstra pathfinding performance in `find_path.py` (eliminating $O(V^2)$ bottlenecks, EOF handling, and train validity checks).
- `data`: Untracked `.topology_cache.pkl` from git tree and added it to `.gitignore`.
- `data`: Fixed double space typo in `Trzemeszno` timetable point file name.
