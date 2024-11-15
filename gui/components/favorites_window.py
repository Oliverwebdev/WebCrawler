# gui/components/favorites_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging

logger = logging.getLogger('FavoritesWindow')


class FavoritesWindow:
    def __init__(self, parent, db_manager):
        """
        Initialisiert das Favoriten-Fenster.
        
        Args:
            parent: Übergeordnetes Tkinter-Widget
            db_manager: Datenbankmanager-Instanz
        """
        self.parent = parent
        self.db_manager = db_manager
        self.window = None

    def show(self):
        """Zeigt das Favoriten-Fenster an."""
        if self.window is not None:
            self.window.lift()
            return

        self.window = tk.Toplevel(self.parent)
        self.window.title("Favoriten")
        self.window.geometry("600x400")
        self.window.transient(self.parent)

        self.create_widgets()
        self.load_favorites()

        def on_closing():
            self.window.destroy()
            self.window = None

        self.window.protocol("WM_DELETE_WINDOW", on_closing)

    def create_widgets(self):
        """Erstellt die GUI-Elemente."""
        # Toolbar
        toolbar = ttk.Frame(self.window)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(
            toolbar,
            text="Aktualisieren",
            command=self.load_favorites
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            toolbar,
            text="Ausgewählte löschen",
            command=self.delete_selected
        ).pack(side=tk.LEFT, padx=5)

        # Treeview
        self.tree_frame = ttk.Frame(self.window)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("title", "price", "source"),
            show="headings"
        )

        # Scrollbars
        y_scrollbar = ttk.Scrollbar(
            self.tree_frame,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(
            self.tree_frame,
            orient=tk.HORIZONTAL,
            command=self.tree.xview
        )
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.configure(
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )

        # Spalten konfigurieren
        self.tree.heading("title", text="Titel")
        self.tree.heading("price", text="Preis")
        self.tree.heading("source", text="Quelle")

        self.tree.column("title", width=300)
        self.tree.column("price", width=100)
        self.tree.column("source", width=100)

        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind('<Double-1>', self.on_double_click)

    def load_favorites(self):
        """Lädt die Favoriten aus der Datenbank."""
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            favorites = self.db_manager.get_favorites()
            for fav in favorites:
                self.tree.insert(
                    "",
                    tk.END,
                    values=(fav['title'], fav['price'], fav['source']),
                    tags=(fav['link'],)
                )

        except Exception as e:
            logger.error(f"Fehler beim Laden der Favoriten: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Laden der Favoriten: {str(e)}"
            )

    def delete_selected(self):
        """Löscht die ausgewählten Favoriten."""
        selection = self.tree.selection()
        if not selection:
            return

        if messagebox.askyesno(
            "Löschen bestätigen",
            "Möchten Sie die ausgewählten Favoriten wirklich löschen?"
        ):
            try:
                for item in selection:
                    link = self.tree.item(item)['tags'][0]
                    self.db_manager.delete_favorite(link)
                    self.tree.delete(item)
            except Exception as e:
                logger.error(f"Fehler beim Löschen der Favoriten: {e}")
                messagebox.showerror(
                    "Fehler",
                    f"Fehler beim Löschen der Favoriten: {str(e)}"
                )

    def on_double_click(self, event):
        """Öffnet den Link bei Doppelklick."""
        item = self.tree.selection()[0]
        link = self.tree.item(item)['tags'][0]
        try:
            import webbrowser
            webbrowser.open(link)
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Links: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Öffnen des Links: {str(e)}"
            )
