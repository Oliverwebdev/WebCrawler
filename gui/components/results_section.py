# gui/components/results_section.py

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import webbrowser

logger = logging.getLogger('ResultsSection')


class ResultsSection:
    def __init__(self, parent, sort_callback):
        """
        Initialisiert die Results Section.
        
        Args:
            parent: Übergeordnetes Tkinter-Widget
            sort_callback: Callback-Funktion für Sortierung
        """
        self.parent = parent
        self.sort_callback = sort_callback
        self.db_manager = None  # Wird von der Hauptanwendung gesetzt
        self.favorites = set()  # Set für schnellen Lookup
        self.current_items = []  # Speichert aktuelle Suchergebnisse
        self.external_double_click_callback = None
        self.create_widgets()

    def create_widgets(self):
        """Erstellt die GUI-Elemente für die Ergebnisanzeige."""
        # Hauptframe für Ergebnisse
        self.results_frame = ttk.LabelFrame(
            self.parent, text="Suchergebnisse", padding="5")
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Kontrollleiste (Sortierung und Filter)
        self.create_control_bar()

        # Ergebnisliste
        self.create_results_tree()

        # Konfiguriere Style für Favoriten
        self.configure_styles()

    def create_control_bar(self):
        """Erstellt die Kontrollleiste mit Sortierung und Filtern."""
        self.controls_frame = ttk.Frame(self.results_frame)
        self.controls_frame.pack(fill=tk.X, pady=(0, 5))

        # Linke Seite: Sortieroptionen
        sort_frame = ttk.Frame(self.controls_frame)
        sort_frame.pack(side=tk.LEFT)

        ttk.Label(sort_frame, text="Sortieren nach:").pack(side=tk.LEFT)
        self.sort_var = tk.StringVar(value="price")
        self.sort_combo = ttk.Combobox(
            sort_frame,
            textvariable=self.sort_var,
            values=["price", "title", "location"],
            state="readonly",
            width=15
        )
        self.sort_combo.pack(side=tk.LEFT, padx=5)
        self.sort_combo.bind('<<ComboboxSelected>>', self.on_sort)

        # Rechte Seite: Favoritenfilter
        filter_frame = ttk.Frame(self.controls_frame)
        filter_frame.pack(side=tk.RIGHT)

        self.show_favorites_var = tk.BooleanVar(value=False)
        self.favorites_filter = ttk.Checkbutton(
            filter_frame,
            text="Nur Favoriten anzeigen",
            variable=self.show_favorites_var,
            command=self.refresh_view
        )
        self.favorites_filter.pack(side=tk.RIGHT, padx=5)

    def create_results_tree(self):
        """Erstellt und konfiguriert den Treeview für Ergebnisse."""
        # Frame für Treeview und Scrollbars
        self.tree_frame = ttk.Frame(self.results_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        y_scrollbar = ttk.Scrollbar(self.tree_frame)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Treeview
        self.results_tree = ttk.Treeview(
            self.tree_frame,
            columns=(
                "favorite", "title", "price", "shipping",
                "location", "source", "link"
            ),
            show="headings",
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )

        # Scrollbar Konfiguration
        y_scrollbar.config(command=self.results_tree.yview)
        x_scrollbar.config(command=self.results_tree.xview)

        # Spalten konfigurieren
        self.configure_tree_columns()

        # Treeview platzieren
        self.results_tree.pack(fill=tk.BOTH, expand=True)

        # Event Bindings
        self.results_tree.bind('<Button-1>', self.on_click)
        self.results_tree.bind('<Return>', lambda e: self.open_selected_link())

    def bind_double_click(self, callback):
        """
        Bindet einen Callback an Doppelklick-Events.
        
        Args:
            callback: Funktion die bei Doppelklick aufgerufen wird
        """
        self.results_tree.bind('<Double-1>', callback)
        self.external_double_click_callback = callback

    def configure_tree_columns(self):
        """Konfiguriert die Spalten des Treeviews."""
        # Spaltenüberschriften
        columns = {
            "favorite": ("★", 30),
            "title": ("Titel", 300),
            "price": ("Preis", 100),
            "shipping": ("Versand", 150),
            "location": ("Standort", 150),
            "source": ("Quelle", 80),
            "link": ("Link", 0)  # Versteckte Spalte
        }

        for col, (heading, width) in columns.items():
            self.results_tree.heading(col, text=heading)
            min_width = 30 if col == "favorite" else width
            stretch = col != "favorite" and col != "link"
            self.results_tree.column(
                col,
                width=width,
                minwidth=min_width,
                stretch=stretch
            )

    def configure_styles(self):
        """Konfiguriert die visuellen Styles für den Treeview."""
        self.results_tree.tag_configure('favorite', background='#fff3e6')

    def set_db_manager(self, db_manager):
        """
        Setzt den Datenbankmanager und lädt initial die Favoriten.
        
        Args:
            db_manager: Instanz des DatabaseManagers
        """
        self.db_manager = db_manager
        self.load_favorites()

    def load_favorites(self):
        """Lädt die Favoriten aus der Datenbank."""
        if self.db_manager:
            try:
                favorites = self.db_manager.get_favorites()
                self.favorites = {fav['link'] for fav in favorites}
                logger.debug(f"Favoriten geladen: {
                             len(self.favorites)} Einträge")
            except Exception as e:
                logger.error(f"Fehler beim Laden der Favoriten: {e}")
                self.favorites = set()

    def on_click(self, event):
        """
        Behandelt Klicks auf die Treeview.
        
        Args:
            event: Tkinter Event-Objekt
        """
        region = self.results_tree.identify_region(event.x, event.y)
        if region == "cell":
            column = self.results_tree.identify_column(event.x)
            if column == "#1":  # Favoriten-Spalte
                item = self.results_tree.identify_row(event.y)
                self.toggle_favorite(item)

    def toggle_favorite(self, item_id):
        """
        Schaltet den Favoriten-Status eines Items um.
        
        Args:
            item_id: ID des Treeview-Items
        """
        if not self.db_manager:
            logger.warning("Kein Datenbankmanager verfügbar")
            return

        values = self.results_tree.item(item_id)['values']
        if not values:
            return

        link = values[6]  # Link ist an Index 6
        item_data = {
            'title': values[1],
            'price': values[2],
            'link': link,
            'source': values[5]
        }

        try:
            if link in self.favorites:
                # Entferne von Favoriten
                self.db_manager.delete_favorite(link)
                self.favorites.remove(link)
                self.results_tree.set(item_id, "favorite", "☆")
                # Entferne das favorite-Tag
                current_tags = list(self.results_tree.item(item_id, 'tags'))
                if 'favorite' in current_tags:
                    current_tags.remove('favorite')
                self.results_tree.item(item_id, tags=tuple(current_tags))
                messagebox.showinfo(
                    "Favoriten",
                    "Artikel wurde aus den Favoriten entfernt"
                )
            else:
                # Füge zu Favoriten hinzu
                self.db_manager.save_favorites([item_data])
                self.favorites.add(link)
                self.results_tree.set(item_id, "favorite", "★")
                # Füge das favorite-Tag hinzu
                current_tags = list(self.results_tree.item(item_id, 'tags'))
                if 'favorite' not in current_tags:
                    current_tags.append('favorite')
                self.results_tree.item(item_id, tags=tuple(current_tags))
                messagebox.showinfo(
                    "Favoriten",
                    "Artikel wurde zu den Favoriten hinzugefügt"
                )

            if self.show_favorites_var.get():
                self.refresh_view()

        except Exception as e:
            logger.error(f"Fehler beim Ändern des Favoritenstatus: {e}")
            messagebox.showerror(
                "Fehler",
                "Der Favoritenstatus konnte nicht geändert werden"
            )

    def clear_results(self):
        """Löscht alle Einträge aus der Ergebnisliste."""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.current_items = []

    def update_results(self, items):
        """
        Aktualisiert die Ergebnisliste mit neuen Items.
        
        Args:
            items: Liste der anzuzeigenden Items
        """
        self.clear_results()
        self.load_favorites()  # Aktualisiere Favoriten
        self.current_items = items

        try:
            for item in items:
                # Überspringe wenn nur Favoriten angezeigt werden sollen
                if self.show_favorites_var.get() and item['link'] not in self.favorites:
                    continue

                # Erstelle Tags für Favoriten
                tags = ('favorite',) if item['link'] in self.favorites else ()

                item_id = self.results_tree.insert(
                    "",
                    tk.END,
                    values=(
                        "★" if item['link'] in self.favorites else "☆",
                        item.get('title', ''),
                        item.get('price', ''),
                        item.get('shipping', ''),
                        item.get('location', ''),
                        item.get('source', ''),
                        item.get('link', '')
                    ),
                    tags=tags
                )

            logger.debug(f"{len(items)} Ergebnisse aktualisiert")

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Ergebnisse: {e}")
            messagebox.showerror(
                "Fehler",
                "Die Ergebnisse konnten nicht aktualisiert werden"
            )

    def refresh_view(self):
        """Aktualisiert die Ansicht basierend auf dem aktuellen Filter."""
        self.update_results(self.current_items)

    def on_sort(self, event=None):
        """
        Callback für Sortierung.
        
        Args:
            event: Optional - Tkinter Event-Objekt
        """
        try:
            sort_by = self.sort_var.get()
            self.sort_callback(sort_by)
        except Exception as e:
            logger.error(f"Fehler beim Sortieren: {e}")
            messagebox.showerror(
                "Fehler",
                "Die Ergebnisse konnten nicht sortiert werden"
            )

    def on_double_click(self, event):
        """
        Behandelt Doppelklick-Events.
        
        Args:
            event: Tkinter Event-Objekt
        """
        if self.external_double_click_callback:
            self.external_double_click_callback(event)
        else:
            self.open_selected_link()

    def open_selected_link(self):
        """Öffnet den Link des ausgewählten Items."""
        selection = self.results_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        values = self.results_tree.item(item_id)['values']
        if values:
            link = values[6]  # Link ist an Index 6
            try:
                webbrowser.open(link)
            except Exception as e:
                logger.error(f"Fehler beim Öffnen des Links: {e}")
                messagebox.showerror(
                    "Fehler",
                    "Der Link konnte nicht geöffnet werden"
                )

    def get_selected_item(self):
        """
        Gibt das ausgewählte Item zurück.
        
        Returns:
            dict: Item-Daten oder None wenn nichts ausgewählt
        """
        selection = self.results_tree.selection()
        if not selection:
            return None

        values = self.results_tree.item(selection[0])['values']
        if not values or len(values) < 7:
            return None

        return {
            'title': values[1],
            'price': values[2],
            'shipping': values[3],
            'location': values[4],
            'source': values[5],
            'link': values[6]
        }
