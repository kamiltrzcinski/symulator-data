# Spec: vehicle-type JSON format

## Overview

Defines the schema contract for files in `data/vehicle_types/**/*.json`.

---

## Fields

GIVEN a valid vehicle-type file
THEN it MUST have:
- `uid`: integer, 1 ≤ value ≤ 2^53-1, DOMAIN=ROLLING_STOCK, KIND=VEHICLE_TYPE (0x01), INSTANCE≠0
- `typeName`: non-empty string
- `vehicleType`: one of `LOCOMOTIVE`, `EMU_UNIT`, `DMU_UNIT`, `FREIGHT_WAGON`, `SERVICE_WAGON`
- `vehicleSubtype`: non-empty string

THEN it MAY have:
- `lengthM`: number > 0
- `massGrossT`: number > 0
- `maxSpeedKmh`: integer > 0
- `massEmptyT`: number > 0
- `axleCount`: integer > 0
- `powerKW`: number > 0
- `tractionForceKN`: number > 0
- `brakingLambdaPct`: number > 0
- `maxSpeedKmh`: integer > 0
- `family`: string
- `multipleCouplingCapable`: boolean

---

## UID uniqueness

GIVEN all vehicle-type files in the repository
WHEN two files have the same `uid` value
THEN validation MUST fail with a duplicate UID error
