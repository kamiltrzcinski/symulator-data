# Changelog

All notable changes are documented here.

## [Unreleased]

### Added
- `ci`: Added `scripts/check-changelog.py` and updated `.githooks/pre-commit` to enforce `CHANGELOG.md` staging and version entry checks, mirroring `symulator` repository rules.
- `scripts`: Added unit tests (`tests/test_find_path.py`) covering `BaseTractionStrategy` and `ElectricTractionStrategy` cost calculations, line change penalties (+5 min), and unelectrified track exclusions (`float('inf')`).

### Changed
- `scripts`: Refactored `find_path.py` pathfinding algorithm to adhere strictly to SOLID principles (SRP and OCP). Extracted edge weight and penalty calculations into a dedicated Strategy Pattern (`CostStrategy`, `BaseTractionStrategy`, `ElectricTractionStrategy`) with Dependency Injection in `dijkstra_segment`.
- `scripts`: Corrected average speed calculation in `enrich_connections.py` (`get_segment_vmax`) to compute time-weighted harmonic mean (`total_length / total_time`) instead of arithmetic mean (`total_v / total_l`), eliminating significant travel time underestimations.
- `scripts`: Enhanced segment lookup in `enrich_connections.py` to support multi-track fallback (`preferred_tracks=("1", "N", "2")`), ensuring secondary tracks (e.g. track 2) are checked when track 1/N parameters are missing.

### Fixed
- `scripts`: Fixed electric traction constraint in `find_path.py` (`ElectricTractionStrategy`) to strictly exclude unelectrified segments (`vmax < 60` and class not in `["C3", "C4", "D3", "D4"]`) by returning `float('inf')` and skipping edges in Dijkstra, replacing the previous soft 3x penalty multiplier.
- `scripts`: Added `safe_line_no()` helper in `enrich_connections.py` to strip `.0` suffixes when parsing integer line numbers from Pandas DataFrames, preventing lookup failures against string keys in connection JSON files.
- `scripts`: Added fallback column name matching in `enrich_connections.py` (e.g. `Km ko`) to handle potential UTF-8 encoding variations in PLK Excel header columns.

## [0.1.1] - 2026-09-04

### Added
- `scripts`: Added `enrich_connections.py` to read PLK Excel registry files (`N_ZAL_2.1` and `N_ZAL_2.4`) and enrich connection JSON files with physical `vmax` and `class` parameters.
- `scripts`: Added `find_path.py` CLI utility for pathfinding across SKRJ topology with options for intermediate waypoints (`--via`), exclusions (`--exclude`), and traction types (`--traction E/S`).

### Changed
- `topology`: Enriched timetable connections with PLK registry parameters (`vmax`, `class`) for physical pathfinding calculations.

## [0.1.0] - 2026-09-02

### Added
- `topology`: Extracted `TIMETABLE_POINT` (0x24) and `TIMETABLE_CONNECTION` (0x25) topology packages from SKRJ Kalkulacja.
- `cd`: Added `timetable-points` and `timetable-connections` to the CD packaging matrix (`.github/workflows/cd.yml`) for automated artifact generation and release tag generation.

### Fixed
- `scripts`: Optimized Dijkstra pathfinding in `find_path.py` by untracking `.topology_cache.pkl`, adding distance calculations, and resolving $O(V^2)$ bottlenecks.
- `data`: Fixed typo in `Trzemeszno` point file name and added `.topology_cache.pkl` to `.gitignore`.
