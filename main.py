# main.py
import tkinter as tk
from tkinter import messagebox
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Konfiguriere Logging sofort
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug.log')
    ]
)

logger = logging.getLogger('Main')


def check_system_requirements() -> bool:
    """
    Überprüft Systemvoraussetzungen und Verzeichnisstruktur.

    Returns:
        bool: True wenn alle Anforderungen erfüllt sind, sonst False
    """
    try:
        logger.debug("Überprüfe Systemvoraussetzungen...")

        # Überprüfe/Erstelle notwendige Verzeichnisse
        required_dirs = [
            'utils',
            'database',
            'scrapers',
            'gui',
            'gui/components'
        ]

        for directory in required_dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Verzeichnis überprüft/erstellt: {directory}")

        return True
    except Exception as e:
        logger.error(f"Fehler bei Systemüberprüfung: {e}")
        return False


def create_gui() -> Optional[tk.Tk]:
    """
    Erstellt das GUI-Fenster mit Fehlerbehandlung.

    Returns:
        Optional[tk.Tk]: Tkinter Root-Fenster oder None bei Fehler
    """
    try:
        logger.debug("Initialisiere GUI...")
        root = tk.Tk()
        root.title("AllYouCanShop")

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


def setup_scrapers(db_manager) -> Dict[str, Any]:
    """
    Initialisiert die Scraper-Instanzen.

    Args:
        db_manager: Datenbankmanager-Instanz

    Returns:
        Dict[str, Any]: Dictionary mit initialisierten Scraper-Instanzen
    """
    try:
        from scrapers.ebay_scraper import EbayScraper
        from scrapers.amazon_scraper import AmazonScraper
        from scrapers.otto_scraper import OttoScraper
        from scrapers.kaufland_scraper import KauflandScraper

        scrapers = {
            'ebay': EbayScraper(db_manager),
            'amazon': AmazonScraper(db_manager),
            'otto': OttoScraper(db_manager),
            'kaufland': KauflandScraper(db_manager)

            
        }
        logger.debug("Scraper erfolgreich initialisiert")
        return scrapers
    except Exception as e:
        logger.error(f"Fehler bei Scraper-Initialisierung: {e}")
        raise


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
        scrapers = setup_scrapers(db_manager)

        # Erstelle Hauptanwendung
        logger.debug("Erstelle Hauptanwendung...")
        app = EbayScraperGUI(root, scrapers, db_manager)

        # Führe Datenmigration durch falls nötig
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
