# Changelog

All notable changes are documented here.

## [Unreleased]

### Added
- Added TIMETABLE_POINT and TIMETABLE_CONNECTION topology extracted directly from SKRJ Kalkulacja, including line_locations and kilometers.
- Added Python script find_path.py for routing.

### Changed
- Transitioned specification from legacy operating_points to timetable_points.
- Restored and enhanced precommit_validate.py to validate UID ranges, timetable points, connections, and vehicle_uid references.
