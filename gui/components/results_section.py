import tkinter as tk
from tkinter import ttk
import logging
from .result_card import ResultCard

logger = logging.getLogger('ResultsSection')


class ResultsSection:
    def __init__(self, parent, on_sort_changed):
        self.parent = parent
        self.on_sort_changed = on_sort_changed
        self.current_row = 0
        self.current_column = 0
        self.sort_var = tk.StringVar(value="Relevanz")
        self.count_var = tk.StringVar(
            value="Gefundene Artikel: 0 (eBay), 0 (Amazon)")
        self.create_widgets()

    def create_widgets(self):
        self.frame = ttk.LabelFrame(
            self.parent,
            text="Suchergebnisse",
            padding=10
        )
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.create_toolbar()
        self.create_scrollable_results()

    def create_toolbar(self):
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(toolbar, text="Sortierung:").pack(side=tk.LEFT)

        sort_combobox = ttk.Combobox(
            toolbar,
            textvariable=self.sort_var,
            values=["Relevanz", "Preis aufsteigend", "Preis absteigend"],
            state="readonly",
            width=20
        )
        sort_combobox.pack(side=tk.LEFT, padx=5)
        sort_combobox.bind('<<ComboboxSelected>>', self.on_sort_changed)

        ttk.Label(
            toolbar,
            textvariable=self.count_var,
            font=("Helvetica", 12)
        ).pack(side=tk.RIGHT)

    def create_scrollable_results(self):
        self.results_container = ttk.Frame(self.frame)
        self.results_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            self.results_container,
            bg='white',
            width=400,
            height=300
        )

        self.scrollbar = ttk.Scrollbar(
            self.results_container,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame_id = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor=tk.NW,
            width=self.canvas.winfo_width()
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(1, weight=1)

        self.setup_bindings()

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_bindings(self):
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.scrollable_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind_all('<Button-4>', self._on_mousewheel)
        self.canvas.bind_all('<Button-5>', self._on_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.scrollable_frame_id, width=event.width)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        if not self.canvas.winfo_height():
            return

        try:
            if event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1
            else:
                delta = event.delta

            scroll_amount = -1 * (delta/120)
            self.canvas.yview_scroll(int(scroll_amount), "units")
        except Exception as e:
            logger.error(f"Fehler beim Scrollen: {e}")

    def clear_results(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.current_row = 0
        self.current_column = 0
        self.canvas.configure(scrollregion=(0, 0, 0, 0))
        self.canvas.update_idletasks()

    def add_result_card(self, item, source, on_favorite_click, on_details_click):
        try:
            if self.current_row >= 2:
                self.current_row = 0
                self.current_column += 2

            column = 0 if source == "ebay" else 1

            card = ResultCard(
                self.scrollable_frame,
                item,
                source,
                on_favorite_click,
                on_details_click
            ).create()

            if card:
                card.grid(
                    row=self.current_row,
                    column=self.current_column + column,
                    padx=10,
                    pady=10,
                    sticky="nsew"
                )

                self.current_row += 1
                self.scrollable_frame.update_idletasks()
                self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen der Ergebniskarte: {e}")

    def update_count(self, ebay_count, amazon_count):
        self.count_var.set(
            f"Gefundene Artikel: {ebay_count} (eBay), {amazon_count} (Amazon)"
        )

    def get_sort_option(self):
        return self.sort_var.get()
