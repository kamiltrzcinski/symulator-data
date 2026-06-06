import tkinter as tk
from tkinter import ttk
from pathlib import Path

from models.vehicle_type import VehicleType
from models.vehicle import Vehicle
from repositories.vehicle_type_repo import VehicleTypeRepository
from repositories.vehicle_repo import VehicleRepository
from sorting.by_type_name import SortByTypeName
from sorting.by_vehicle_type import SortByVehicleType
from sorting.by_vehicle_subtype import SortByVehicleSubtype
from ui.sortable_table import SortableTable

TYPE_COLUMNS = [
    ("uid", 140), ("typeName", 100), ("vehicleType", 110),
    ("vehicleSubtype", 110), ("lengthM", 70), ("massGrossT", 80), ("maxSpeedKmh", 90),
]

VEHICLE_COLUMNS = [
    ("uid", 140), ("pID", 120), ("displayName", 200), ("type_uid", 140),
]


class MainWindow:
    def __init__(self, root: Path):
        self._root_path = root
        self._win = tk.Tk()
        self._win.title("vehicle-browser — symulator-data")
        self._win.geometry("1100x600")
        self._build_ui()
        self._load_data()

    def _build_ui(self) -> None:
        top = ttk.Frame(self._win, padding=4)
        top.pack(fill="x")
        ttk.Label(top, text="Filtruj:").pack(side="left")
        self._filter_var = tk.StringVar()
        self._filter_var.trace_add("write", self._on_filter_changed)
        ttk.Entry(top, textvariable=self._filter_var, width=40).pack(side="left", padx=4)

        nb = ttk.Notebook(self._win)
        nb.pack(fill="both", expand=True, padx=4, pady=4)

        types_frame = ttk.Frame(nb)
        nb.add(types_frame, text="Typy pojazdów")
        self._types_table = SortableTable(types_frame, TYPE_COLUMNS)
        self._types_table.pack(fill="both", expand=True)

        vehicles_frame = ttk.Frame(nb)
        nb.add(vehicles_frame, text="Pojazdy")
        self._vehicles_table = SortableTable(vehicles_frame, VEHICLE_COLUMNS)
        self._vehicles_table.pack(fill="both", expand=True)

        self._nb = nb
        self._nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _load_data(self) -> None:
        types: list[VehicleType] = VehicleTypeRepository(self._root_path).load_all()
        vehicles: list[Vehicle] = VehicleRepository(self._root_path).load_all()

        self._type_rows = [
            (t.uid, t.typeName, t.vehicleType, t.vehicleSubtype,
             t.lengthM, t.massGrossT, t.maxSpeedKmh)
            for t in types
        ]
        self._vehicle_rows = [
            (v.uid, v.pID, v.displayName, v.type_uid)
            for v in vehicles
        ]

        self._types_table.set_rows(self._type_rows)
        self._vehicles_table.set_rows(self._vehicle_rows)

        self._win.title(
            f"vehicle-browser — {len(types)} typów, {len(vehicles)} pojazdów"
        )

    def _on_filter_changed(self, *_) -> None:
        text = self._filter_var.get()
        self._types_table.filter_rows(text)
        self._vehicles_table.filter_rows(text)

    def _on_tab_changed(self, *_) -> None:
        pass

    def run(self) -> None:
        self._win.mainloop()
