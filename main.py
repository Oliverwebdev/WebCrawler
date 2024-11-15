# main.py
import tkinter as tk
from tkinter import messagebox
import logging
import sys
import os
from pathlib import Path

# Konfiguriere Logging sofort
logging.basicConfig(
    level=logging.DEBUG,  # Setze auf DEBUG für mehr Details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug.log')
    ]
)

logger = logging.getLogger('Main')


def check_system_requirements():
    """Überprüft Systemvoraussetzungen und Verzeichnisstruktur."""
    try:
        logger.debug("Überprüfe Systemvoraussetzungen...")

        # Überprüfe/Erstelle notwendige Verzeichnisse
        required_dirs = ['utils', 'database',
                         'scraper', 'gui', 'gui/components']
        for directory in required_dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Verzeichnis überprüft/erstellt: {directory}")

        # Überprüfe Datenbankdatei
        if not Path('utils/scraper.db').exists():
            logger.debug("Datenbank existiert noch nicht - wird erstellt")

        return True
    except Exception as e:
        logger.error(f"Fehler bei Systemüberprüfung: {e}")
        return False


def create_gui():
    """Erstellt das GUI-Fenster mit Fehlerbehandlung."""
    try:
        logger.debug("Initialisiere GUI...")
        root = tk.Tk()
        root.title("eBay/Amazon Scraper")

        # Setze Fenstergröße und -position
        window_width = 800
        window_height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)

        root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        logger.debug("GUI-Fenster erstellt und positioniert")

        return root
    except Exception as e:
        logger.error(f"Fehler bei GUI-Erstellung: {e}")
        return None


def main():
    """Hauptfunktion mit verbesserter Fehlerbehandlung und Debugging."""
    try:
        logger.info("Starte Anwendung...")

        # Prüfe Systemvoraussetzungen
        if not check_system_requirements():
            logger.error("Systemvoraussetzungen nicht erfüllt")
            sys.exit(1)

        # Importiere erst nach Systemcheck
        logger.debug("Importiere Module...")
        from gui.gui import EbayScraperGUI
        from scraper.ebay_scraper import EbayScraper
        from scraper.amazon_scraper import AmazonScraper
        from database.database_manager import DatabaseManager
        from x11_config import configure_x11_environment, check_display_server

        # Konfiguriere X11 wenn nötig
        if sys.platform.startswith('linux'):
            logger.debug("Konfiguriere X11...")
            configure_x11_environment()
            display_server = check_display_server()
            logger.info(f"Display Server: {display_server}")

        # Initialisiere Datenbank
        logger.debug("Initialisiere Datenbank...")
        db_manager = DatabaseManager()

        # Erstelle GUI
        logger.debug("Erstelle GUI...")
        root = create_gui()
        if not root:
            logger.error("GUI konnte nicht erstellt werden")
            sys.exit(1)

        # Initialisiere Scraper
        logger.debug("Initialisiere Scraper...")
        ebay_scraper = EbayScraper(db_manager)
        amazon_scraper = AmazonScraper(db_manager)

        # Erstelle Hauptanwendung
        logger.debug("Erstelle Hauptanwendung...")
        app = EbayScraperGUI(root, ebay_scraper, amazon_scraper, db_manager)

        # Führe Datenmigration durch
        logger.debug("Führe Datenmigration durch...")
        db_manager.migrate_from_json()

        logger.info("Anwendung erfolgreich initialisiert")
        root.mainloop()

    except Exception as e:
        logger.critical(f"Kritischer Fehler beim Programmstart: {
                        e}", exc_info=True)
        try:
            messagebox.showerror(
                "Kritischer Fehler",
                f"Die Anwendung konnte nicht gestartet werden:\n{str(e)}"
            )
        except:
            print(f"Kritischer Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
