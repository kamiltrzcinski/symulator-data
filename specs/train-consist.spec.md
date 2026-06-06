# Spec: train-consist JSON format

## Overview

Defines the schema contract for files in `data/trains/**/*.json`.

---

## Fields

GIVEN a valid train-consist file
THEN it MUST have:
- `uid`: integer, DOMAIN=ROLLING_STOCK, KIND=TRAIN_CONSIST (0x03), INSTANCE≠0
- `pID`: non-empty string
- `displayName`: non-empty string

THEN it MAY have:
- `vehicle_uids`: array of integers — each must reference a valid VEHICLE uid in `data/vehicles/`
- `trainCategory`: string
- `trainType`: one of `PASSENGER`, `FREIGHT`, `SERVICE`

---

## Cross-reference

GIVEN a train-consist file with `vehicle_uids`
WHEN any value in `vehicle_uids` does not match a `uid` in `data/vehicles/`
THEN validation MUST fail with an unknown vehicle uid error
