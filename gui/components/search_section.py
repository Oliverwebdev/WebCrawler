import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger('SearchSection')


class SearchSection:
    def __init__(self, parent, search_callback):
        self.parent = parent
        self.search_callback = search_callback
        self.search_var = tk.StringVar()
        self.min_price_var = tk.StringVar()
        self.max_price_var = tk.StringVar()
        self.condition_var = tk.StringVar(value="Alle")
        self.search_active = False
        self.search_button = None
        self.create_widgets()

    def create_widgets(self):
        search_frame = ttk.LabelFrame(
            self.parent,
            text="Suchoptionen",
            padding=10
        )
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=40,
            font=("Helvetica", 12)
        )
        search_entry.pack(side=tk.LEFT, padx=5)

        self.search_button = ttk.Button(
            search_frame,
            text="Suchen",
            command=self.start_search,
            style="Action.TButton"
        )
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.create_advanced_options(search_frame)

    def create_advanced_options(self, parent):
        options_frame = ttk.Frame(parent)
        options_frame.pack(side=tk.LEFT, padx=20)

        # Preis-Bereich
        price_frame = ttk.Frame(options_frame)
        price_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(price_frame, text="Preis von:").pack(side=tk.LEFT)
        ttk.Entry(
            price_frame,
            textvariable=self.min_price_var,
            width=10
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(price_frame, text="bis:").pack(side=tk.LEFT)
        ttk.Entry(
            price_frame,
            textvariable=self.max_price_var,
            width=10
        ).pack(side=tk.LEFT, padx=5)

        # Zustand
        condition_frame = ttk.Frame(options_frame)
        condition_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Label(condition_frame, text="Zustand:").pack(side=tk.LEFT)
        ttk.Combobox(
            condition_frame,
            textvariable=self.condition_var,
            values=["Alle", "Neu", "Gebraucht"],
            state="readonly",
            width=15
        ).pack(side=tk.LEFT, padx=5)

    def start_search(self):
        if self.search_active:
            return

        search_params = {
            'keyword': self.search_var.get().strip(),
            'min_price': self.min_price_var.get(),
            'max_price': self.max_price_var.get(),
            'condition': self.condition_var.get()
        }

        self.search_callback(search_params)

    def set_search_state(self, active):
        self.search_active = active
        if active:
            self.search_button.state(['disabled'])
        else:
            self.search_button.state(['!disabled'])

    def get_search_params(self):
        return {
            'keyword': self.search_var.get().strip(),
            'min_price': self.min_price_var.get(),
            'max_price': self.max_price_var.get(),
            'condition': self.condition_var.get()
        }
