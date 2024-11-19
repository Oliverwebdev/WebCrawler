from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import logging
import urllib.parse
from typing import List, Dict, Optional

# Logger einrichten
logger = logging.getLogger('KauflandScraper')
logging.basicConfig(level=logging.INFO)

class KauflandScraper:
    def __init__(self, db_manager=None):
        """
        Initialisiert den Kaufland-Scraper.
        
        Args:
            db_manager (optional): Datenbank-Manager, falls benötigt.
        """
        self.chrome_options = Options()
        # Entferne die Headless-Option
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--lang=de-DE')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        # Füge einen User-Agent hinzu
        self.chrome_options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        )
        self.driver = None
        self.base_url = "https://www.kaufland.de/suche/"
        self.db_manager = db_manager  # Falls später eine Datenbankanbindung benötigt wird
        
    def _init_browser(self):
        """Initialisiert den Browser."""
        if not self.driver:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            logger.info("Browser gestartet.")

    def _build_search_url(self, keyword: str, page: int = 1) -> str:
        """Erstellt die URL für die Produktsuche."""
        keyword_encoded = urllib.parse.quote(keyword)
        url = f"{self.base_url}?q={keyword_encoded}"
        if page > 1:
            url += f"&page={page}"
        return url

    def search(self, keyword, max_pages=3, min_price=None, max_price=None, condition=None):
        """
        Führt eine Suche auf der Kaufland-Website durch.
        
        Args:
            keyword (str): Suchbegriff.
            max_pages (int, optional): Maximale Anzahl von Seiten. Standard ist 3.
            min_price (float, optional): Minimaler Preisfilter. Standard ist None.
            max_price (float, optional): Maximaler Preisfilter. Standard ist None.
            condition (str, optional): Zustand (neu/gebraucht). Standard ist None.
        
        Returns:
            List[Dict[str, str]]: Liste der gefundenen Artikel.
        """
        logger.info(f"Starte Kaufland-Suche für: {keyword}")
        all_items = []

        try:
            for page in range(1, max_pages + 1):
                url = self._build_search_url(keyword, page)
                soup = self._get_page_content(url)
                if soup:
                    items = self._parse_page(soup)
                    all_items.extend(items)

            if all_items and self.db_manager:
                self.db_manager.save_search_results('kaufland', keyword, all_items)

            logger.info(f"Kaufland-Suche abgeschlossen. {len(all_items)} Artikel gefunden.")
            return all_items
        except Exception as e:
            logger.error(f"Kritischer Fehler bei der Kaufland-Suche: {str(e)}")
            return []
    
    def _get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Lädt die Seite und gibt deren Inhalt zurück."""
        try:
            if not self.driver:
                self._init_browser()
            self.driver.get(url)
            time.sleep(random.uniform(2, 5))  # Menschliches Verhalten simulieren
            return BeautifulSoup(self.driver.page_source, 'html.parser')
        except Exception as e:
            logger.error(f"Fehler beim Laden der Seite {url}: {e}")
            return None

    def _parse_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Parst Produktinformationen von der Seite."""
        items = []
        try:
            for product in soup.select(".product-tile"):
                try:
                    title = product.select_one(".product-title").get_text(strip=True)
                    link = product.select_one(".product-title").get("href")
                    price = product.select_one(".product-price, .special-price").get_text(strip=True)
                    if not link.startswith("http"):
                        link = f"https://www.kaufland.de{link}"
                    
                    items.append({
                        "title": title,
                        "price": price,
                        "link": link
                    })
                except Exception as e:
                    logger.warning(f"Fehler beim Parsen eines Produkts: {e}")
        except Exception as e:
            logger.error(f"Fehler beim Parsen der Seite: {e}")
        return items
