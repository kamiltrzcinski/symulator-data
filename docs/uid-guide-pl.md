# Przewodnik po UID — dla współtwórców

## Czym jest UID i dlaczego ma taką postać

Każdy obiekt w symulatorze (typ pojazdu, pojazd, skład, rozkład jazdy) ma unikalny
64-bitowy identyfikator liczbowy — **UID**. Dzięki temu silnik gry może jednoznacznie
odwoływać się do danych bez ryzyka kolizji nazw.

UID jest podzielony na cztery pola:

```
 63      48 47    40 39    32 31           16 15            0
┌──────────┬────────┬────────┬──────────────┬────────────────┐
│ reserved │ DOMAIN │  KIND  │    SCOPE     │    INSTANCE    │
│  16 bits │ 8 bits │ 8 bits │   16 bits    │    16 bits     │
└──────────┴────────┴────────┴──────────────┴────────────────┘
```

| Pole     | Znaczenie |
|----------|-----------|
| DOMAIN   | Kategoria: `ROLLING_STOCK` (tabor) lub `INFRASTRUCTURE` / `OPERATIONS` |
| KIND     | Rodzaj obiektu (np. `VEHICLE_TYPE`, `TRAIN_CONSIST`) |
| SCOPE    | Kontekst (seria pojazdu lub `0`) |
| INSTANCE | Numer kolejny w ramach SCOPE |

W plikach JSON UID jest zapisywany jako **liczba całkowita** (np. `1103806595650`).

---

## Tabela domen i rodzajów (tabor)

Tylko te rodzaje są istotne dla współtwórców rozkładów jazdy i danych taboru:

| KIND (hex) | Nazwa           | Używany w |
|------------|-----------------|-----------|
| `0x01`     | `VEHICLE_TYPE`  | `data/vehicle_types/` |
| `0x02`     | `VEHICLE`       | `data/vehicles/`      |
| `0x03`     | `TRAIN_CONSIST` | `data/trains/`        |

Rozkłady jazdy (`schedules/`) odwołują się do powyższych przez pole `vehicle_uids`.

---

## Jak wygenerować UID dla nowego rozkładu jazdy

1. Pobierz `uid-generator` z zakładki **Releases** w tym repozytorium
   (dostępne wersje: Linux, Windows `.exe`, macOS)

2. Uruchom narzędzie z odpowiednimi parametrami:
   ```
   uid-generator --domain ROLLING_STOCK --kind TRAIN_CONSIST
   ```
   Przykładowe wyjście:
   ```
   Scanning existing UIDs...  12 TRAIN_CONSIST UIDs found
   Next UID: 844424930131981
   Hex:      0x0003_0000_0000_000D (domain=RS, kind=TRAIN_CONSIST, scope=0, instance=13)
   ```

3. Skopiuj wartość liczbową (np. `844424930131981`) do pola `uid` w swoim pliku JSON.

4. Upewnij się, że plik JSON ma wymagane pola — patrz `specs/schedule.spec.md`.

---

## Czego NIE robić

- **Nie wymyślaj UIDs ręcznie** — wpisujesz błędny zakres i trafia się kolizja.
- **Nie duplikuj** UID z innego pliku — pre-commit hook blokuje commit z duplikatem.
- **Nie zmieniaj** UIDs istniejących plików — silnik gry ma je zahardkodowane w scenariuszach.
