import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import webbrowser
from datetime import datetime
import json
import logging
from config import CONFIG
from utils import save_to_json, load_from_json
from ebay_scraper import EbayScraper

logger = logging.getLogger('EbayScraperGUI')

class EbayScraperGUI:
    def __init__(self, root):
        """Initialisiert die GUI mit dem Root-Fenster."""
        self.root = root
        self.setup_main_window()
        self.setup_variables()
        self.setup_styles()
        self.create_widgets()
        self.load_user_settings()
        self.current_column = 0
        self.current_row = 0
        logger.info("GUI wurde initialisiert")

    def setup_main_window(self):
        """Konfiguriert das Hauptfenster der Anwendung."""
        self.root.title("eBay Artikel-Suche")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_variables(self):
        """Initialisiert alle benötigten Variablen und Objekte."""
        self.scraper = EbayScraper()
        self.favorites = []
        self.current_results = []
        self.search_active = False
        self.favorites_window = None
        
        # Tkinter Variablen
        self.search_var = tk.StringVar()
        self.min_price_var = tk.StringVar()
        self.max_price_var = tk.StringVar()
        self.condition_var = tk.StringVar(value="Alle")
        self.sort_var = tk.StringVar(value="Relevanz")
        self.progress_var = tk.IntVar(value=0)
        self.status_var = tk.StringVar(value="Bereit für die Suche")
        self.count_var = tk.StringVar(value="Gefundene Artikel: 0")
        self.favorites_count_var = tk.StringVar(value="Favoriten: 0")

    def setup_styles(self):
        """Konfiguriert das Aussehen der GUI-Elemente."""
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Hauptframe Style
        self.style.configure(
            "Main.TFrame",
            background="#f0f0f0",
            padding=10
        )
        
        # Button Styles
        self.style.configure(
            "Action.TButton",
            padding=6,
            background="#4CAF50",
            foreground="white",
            font=("Helvetica", 12)
        )
        
        self.style.configure(
            "Favorites.TButton",
            padding=6,
            background="#FF69B4",
            foreground="white",
            font=("Helvetica", 12)
        )
        
        # Label Styles
        self.style.configure(
            "Info.TLabel",
            padding=6,
            font=("Helvetica", 12)
        )
        
        self.style.configure(
            "Header.TLabel",
            font=("Helvetica", 16, "bold"),
            background="#4CAF50",
            foreground="white",
            padding=10
        )
        
        # Card Style
        self.style.configure(
            "Card.TFrame",
            background="white",
            relief="raised",
            borderwidth=1,
            padding=10
        )

    def create_widgets(self):
        """Erstellt alle GUI-Elemente."""
        self.create_main_frame()
        self.create_search_section()
        self.create_results_section()
        self.create_status_bar()

    def create_main_frame(self):
        """Erstellt den Hauptframe der Anwendung."""
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header Frame mit Titel und Favoriten-Button
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        # Header
        header = ttk.Label(
            header_frame,
            text="eBay Artikel-Suche",
            style="Header.TLabel"
        )
        header.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Favoriten Button
        favorites_btn = ttk.Button(
            header_frame,
            text="❤ Favoriten",
            command=self.show_favorites,
            style="Favorites.TButton"
        )
        favorites_btn.pack(side=tk.RIGHT, padx=10)

    def create_search_section(self):
        """Erstellt den Suchbereich der Anwendung."""
        search_frame = ttk.LabelFrame(
            self.main_frame,
            text="Suchoptionen",
            padding=10
        )
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        # Suchleiste
        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=40,
            font=("Helvetica", 12)
        )
        search_entry.pack(side=tk.LEFT, padx=5)

        # Such-Button
        self.search_button = ttk.Button(
            search_frame,
            text="Suchen",
            command=self.start_search,
            style="Action.TButton"
        )
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.create_advanced_search_options(search_frame)

    def create_advanced_search_options(self, parent):
        """Erstellt erweiterte Suchoptionen."""
        options_frame = ttk.Frame(parent)
        options_frame.pack(side=tk.LEFT, padx=20)

        # Preisbereich
        price_frame = ttk.Frame(options_frame)
        price_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(price_frame, text="Preis von:").pack(side=tk.LEFT)
        ttk.Entry(
            price_frame, 
            textvariable=self.min_price_var, 
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(price_frame, text="bis:").pack(side=tk.LEFT)
        ttk.Entry(
            price_frame, 
            textvariable=self.max_price_var, 
            width=10
        ).pack(side=tk.LEFT, padx=5)

        # Artikelzustand
        condition_frame = ttk.Frame(options_frame)
        condition_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Label(condition_frame, text="Zustand:").pack(side=tk.LEFT)
        ttk.Combobox(
            condition_frame,
            textvariable=self.condition_var,
            values=["Alle", "Neu", "Gebraucht"],
            state="readonly",
            width=15
        ).pack(side=tk.LEFT, padx=5)

    def create_results_section(self):
        """Erstellt den Bereich für Suchergebnisse."""
        results_frame = ttk.LabelFrame(
            self.main_frame,
            text="Suchergebnisse",
            padding=10
        )
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.create_results_toolbar(results_frame)
        self.create_scrollable_results(results_frame)

    def create_results_toolbar(self, parent):
        """Erstellt die Toolbar für die Suchergebnisse."""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(toolbar, text="Sortierung:").pack(side=tk.LEFT)
        
        sort_combobox = ttk.Combobox(
            toolbar,
            textvariable=self.sort_var,
            values=["Relevanz", "Preis aufsteigend", "Preis absteigend"],
            state="readonly",
            width=20
        )
        sort_combobox.pack(side=tk.LEFT, padx=5)
        
        sort_combobox.bind('<<ComboboxSelected>>', self.sort_results)

        ttk.Label(
            toolbar,
            textvariable=self.count_var,
            font=("Helvetica", 12)
        ).pack(side=tk.RIGHT)

    def create_scrollable_results(self, parent):
        """Erstellt den scrollbaren Bereich für Suchergebnisse."""
        self.canvas = tk.Canvas(parent, bg='white')
        scrollbar = ttk.Scrollbar(
            parent,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor=tk.NW)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_status_bar(self):
        """Erstellt die Statusleiste."""
        status_bar = ttk.Frame(self.main_frame)
        status_bar.pack(fill=tk.X, pady=5)

        ttk.Progressbar(
            status_bar,
            variable=self.progress_var,
            length=200,
            mode='determinate'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Label(
            status_bar,
            textvariable=self.status_var
        ).pack(side=tk.LEFT, padx=5)

    def create_favorites_window(self):
        """Erstellt das Favoriten-Fenster."""
        if self.favorites_window is not None and self.favorites_window.winfo_exists():
            return

        try:
            self.favorites_window = tk.Toplevel(self.root)
            self.favorites_window.title("Favoriten")
            self.favorites_window.geometry("800x600")
            self.favorites_window.withdraw()
            
            # Handling für das Schließen des Fensters
            self.favorites_window.protocol("WM_DELETE_WINDOW", self.hide_favorites)
            
            # Verhindern, dass das Fenster als eigenständiges Fenster behandelt wird
            self.favorites_window.transient(self.root)

            favorites_frame = ttk.Frame(self.favorites_window, padding="10")
            favorites_frame.pack(fill=tk.BOTH, expand=True)

            # Toolbar
            toolbar = ttk.Frame(favorites_frame)
            toolbar.pack(fill=tk.X, pady=(0, 10))

            delete_btn = ttk.Button(
                toolbar,
                text="Ausgewählte löschen",
                command=self.delete_selected_favorites,
                style="Action.TButton"
            )
            delete_btn.pack(side=tk.LEFT, padx=5)

            delete_all_btn = ttk.Button(
                toolbar,
                text="Alle löschen",
                command=self.delete_all_favorites,
                style="Action.TButton"
            )
            delete_all_btn.pack(side=tk.LEFT, padx=5)

            ttk.Label(
                toolbar,
                textvariable=self.favorites_count_var,
                font=("Helvetica", 10)
            ).pack(side=tk.RIGHT, padx=5)

            # Treeview für Favoriten
            tree_frame = ttk.Frame(favorites_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            scrollbar = ttk.Scrollbar(tree_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            self.favorites_tree = ttk.Treeview(
                tree_frame,
                columns=("Titel", "Preis", "Link"),
                show="headings",
                selectmode="extended"
            )
            self.favorites_tree.pack(fill=tk.BOTH, expand=True)

            scrollbar.config(command=self.favorites_tree.yview)
            self.favorites_tree.config(yscrollcommand=scrollbar.set)

            # Spalten konfigurieren
            self.favorites_tree.heading("Titel", text="Titel")
            self.favorites_tree.heading("Preis", text="Preis")
            self.favorites_tree.heading("Link", text="Link")

            self.favorites_tree.column("Titel", width=400)
            self.favorites_tree.column("Preis", width=100)
            self.favorites_tree.column("Link", width=200)

            self.favorites_tree.bind("<Double-1>", self.on_favorite_double_click)
            
            self.create_context_menu()

        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Favoriten-Fensters: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Erstellen des Favoriten-Fensters:\n{str(e)}"
            )

    def create_context_menu(self):
        """Erstellt das Kontextmenü für die Favoriten."""
        try:
            self.context_menu = tk.Menu(self.favorites_window, tearoff=0)
            self.context_menu.add_command(
                label="Öffnen in eBay",
                command=lambda: self.open_selected_favorite()
            )
            self.context_menu.add_command(
                label="Löschen",
                command=self.delete_selected_favorites
            )
            
            self.favorites_tree.bind("<Button-3>", self.show_context_menu)
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Kontextmenüs: {e}")

    def show_context_menu(self, event):
        """Zeigt das Kontextmenü an der Mausposition."""
        try:
            self.favorites_tree.selection_set(
                self.favorites_tree.identify_row(event.y)
            )
            self.context_menu.tk_popup(event.x_root, event.y_root)
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen des Kontextmenüs: {e}")
        finally:
            self.context_menu.grab_release()

    def on_favorite_double_click(self, event):
        """Behandelt Doppelklick auf einen Favoriten."""
        try:
            self.open_selected_favorite()
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Favoriten: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Öffnen des Favoriten:\n{str(e)}"
            )

    def open_selected_favorite(self):
        """Öffnet den ausgewählten Favoriten im Browser."""
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

    def add_favorite(self, item):
        """Fügt einen Artikel zu den Favoriten hinzu."""
        try:
            favorite = (item['title'], item['price'], item['link'])
            if favorite not in self.favorites:
                self.favorites.append(favorite)
                
                # Stelle sicher, dass das Favoriten-Fenster existiert
                if not self.favorites_window or not self.favorites_window.winfo_exists():
                    self.create_favorites_window()
                    
                self.favorites_tree.insert("", tk.END, values=favorite)
                self.update_favorites_count()
                self.save_user_settings()
                
                messagebox.showinfo(
                    "Favorit hinzugefügt", 
                    "Der Artikel wurde zu deinen Favoriten hinzugefügt!"
                )
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Favoriten: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Hinzufügen zu Favoriten:\n{str(e)}"
            )

    def show_favorites(self):
        """Zeigt das Favoriten-Fenster an."""
        try:
            if not self.favorites_window or not self.favorites_window.winfo_exists():
                self.create_favorites_window()
            
            self.favorites_window.deiconify()
            self.favorites_window.lift()
            self.update_favorites_count()
            
        except Exception as e:
            logger.error(f"Fehler beim Anzeigen des Favoriten-Fensters: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Anzeigen der Favoriten:\n{str(e)}"
            )

    def hide_favorites(self):
        """Verbirgt das Favoriten-Fenster."""
        try:
            if self.favorites_window and self.favorites_window.winfo_exists():
                self.favorites_window.withdraw()
        except Exception as e:
            logger.error(f"Fehler beim Verbergen des Favoriten-Fensters: {e}")

    def delete_selected_favorites(self):
        """Löscht ausgewählte Favoriten."""
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
                
                self.update_favorites_count()
                self.save_user_settings()
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Favoriten: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Löschen der Favoriten:\n{str(e)}"
            )

    def delete_all_favorites(self):
        """Löscht alle Favoriten."""
        try:
            if messagebox.askyesno(
                "Bestätigung",
                "Möchten Sie wirklich alle Favoriten löschen?"
            ):
                self.favorites_tree.delete(*self.favorites_tree.get_children())
                self.favorites = []
                self.update_favorites_count()
                self.save_user_settings()
        except Exception as e:
            logger.error(f"Fehler beim Löschen aller Favoriten: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Löschen aller Favoriten:\n{str(e)}"
            )

    def update_favorites_count(self):
        """Aktualisiert den Favoriten-Zähler."""
        try:
            count = len(self.favorites)
            self.favorites_count_var.set(f"Favoriten: {count}")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Favoriten-Zählers: {e}")

    def start_search(self):
        """Startet die Suche."""
        if self.search_active:
            return

        try:
            keyword = self.search_var.get().strip()
            if not keyword:
                messagebox.showwarning(
                    "Warnung",
                    "Bitte geben Sie einen Suchbegriff ein!"
                )
                return

            self.search_active = True
            self.update_gui_before_search()
            
            # Starte Suche in separatem Thread
            thread = threading.Thread(target=self.perform_search, args=(keyword,))
            thread.daemon = True
            thread.start()
        except Exception as e:
            logger.error(f"Fehler beim Starten der Suche: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Starten der Suche:\n{str(e)}"
            )
            self.search_active = False

    def perform_search(self, keyword):
        """Führt die eigentliche Suche durch."""
        try:
            # Parameter vorbereiten
            params = {
                'keyword': keyword,
                'max_pages': CONFIG['DEFAULT_MAX_PAGES'],
                'min_price': self.min_price_var.get() or None,
                'max_price': self.max_price_var.get() or None,
                'condition': self.condition_var.get() if self.condition_var.get() != "Alle" else None
            }

            # Suche durchführen
            results = self.scraper.search(**params)
            
            # GUI aktualisieren
            self.root.after(0, lambda: self.update_results(results))
            
        except Exception as e:
            logger.error(f"Fehler bei der Suche: {str(e)}")
            self.root.after(0, lambda: self.show_error(str(e)))
        finally:
            self.root.after(0, self.search_completed)

    def update_gui_before_search(self):
        """Aktualisiert die GUI vor der Suche."""
        try:
            self.search_button.state(['disabled'])
            self.progress_var.set(0)
            self.status_var.set("Suche läuft...")
            self.clear_results()
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der GUI: {e}")

    def update_results(self, results, skip_sort=False):
        """Aktualisiert die Anzeige der Suchergebnisse."""
        try:
            self.current_results = results
            self.clear_results()

            # Nur sortieren wenn skip_sort False ist
            if not skip_sort:
                sorted_results = self._get_sorted_results(self.current_results)
            else:
                sorted_results = results

            # Ergebnisse anzeigen
            for item in sorted_results:
                self.create_result_card(item)

            self.count_var.set(f"Gefundene Artikel: {len(results)}")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Ergebnisse: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Anzeigen der Ergebnisse:\n{str(e)}"
            )

    def sort_results(self, *args):
        """Sortiert die Suchergebnisse neu."""
        try:
            if self.current_results:
                self.update_results(self.current_results, skip_sort=True)
        except Exception as e:
            logger.error(f"Fehler beim Sortieren der Ergebnisse: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Sortieren der Ergebnisse:\n{str(e)}"
            )

    def _get_sorted_results(self, results):
        """Sortiert die Ergebnisse basierend auf der ausgewählten Sortierung."""
        if not results:
            return []
        
        try:
            sorted_results = results.copy()
            sort_option = self.sort_var.get()
            
            if sort_option == "Preis aufsteigend":
                sorted_results.sort(key=lambda x: self.extract_price(x['price']))
            elif sort_option == "Preis absteigend":
                sorted_results.sort(key=lambda x: self.extract_price(x['price']), reverse=True)
                
            return sorted_results
        except Exception as e:
            logger.error(f"Fehler beim Sortieren: {e}")
            return results

    def create_result_card(self, item):
        """Erstellt eine Karte für ein einzelnes Suchergebnis."""
        try:
            if self.current_column >= 2:
                self.current_column = 0
                self.current_row += 1

            card = ttk.Frame(self.scrollable_frame, style="Card.TFrame")
            card.grid(row=self.current_row, column=self.current_column, 
                     padx=10, pady=10, sticky="nsew")

            card.grid_columnconfigure(0, weight=1)

            # Titel
            title_label = ttk.Label(
                card,
                text=item['title'],
                wraplength=400,
                font=("Helvetica", 12, "bold")
            )
            title_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

            # Preis
            price_label = ttk.Label(
                card,
                text=item['price'],
                font=("Helvetica", 12)
            )
            price_label.grid(row=1, column=0, sticky="w", pady=(0, 5))

            # Versand
            if 'shipping' in item:
                shipping_label = ttk.Label(
                    card,
                    text=f"Versand: {item['shipping']}"
                )
                shipping_label.grid(row=2, column=0, sticky="w", pady=(0, 5))

            # Standort
            if 'location' in item:
                location_label = ttk.Label(
                    card,
                    text=f"Standort: {item['location']}"
                )
                location_label.grid(row=3, column=0, sticky="w", pady=(0, 5))

            # Buttons
            button_frame = ttk.Frame(card)
            button_frame.grid(row=4, column=0, sticky="e", pady=(5, 0))

            self._create_details_button(button_frame, item['link'])
            self._create_favorite_button(button_frame, item)

            self.current_column += 1

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Ergebniskarte: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Erstellen der Ergebniskarte:\n{str(e)}"
            )

    def _create_details_button(self, parent, link):
        """Erstellt einen Button zum Öffnen des Artikels."""
        try:
            def open_link():
                webbrowser.open(link)
            
            ttk.Button(
                parent,
                text="Details",
                command=open_link,
                style="Action.TButton"
            ).pack(side=tk.LEFT, padx=2)
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Detail-Buttons: {e}")

    def _create_favorite_button(self, parent, item):
        """Erstellt einen Button zum Hinzufügen zu Favoriten."""
        try:
            def add_to_favorites():
                self.add_favorite(item)
            
            ttk.Button(
                parent,
                text="❤",
                command=add_to_favorites,
                style="Action.TButton"
            ).pack(side=tk.LEFT, padx=2)
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Favoriten-Buttons: {e}")

    def clear_results(self):
        """Löscht alle Suchergebnisse aus der Anzeige."""
        try:
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            self.current_row = 0
            self.current_column = 0
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Ergebnisse: {e}")

    def show_error(self, message):
        """Zeigt eine Fehlermeldung an."""
        messagebox.showerror("Fehler", message)
        self.status_var.set(f"Fehler: {message}")

    def search_completed(self):
        """Wird aufgerufen, wenn die Suche abgeschlossen ist."""
        try:
            self.search_active = False
            self.search_button.state(['!disabled'])
            self.status_var.set("Suche abgeschlossen")
            self.progress_var.set(100)
        except Exception as e:
            logger.error(f"Fehler beim Abschließen der Suche: {e}")

    def extract_price(self, price_str):
        """Extrahiert den numerischen Preis aus einem Preis-String."""
        try:
            clean_price = ''.join(c for c in price_str if c.isdigit() or c in '.,')
            clean_price = clean_price.replace(',', '.')
            return float(clean_price)
        except (ValueError, AttributeError, TypeError) as e:
            logger.error(f"Fehler bei der Preisextraktion für {price_str}: {e}")
            return 0.0

    def load_user_settings(self):
        """Lädt die gespeicherten Benutzereinstellungen."""
        try:
            data = load_from_json(CONFIG['SETTINGS_FILE'])
            if data:
                self.settings = data.get('settings', {})
                self.favorites = data.get('favorites', [])
                
                # Favoriten in TreeView laden
                if not self.favorites_window or not self.favorites_window.winfo_exists():
                    self.create_favorites_window()
                
                for favorite in self.favorites:
                    self.favorites_tree.insert("", tk.END, values=favorite)
                    
                self.update_favorites_count()
            else:
                self.settings = {
                    'max_pages': CONFIG['DEFAULT_MAX_PAGES'],
                    'default_search_period': CONFIG['DEFAULT_SEARCH_PERIOD']
                }
                self.favorites = []
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Einstellungen: {str(e)}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Laden der Einstellungen:\n{str(e)}"
            )
            # Standardeinstellungen verwenden
            self.settings = {
                'max_pages': CONFIG['DEFAULT_MAX_PAGES'],
                'default_search_period': CONFIG['DEFAULT_SEARCH_PERIOD']
            }
            self.favorites = []

    def save_user_settings(self):
        """Speichert die Benutzereinstellungen."""
        try:
            data = {
                'settings': self.settings,
                'favorites': self.favorites
            }
            save_to_json(data, CONFIG['SETTINGS_FILE'])
            logger.info("Benutzereinstellungen erfolgreich gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {str(e)}")
            messagebox.showerror(
                "Fehler",
                f"Die Einstellungen konnten nicht gespeichert werden:\n{str(e)}"
            )

    def on_closing(self):
        """Wird beim Schließen der Anwendung aufgerufen."""
        try:
            self.save_user_settings()
            
            # Cleanup des Favoriten-Fensters
            if self.favorites_window and self.favorites_window.winfo_exists():
                self.favorites_window.destroy()
                
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"Fehler beim Schließen der Anwendung: {str(e)}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Speichern der Einstellungen:\n{str(e)}"
            )
            self.root.destroy()

if __name__ == "__main__":
    # Logging-Konfiguration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ebay_scraper.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        root = tk.Tk()
        app = EbayScraperGUI(root)
        root.mainloop()
    except Exception as e:
        logger.critical(f"Kritischer Fehler in der Anwendung: {str(e)}")
        messagebox.showerror(
            "Kritischer Fehler",
            f"Die Anwendung wurde aufgrund eines kritischen Fehlers beendet:\n{str(e)}"
        )