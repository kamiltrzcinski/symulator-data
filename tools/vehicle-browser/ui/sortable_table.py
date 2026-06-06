import tkinter as tk
from tkinter import ttk


class SortableTable(ttk.Frame):
    def __init__(self, parent, columns: list[tuple[str, int]], **kwargs):
        super().__init__(parent, **kwargs)
        self._sort_col: str | None = None
        self._sort_reverse = False

        self._tree = ttk.Treeview(self, columns=[c for c, _ in columns],
                                  show="headings", selectmode="browse")
        vsb = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)

        for col, width in columns:
            self._tree.heading(col, text=col,
                               command=lambda c=col: self._on_header_click(c))
            self._tree.column(col, width=width, anchor="w")

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._all_rows: list[tuple] = []
        self._columns = [c for c, _ in columns]

    def set_rows(self, rows: list[tuple]) -> None:
        self._all_rows = list(rows)
        self._refresh()

    def filter_rows(self, text: str) -> None:
        text = text.lower()
        if text:
            filtered = [r for r in self._all_rows
                        if any(text in str(v).lower() for v in r)]
        else:
            filtered = list(self._all_rows)
        self._refresh(filtered)

    def _refresh(self, rows: list[tuple] | None = None) -> None:
        self._tree.delete(*self._tree.get_children())
        for row in (rows if rows is not None else self._all_rows):
            self._tree.insert("", "end", values=row)

    def _on_header_click(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = False

        col_idx = self._columns.index(col)
        rows = [self._tree.item(c)["values"] for c in self._tree.get_children()]
        rows.sort(key=lambda r: (r[col_idx] is None, str(r[col_idx]).lower()),
                  reverse=self._sort_reverse)
        self._refresh(rows)

        for c in self._columns:
            indicator = ""
            if c == col:
                indicator = " ▼" if self._sort_reverse else " ▲"
            self._tree.heading(c, text=c + indicator,
                               command=lambda cc=c: self._on_header_click(cc))
