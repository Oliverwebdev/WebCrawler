# main.py
import tkinter as tk
import logging
import sys
from gui.gui import EbayScraperGUI
from scraper.ebay_scraper import EbayScraper
from scraper.amazon_scraper import AmazonScraper
from x11_config import configure_x11_environment, check_display_server

def setup_logging():
    """Konfiguriert das Logging-System."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('utils/scraper.log'),
            logging.StreamHandler()
        ]
    )

def check_system_requirements():
    """Überprüft Systemvoraussetzungen."""
    logger = logging.getLogger('SystemCheck')
    
    try:
        # Prüfe Python-Version
        if sys.version_info < (3, 7):
            logger.error("Python 3.7 oder höher wird benötigt")
            return False
            
        # Prüfe tkinter Installation
        tk.Tk().destroy()
        
        # Prüfe Display-Server
        display_server = check_display_server()
        if display_server == "unbekannt":
            logger.warning("Display-Server konnte nicht erkannt werden")
            
        return True
        
    except Exception as e:
        logger.error(f"Systemanforderungen nicht erfüllt: {e}")
        return False

def main():
    """Hauptfunktion mit verbesserter Fehlerbehandlung."""
    setup_logging()
    logger = logging.getLogger('Main')
    
    try:
        # Prüfe Systemvoraussetzungen
        if not check_system_requirements():
            sys.exit(1)
            
        # Konfiguriere X11-Umgebung
        configure_x11_environment()
        
        # Initialisiere Tk mit Fehlerbehandlung
        root = tk.Tk()
        root.withdraw()  # Verstecke Hauptfenster während der Initialisierung
        
        # Initialisiere Scraper
        ebay_scraper = EbayScraper()
        amazon_scraper = AmazonScraper()
        
        # Erstelle GUI
        app = EbayScraperGUI(root, ebay_scraper, amazon_scraper)
        
        # Zeige Hauptfenster
        root.deiconify()
        
        # Starte Event-Loop
        root.mainloop()
        
    except Exception as e:
        logger.critical(f"Kritischer Fehler beim Programmstart: {e}", exc_info=True)
        try:
            tk.messagebox.showerror(
                "Kritischer Fehler",
                f"Die Anwendung konnte nicht gestartet werden:\n{str(e)}"
            )
        except:
            print(f"Kritischer Fehler: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()