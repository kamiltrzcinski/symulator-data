# Timetable Point Specification

## Domain and Kind
- **Domain**: OPERATIONS (0x03)
- **Kind**: TIMETABLE_POINT (0x24)

## Schema
Każdy plik w katalogu `data/timetable_points/` reprezentuje pojedynczy punkt konstrukcyjny.

```json
{
  "uid": 123456789,
  "type": "TIMETABLE_POINT",
  "name": "Rudzienice Suskie",
  "point_type": "STATION",
  "short_name": "Rud",
  "external_ids": {
    "skrj_kalkulacja": "12345"
  }
}
```

### Required Fields
- `uid` (integer): Zgodny z mechanizmem UID, unikalny, stabilny.
- `type` (string): Zawsze "TIMETABLE_POINT".
- `name` (string): Nazwa punktu (niepusta).
- `point_type` (string): Typ punktu, dozwolone wartości: STATION, PASSENGER_STOP, JUNCTION_POST, SIDING_POST, LOADING_POINT, PASSING_LOOP, BORDER_POINT, TECHNICAL_POINT, OTHER.

### Optional Fields
- `short_name` (string)
- `abbreviation` (string)
- `aliases` (array of strings)
- `external_ids` (object): Słownik systemów zewnętrznych i ich id.
- `line_locations` (array of objects): Lista lokacji punktu na liniach kolejowych.
  - `line_no` (string): Numer linii.
  - `meter` (number): Kilometraż na linii w metrach.
- `validity` (object)

---

# Timetable Connection Specification

## Domain and Kind
- **Domain**: OPERATIONS (0x03)
- **Kind**: TIMETABLE_CONNECTION (0x25)

## Schema
Pliki w katalogu `data/timetable_connections/` reprezentują krawędzie w topologii.

```json
{
  "uid": 987654321,
  "type": "TIMETABLE_CONNECTION",
  "from_uid": 123456789,
  "to_uid": 123456790,
  "lines": [
    {
      "line_no": "1",
      "from_meter": 2405,
      "to_meter": 2482
    }
  ]
}
```

### Required Fields
- `uid` (integer): UID połączenia.
- `type` (string): Zawsze "TIMETABLE_CONNECTION".
- `from_uid` (integer): Referencja do TIMETABLE_POINT.
- `to_uid` (integer): Referencja do TIMETABLE_POINT.
- `lines` (array of objects): Lista linii po których przebiega to połączenie, zawierająca:
  - `line_no` (string): Numer linii.
  - `from_meter` (number): Początkowy kilometraż krawędzi (w metrach).
  - `to_meter` (number): Końcowy kilometraż krawędzi (w metrach).
