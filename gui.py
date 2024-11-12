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
from amazon_scraper import AmazonScraper

logger = logging.getLogger('EbayScraperGUI')

class EbayScraperGUI:
    def __init__(self, root, ebay_scraper, amazon_scraper):
        self.root = root
        self.ebay_scraper = ebay_scraper
        self.amazon_scraper = amazon_scraper
        self.setup_main_window()
        self.setup_variables()
        self.setup_styles()
        self.create_widgets()
        self.load_user_settings()
        self.current_column = 0
        self.current_row = 0
        logger.info("GUI wurde initialisiert")

    def setup_main_window(self):
        self.root.title("eBay & Amazon Artikel-Suche")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_variables(self):
        self.favorites = []
        self.current_ebay_results = []
        self.current_amazon_results = []
        self.search_active = False
        self.favorites_window = None
        
        self.search_var = tk.StringVar()
        self.min_price_var = tk.StringVar()
        self.max_price_var = tk.StringVar()
        self.condition_var = tk.StringVar(value="Alle")
        self.sort_var = tk.StringVar(value="Relevanz")
        self.progress_var = tk.IntVar(value=0)
        self.status_var = tk.StringVar(value="Bereit für die Suche")
        self.count_var = tk.StringVar(value="Gefundene Artikel: 0 (eBay), 0 (Amazon)")
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

    def create_main_frame(self):
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        header = ttk.Label(
            header_frame,
            text="eBay & Amazon Artikel-Suche",
            style="Header.TLabel"
        )
        header.pack(side=tk.LEFT, fill=tk.X, expand=True)

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

        search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=40,
            font=("Helvetica", 12)
        )
        search_entry.pack(side=tk.LEFT, padx=5)

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
        """Erstellt einen verbesserten scrollbaren Bereich für Suchergebnisse."""
        # Container für den scrollbaren Bereich
        self.results_container = ttk.Frame(parent)
        self.results_container.pack(fill=tk.BOTH, expand=True)
        
        # Erstelle Canvas mit fester Größe
        self.canvas = tk.Canvas(
            self.results_container,
            bg='white',
            width=400,  # Initiale Breite
            height=300   # Initiale Höhe
        )
        
        # Scrollbar erstellen
        self.scrollbar = ttk.Scrollbar(
            self.results_container,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        
        # Frame für die Ergebnisse
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame_id = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor=tk.NW,
            width=self.canvas.winfo_width()  # Wichtig: Setze initiale Breite
        )
        
        # Konfiguriere Canvas
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid-Konfiguration für responsives Layout
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(1, weight=1)
        
        # Binding für Größenänderungen
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.scrollable_frame.bind('<Configure>', self._on_frame_configure)
        
        # Binding für Mausrad
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind_all('<Button-4>', self._on_mousewheel)
        self.canvas.bind_all('<Button-5>', self._on_mousewheel)
        
        # Packen der Widgets
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _on_canvas_configure(self, event):
        """Handler für Canvas-Größenänderungen."""
        # Update die Breite des inneren Frames
        self.canvas.itemconfig(
            self.scrollable_frame_id,
            width=event.width
        )
        
    def _on_frame_configure(self, event):
        """Handler für Frame-Größenänderungen."""
        # Update die Scroll-Region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        
    def _on_mousewheel(self, event):
        """Verbesserte Mausrad-Unterstützung."""
        if not self.canvas.winfo_height():
            return
            
        try:
            # Identifiziere die Scrollrichtung basierend auf dem Event
            if event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1
            else:
                delta = event.delta

            # Normalisiere den Scroll-Delta
            scroll_amount = -1 * (delta/120)
            
            # Scrolle den Canvas
            self.canvas.yview_scroll(int(scroll_amount), "units")
        except Exception as e:
            logger.error(f"Fehler beim Scrollen: {e}")

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

    def create_favorites_window(self):
        if self.favorites_window is not None and self.favorites_window.winfo_exists():
            return

        try:
            self.favorites_window = tk.Toplevel(self.root)
            self.favorites_window.title("Favoriten")
            self.favorites_window.geometry("800x600")
            self.favorites_window.withdraw()
            
            self.favorites_window.protocol("WM_DELETE_WINDOW", self.hide_favorites)
            
            self.favorites_window.transient(self.root)

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
                columns=("Titel", "Preis", "Link", "Quelle"),
                show="headings",
                selectmode="extended"
            )
            self.favorites_tree.pack(fill=tk.BOTH, expand=True)

            scrollbar.config(command=self.favorites_tree.yview)
            self.favorites_tree.config(yscrollcommand=scrollbar.set)

            self.favorites_tree.heading("Titel", text="Titel")
            self.favorites_tree.heading("Preis", text="Preis")
            self.favorites_tree.heading("Link", text="Link")
            self.favorites_tree.heading("Quelle", text="Quelle")

            self.favorites_tree.column("Titel", width=400)
            self.favorites_tree.column("Preis", width=100)
            self.favorites_tree.column("Link", width=200)
            self.favorites_tree.column("Quelle", width=80)

            self.favorites_tree.bind("<Double-1>", self.on_favorite_double_click)
            
            self.create_context_menu()

        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Favoriten-Fensters: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Erstellen des Favoriten-Fensters:\n{str(e)}"
            )

    def create_context_menu(self):
        try:
            self.context_menu = tk.Menu(self.favorites_window, tearoff=0)
            self.context_menu.add_command(
                label="Öffnen in Browser",
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
        try:
            self.open_selected_favorite()
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Favoriten: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Öffnen des Favoriten:\n{str(e)}"
            )

    def open_selected_favorite(self):
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
        try:
            if self.favorites_window and self.favorites_window.winfo_exists():
                self.favorites_window.withdraw()
        except Exception as e:
            logger.error(f"Fehler beim Verbergen des Favoriten-Fensters: {e}")

    def delete_selected_favorites(self):
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
        try:
            count = len(self.favorites)
            self.favorites_count_var.set(f"Favoriten: {count}")
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren des Favoriten-Zählers: {e}")

    def start_search(self):
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
        try:
            params = {
                'keyword': keyword,
                'max_pages': CONFIG['DEFAULT_MAX_PAGES'],
                'min_price': self.min_price_var.get() or None,
                'max_price': self.max_price_var.get() or None,
                'condition': self.condition_var.get() if self.condition_var.get() != "Alle" else None
            }

            ebay_results = self.ebay_scraper.search(**params)
            amazon_results = self.amazon_scraper.search(**params)
            
            self.root.after(0, lambda: self.update_results(ebay_results, amazon_results))
            
        except Exception as e:
            logger.error(f"Fehler bei der Suche: {str(e)}")
            self.root.after(0, lambda: self.show_error(str(e)))
        finally:
            self.root.after(0, self.search_completed)

    def update_gui_before_search(self):
        try:
            self.search_button.state(['disabled'])
            self.progress_var.set(0)
            self.status_var.set("Suche läuft...")
            self.clear_results()
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der GUI: {e}")

    def update_results(self, ebay_results, amazon_results, skip_sort=False):
        try:
            self.current_ebay_results = ebay_results
            self.current_amazon_results = amazon_results
            self.clear_results()

            if not skip_sort:
                sorted_ebay_results = self._get_sorted_results(self.current_ebay_results)
                sorted_amazon_results = self._get_sorted_results(self.current_amazon_results)
            else:
                sorted_ebay_results = ebay_results
                sorted_amazon_results = amazon_results

            for item in sorted_ebay_results:
                self.create_result_card(item, "ebay")

            for item in sorted_amazon_results:
                self.create_result_card(item, "amazon")

            self.count_var.set(
                f"Gefundene Artikel: {len(ebay_results)} (eBay), {len(amazon_results)} (Amazon)"
            )
        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Ergebnisse: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Anzeigen der Ergebnisse:\n{str(e)}"
            )

    def sort_results(self, *args):
        try:
            if self.current_ebay_results or self.current_amazon_results:
                self.update_results(self.current_ebay_results, self.current_amazon_results, skip_sort=True)
        except Exception as e:
            logger.error(f"Fehler beim Sortieren der Ergebnisse: {e}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Sortieren der Ergebnisse:\n{str(e)}"
            )

    def _get_sorted_results(self, results):
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

    def create_result_card(self, item, source):
        """Erstellt eine Ergebniskarte mit verbessertem Layout."""
        try:
            if self.current_row >= 2:
                self.current_row = 0
                self.current_column += 2

            column = 0 if source == "ebay" else 1

            # Erstelle einen Container für die Karte
            card_container = ttk.Frame(self.scrollable_frame)
            card_container.grid(
                row=self.current_row,
                column=self.current_column + column,
                padx=10,
                pady=10,
                sticky="nsew"
            )
            card_container.columnconfigure(0, weight=1)

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
                text=item['title'],
                wraplength=300,  # Feste Breite für bessere Kontrolle
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

            # Button-Container
            button_frame = ttk.Frame(card)
            button_frame.grid(row=4, column=0, sticky="e", pady=(5, 0))

            # Buttons
            details_btn = ttk.Button(
                button_frame,
                text="Details",
                command=lambda link=item['link']: self.open_link(link),
                style="Action.TButton"
            )
            details_btn.pack(side=tk.LEFT, padx=2)

            favorite_btn = ttk.Button(
                button_frame,
                text="❤",
                command=lambda: self.add_favorite(item, source),
                style="Action.TButton"
            )
            favorite_btn.pack(side=tk.LEFT, padx=2)

            # Quelle
            source_label = ttk.Label(
                card,
                text=f"Quelle: {source.capitalize()}",
                font=("Helvetica", 10, "italic")
            )
            source_label.grid(row=5, column=0, sticky="w", pady=(5, 0))

            self.current_row += 1

            # Force update der Scrollregion
            self.scrollable_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Ergebniskarte: {e}")
            self.show_error(f"Fehler beim Anzeigen eines Ergebnisses: {str(e)}")

    def _create_details_button(self, parent, link):
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

    def _create_favorite_button(self, parent, item, source):
        try:
            def add_to_favorites():
                self.add_favorite(item, source)
            
            ttk.Button(
                parent,
                text="❤",
                command=add_to_favorites,
                style="Action.TButton"
            ).pack(side=tk.LEFT, padx=2)
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Favoriten-Buttons: {e}")

    def clear_results(self):
        """Verbesserte Methode zum Löschen der Ergebnisse."""
        try:
            # Lösche alle Widgets im scrollbaren Frame
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
                
            # Reset der Positionszähler
            self.current_row = 0
            self.current_column = 0
            
            # Reset der Scrollregion
            self.canvas.configure(scrollregion=(0, 0, 0, 0))
            
            # Force update
            self.canvas.update_idletasks()
            
        except Exception as e:
            logger.error(f"Fehler beim Löschen der Ergebnisse: {e}")

    def show_error(self, message):
        messagebox.showerror("Fehler", message)
        self.status_var.set(f"Fehler: {message}")

    def search_completed(self):
        try:
            self.search_active = False
            self.search_button.state(['!disabled'])
            self.status_var.set("Suche abgeschlossen")
            self.progress_var.set(100)
        except Exception as e:
            logger.error(f"Fehler beim Abschließen der Suche: {e}")

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
            logger.info("Benutzereinstellungen erfolgreich gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {str(e)}")
            messagebox.showerror(
                "Fehler",
                f"Die Einstellungen konnten nicht gespeichert werden:\n{str(e)}"
            )

    def on_closing(self):
        try:
            self.save_user_settings()
            
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
        ebay_scraper = EbayScraper()
        amazon_scraper = AmazonScraper()
        app = EbayScraperGUI(root, ebay_scraper, amazon_scraper)
        root.mainloop()
    except Exception as e:
        logger.critical(f"Kritischer Fehler in der Anwendung: {str(e)}")
        messagebox.showerror(
            "Kritischer Fehler",
            f"Die Anwendung wurde aufgrund eines kritischen Fehlers beendet:\n{str(e)}"
        )


