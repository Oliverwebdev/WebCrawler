import tkinter as tk
from tkinter import ttk
import logging
from .result_card import ResultCard

logger = logging.getLogger('PaginatedResultView')


class PaginatedResultView:
    def __init__(self, parent, source, db_manager):
        """
        Initialisiert eine paginierte Ergebnisansicht mit Datenbankanbindung.
        
        Args:
            parent: Übergeordnetes Widget
            source: Quelle der Ergebnisse ("ebay" oder "amazon")
            db_manager: Instanz des DatabaseManagers
        """
        self.parent = parent
        self.source = source
        self.db_manager = db_manager
        self.current_page = 0
        self.items_per_page = 10
        self.all_items = []
        self.current_cards = []
        self.on_favorite_click = None
        self.on_details_click = None
        self.search_filter = ""
        self.setup_ui()

    def setup_ui(self):
        """Erstellt das erweiterte UI-Layout für die paginierte Ansicht."""
        self.frame = ttk.Frame(self.parent)

        # Header mit Titel, Filter und Seitennavigation
        header = ttk.Frame(self.frame)
        header.pack(fill=tk.X, pady=(0, 5))

        # Linke Seite: Plattform-Label und Filter
        left_frame = ttk.Frame(header)
        left_frame.pack(side=tk.LEFT, fill=tk.X)

        # Plattform-Label mit Icon
        icon_text = "🏪" if self.source == "ebay" else "📦"
        title_text = f"{icon_text} {self.source.upper()}"

        ttk.Label(
            left_frame,
            text=title_text,
            font=("Helvetica", 12, "bold")
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Suchfilter
        ttk.Label(
            left_frame,
            text="Filter:"
        ).pack(side=tk.LEFT)

        self.filter_entry = ttk.Entry(left_frame, width=20)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind('<KeyRelease>', self.apply_filter)

        # Navigation
        nav_frame = ttk.Frame(header)
        nav_frame.pack(side=tk.RIGHT)

        self.prev_btn = ttk.Button(
            nav_frame,
            text="←",
            command=self.prev_page,
            state=tk.DISABLED,
            width=3
        )
        self.prev_btn.pack(side=tk.LEFT, padx=2)

        self.page_label = ttk.Label(
            nav_frame,
            text="Seite 1",
            width=15,
            anchor="center"
        )
        self.page_label.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(
            nav_frame,
            text="→",
            command=self.next_page,
            state=tk.DISABLED,
            width=3
        )
        self.next_btn.pack(side=tk.LEFT, padx=2)

        # Ergebnisse pro Seite Auswahl
        ttk.Label(
            nav_frame,
            text="Ergebnisse pro Seite:"
        ).pack(side=tk.LEFT, padx=(10, 0))

        self.items_per_page_var = tk.StringVar(value="10")
        items_per_page_combo = ttk.Combobox(
            nav_frame,
            textvariable=self.items_per_page_var,
            values=["5", "10", "20", "50"],
            width=3,
            state="readonly"
        )
        items_per_page_combo.pack(side=tk.LEFT, padx=5)
        items_per_page_combo.bind(
            '<<ComboboxSelected>>', self.change_items_per_page)

        # Scrollbarer Container für Ergebniskarten
        self.create_scrollable_frame()

    def create_scrollable_frame(self):
        """Erstellt den scrollbaren Container für die Ergebniskarten."""
        # Canvas und Scrollbar
        self.canvas = tk.Canvas(self.frame, bg='white')
        self.scrollbar = ttk.Scrollbar(
            self.frame,
            orient="vertical",
            command=self.canvas.yview
        )

        self.results_frame = ttk.Frame(self.canvas)
        self.results_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_frame = self.canvas.create_window(
            (0, 0),
            window=self.results_frame,
            anchor="nw",
            width=self.canvas.winfo_reqwidth()
        )

        # Canvas Konfiguration
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        # Layout
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Mausrad-Bindings
        self._bind_mouse_scroll()

    def apply_filter(self, event=None):
        """Wendet den Suchfilter auf die Ergebnisse an."""
        try:
            self.search_filter = self.filter_entry.get().lower()
            filtered_items = [
                item for item in self.all_items
                if self.search_filter in item['title'].lower()
            ]
            self.current_page = 0
            self.update_page(filtered_items)
            self.update_navigation(filtered_items)
        except Exception as e:
            logger.error(f"Fehler beim Anwenden des Filters: {e}")

    def change_items_per_page(self, event=None):
        """Ändert die Anzahl der Ergebnisse pro Seite."""
        try:
            self.items_per_page = int(self.items_per_page_var.get())
            self.current_page = 0
            filtered_items = [
                item for item in self.all_items
                if self.search_filter in item['title'].lower()
            ]
            self.update_page(filtered_items)
            self.update_navigation(filtered_items)
        except Exception as e:
            logger.error(f"Fehler beim Ändern der Ergebnisse pro Seite: {e}")

    def set_items(self, items):
        """
        Setzt die anzuzeigenden Items und aktualisiert die Ansicht.
        
        Args:
            items: Liste der anzuzeigenden Items
        """
        self.all_items = items
        self.current_page = 0
        filtered_items = [
            item for item in items
            if self.search_filter in item['title'].lower()
        ]
        self.update_page(filtered_items)
        self.update_navigation(filtered_items)

    def update_page(self, items):
        """Aktualisiert die Anzeige der aktuellen Seite."""
        self._clear_current_cards()

        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        current_items = items[start_idx:end_idx]

        for idx, item in enumerate(current_items):
            try:
                card = ResultCard(
                    self.results_frame,
                    item,
                    self.source,
                    self.on_favorite_click,
                    self.on_details_click,
                    self.db_manager  # Neue Referenz zum DatabaseManager
                ).create()

                if card:
                    card.grid(
                        row=idx,
                        column=0,
                        sticky="ew",
                        padx=5,
                        pady=5
                    )
                    self.current_cards.append(card)

            except Exception as e:
                logger.error(f"Fehler beim Erstellen der Karte: {e}")

        # Scrolle nach oben bei Seitenwechsel
        self.canvas.yview_moveto(0)

    def update_navigation(self, items):
        """Aktualisiert den Zustand der Navigationsbuttons."""
        total_items = len(items)
        total_pages = max(1, (total_items - 1) // self.items_per_page + 1)

        self.prev_btn.configure(
            state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_btn.configure(
            state=tk.NORMAL
            if self.current_page < total_pages - 1 and items
            else tk.DISABLED
        )

        if items:
            start_idx = self.current_page * self.items_per_page + 1
            end_idx = min((self.current_page + 1) *
                          self.items_per_page, total_items)
            self.page_label.configure(
                text=f"Seite {self.current_page + 1}/{total_pages}\n"
                f"({start_idx}-{end_idx} von {total_items})"
            )
        else:
            self.page_label.configure(text="Keine Ergebnisse")

    # ... [Andere Methoden bleiben größtenteils unverändert] ...
