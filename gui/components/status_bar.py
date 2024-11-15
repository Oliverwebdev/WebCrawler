# gui/components/status_bar.py
import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger('StatusBar')


class StatusBar:
    def __init__(self, parent):
        """
        Initialisiert die Statusleiste.
        
        Args:
            parent: Übergeordnetes Tkinter-Widget
        """
        self.parent = parent
        self.create_widgets()

    def create_widgets(self):
        """Erstellt die Statusleisten-Widgets."""
        self.frame = ttk.Frame(self.parent)
        self.frame.pack(fill=tk.X, side=tk.BOTTOM, pady=2)

        # Status-Label
        self.status_var = tk.StringVar(value="Bereit")
        self.status_label = ttk.Label(
            self.frame,
            textvariable=self.status_var,
            style='Status.TLabel'
        )
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Trennlinie
        ttk.Separator(self.parent, orient='horizontal').pack(
            fill=tk.X,
            side=tk.BOTTOM,
            before=self.frame
        )

    def update_status(self, message):
        """
        Aktualisiert die Statusnachricht.
        
        Args:
            message: Anzuzeigende Nachricht
        """
        try:
            self.status_var.set(message)
            logger.debug(f"Status aktualisiert: {message}")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Status: {e}")
