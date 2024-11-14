import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger('StatusBar')


class StatusBar:
    def __init__(self, parent):
        self.parent = parent
        self.progress_var = tk.IntVar(value=0)
        self.status_var = tk.StringVar(value="Bereit für die Suche")
        self.create_widgets()

    def create_widgets(self):
        try:
            status_bar = ttk.Frame(self.parent)
            status_bar.pack(fill=tk.X, pady=5)

            self.progress_bar = ttk.Progressbar(
                status_bar,
                variable=self.progress_var,
                length=200,
                mode='determinate'
            )
            self.progress_bar.pack(side=tk.LEFT, padx=5)

            self.status_label = ttk.Label(
                status_bar,
                textvariable=self.status_var
            )
            self.status_label.pack(side=tk.LEFT, padx=5)

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der StatusBar: {e}")

    def set_progress(self, value):
        self.progress_var.set(value)

    def set_status(self, text):
        self.status_var.set(text)

    def reset(self):
        self.progress_var.set(0)
        self.status_var.set("Bereit für die Suche")
