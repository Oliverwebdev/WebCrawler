from abc import ABC, abstractmethod
import logging
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from typing import List, Dict, Optional, Any
from config import CONFIG

logger = logging.getLogger('BaseScraper')

class BaseScraper(ABC):
    """Abstrakte Basisklasse für Shop-Scraper mit verbesserten Anti-Block-Mechanismen"""
    
    def __init__(self, db_manager, shop_name: str):
        self.shop_name = shop_name
        self.proxies: List[str] = []
        self.retry_count = 3
        self.retry_delay = 2
        self.session = requests.Session()
        self.lock = threading.Lock()
        self.db_manager = db_manager
        self.last_request_time = 0
        self.min_request_delay = 1.5  # Minimale Verzögerung zwischen Anfragen
        
        # Liste von User-Agents für Rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]

    def _get_headers(self) -> Dict[str, str]:
        """Generiert Browser-Header mit User-Agent Rotation."""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

    def _wait_between_requests(self):
        """Implementiert eine dynamische Verzögerung zwischen Anfragen."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_delay:
            sleep_time = self.min_request_delay - time_since_last_request + random.uniform(0.1, 0.5)
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()

    def _handle_response(self, response, url: str) -> Optional[BeautifulSoup]:
        """Behandelt die Server-Response und gibt entsprechendes Feedback."""
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
        elif response.status_code == 503:
            logger.warning(f"Server überlastet oder blockiert Zugriff: {url}")
            raise Exception("Der Server ist derzeit nicht verfügbar. Möglicherweise zu viele Anfragen.")
        elif response.status_code == 403:
            logger.warning(f"Zugriff verweigert: {url}")
            raise Exception("Der Zugriff wurde verweigert. Bitte später erneut versuchen.")
        else:
            logger.warning(f"Unerwarteter Status Code {response.status_code}: {url}")
            raise Exception(f"Unerwarteter Fehler (Status {response.status_code})")

    def _search_page(self, url: str) -> List[Dict[str, Any]]:
        """Durchsucht eine einzelne Seite mit verbessertem Error-Handling."""
        for attempt in range(self.retry_count):
            try:
                self._wait_between_requests()
                
                proxy = random.choice(self.proxies) if self.proxies else None
                proxy_config = {'http': proxy, 'https': proxy} if proxy else None
                
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    proxies=proxy_config,
                    timeout=CONFIG['DEFAULT_TIMEOUT']
                )
                
                soup = self._handle_response(response, url)
                if soup:
                    return self._parse_page(soup)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request Fehler (Versuch {attempt + 1}/{self.retry_count}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))  # Exponentielles Backoff
                continue
            except Exception as e:
                logger.error(f"Fehler bei der Verarbeitung: {str(e)}")
                raise

        return []

    def search(self, keyword: str, max_pages: int = 3, min_price: Optional[float] = None, 
              max_price: Optional[float] = None, condition: Optional[str] = None) -> List[Dict[str, Any]]:
        """Führt eine Suche mit verbessertem Error-Handling durch."""
        logger.info(f"Starte {self.shop_name}-Suche für: {keyword}")
        all_items = []

        try:
            urls = [
                self._build_search_url(keyword, page, min_price, max_price, condition)
                for page in range(1, max_pages + 1)
            ]

            # Reduziere die Anzahl paralleler Anfragen
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_to_url = {executor.submit(self._search_page, url): url for url in urls}

                for future in future_to_url:
                    try:
                        items = future.result(timeout=30)
                        with self.lock:
                            all_items.extend(items)
                    except Exception as e:
                        logger.error(f"Fehler bei der Verarbeitung der Suchergebnisse: {str(e)}")
                        # Propagiere den Fehler nach oben für besseres Benutzer-Feedback
                        raise

            if all_items:
                self.db_manager.save_search_results(self.shop_name, keyword, all_items)

            logger.info(f"{self.shop_name}-Suche abgeschlossen. {len(all_items)} Artikel gefunden.")
            return all_items

        except Exception as e:
            logger.error(f"Kritischer Fehler bei der {self.shop_name}-Suche: {str(e)}")
            raise Exception(f"Fehler bei der Suche auf {self.shop_name}: {str(e)}")