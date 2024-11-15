import tkinter as tk
from tkinter import ttk
import logging
from .result_card import ResultCard

logger = logging.getLogger('PaginatedResultView')


class PaginatedResultView:
    def __init__(self, parent, source):
        """
        Initialisiert eine paginierte Ergebnisansicht.
        
        Args:
            parent: Übergeordnetes Widget
            source: Quelle der Ergebnisse ("ebay" oder "amazon")
        """
        self.parent = parent
        self.source = source
        self.current_page = 0
        self.items_per_page = 10
        self.all_items = []
        self.current_cards = []
        self.on_favorite_click = None
        self.on_details_click = None
        self.setup_ui()

    def setup_ui(self):
        """Erstellt das UI-Layout für die paginierte Ansicht."""
        self.frame = ttk.Frame(self.parent)

        # Header mit Titel und Seitennavigation
        header = ttk.Frame(self.frame)
        header.pack(fill=tk.X, pady=(0, 5))

        # Plattform-Label mit Icon
        icon_text = "🏪" if self.source == "ebay" else "📦"
        title_text = f"{icon_text} {self.source.upper()} Ergebnisse"

        ttk.Label(
            header,
            text=title_text,
            font=("Helvetica", 12, "bold")
        ).pack(side=tk.LEFT)

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

        # Scrollbarer Container für Ergebniskarten
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

        # Mausrad-Binding
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_canvas_configure(self, event):
        """Passt die Breite des Frames an die Canvas-Breite an."""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _on_mousewheel(self, event):
        """Behandelt Mausrad-Events für das Scrollen."""
        if not self.canvas.winfo_height():
            return

        try:
            if event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1
            else:
                delta = -1 * (event.delta // 120)

            self.canvas.yview_scroll(int(delta), "units")
        except Exception as e:
            logger.error(f"Fehler beim Scrollen: {e}")

    def set_items(self, items):
        """
        Setzt die anzuzeigenden Items und aktualisiert die Ansicht.
        
        Args:
            items: Liste der anzuzeigenden Items
        """
        self.all_items = items
        self.current_page = 0
        self.update_page()
        self.update_navigation()

    def clear(self):
        """Löscht alle angezeigten Karten und setzt Status zurück."""
        self._clear_current_cards()
        self.all_items = []
        self.current_page = 0
        self.update_navigation()

    def _clear_current_cards(self):
        """Entfernt aktuelle Ergebniskarten und gibt Speicher frei."""
        for card in self.current_cards:
            if card.winfo_exists():
                card.destroy()
        self.current_cards = []

        # Force garbage collection für widgets
        for widget in self.results_frame.winfo_children():
            widget.destroy()

    def update_page(self):
        """Aktualisiert die Anzeige der aktuellen Seite."""
        self._clear_current_cards()

        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        current_items = self.all_items[start_idx:end_idx]

        for idx, item in enumerate(current_items):
            try:
                card = ResultCard(
                    self.results_frame,
                    item,
                    self.source,
                    self.on_favorite_click,
                    self.on_details_click
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

    def update_navigation(self):
        """Aktualisiert den Zustand der Navigationsbuttons."""
        total_pages = max(1, (len(self.all_items) - 1) //
                          self.items_per_page + 1)

        self.prev_btn.configure(
            state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_btn.configure(
            state=tk.NORMAL
            if self.current_page < total_pages - 1 and self.all_items
            else tk.DISABLED
        )

        if self.all_items:
            start_idx = self.current_page * self.items_per_page + 1
            end_idx = min((self.current_page + 1) *
                          self.items_per_page, len(self.all_items))
            self.page_label.configure(
                text=f"Seite {
                    self.current_page + 1}/{total_pages}\n({start_idx}-{end_idx} von {len(self.all_items)})"
            )
        else:
            self.page_label.configure(text="Keine Ergebnisse")

    def next_page(self):
        """Wechselt zur nächsten Seite."""
        if (self.current_page + 1) * self.items_per_page < len(self.all_items):
            self.current_page += 1
            self.update_page()
            self.update_navigation()

    def prev_page(self):
        """Wechselt zur vorherigen Seite."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()
            self.update_navigation()

    def get_frame(self):
        """Gibt das Haupt-Frame zurück."""
        return self.frame

    def set_callbacks(self, on_favorite_click, on_details_click):
        """Setzt die Callback-Funktionen für die Ergebniskarten."""
        self.on_favorite_click = on_favorite_click
        self.on_details_click = on_details_click
