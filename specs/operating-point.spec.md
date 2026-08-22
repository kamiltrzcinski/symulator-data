# Spec: operating points (posterunki i punkty rozkładowe) JSON format

## Overview

Defines the schema contract for `data/operating_points/operating_points.json`.
This registry contains all valid operating points, stations, switch heads, block posts, transit groups, service stops, and kilometrage points permitted in train schedules (`data/schedules/**/*.json`).

---

## Structure

`data/operating_points/operating_points.json` contains a JSON array of Operating Point objects.

GIVEN an operating point object in the registry
THEN it MUST have:
- `uid`: integer, DOMAIN=INFRASTRUCTURE (`0x02`), KIND=STATION (`0x11`), SCOPE=`0`, INSTANCE≠0
- `name`: non-empty string — unique official name of the operating point / construction point

---

## Validation Rules

1. Every `uid` MUST be a valid 48-bit UID within DOMAIN `INFRASTRUCTURE (0x02)` and KIND `STATION (0x11)`.
2. Every `uid` MUST be globally unique.
3. Every `name` MUST be unique across the registry.
4. Any station/point referenced in `data/schedules/**/*.json` MUST match a registered `name` in this file.
