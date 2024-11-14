import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger('ResultCard')


class ResultCard:
    def __init__(self, parent, item, source, on_favorite_click, on_details_click):
        """
        Initialisiert eine Ergebniskarte.
        
        Args:
            parent: Das übergeordnete Widget
            item (dict): Das Artikel-Dictionary mit title, price, shipping, etc.
            source (str): Die Quelle des Artikels (ebay/amazon)
            on_favorite_click: Callback für Favoriten-Button
            on_details_click: Callback für Details-Button
        """
        self.parent = parent
        self.item = item
        self.source = source
        self.on_favorite_click = on_favorite_click
        self.on_details_click = on_details_click

    def create(self):
        """Erstellt und gibt die Ergebniskarte zurück."""
        try:
            # Container für die Karte
            card_container = ttk.Frame(self.parent)

            # Erstelle die eigentliche Karte
            card = ttk.Frame(
                card_container,
                style="Card.TFrame",
                padding=10
            )
            card.grid(row=0, column=0, sticky="nsew")
            card.columnconfigure(0, weight=1)

            # Titel
            title_label = ttk.Label(
                card,
                text=self.item['title'],
                wraplength=300,
                font=("Helvetica", 12, "bold")
            )
            title_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

            # Preis
            price_label = ttk.Label(
                card,
                text=self.item['price'],
                font=("Helvetica", 12)
            )
            price_label.grid(row=1, column=0, sticky="w", pady=(0, 5))

            # Versand
            if 'shipping' in self.item:
                shipping_label = ttk.Label(
                    card,
                    text=f"Versand: {self.item['shipping']}"
                )
                shipping_label.grid(row=2, column=0, sticky="w", pady=(0, 5))

            # Standort (nur für eBay)
            if 'location' in self.item:
                location_label = ttk.Label(
                    card,
                    text=f"Standort: {self.item['location']}"
                )
                location_label.grid(row=3, column=0, sticky="w", pady=(0, 5))

            # Button-Container
            button_frame = ttk.Frame(card)
            button_frame.grid(row=4, column=0, sticky="e", pady=(5, 0))

            # Details-Button
            details_btn = ttk.Button(
                button_frame,
                text="Details",
                command=lambda: self.on_details_click(self.item['link']),
                style="Action.TButton"
            )
            details_btn.pack(side=tk.LEFT, padx=2)

            # Favoriten-Button
            favorite_btn = ttk.Button(
                button_frame,
                text="❤",
                command=lambda: self.on_favorite_click(self.item, self.source),
                style="Action.TButton"
            )
            favorite_btn.pack(side=tk.LEFT, padx=2)

            # Quelle
            source_label = ttk.Label(
                card,
                text=f"Quelle: {self.source.capitalize()}",
                font=("Helvetica", 10, "italic")
            )
            source_label.grid(row=5, column=0, sticky="w", pady=(5, 0))

            return card_container

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Ergebniskarte: {e}")
            return None

    def update(self, item):
        """
        Aktualisiert die Daten der Karte.
        
        Args:
            item (dict): Neue Artikel-Daten
        """
        try:
            self.item = item
            # Hier könnte man die Aktualisierungslogik implementieren,
            # falls die Karten dynamisch aktualisiert werden sollen
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Ergebniskarte: {e}")
