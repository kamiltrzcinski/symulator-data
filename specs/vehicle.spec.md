# Spec: vehicle JSON format

## Overview

Defines the schema contract for files at `data/vehicles/**/vehicle.json`.

---

## Fields

GIVEN a valid vehicle file
THEN it MUST have:
- `uid`: integer, DOMAIN=ROLLING_STOCK, KIND=VEHICLE (0x02), INSTANCE≠0
- `pID`: non-empty string — physical/inventory identifier
- `displayName`: non-empty string — human-readable name

THEN it MAY have:
- `type_uid`: integer, references a valid VEHICLE_TYPE uid in `data/vehicle_types/`

---

## UID uniqueness

GIVEN all vehicle files in the repository
WHEN two files have the same `uid` value
THEN validation MUST fail with a duplicate UID error
