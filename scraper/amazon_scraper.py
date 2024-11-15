# amazon_scraper.py
import logging
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from config import CONFIG

logger = logging.getLogger('AmazonScraper')


class AmazonScraper:
    def __init__(self, db_manager):
        """Initialisiert den AmazonScraper mit Datenbankanbindung."""
        self.base_url = "https://www.amazon.de/s?k={}"
        self.proxies = []
        self.retry_count = 3
        self.retry_delay = 2
        self.session = requests.Session()
        self.lock = threading.Lock()
        self.db_manager = db_manager

    def _get_headers(self):
        """Generiert Browser-Header für Anfragen."""
        return {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def _build_search_url(self, keyword, page, min_price=None, max_price=None, condition=None):
        """Erstellt die Such-URL mit Parametern."""
        url = self.base_url.format(keyword.replace(' ', '+'))
        params = []

        if page > 1:
            params.append(f"page={page}")
        if min_price:
            params.append(f"low-price={min_price}")
        if max_price:
            params.append(f"high-price={max_price}")
        if condition:
            if condition.lower() == "neu":
                params.append("condition=new")
            elif condition.lower() == "gebraucht":
                params.append("condition=used")

        if params:
            url += "&" + "&".join(params)

        return url

    def _parse_price(self, price_element):
        """Extrahiert und formatiert den Preis."""
        try:
            if not price_element:
                return "Nicht verfügbar"

            price_text = price_element.get_text().strip()
            # Entferne alle Zeichen außer Zahlen, Komma und Punkt
            price = ''.join(c for c in price_text if c.isdigit()
                            or c in [',', '.'])
            return f"{price}€" if price else "Nicht verfügbar"
        except Exception:
            return "Nicht verfügbar"

    def _search_page(self, url):
        """Durchsucht eine einzelne Seite mit Retry-Mechanismus."""
        for attempt in range(self.retry_count):
            try:
                proxy = random.choice(self.proxies) if self.proxies else None
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    proxies={'http': proxy, 'https': proxy} if proxy else None,
                    timeout=CONFIG['DEFAULT_TIMEOUT']
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    items = self._parse_page(soup)
                    return items
                else:
                    logger.warning(f"Unerwarteter Status Code: {
                                   response.status_code}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Request Fehler (Versuch {
                             attempt + 1}/{self.retry_count}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                continue

        return []

    def _parse_page(self, soup):
        """Extrahiert Artikelinformationen aus der HTML-Seite."""
        items = []
        product_list = soup.find_all(
            'div', {'data-component-type': 's-search-result'})

        for product in product_list:
            try:
                # Titel und Link
                title_element = product.find('h2')
                if not title_element:
                    continue

                title = title_element.get_text().strip()
                link_element = title_element.find('a')
                if not link_element:
                    continue

                link = "https://www.amazon.de" + link_element.get('href', '')

                # Preis
                price_element = product.find('span', {'class': 'a-price'})
                price = self._parse_price(price_element)

                # Versand
                shipping_element = product.find(
                    'div', {'class': 'a-row a-size-base a-color-secondary'})
                shipping = shipping_element.get_text().strip(
                ) if shipping_element else "Versand: siehe Website"

                item = {
                    'title': title,
                    'price': price,
                    'link': link,
                    'shipping': shipping,
                    'location': 'Amazon.de',  # Standard für Amazon
                    'timestamp': datetime.now().isoformat()
                }
                items.append(item)

            except Exception as e:
                logger.error(f"Fehler beim Parsen eines Produkts: {str(e)}")
                continue

        return items

    def search(self, keyword, max_pages=3, min_price=None, max_price=None, condition=None):
        """Führt eine Suche auf Amazon durch und speichert in der Datenbank."""
        logger.info(f"Starte Amazon-Suche für: {keyword}")
        all_items = []

        try:
            urls = [self._build_search_url(keyword, page, min_price, max_price, condition)
                    for page in range(1, max_pages + 1)]

            with ThreadPoolExecutor(max_workers=min(5, max_pages)) as executor:
                future_to_url = {executor.submit(
                    self._search_page, url): url for url in urls}

                for future in future_to_url:
                    try:
                        items = future.result(timeout=30)
                        with self.lock:
                            all_items.extend(items)
                    except Exception as e:
                        logger.error(
                            f"Fehler bei der Verarbeitung der Amazon-Suchergebnisse: {str(e)}")

            if all_items:
                self.db_manager.save_search_results(
                    'amazon', keyword, all_items)

            logger.info(
                f"Amazon-Suche abgeschlossen. {len(all_items)} Artikel gefunden.")
            return all_items

        except Exception as e:
            logger.error(f"Kritischer Fehler bei der Amazon-Suche: {str(e)}")
            return []

    def get_saved_results(self, keyword=None):
        """Lädt gespeicherte Suchergebnisse aus der Datenbank."""
        try:
            return self.db_manager.get_search_results('amazon', keyword) if keyword else []
        except Exception as e:
            logger.error(f"Fehler beim Laden der Ergebnisse: {str(e)}")
            return []
