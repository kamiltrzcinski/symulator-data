# Changelog

All notable changes are documented here.

## [Unreleased]

### Added
- Added `enrich_connections.py` script to bake exact segment speeds and line classifications directly from PLK registries into connection topology data.
- Added TIMETABLE_POINT and TIMETABLE_CONNECTION topology extracted directly from SKRJ Kalkulacja, including line_locations and kilometers.
- Added Python script find_path.py for routing.

### Changed
- Replaced heuristic pathfinding weights in `find_path.py` with precise time-based physical costs (`distance / vmax`) using embedded PLK registry parameters.
- Upgraded `find_path.py` to support explicit traction requirements (`-t E/S`).
- Transitioned specification from legacy operating_points to timetable_points.
- Restored and enhanced precommit_validate.py to validate UID ranges, timetable points, connections, and vehicle_uid references.
