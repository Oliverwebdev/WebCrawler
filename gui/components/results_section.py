import tkinter as tk
from tkinter import ttk
import logging
from .paginated_result_view import PaginatedResultView

logger = logging.getLogger('ResultsSection')


class ResultsSection:
    def __init__(self, parent, on_sort_changed):
        """
        Initialisiert die ResultsSection mit zwei paginierten Views.

        Args:
            parent: Übergeordnetes Widget
            on_sort_changed: Callback für Sortierungsänderungen
        """
        self.parent = parent
        self.on_sort_changed = on_sort_changed
        self.sort_var = tk.StringVar(value="Relevanz")
        self.count_var = tk.StringVar(
            value="Gefundene Artikel: 0 (eBay), 0 (Amazon)")
        self.ebay_results = []
        self.amazon_results = []
        self.create_widgets()

    def create_widgets(self):
        """Erstellt das Layout mit Toolbar und zwei Ergebnisansichten."""
        # Hauptcontainer
        self.frame = ttk.LabelFrame(
            self.parent,
            text="Suchergebnisse",
            padding=10
        )
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Toolbar mit Sortierung und Zähler
        self.create_toolbar()

        # Container für die Ergebnisansichten
        results_container = ttk.Frame(self.frame)
        results_container.pack(fill=tk.BOTH, expand=True)
        results_container.columnconfigure(0, weight=1)
        results_container.columnconfigure(1, weight=1)

        # Separator zwischen den Views
        ttk.Separator(results_container, orient=tk.VERTICAL).grid(
            row=0, column=1, sticky="ns", padx=10)

        # eBay und Amazon Views
        self.ebay_view = PaginatedResultView(results_container, "ebay")
        self.amazon_view = PaginatedResultView(results_container, "amazon")

        # Platziere Views nebeneinander
        self.ebay_view.get_frame().grid(row=0, column=0, sticky="nsew")
        self.amazon_view.get_frame().grid(row=0, column=2, sticky="nsew")

    def create_toolbar(self):
        """Erstellt die Toolbar mit Sortieroptionen und Zähler."""
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        # Sortierungsbereich
        sort_frame = ttk.Frame(toolbar)
        sort_frame.pack(side=tk.LEFT)

        ttk.Label(sort_frame, text="Sortierung:").pack(side=tk.LEFT)
        sort_combobox = ttk.Combobox(
            sort_frame,
            textvariable=self.sort_var,
            values=["Relevanz", "Preis aufsteigend", "Preis absteigend"],
            state="readonly",
            width=20
        )
        sort_combobox.pack(side=tk.LEFT, padx=5)
        sort_combobox.bind('<<ComboboxSelected>>', self._handle_sort_change)

        # Ergebniszähler
        ttk.Label(
            toolbar,
            textvariable=self.count_var,
            font=("Helvetica", 12)
        ).pack(side=tk.RIGHT)

    def _handle_sort_change(self, event=None):
        """Behandelt Änderungen der Sortierung."""
        try:
            self.sort_results()
            # Aktualisiere beide Views mit den sortierten Ergebnissen
            self.ebay_view.set_items(self.ebay_results)
            self.amazon_view.set_items(self.amazon_results)
        except Exception as e:
            logger.error(f"Fehler beim Sortieren der Ergebnisse: {e}")

    def sort_results(self):
        """Sortiert die Ergebnisse nach der ausgewählten Option."""
        sort_option = self.sort_var.get()

        try:
            if sort_option == "Preis aufsteigend":
                self.ebay_results.sort(
                    key=lambda x: self._extract_price(x['price']))
                self.amazon_results.sort(
                    key=lambda x: self._extract_price(x['price']))
            elif sort_option == "Preis absteigend":
                self.ebay_results.sort(
                    key=lambda x: self._extract_price(x['price']),
                    reverse=True
                )
                self.amazon_results.sort(
                    key=lambda x: self._extract_price(x['price']),
                    reverse=True
                )
        except Exception as e:
            logger.error(f"Fehler beim Sortieren: {e}")

    def _extract_price(self, price_str):
        """Extrahiert den numerischen Preis aus einem Preisstring."""
        try:
            clean_price = ''.join(
                c for c in price_str if c.isdigit() or c in '.,')
            clean_price = clean_price.replace(',', '.')
            return float(clean_price)
        except (ValueError, AttributeError, TypeError) as e:
            logger.error(f"Fehler bei der Preisextraktion für {
                         price_str}: {e}")
            return 0.0

    def clear_results(self):
        """Leert alle Ergebnisse und setzt die Views zurück."""
        self.ebay_results = []
        self.amazon_results = []
        self.ebay_view.clear()
        self.amazon_view.clear()
        self.update_count(0, 0)

    def update_results(self, ebay_results, amazon_results):
        """
        Aktualisiert die Ergebnisse beider Plattformen.
        
        Args:
            ebay_results: Liste der eBay-Ergebnisse
            amazon_results: Liste der Amazon-Ergebnisse
        """
        try:
            self.ebay_results = ebay_results
            self.amazon_results = amazon_results

            # Sortiere Ergebnisse falls nötig
            if self.sort_var.get() != "Relevanz":
                self.sort_results()

            # Aktualisiere Views
            self.ebay_view.set_items(self.ebay_results)
            self.amazon_view.set_items(self.amazon_results)

            # Aktualisiere Zähler
            self.update_count(len(ebay_results), len(amazon_results))

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Ergebnisse: {e}")

    def update_count(self, ebay_count, amazon_count):
        """Aktualisiert den Ergebniszähler."""
        self.count_var.set(
            f"Gefundene Artikel: {ebay_count} (eBay), {amazon_count} (Amazon)"
        )

    def set_callbacks(self, on_favorite_click, on_details_click):
        """Setzt die Callbacks für beide Views."""
        self.ebay_view.set_callbacks(on_favorite_click, on_details_click)
        self.amazon_view.set_callbacks(on_favorite_click, on_details_click)

    def get_sort_option(self):
        """Gibt die aktuelle Sortierungsoption zurück."""
        return self.sort_var.get()
