import tkinter as tk
from tkinter import ttk, messagebox
import logging
import webbrowser

logger = logging.getLogger('FavoritesWindow')


class FavoritesWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.favorites = []
        self.favorites_tree = None
        self.favorites_count_var = tk.StringVar(value="Favoriten: 0")
        self.context_menu = None

    def show(self):
        if not self.window or not self.window.winfo_exists():
            self.create_window()
        self.window.deiconify()
        self.window.lift()
        self.update_count()

    def hide(self):
        if self.window and self.window.winfo_exists():
            self.window.withdraw()

    def create_window(self):
        try:
            self.window = tk.Toplevel(self.parent)
            self.window.title("Favoriten")
            self.window.geometry("800x600")
            self.window.withdraw()
            self.window.protocol("WM_DELETE_WINDOW", self.hide)
            self.window.transient(self.parent)

            self.create_content()
            self.create_context_menu()

        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Favoriten-Fensters: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Erstellen des Favoriten-Fensters:\n{str(e)}"
            )

    def create_content(self):
        favorites_frame = ttk.Frame(self.window, padding="10")
        favorites_frame.pack(fill=tk.BOTH, expand=True)

        self.create_toolbar(favorites_frame)
        self.create_tree(favorites_frame)

    def create_toolbar(self, parent):
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        delete_btn = ttk.Button(
            toolbar,
            text="Ausgewählte löschen",
            command=self.delete_selected,
            style="Action.TButton"
        )
        delete_btn.pack(side=tk.LEFT, padx=5)

        delete_all_btn = ttk.Button(
            toolbar,
            text="Alle löschen",
            command=self.delete_all,
            style="Action.TButton"
        )
        delete_all_btn.pack(side=tk.LEFT, padx=5)

        ttk.Label(
            toolbar,
            textvariable=self.favorites_count_var,
            font=("Helvetica", 10)
        ).pack(side=tk.RIGHT, padx=5)

    def create_tree(self, parent):
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.favorites_tree = ttk.Treeview(
            tree_frame,
            columns=("Titel", "Preis", "Link", "Quelle"),
            show="headings",
            selectmode="extended"
        )
        self.favorites_tree.pack(fill=tk.BOTH, expand=True)

        scrollbar.config(command=self.favorites_tree.yview)
        self.favorites_tree.config(yscrollcommand=scrollbar.set)

        # Spalten konfigurieren
        columns = {
            "Titel": 400,
            "Preis": 100,
            "Link": 200,
            "Quelle": 80
        }

        for col, width in columns.items():
            self.favorites_tree.heading(col, text=col)
            self.favorites_tree.column(col, width=width)

        self.favorites_tree.bind("<Double-1>", self.on_double_click)

    def create_context_menu(self):
        try:
            self.context_menu = tk.Menu(self.window, tearoff=0)
            self.context_menu.add_command(
                label="Öffnen in Browser",
                command=self.open_selected
            )
            self.context_menu.add_command(
                label="Löschen",
                command=self.delete_selected
            )

            self.favorites_tree.bind("<Button-3>", self.show_context_menu)
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Kontextmenüs: {e}")

    def show_context_menu(self, event):
        try:
            self.favorites_tree.selection_set(
                self.favorites_tree.identify_row(event.y)
            )
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen des Kontextmenüs: {e}")
        finally:
            self.context_menu.grab_release()

    def on_double_click(self, event):
        try:
            self.open_selected()
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Favoriten: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Öffnen des Favoriten:\n{str(e)}"
            )

    def open_selected(self):
        try:
            selected = self.favorites_tree.selection()
            if not selected:
                return

            item = self.favorites_tree.item(selected[0])
            link = item['values'][2]
            if link:
                webbrowser.open(link)
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Links: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Öffnen des Links:\n{str(e)}"
            )

    def add_favorite(self, item, source):
        try:
            favorite = (item['title'], item['price'], item['link'], source)
            if favorite not in self.favorites:
                self.favorites.append(favorite)

                if not self.window or not self.window.winfo_exists():
                    self.create_window()

                self.favorites_tree.insert("", tk.END, values=favorite)
                self.update_count()

                messagebox.showinfo(
                    "Favorit hinzugefügt",
                    "Der Artikel wurde zu deinen Favoriten hinzugefügt!"
                )

                return True
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Favoriten: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Hinzufügen zu Favoriten:\n{str(e)}"
            )
        return False

    def delete_selected(self):
        try:
            selected = self.favorites_tree.selection()
            if not selected:
                return

            if messagebox.askyesno(
                "Löschen bestätigen",
                "Möchten Sie die ausgewählten Favoriten wirklich löschen?"
            ):
                for item_id in selected:
                    values = self.favorites_tree.item(item_id)['values']
                    self.favorites = [
                        fav for fav in self.favorites
                        if fav[0] != values[0]
                    ]
                    self.favorites_tree.delete(item_id)

                self.update_count()
                return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Favoriten: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Löschen der Favoriten:\n{str(e)}"
            )
        return False

    def delete_all(self):
        try:
            if messagebox.askyesno(
                "Bestätigung",
                "Möchten Sie wirklich alle Favoriten löschen?"
            ):
                self.favorites_tree.delete(*self.favorites_tree.get_children())
                self.favorites = []
                self.update_count()
                return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen aller Favoriten: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Löschen aller Favoriten:\n{str(e)}"
            )
        return False

    def update_count(self):
        try:
            count = len(self.favorites)
            self.favorites_count_var.set(f"Favoriten: {count}")
        except Exception as e:
            logger.error(
                f"Fehler beim Aktualisieren des Favoriten-Zählers: {e}")

    def get_favorites(self):
        return self.favorites

    def load_favorites(self, favorites):
        try:
            self.favorites = favorites
            if not self.window or not self.window.winfo_exists():
                self.create_window()

            # Lösche bestehende Einträge
            self.favorites_tree.delete(*self.favorites_tree.get_children())

            # Füge neue Einträge hinzu
            for favorite in self.favorites:
                self.favorites_tree.insert("", tk.END, values=favorite)

            self.update_count()
        except Exception as e:
            logger.error(f"Fehler beim Laden der Favoriten: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Laden der Favoriten:\n{str(e)}"
            )
