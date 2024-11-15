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
        self.widgets = []  # Liste aller erstellten Widgets für cleanup

    def create(self):
        """Erstellt und gibt die Ergebniskarte zurück."""
        try:
            # Container für die Karte
            card_container = ttk.Frame(self.parent)
            self.widgets.append(card_container)

            # Hauptkarte mit Schatten-Effekt
            card = ttk.Frame(
                card_container,
                style="Card.TFrame",
                padding=10
            )
            card.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            card.columnconfigure(0, weight=1)
            self.widgets.append(card)

            # Plattform-Icon
            icon = "🏪" if self.source == "ebay" else "📦"
            icon_label = ttk.Label(
                card,
                text=icon,
                font=("Helvetica", 16)
            )
            icon_label.grid(row=0, column=0, sticky="w")
            self.widgets.append(icon_label)

            # Titel mit Clipping
            title_text = self.item['title'][:100] + \
                "..." if len(self.item['title']) > 100 else self.item['title']
            title_label = ttk.Label(
                card,
                text=title_text,
                wraplength=300,
                font=("Helvetica", 11, "bold"),
                justify=tk.LEFT
            )
            title_label.grid(row=1, column=0, sticky="w", pady=(5, 10))
            self.widgets.append(title_label)

            # Preis hervorgehoben
            price_frame = ttk.Frame(card)
            price_frame.grid(row=2, column=0, sticky="w", pady=(0, 5))
            self.widgets.append(price_frame)

            price_label = ttk.Label(
                price_frame,
                text=self.item['price'],
                font=("Helvetica", 14, "bold")
            )
            price_label.pack(side=tk.LEFT)
            self.widgets.append(price_label)

            # Versandinfo
            if 'shipping' in self.item:
                shipping_label = ttk.Label(
                    card,
                    text=f"Versand: {self.item['shipping']}",
                    font=("Helvetica", 10)
                )
                shipping_label.grid(row=3, column=0, sticky="w", pady=(0, 5))
                self.widgets.append(shipping_label)

            # Standort (nur für eBay)
            if 'location' in self.item and self.source == "ebay":
                location_label = ttk.Label(
                    card,
                    text=f"Standort: {self.item['location']}",
                    font=("Helvetica", 10)
                )
                location_label.grid(row=4, column=0, sticky="w", pady=(0, 5))
                self.widgets.append(location_label)

            # Button-Container
            button_frame = ttk.Frame(card)
            button_frame.grid(row=5, column=0, sticky="e", pady=(10, 0))
            self.widgets.append(button_frame)

            # Details-Button
            details_btn = ttk.Button(
                button_frame,
                text="Details →",
                command=lambda: self.on_details_click(self.item['link']),
                style="Action.TButton"
            )
            details_btn.pack(side=tk.LEFT, padx=2)
            self.widgets.append(details_btn)

            # Favoriten-Button
            favorite_btn = ttk.Button(
                button_frame,
                text="❤",
                command=lambda: self.on_favorite_click(self.item, self.source),
                style="Favorites.TButton",
                width=3
            )
            favorite_btn.pack(side=tk.LEFT, padx=2)
            self.widgets.append(favorite_btn)

            return card_container

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Ergebniskarte: {e}")
            return None

    def destroy(self):
        """Zerstört alle Widgets dieser Karte."""
        try:
            for widget in self.widgets:
                if widget.winfo_exists():
                    widget.destroy()
            self.widgets = []
        except Exception as e:
            logger.error(f"Fehler beim Zerstören der Ergebniskarte: {e}")
