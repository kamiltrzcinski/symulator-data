#!/usr/bin/env python3
"""uid-generator — generate the next free UID for a given domain/kind/scope."""

import argparse
import sys
from pathlib import Path

# Allow running from the tools/uid-generator/ directory or as PyInstaller bundle
sys.path.insert(0, str(Path(__file__).parent))

from uid_codec import UIDCodec
from uid_registry import UIDRegistry
from uid_generator import UIDGenerator
from formatters.decimal_formatter import DecimalFormatter
from formatters.hex_formatter import HexFormatter

DOMAINS = {
    "ROLLING_STOCK": 0x01,
    "INFRASTRUCTURE": 0x02,
    "OPERATIONS": 0x03,
}

KINDS = {
    "VEHICLE_TYPE": 0x01,
    "VEHICLE": 0x02,
    "TRAIN_CONSIST": 0x03,
    "CARRIER": 0x04,
    "STATION": 0x11,
    "DISPATCH_AREA": 0x12,
    "TRACK_SECTION": 0x13,
    "SWITCH": 0x14,
    "SIGNAL": 0x15,
    "DERAILER": 0x16,
    "BLOCK_SECTION": 0x17,
    "BOUNDARY_NODE": 0x18,
    "LEVEL_CROSSING": 0x19,
    "AXLE_COUNTER": 0x1A,
    "INTERLOCKING": 0x1B,
    "POWER_SUPPLY": 0x1C,
    "ROUTE": 0x21,
    "ALARM": 0x22,
    "DISPATCH_EXCHANGE": 0x23,
}

DOMAIN_NAMES = {v: k for k, v in DOMAINS.items()}
KIND_NAMES = {v: k for k, v in KINDS.items()}


def find_repo_root() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in [here, here.parent, here.parent.parent]:
        if (candidate / "data").exists() or (candidate / "schedules").exists():
            return candidate
    return here.parent.parent


def interactive_mode(registry: UIDRegistry) -> tuple[int, int, int]:
    print("\n=== uid-generator — tryb interaktywny ===\n")

    print("Dostępne domeny:")
    for i, (name, val) in enumerate(DOMAINS.items(), 1):
        print(f"  {i}. {name} ({val:#04x})")
    domain_idx = int(input("Wybierz domenę [1-3]: ").strip()) - 1
    domain_name = list(DOMAINS.keys())[domain_idx]
    domain = DOMAINS[domain_name]

    print(f"\nDostępne rodzaje dla {domain_name}:")
    relevant_kinds = {k: v for k, v in KINDS.items()}
    for i, (name, val) in enumerate(relevant_kinds.items(), 1):
        count = len(registry.uids_for_kind(val))
        print(f"  {i:2}. {name:<20} ({val:#04x})  [{count} UIDs]")
    kind_idx = int(input(f"Wybierz rodzaj [1-{len(relevant_kinds)}]: ").strip()) - 1
    kind_name = list(relevant_kinds.keys())[kind_idx]
    kind = relevant_kinds[kind_name]

    scope_str = input("\nSCOPE (0 dla taboru, numer stacji dla infrastruktury) [domyślnie 0]: ").strip()
    scope = int(scope_str) if scope_str else 0

    return domain, kind, scope


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the next free UID for a given domain/kind/scope."
    )
    parser.add_argument("--domain", choices=list(DOMAINS.keys()),
                        help="UID domain (e.g. ROLLING_STOCK)")
    parser.add_argument("--kind", choices=list(KINDS.keys()),
                        help="UID kind (e.g. VEHICLE_TYPE)")
    parser.add_argument("--scope", type=int, default=0,
                        help="SCOPE value (default: 0)")
    parser.add_argument("--root", type=Path, default=None,
                        help="Path to symulator-data repo root (auto-detected if omitted)")
    args = parser.parse_args()

    root = args.root or find_repo_root()
    print(f"Scanning existing UIDs in: {root}")

    registry = UIDRegistry(root)
    registry.scan()

    if args.domain and args.kind:
        domain = DOMAINS[args.domain]
        kind = KINDS[args.kind]
        scope = args.scope
    else:
        domain, kind, scope = interactive_mode(registry)

    kind_uids = registry.uids_for_kind(kind)
    print(f"\nScanning existing UIDs...  {len(kind_uids)} {KIND_NAMES.get(kind, kind)} UIDs found")

    generator = UIDGenerator(registry)
    uid = generator.next_uid(domain, kind, scope)

    _, _, _, instance = UIDCodec.decode(uid)
    dec_fmt = DecimalFormatter()
    hex_fmt = HexFormatter()

    domain_label = DOMAIN_NAMES.get(domain, f"{domain:#x}")
    kind_label = KIND_NAMES.get(kind, f"{kind:#x}")

    print(f"Next UID:  {dec_fmt.format(uid, domain, kind, scope, instance)}")
    print(f"Hex:       {hex_fmt.format(uid, domain, kind, scope, instance)}")
    print(f"\n  domain={domain_label}, kind={kind_label}, scope={scope}, instance={instance}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
