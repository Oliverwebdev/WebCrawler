# ebay_scraper.py
import logging
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from config import CONFIG
from utils import save_to_json, load_from_json

logger = logging.getLogger('EbayScraper')

class UserAgentManager:
    """Verwaltet User Agents mit Fallback-Mechanismus"""
    def __init__(self):
        self.use_fake_ua = False
        self.fallback_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/120.0.0.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
        ]
        
        try:
            from fake_useragent import UserAgent
            self.ua = UserAgent()
            self.use_fake_ua = True
            logger.info("Fake UserAgent erfolgreich initialisiert")
        except Exception as e:
            logger.warning(f"Konnte fake-useragent nicht laden: {e}. Verwende Fallback.")
            self.use_fake_ua = False

    def get_user_agent(self):
        """Gibt einen User Agent zurück"""
        try:
            if self.use_fake_ua:
                return self.ua.random
        except Exception as e:
            logger.warning(f"Fehler beim Abrufen des fake user agent: {e}")
            self.use_fake_ua = False
        
        return random.choice(self.fallback_agents)

class EbayScraper:
    def __init__(self):
        """Initialisiert den EbayScraper mit grundlegenden Einstellungen."""
        self.base_url = "https://www.ebay.de/sch/i.html?_nkw={}"
        self.proxies = []
        self.results_file = CONFIG['RESULTS_FILE']
        self.retry_count = 3
        self.retry_delay = 2
        self.session = requests.Session()
        self.ua_manager = UserAgentManager()
        self.lock = threading.Lock()  # Thread-Sicherheit für gemeinsam genutzte Ressourcen

    def _get_headers(self):
        """Generiert Browser-Header für Anfragen."""
        return {
            'User-Agent': self.ua_manager.get_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }

    def search(self, keyword, max_pages=3, min_price=None, max_price=None, condition=None):
        """
        Führt eine Suche auf eBay durch.
        
        Args:
            keyword (str): Suchbegriff
            max_pages (int): Maximale Anzahl der zu durchsuchenden Seiten
            min_price (float): Minimaler Preis
            max_price (float): Maximaler Preis
            condition (str): Artikelzustand (neu, gebraucht, etc.)
            
        Returns:
            list: Liste der gefundenen Artikel
        """
        logger.info(f"Starte Suche für: {keyword}")
        all_items = []
        
        try:
            urls = [self._build_search_url(keyword, page, min_price, max_price, condition) 
                   for page in range(1, max_pages + 1)]
            
            # Verwende ThreadPoolExecutor für parallele Verarbeitung
            with ThreadPoolExecutor(max_workers=min(5, max_pages)) as executor:
                future_to_url = {executor.submit(self._search_page, url): url for url in urls}
                
                for future in future_to_url:
                    try:
                        items = future.result(timeout=30)
                        with self.lock:  # Thread-sicheres Hinzufügen von Items
                            all_items.extend(items)
                    except Exception as e:
                        logger.error(f"Fehler bei der Verarbeitung der Suchergebnisse: {str(e)}")
            
            if all_items:
                self._save_results(keyword, all_items)
            
            logger.info(f"Suche abgeschlossen. {len(all_items)} Artikel gefunden.")
            return all_items
            
        except Exception as e:
            logger.error(f"Kritischer Fehler bei der Suche: {str(e)}")
            return []

    def _build_search_url(self, keyword, page, min_price, max_price, condition):
        """Erstellt die Such-URL mit allen Parametern."""
        url = self.base_url.format(keyword)
        
        params = []
        if page > 1:
            params.append(f"_pgn={page}")
        if min_price:
            params.append(f"_udlo={min_price}")
        if max_price:
            params.append(f"_udhi={max_price}")
        if condition:
            if condition.lower() == "neu":
                params.append("LH_ItemCondition=1000")
            elif condition.lower() == "gebraucht":
                params.append("LH_ItemCondition=3000")
            
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
                    logger.warning(f"Unerwarteter Status Code: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request Fehler (Versuch {attempt + 1}/{self.retry_count}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                continue
                
        return []

    def _parse_page(self, soup):
        """Extrahiert Artikelinformationen aus der HTML-Seite."""
        items = []
        listings = soup.find_all('div', class_='s-item__wrapper')
        
        for listing in listings:
            try:
                item = self._parse_listing(listing)
                if item:
                    items.append(item)
            except Exception as e:
                logger.error(f"Fehler beim Parsen eines Artikels: {str(e)}")
                continue
                
        return items

    def _parse_listing(self, listing):
        """Extrahiert Informationen aus einem einzelnen Listing."""
        try:
            title_element = listing.find('div', class_='s-item__title')
            if not title_element or "Shop on eBay" in title_element.get_text(strip=True):
                return None
                
            price_element = listing.find('span', class_='s-item__price')
            link_element = listing.find('a', class_='s-item__link')
            shipping_element = listing.find('span', class_='s-item__shipping')
            location_element = listing.find('span', class_='s-item__location')
            
            if all([title_element, price_element, link_element]):
                return {
                    'title': title_element.get_text(strip=True),
                    'price': price_element.get_text(strip=True),
                    'link': link_element['href'],
                    'shipping': shipping_element.get_text(strip=True) if shipping_element else 'Keine Angabe',
                    'location': location_element.get_text(strip=True) if location_element else 'Keine Angabe',
                    'timestamp': datetime.now().isoformat()
                }
            return None
            
        except Exception as e:
            logger.error(f"Fehler beim Parsen eines Listings: {str(e)}")
            return None

    def _save_results(self, keyword, items):
        """Speichert die Suchergebnisse in einer JSON-Datei."""
        data = {
            'keyword': keyword,
            'timestamp': datetime.now().isoformat(),
            'items': items
        }
        
        try:
            with self.lock:  # Thread-sicheres Speichern
                existing_data = []
                try:
                    existing_data = load_from_json(self.results_file) or []
                except FileNotFoundError:
                    pass
                    
                existing_data.append(data)
                save_to_json(existing_data, self.results_file)
                logger.info(f"Ergebnisse erfolgreich gespeichert: {len(items)} Artikel")
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Ergebnisse: {str(e)}")

    def get_saved_results(self, keyword=None):
        """Lädt gespeicherte Suchergebnisse."""
        try:
            with self.lock:  # Thread-sicheres Laden
                data = load_from_json(self.results_file)
                
                if not data:
                    return []
                    
                if keyword:
                    data = [d for d in data if d['keyword'].lower() == keyword.lower()]
                    
                return data
                
        except Exception as e:
            logger.error(f"Fehler beim Laden der Ergebnisse: {str(e)}")
            return []

    def add_proxy(self, proxy):
        """
        Fügt einen Proxy zur Proxy-Liste hinzu.
        """
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            
    def clear_proxies(self):
        """
        Leert die Proxy-Liste.
        """
        self.proxies = []

    def get_proxy_count(self):
        """
        Gibt die Anzahl der verfügbaren Proxies zurück.
        """
        return len(self.proxies)

if __name__ == "__main__":
    # Beispiel für die direkte Verwendung
    scraper = EbayScraper()
    results = scraper.search("laptop", max_pages=1)
    print(f"Gefundene Artikel: {len(results)}")