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
        self.root.title("eBay Artikel-Suche")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_variables(self):
        self.scraper = EbayScraper()
        self.favorites = []
        self.current_results = []
        self.search_active = False
        
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
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure(
            "Main.TFrame",
            background="#f0f0f0",
            padding=10
        )
        
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
        
        self.style.configure(
            "Card.TFrame",
            background="white",
            relief="raised",
            borderwidth=1,
            padding=10
        )

    def create_widgets(self):
        self.create_main_frame()
        self.create_search_section()
        self.create_results_section()
        self.create_status_bar()
        self.create_favorites_window()

    def create_main_frame(self):
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
        results_frame = ttk.LabelFrame(
            self.main_frame,
            text="Suchergebnisse",
            padding=10
        )
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.create_results_toolbar(results_frame)
        self.create_scrollable_results(results_frame)

    def create_results_toolbar(self, parent):
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
    
    def start_search(self):
        """Startet die Suche."""
        if self.search_active:
            return

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
        self.search_button.state(['disabled'])
        self.progress_var.set(0)
        self.status_var.set("Suche läuft...")
        self.clear_results()

    def update_results(self, results, skip_sort=False):
        """Aktualisiert die Anzeige der Suchergebnisse."""
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

    def sort_results(self, *args):
        """Wird aufgerufen, wenn sich die Sortierung ändert."""
        if self.current_results:
            # Ergebnisse neu sortieren und anzeigen, ohne erneute Sortierung auszulösen
            self.update_results(self.current_results, skip_sort=True)

    def _get_sorted_results(self, results):
        """Sortiert die Ergebnisse basierend auf der ausgewählten Sortierung."""
        if not results:
            return []
        
        sorted_results = results.copy()
        sort_option = self.sort_var.get()
        
        try:
            if sort_option == "Preis aufsteigend":
                sorted_results.sort(key=lambda x: self.extract_price(x['price']))
            elif sort_option == "Preis absteigend":
                sorted_results.sort(key=lambda x: self.extract_price(x['price']), reverse=True)
        except Exception as e:
            logger.error(f"Fehler beim Sortieren: {e}")
            
        return sorted_results

    def create_favorites_window(self):
        self.favorites_window = tk.Toplevel(self.root)
        self.favorites_window.title("Favoriten")
        self.favorites_window.geometry("800x600")
        self.favorites_window.withdraw()

        favorites_frame = ttk.Frame(self.favorites_window, padding="10")
        favorites_frame.pack(fill=tk.BOTH, expand=True)

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

        self.favorites_tree.heading("Titel", text="Titel")
        self.favorites_tree.heading("Preis", text="Preis")
        self.favorites_tree.heading("Link", text="Link")

        self.favorites_tree.column("Titel", width=400)
        self.favorites_tree.column("Preis", width=100)
        self.favorites_tree.column("Link", width=200)

        self.favorites_tree.bind("<Double-1>", self.on_favorite_double_click)
        
        self.create_context_menu()

    def create_context_menu(self):
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

    def show_context_menu(self, event):
        try:
            self.favorites_tree.selection_set(
                self.favorites_tree.identify_row(event.y)
            )
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def on_favorite_double_click(self, event):
        self.open_selected_favorite()

    def open_selected_favorite(self):
        selected = self.favorites_tree.selection()
        if not selected:
            return
            
        item = self.favorites_tree.item(selected[0])
        link = item['values'][2]
        if link:
            webbrowser.open(link)

    def add_favorite(self, item):
        favorite = (item['title'], item['price'], item['link'])
        if favorite not in self.favorites:
            self.favorites.append(favorite)
            self.favorites_tree.insert(
                "", tk.END,
                values=(item['title'], item['price'], item['link'])
            )
            self.update_favorites_count()
            self.save_user_settings()
            messagebox.showinfo(
                "Favorit hinzugefügt", 
                "Der Artikel wurde zu deinen Favoriten hinzugefügt!"
            )

    def show_favorites(self):
        self.favorites_window.deiconify()
        self.favorites_window.lift()
        self.update_favorites_count()

    def delete_selected_favorites(self):
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

    def delete_all_favorites(self):
        if messagebox.askyesno(
            "Bestätigung",
            "Möchten Sie wirklich alle Favoriten löschen?"
        ):
            self.favorites_tree.delete(*self.favorites_tree.get_children())
            self.favorites = []
            self.update_favorites_count()
            self.save_user_settings()

    def update_favorites_count(self):
        count = len(self.favorites)
        self.favorites_count_var.set(f"Favoriten: {count}")

    def create_result_card(self, item):
        try:
            if self.current_column >= 2:
                self.current_column = 0
                self.current_row += 1

            card = ttk.Frame(self.scrollable_frame, style="Card.TFrame")
            card.grid(row=self.current_row, column=self.current_column, 
                     padx=10, pady=10, sticky="nsew")

            card.grid_columnconfigure(0, weight=1)

            title_label = ttk.Label(
                card,
                text=item['title'],
                wraplength=400,
                font=("Helvetica", 12, "bold")
            )
            title_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

            price_label = ttk.Label(
                card,
                text=item['price'],
                font=("Helvetica", 12)
            )
            price_label.grid(row=1, column=0, sticky="w", pady=(0, 5))

            if 'shipping' in item:
                shipping_label = ttk.Label(
                    card,
                    text=f"Versand: {item['shipping']}"
                )
                shipping_label.grid(row=2, column=0, sticky="w", pady=(0, 5))

            if 'location' in item:
                location_label = ttk.Label(
                    card,
                    text=f"Standort: {item['location']}"
                )
                location_label.grid(row=3, column=0, sticky="w", pady=(0, 5))

            button_frame = ttk.Frame(card)
            button_frame.grid(row=4, column=0, sticky="e", pady=(5, 0))

            self._create_details_button(button_frame, item['link'])
            self._create_favorite_button(button_frame, item)

            self.current_column += 1

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Ergebniskarte: {e}")

    def _create_details_button(self, parent, link):
        def open_link():
            webbrowser.open(link)
        
        ttk.Button(
            parent,
            text="Details",
            command=open_link,
            style="Action.TButton"
        ).pack(side=tk.LEFT, padx=2)

    def _create_favorite_button(self, parent, item):
        def add_to_favorites():
            self.add_favorite(item)
        
        ttk.Button(
            parent,
            text="❤",
            command=add_to_favorites,
            style="Action.TButton"
        ).pack(side=tk.LEFT, padx=2)

    def clear_results(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.current_row = 0
        self.current_column = 0

    def show_error(self, message):
        messagebox.showerror("Fehler", message)
        self.status_var.set(f"Fehler: {message}")

    def search_completed(self):
        self.search_active = False
        self.search_button.state(['!disabled'])
        self.status_var.set("Suche abgeschlossen")
        self.progress_var.set(100)

    def extract_price(self, price_str):
        try:
            clean_price = ''.join(c for c in price_str if c.isdigit() or c in '.,')
            clean_price = clean_price.replace(',', '.')
            return float(clean_price)
        except (ValueError, AttributeError, TypeError) as e:
            logger.error(f"Fehler bei der Preisextraktion für {price_str}: {e}")
            return 0.0

    def load_user_settings(self):
        try:
            data = load_from_json(CONFIG['SETTINGS_FILE'])
            if data:
                self.settings = data.get('settings', {})
                self.favorites = data.get('favorites', [])
                
                # Favoriten in TreeView laden
                for favorite in self.favorites:
                    self.favorites_tree.insert(
                        "", tk.END, values=favorite)  # Jetzt werden alle drei Werte geladen
                    
                self.update_favorites_count()
            else:
                self.settings = {
                    'max_pages': CONFIG['DEFAULT_MAX_PAGES'],
                    'default_search_period': CONFIG['DEFAULT_SEARCH_PERIOD']
                }
                self.favorites = []
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Einstellungen: {str(e)}")
            self.settings = {
                'max_pages': CONFIG['DEFAULT_MAX_PAGES'],
                'default_search_period': CONFIG['DEFAULT_SEARCH_PERIOD']
            }
            self.favorites = []

    def save_user_settings(self):
        try:
            data = {
                'settings': self.settings,
                'favorites': self.favorites
            }
            save_to_json(data, CONFIG['SETTINGS_FILE'])
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {str(e)}")
            messagebox.showerror(
                "Fehler",
                "Die Einstellungen konnten nicht gespeichert werden."
            )

    def on_closing(self):
        try:
            self.save_user_settings()
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {str(e)}")
        finally:
            self.root.destroy()