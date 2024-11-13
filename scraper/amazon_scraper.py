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
from utils.utils import save_to_json, load_from_json

logger = logging.getLogger('AmazonScraper')

class AmazonScraper:
    def __init__(self):
        """Initialisiert den AmazonScraper mit grundlegenden Einstellungen."""
        self.base_url = "https://www.amazon.de/s?k={}"
        self.proxies = []
        self.results_file = 'utils/amazon_results.json'  # Default Wert
        self.retry_count = 3
        self.retry_delay = 2
        self.session = requests.Session()
        self.lock = threading.Lock()

    def _get_headers(self):
        """Generiert Browser-Header für Anfragen."""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }

    def search(self, keyword, max_pages=3, min_price=None, max_price=None, condition=None):
        """
        Führt eine Suche auf Amazon durch.
        
        Args:
            keyword (str): Suchbegriff
            max_pages (int): Maximale Anzahl der zu durchsuchenden Seiten
            min_price (float): Minimaler Preis
            max_price (float): Maximaler Preis
            condition (str): Artikelzustand (neu, gebraucht, etc.)
            
        Returns:
            list: Liste der gefundenen Artikel
        """
        logger.info(f"Starte Amazon-Suche für: {keyword}")
        all_items = []
        
        try:
            urls = [self._build_search_url(keyword, page, min_price, max_price, condition) 
                   for page in range(1, max_pages + 1)]
            
            with ThreadPoolExecutor(max_workers=min(5, max_pages)) as executor:
                future_to_url = {executor.submit(self._search_page, url): url for url in urls}
                
                for future in future_to_url:
                    try:
                        items = future.result(timeout=30)
                        with self.lock:
                            all_items.extend(items)
                    except Exception as e:
                        logger.error(f"Fehler bei der Verarbeitung der Amazon-Suchergebnisse: {str(e)}")
            
            if all_items:
                self._save_results(keyword, all_items)
            
            logger.info(f"Amazon-Suche abgeschlossen. {len(all_items)} Artikel gefunden.")
            return all_items
            
        except Exception as e:
            logger.error(f"Kritischer Fehler bei der Amazon-Suche: {str(e)}")
            return []

    def _build_search_url(self, keyword, page, min_price, max_price, condition):
        """Erstellt die Such-URL mit allen Parametern."""
        url = self.base_url.format(keyword)
        
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
                    logger.warning(f"Unerwarteter Status Code von Amazon: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request Fehler bei Amazon (Versuch {attempt + 1}/{self.retry_count}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                continue
                
        return []

    def _parse_page(self, soup):
        """Extrahiert Artikelinformationen aus der Amazon-Seite."""
        items = []
        listings = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        for listing in listings:
            try:
                item = self._parse_listing(listing)
                if item:
                    items.append(item)
            except Exception as e:
                logger.error(f"Fehler beim Parsen eines Amazon-Artikels: {str(e)}")
                continue
                
        return items

    def _parse_listing(self, listing):
        """Extrahiert Informationen aus einem einzelnen Amazon-Listing."""
        try:
            title_element = listing.find('span', {'class': 'a-text-normal'})
            price_element = listing.find('span', {'class': 'a-price'})
            link_element = listing.find('a', {'class': 'a-link-normal s-no-outline'})
            
            if all([title_element, price_element, link_element]):
                price_text = price_element.find('span', {'class': 'a-offscreen'}).text
                
                return {
                    'title': title_element.text.strip(),
                    'price': price_text,
                    'link': 'https://www.amazon.de' + link_element['href'],
                    'shipping': 'Prime' if listing.find('i', {'class': 'a-icon-prime'}) else 'Standard',
                    'timestamp': datetime.now().isoformat()
                }
            return None
            
        except Exception as e:
            logger.error(f"Fehler beim Parsen eines Amazon-Listings: {str(e)}")
            return None

    def _save_results(self, keyword, items):
        """Speichert die Amazon-Suchergebnisse."""
        data = {
            'keyword': keyword,
            'timestamp': datetime.now().isoformat(),
            'items': items
        }
        
        try:
            with self.lock:
                existing_data = []
                try:
                    existing_data = load_from_json(self.results_file) or []
                except FileNotFoundError:
                    pass
                    
                existing_data.append(data)
                save_to_json(existing_data, self.results_file)
                logger.info(f"Amazon-Ergebnisse erfolgreich gespeichert: {len(items)} Artikel")
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Amazon-Ergebnisse: {str(e)}")

    # Proxy-Management-Methoden
    def add_proxy(self, proxy):
        """Fügt einen Proxy zur Proxy-Liste hinzu."""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            
    def clear_proxies(self):
        """Leert die Proxy-Liste."""
        self.proxies = []

    
    
    def get_proxy_count(self):
        """Gibt die Anzahl der verfügbaren Proxies zurück."""
        return len(self.proxies)
    



