import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import webbrowser
from datetime import datetime
from config import CONFIG
from utils.utils import save_to_json, load_from_json
from .components.search_section import SearchSection
from .components.results_section import ResultsSection
from .components.favorites_window import FavoritesWindow
from .components.status_bar import StatusBar

logger = logging.getLogger('EbayScraperGUI')


class EbayScraperGUI:
    def __init__(self, root, ebay_scraper, amazon_scraper):
        self.root = root
        self.ebay_scraper = ebay_scraper
        self.amazon_scraper = amazon_scraper
        self.search_active = False
        self.current_ebay_results = []
        self.current_amazon_results = []

        self.setup_main_window()
        self.setup_styles()
        self.create_components()
        self.load_user_settings()

        logger.info("GUI wurde initialisiert")

    def setup_main_window(self):
        self.root.title("eBay & Amazon Artikel-Suche")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Main Frame
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        styles = {
            "Main.TFrame": {
                "configure": {"background": "#f0f0f0", "padding": 10}
            },
            "Action.TButton": {
                "configure": {
                    "padding": 6,
                    "background": "#4CAF50",
                    "foreground": "white",
                    "font": ("Helvetica", 12)
                }
            },
            "Favorites.TButton": {
                "configure": {
                    "padding": 6,
                    "background": "#FF69B4",
                    "foreground": "white",
                    "font": ("Helvetica", 12)
                }
            },
            "Info.TLabel": {
                "configure": {"padding": 6, "font": ("Helvetica", 12)}
            },
            "Header.TLabel": {
                "configure": {
                    "font": ("Helvetica", 16, "bold"),
                    "background": "#4CAF50",
                    "foreground": "white",
                    "padding": 10
                }
            },
            "Card.TFrame": {
                "configure": {
                    "background": "white",
                    "relief": "raised",
                    "borderwidth": 1,
                    "padding": 10
                }
            }
        }

        for style_name, style_opts in styles.items():
            self.style.configure(style_name, **style_opts["configure"])

    def create_components(self):
        # Header
        self.create_header()

        # Search Section
        self.search_section = SearchSection(
            self.main_frame,
            self.start_search
        )

        # Results Section
        self.results_section = ResultsSection(
            self.main_frame,
            self.sort_results
        )

        # Status Bar
        self.status_bar = StatusBar(self.main_frame)

        # Favorites Window
        self.favorites_window = FavoritesWindow(self.root)

    def create_header(self):
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

    def start_search(self, search_params):
        if self.search_active:
            return

        try:
            keyword = search_params['keyword']
            if not keyword:
                messagebox.showwarning(
                    "Warnung",
                    "Bitte geben Sie einen Suchbegriff ein!"
                )
                return

            self.search_active = True
            self.update_gui_before_search()

            thread = threading.Thread(
                target=self.perform_search,
                args=(search_params,)
            )
            thread.daemon = True
            thread.start()

        except Exception as e:
            logger.error(f"Fehler beim Starten der Suche: {e}")
            self.show_error(f"Fehler beim Starten der Suche:\n{str(e)}")
            self.search_active = False

    def perform_search(self, search_params):
        try:
            ebay_results = self.ebay_scraper.search(**search_params)
            amazon_results = self.amazon_scraper.search(**search_params)

            self.root.after(0, lambda: self.update_results(
                ebay_results, amazon_results))

        except Exception as e:
            logger.error(f"Fehler bei der Suche: {str(e)}")
            self.root.after(0, lambda: self.show_error(str(e)))
        finally:
            self.root.after(0, self.search_completed)

    def update_gui_before_search(self):
        self.search_section.set_search_state(True)
        self.status_bar.set_progress(0)
        self.status_bar.set_status("Suche läuft...")
        self.results_section.clear_results()

    def update_results(self, ebay_results, amazon_results):
        try:
            self.current_ebay_results = ebay_results
            self.current_amazon_results = amazon_results

            self.results_section.clear_results()

            # Sortiere und zeige Ergebnisse
            self.apply_sorting_and_display_results()

            self.results_section.update_count(
                len(ebay_results),
                len(amazon_results)
            )

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Ergebnisse: {e}")
            self.show_error(f"Fehler beim Anzeigen der Ergebnisse:\n{str(e)}")

    def apply_sorting_and_display_results(self):
        sort_option = self.results_section.get_sort_option()

        # Sortiere Ergebnisse
        sorted_ebay = self.sort_results_by_option(
            self.current_ebay_results,
            sort_option
        )
        sorted_amazon = self.sort_results_by_option(
            self.current_amazon_results,
            sort_option
        )

        # Zeige Ergebnisse
        for item in sorted_ebay:
            self.results_section.add_result_card(
                item,
                "ebay",
                self.add_to_favorites,
                self.open_link
            )

        for item in sorted_amazon:
            self.results_section.add_result_card(
                item,
                "amazon",
                self.add_to_favorites,
                self.open_link
            )

    def sort_results_by_option(self, results, sort_option):
        if not results:
            return []

        sorted_results = results.copy()

        if sort_option == "Preis aufsteigend":
            sorted_results.sort(key=lambda x: self.extract_price(x['price']))
        elif sort_option == "Preis absteigend":
            sorted_results.sort(
                key=lambda x: self.extract_price(x['price']),
                reverse=True
            )

        return sorted_results

    def extract_price(self, price_str):
        try:
            clean_price = ''.join(
                c for c in price_str if c.isdigit() or c in '.,')
            clean_price = clean_price.replace(',', '.')
            return float(clean_price)
        except (ValueError, AttributeError, TypeError) as e:
            logger.error(f"Fehler bei der Preisextraktion für {
                         price_str}: {e}")
            return 0.0

    def sort_results(self, event=None):
        self.apply_sorting_and_display_results()

    def show_favorites(self):
        self.favorites_window.show()

    def add_to_favorites(self, item, source):
        if self.favorites_window.add_favorite(item, source):
            self.save_user_settings()

    def open_link(self, link):
        try:
            webbrowser.open(link)
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Links: {e}")
            self.show_error(
                f"Der Link konnte nicht geöffnet werden:\n{str(e)}")

    def show_error(self, message):
        messagebox.showerror("Fehler", message)
        self.status_bar.set_status(f"Fehler: {message}")

    def search_completed(self):
        self.search_active = False
        self.search_section.set_search_state(False)
        self.status_bar.set_status("Suche abgeschlossen")
        self.status_bar.set_progress(100)

    def load_user_settings(self):
        try:
            data = load_from_json(CONFIG['SETTINGS_FILE'])
            if data:
                self.settings = data.get('settings', {})
                favorites = data.get('favorites', [])
                self.favorites_window.load_favorites(favorites)
            else:
                self.settings = {
                    'max_pages': CONFIG['DEFAULT_MAX_PAGES'],
                    'default_search_period': CONFIG['DEFAULT_SEARCH_PERIOD']
                }

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

    def save_user_settings(self):
        try:
            data = {
                'settings': self.settings,
                'favorites': self.favorites_window.get_favorites()
            }
            save_to_json(data, CONFIG['SETTINGS_FILE'])
            logger.info("Benutzereinstellungen erfolgreich gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {str(e)}")
            messagebox.showerror(
                "Fehler",
                f"Die Einstellungen konnten nicht gespeichert werden:\n{
                    str(e)}"
            )

    def on_closing(self):
        try:
            self.save_user_settings()
            self.root.destroy()
        except Exception as e:
            logger.error(f"Fehler beim Schließen der Anwendung: {str(e)}")
            messagebox.showerror(
                "Fehler",
                f"Fehler beim Speichern der Einstellungen:\n{str(e)}"
            )
            self.root.destroy()
