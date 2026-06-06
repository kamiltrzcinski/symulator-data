# Spec: schedule JSON format

## Overview

Defines the schema contract for files in `schedules/**/*.json`.

---

## Fields

GIVEN a valid schedule file
THEN it MUST have:
- `uid`: integer, DOMAIN=ROLLING_STOCK (any KIND from the ROLLING_STOCK domain), INSTANCE≠0
- `pID`: non-empty string — timetable/train number identifier
- `displayName`: non-empty string

THEN it MAY have:
- `vehicle_uids`: array of integers — each references a VEHICLE uid from `data/vehicles/`
- `vehicleComposition`: object with `locomotive` and/or `wagon` string arrays (legacy format)
- `displayRoute`: string
- `trainType`: string
- `trainCategory`: string
- `route`: array of stop objects

---

## Stop object

GIVEN a stop object in `route`
THEN it MUST have:
- `stationName`: non-empty string
- `arrival`: string (time "HH:MM,s") or null
- `departure`: string (time "HH:MM,s") or null

THEN it MAY have:
- `platform`: string or null
- `track`: integer or null
- `stopType`: string or null

---

## UID uniqueness

GIVEN all schedule files in the repository
WHEN two files have the same `uid` value
THEN validation MUST fail with a duplicate UID error

---

## Authorship

Each new schedule file added via PR MUST declare its author in the PR description.
External contributors retain copyright to their schedule files only.
They have no rights to content in `data/vehicle_types/`, `data/vehicles/`, or `data/trains/`.
