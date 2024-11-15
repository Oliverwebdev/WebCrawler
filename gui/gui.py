# gui.py
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
        """
        Initialisiert die Hauptanwendung.
        
        Args:
            root: Tkinter Root Window
            ebay_scraper: Instanz des EbayScrapers
            amazon_scraper: Instanz des AmazonScrapers
        """
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
        """Konfiguriert das Hauptfenster der Anwendung."""
        self.root.title("eBay & Amazon Artikel-Suche")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Main Frame
        self.main_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

    def setup_styles(self):
        """Konfiguriert die Styles für die GUI."""
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
            "Card.TFrame": {
                "configure": {
                    "background": "white",
                    "relief": "raised",
                    "borderwidth": 1,
                    "padding": 10
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
            }
        }

        for style_name, style_opts in styles.items():
            self.style.configure(style_name, **style_opts["configure"])

    def create_components(self):
        """Erstellt alle GUI-Komponenten."""
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

        # Setze initiale Callbacks
        self.results_section.set_callbacks(
            self.add_to_favorites,
            self.open_link
        )

    def create_header(self):
        """Erstellt den Header-Bereich der Anwendung."""
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
        """
        Startet eine neue Suche mit den gegebenen Parametern.
        
        Args:
            search_params (dict): Suchparameter
        """
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
        """
        Führt die Suche asynchron aus.
        
        Args:
            search_params (dict): Suchparameter
        """
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
        """Aktualisiert die GUI-Elemente vor Beginn der Suche."""
        self.search_section.set_search_state(True)
        self.status_bar.set_progress(0)
        self.status_bar.set_status("Suche läuft...")
        self.results_section.clear_results()

    def update_results(self, ebay_results, amazon_results):
        """
        Aktualisiert die Suchergebnisse in der GUI.
        
        Args:
            ebay_results (list): Liste der eBay-Ergebnisse
            amazon_results (list): Liste der Amazon-Ergebnisse
        """
        try:
            self.current_ebay_results = ebay_results
            self.current_amazon_results = amazon_results

            # Aktualisiere die Ergebnisse in der ResultsSection
            self.results_section.update_results(ebay_results, amazon_results)

            # Setze die Callbacks für die Interaktionen
            self.results_section.set_callbacks(
                self.add_to_favorites,
                self.open_link
            )

        except Exception as e:
            logger.error(f"Fehler beim Aktualisieren der Ergebnisse: {e}")
            self.show_error(f"Fehler beim Anzeigen der Ergebnisse:\n{str(e)}")

    def sort_results(self, event=None):
        """Callback für Sortierungsänderungen."""
        try:
            self.results_section.sort_results()
        except Exception as e:
            logger.error(f"Fehler beim Sortieren der Ergebnisse: {e}")
            self.show_error(f"Fehler beim Sortieren der Ergebnisse:\n{str(e)}")

    def show_favorites(self):
        """Zeigt das Favoriten-Fenster an."""
        self.favorites_window.show()

    def add_to_favorites(self, item, source):
        """
        Fügt einen Artikel zu den Favoriten hinzu.
        
        Args:
            item (dict): Der zu favorisierende Artikel
            source (str): Quelle des Artikels (ebay/amazon)
        """
        if self.favorites_window.add_favorite(item, source):
            self.save_user_settings()

    def open_link(self, link):
        """
        Öffnet einen Link im Standard-Browser.
        
        Args:
            link (str): Zu öffnende URL
        """
        try:
            webbrowser.open(link)
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Links: {e}")
            self.show_error(
                f"Der Link konnte nicht geöffnet werden:\n{str(e)}")

    def show_error(self, message):
        """
        Zeigt eine Fehlermeldung an.
        
        Args:
            message (str): Anzuzeigende Fehlermeldung
        """
        messagebox.showerror("Fehler", message)
        self.status_bar.set_status(f"Fehler: {message}")

    def search_completed(self):
        """Wird aufgerufen, wenn die Suche abgeschlossen ist."""
        self.search_active = False
        self.search_section.set_search_state(False)
        self.status_bar.set_status("Suche abgeschlossen")
        self.status_bar.set_progress(100)

    def load_user_settings(self):
        """Lädt die Benutzereinstellungen aus der Datei."""
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
        """Speichert die Benutzereinstellungen in die Datei."""
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
        """Handler für das Schließen der Anwendung."""
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
