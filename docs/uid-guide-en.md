# UID Guide — for contributors

## What is a UID and why does it look like this

Every object in the simulator (vehicle type, vehicle, train consist, schedule) has a
unique 64-bit numeric identifier — a **UID**. This lets the engine reference data
unambiguously without name collisions.

A UID is split into four fields:

```
 63      48 47    40 39    32 31           16 15            0
┌──────────┬────────┬────────┬──────────────┬────────────────┐
│ reserved │ DOMAIN │  KIND  │    SCOPE     │    INSTANCE    │
│  16 bits │ 8 bits │ 8 bits │   16 bits    │    16 bits     │
└──────────┴────────┴────────┴──────────────┴────────────────┘
```

| Field    | Meaning |
|----------|---------|
| DOMAIN   | Category: `ROLLING_STOCK` or `INFRASTRUCTURE` / `OPERATIONS` |
| KIND     | Object type (e.g. `VEHICLE_TYPE`, `TRAIN_CONSIST`) |
| SCOPE    | Context (vehicle series or `0`) |
| INSTANCE | Sequential number within SCOPE |

In JSON files the UID is stored as an **integer** (e.g. `1103806595650`).

---

## Domain and kind table (rolling stock)

Only these kinds are relevant for schedule and rolling-stock contributors:

| KIND (hex) | Name            | Used in |
|------------|-----------------|---------|
| `0x01`     | `VEHICLE_TYPE`  | `data/vehicle_types/` |
| `0x02`     | `VEHICLE`       | `data/vehicles/`      |
| `0x03`     | `TRAIN_CONSIST` | `data/trains/`        |

Schedules (`schedules/`) reference the above through the `vehicle_uids` field.

---

## How to generate a UID for a new schedule

1. Download `uid-generator` from the **Releases** tab in this repository
   (available for Linux, Windows `.exe`, macOS)

2. Run the tool with the appropriate parameters:
   ```
   uid-generator --domain ROLLING_STOCK --kind TRAIN_CONSIST
   ```
   Example output:
   ```
   Scanning existing UIDs...  12 TRAIN_CONSIST UIDs found
   Next UID: 844424930131981
   Hex:      0x0003_0000_0000_000D (domain=RS, kind=TRAIN_CONSIST, scope=0, instance=13)
   ```

3. Copy the numeric value (e.g. `844424930131981`) into the `uid` field of your JSON file.

4. Make sure your JSON file has all required fields — see `specs/schedule.spec.md`.

---

## What NOT to do

- **Do not invent UIDs manually** — you'll pick the wrong range and cause a collision.
- **Do not duplicate** a UID from another file — the pre-commit hook blocks commits with duplicates.
- **Do not change** UIDs of existing files — the engine has them hardcoded in scenario files.
