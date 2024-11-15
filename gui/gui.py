# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import webbrowser
from datetime import datetime
from config import CONFIG
from .components.search_section import SearchSection
from .components.results_section import ResultsSection
from .components.favorites_window import FavoritesWindow
from .components.status_bar import StatusBar

logger = logging.getLogger('EbayScraperGUI')


# gui.py

logger = logging.getLogger('EbayScraperGUI')


class EbayScraperGUI:
    def __init__(self, root, ebay_scraper, amazon_scraper, db_manager):
        """Initialisiert die Hauptanwendung."""
        self.root = root
        self.db_manager = db_manager  # Speichere db_manager als Instanzvariable
        self.ebay_scraper = ebay_scraper
        self.amazon_scraper = amazon_scraper
        self.search_active = False
        self.current_ebay_results = []
        self.current_amazon_results = []

        self.setup_main_window()
        self.setup_styles()
        self.create_components()
        self.load_user_settings()

    def setup_main_window(self):
        """Konfiguriert das Hauptfenster."""
        self.root.title("eBay/Amazon Scraper")
        self.root.minsize(800, 600)

        # Erstelle Hauptframe
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def setup_styles(self):
        """Konfiguriert das Aussehen der Anwendung."""
        style = ttk.Style()
        style.configure('TFrame', background='white')
        style.configure('TLabel', background='white', font=('Helvetica', 10))
        style.configure('TButton', font=('Helvetica', 10))
        style.configure('Header.TLabel', font=('Helvetica', 12, 'bold'))
        style.configure('Status.TLabel', font=('Helvetica', 9))
        style.configure('Search.TButton', padding=5)

    def create_components(self):
        """Erstellt alle GUI-Komponenten."""
        try:
            # Favorites Window
            self.favorites_window = FavoritesWindow(self.root, self.db_manager)

            # Header
            self.create_header()

            # Search Section
            self.search_section = SearchSection(
                self.main_frame, self.start_search)

            # Results Section
            self.results_section = ResultsSection(
                self.main_frame, self.sort_results)
            # Wichtig: Setze den Datenbankmanager direkt nach der Initialisierung
            self.results_section.set_db_manager(self.db_manager)

            # Setze Callbacks für Results Section
            self.results_section.bind_double_click(
                lambda event: self.open_link(
                    self.results_section.get_selected_item()['link'])
            )

            # Status Bar
            self.status_bar = StatusBar(self.main_frame)

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Komponenten: {e}")
            raise

    def create_header(self):
        """Erstellt den Header-Bereich."""
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))

        # Titel
        title_label = ttk.Label(
            self.header_frame,
            text="eBay/Amazon Preisvergleich",
            style='Header.TLabel'
        )
        title_label.pack(side=tk.LEFT)

        # Buttons
        button_frame = ttk.Frame(self.header_frame)
        button_frame.pack(side=tk.RIGHT)

        ttk.Button(
            button_frame,
            text="Favoriten",
            command=self.favorites_window.show
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Einstellungen",
            command=self.show_settings
        ).pack(side=tk.LEFT, padx=5)

    def show_settings(self):
        """Zeigt das Einstellungsfenster."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Einstellungen")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()

        # Einstellungsoptionen
        settings_frame = ttk.Frame(settings_window, padding="20")
        settings_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(settings_frame, text="Maximale Seitenanzahl:").pack(pady=5)
        max_pages = ttk.Entry(settings_frame)
        max_pages.insert(0, str(self.settings.get('max_pages', 3)))
        max_pages.pack(pady=5)

        ttk.Label(settings_frame,
                  text="Standard-Suchzeitraum (Tage):").pack(pady=5)
        search_period = ttk.Entry(settings_frame)
        search_period.insert(
            0, str(self.settings.get('default_search_period', 30)))
        search_period.pack(pady=5)

        def save_settings():
            try:
                self.settings['max_pages'] = int(max_pages.get())
                self.settings['default_search_period'] = int(
                    search_period.get())
                self.save_user_settings()
                settings_window.destroy()
                messagebox.showinfo(
                    "Erfolg", "Einstellungen wurden gespeichert")
            except ValueError:
                messagebox.showerror(
                    "Fehler", "Bitte geben Sie gültige Zahlen ein")

        ttk.Button(
            settings_frame,
            text="Speichern",
            command=save_settings
        ).pack(pady=20)

    def start_search(self, keyword, source='both', min_price=None, max_price=None, condition=None):
        """Startet eine neue Suche."""
        if not keyword:
            messagebox.showwarning(
                "Warnung", "Bitte geben Sie einen Suchbegriff ein")
            return

        if self.search_active:
            messagebox.showwarning("Warnung", "Eine Suche läuft bereits")
            return

        self.search_active = True
        self.status_bar.update_status("Suche läuft...")

        def search_thread():
            try:
                if source in ['both', 'ebay']:
                    self.current_ebay_results = self.ebay_scraper.search(
                        keyword,
                        self.settings.get('max_pages', 3),
                        min_price,
                        max_price,
                        condition
                    )

                if source in ['both', 'amazon']:
                    self.current_amazon_results = self.amazon_scraper.search(
                        keyword,
                        self.settings.get('max_pages', 3),
                        min_price,
                        max_price,
                        condition
                    )

                all_results = self.current_ebay_results + self.current_amazon_results
                self.root.after(
                    0, lambda: self.results_section.update_results(all_results))
                self.root.after(0, lambda: self.status_bar.update_status(
                    f"Suche abgeschlossen. {
                        len(all_results)} Ergebnisse gefunden."
                ))

            except Exception as e:
                logger.error(f"Fehler bei der Suche: {str(e)}")
                self.root.after(0, lambda: messagebox.showerror(
                    "Fehler",
                    f"Fehler bei der Suche: {str(e)}"
                ))
            finally:
                self.search_active = False

        threading.Thread(target=search_thread, daemon=True).start()

    def sort_results(self, sort_by):
        """Sortiert die Ergebnisse."""
        try:
            all_results = self.current_ebay_results + self.current_amazon_results

            if sort_by == 'price':
                all_results.sort(key=lambda x: float(
                    x['price'].replace('€', '').replace(',', '.').strip()))
            else:
                all_results.sort(key=lambda x: x[sort_by])

            self.results_section.update_results(all_results)

        except Exception as e:
            logger.error(f"Fehler beim Sortieren: {str(e)}")
            messagebox.showerror("Fehler", f"Fehler beim Sortieren: {str(e)}")

    def add_to_favorites(self, item):
        """Fügt ein Item zu den Favoriten hinzu."""
        try:
            self.db_manager.save_favorites([item])
            messagebox.showinfo(
                "Erfolg", "Artikel wurde zu den Favoriten hinzugefügt")
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen zu Favoriten: {str(e)}")
            messagebox.showerror(
                "Fehler", f"Fehler beim Hinzufügen zu Favoriten: {str(e)}")

    def open_link(self, url):
        """Öffnet einen Link im Standardbrowser."""
        try:
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Fehler beim Öffnen des Links: {str(e)}")
            messagebox.showerror(
                "Fehler", f"Fehler beim Öffnen des Links: {str(e)}")

    def load_user_settings(self):
        """Lädt die Benutzereinstellungen."""
        try:
            self.settings = self.db_manager.get_settings()
        except Exception as e:
            logger.error(f"Fehler beim Laden der Einstellungen: {str(e)}")
            self.settings = {
                'max_pages': CONFIG['DEFAULT_MAX_PAGES'],
                'default_search_period': CONFIG['DEFAULT_SEARCH_PERIOD']
            }

    def save_user_settings(self):
        """Speichert die Benutzereinstellungen."""
        try:
            self.db_manager.save_settings(self.settings)
            logger.info("Benutzereinstellungen erfolgreich gespeichert")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {str(e)}")
            messagebox.showerror(
                "Fehler",
                f"Die Einstellungen konnten nicht gespeichert werden:\n{
                    str(e)}"
            )
