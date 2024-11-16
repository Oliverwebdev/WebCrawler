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
import json

logger = logging.getLogger('BaseScraper')

class BaseScraper(ABC):
    """Abstrakte Basisklasse für Shop-Scraper"""
    
    def __init__(self, db_manager, shop_name: str):
        """
        Initialisiert den Basis-Scraper.
        
        Args:
            db_manager: Datenbankmanager-Instanz
            shop_name: Name des Shops (z.B. 'ebay', 'amazon', 'otto')
        """
        self.shop_name = shop_name
        self.proxies: List[str] = []
        self.retry_count = 3
        self.retry_delay = 5  # Erhöht für bessere Stabilität
        self.lock = threading.Lock()
        self.db_manager = db_manager

        # Initialisiere Session mit erweiterten Einstellungen
        self.session = requests.Session()
        self.session.verify = True
        self.session.timeout = 15
        
        # Setze Standard-Headers
        self.session.headers.update(self._get_headers())

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Basis-URL des Shops"""
        pass

    @abstractmethod
    def _parse_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Parst eine Seite mit Suchergebnissen.
        
        Args:
            soup: BeautifulSoup Objekt der Seite
            
        Returns:
            Liste von Artikeln mit ihren Eigenschaften
        """
        pass

    @abstractmethod
    def _build_search_url(self, keyword: str, page: int, min_price: Optional[float] = None, 
                         max_price: Optional[float] = None, condition: Optional[str] = None) -> str:
        """
        Erstellt die Such-URL mit allen Parametern.
        
        Args:
            keyword: Suchbegriff
            page: Seitennummer
            min_price: Minimaler Preis
            max_price: Maximaler Preis
            condition: Artikelzustand
            
        Returns:
            Vollständige Such-URL
        """
        pass

    def _get_headers(self) -> Dict[str, str]:
        """
        Generiert erweiterte Browser-Header für Anfragen.
        
        Returns:
            Dictionary mit Header-Informationen
        """
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
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        }

    def _make_request(self, url: str, method: str = 'GET', data: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Führt eine HTTP-Anfrage mit Retry-Mechanismus durch.
        
        Args:
            url: Ziel-URL
            method: HTTP-Methode ('GET' oder 'POST')
            data: Optional - Daten für POST-Anfragen
            
        Returns:
            Response-Objekt oder None bei Fehler
        """
        for attempt in range(self.retry_count):
            try:
                # Wähle zufälligen Proxy falls verfügbar
                proxy = random.choice(self.proxies) if self.proxies else None
                proxy_dict = {'http': proxy, 'https': proxy} if proxy else None

                # Aktualisiere Headers für diese Anfrage
                current_headers = self._get_headers()
                
                # Führe Anfrage durch
                if method.upper() == 'POST':
                    response = self.session.post(
                        url,
                        headers=current_headers,
                        proxies=proxy_dict,
                        json=data,
                        timeout=self.session.timeout
                    )
                else:
                    response = self.session.get(
                        url,
                        headers=current_headers,
                        proxies=proxy_dict,
                        timeout=self.session.timeout
                    )

                # Überprüfe Response
                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"{self.shop_name}: Anfrage fehlgeschlagen (Versuch {attempt + 1}/{self.retry_count}): {str(e)}"
                )
                if attempt < self.retry_count - 1:
                    delay = self.retry_delay * (attempt + 1)  # Progressives Delay
                    time.sleep(delay)
                continue

        return None

    def _search_page(self, url: str) -> List[Dict[str, Any]]:
        """
        Durchsucht eine einzelne Seite mit Retry-Mechanismus.
        
        Args:
            url: URL der zu durchsuchenden Seite
            
        Returns:
            Liste gefundener Artikel
        """
        try:
            logger.debug(f"{self.shop_name}: Starte Suche auf URL: {url}")
            
            response = self._make_request(url)
            if not response:
                logger.error(f"{self.shop_name}: Keine Antwort erhalten für URL: {url}")
                return []

            if response.status_code == 200:
                # Prüfe Content-Type
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/json' in content_type:
                    # Verarbeite JSON-Antwort
                    try:
                        json_data = response.json()
                        logger.debug(f"{self.shop_name}: JSON-Daten erfolgreich empfangen")
                        if hasattr(self, '_parse_api_response'):
                            return self._parse_api_response(json_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"{self.shop_name}: Fehler beim JSON-Parsing: {e}")
                        return []
                else:
                    # Verarbeite HTML-Antwort
                    soup = BeautifulSoup(response.text, 'html.parser')
                    logger.debug(f"{self.shop_name}: HTML erfolgreich geparst")
                    return self._parse_page(soup)
            else:
                logger.warning(f"{self.shop_name}: Unerwarteter Status Code: {response.status_code}")

        except Exception as e:
            logger.error(f"{self.shop_name}: Fehler bei der Seitenverarbeitung: {str(e)}")

        return []

    def search(self, keyword: str, max_pages: int = 3, min_price: Optional[float] = None, 
              max_price: Optional[float] = None, condition: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Führt eine Suche durch und speichert in der Datenbank.
        
        Args:
            keyword: Suchbegriff
            max_pages: Maximale Anzahl zu durchsuchender Seiten
            min_price: Minimaler Preis
            max_price: Maximaler Preis
            condition: Artikelzustand
            
        Returns:
            Liste gefundener Artikel
        """
        logger.info(f"{self.shop_name}: Starte Suche für: {keyword}")
        all_items = []

        try:
            urls = [
                self._build_search_url(keyword, page, min_price, max_price, condition)
                for page in range(1, max_pages + 1)
            ]

            with ThreadPoolExecutor(max_workers=min(3, max_pages)) as executor:
                future_to_url = {executor.submit(self._search_page, url): url for url in urls}

                for future in future_to_url:
                    try:
                        items = future.result(timeout=30)
                        with self.lock:
                            all_items.extend(items)
                    except Exception as e:
                        logger.error(f"{self.shop_name}: Fehler bei der Verarbeitung der Suchergebnisse: {str(e)}")

            if all_items:
                logger.debug(f"{self.shop_name}: Speichere {len(all_items)} Ergebnisse in der Datenbank")
                self.db_manager.save_search_results(self.shop_name, keyword, all_items)

            logger.info(f"{self.shop_name}: Suche abgeschlossen. {len(all_items)} Artikel gefunden.")
            return all_items

        except Exception as e:
            logger.error(f"{self.shop_name}: Kritischer Fehler bei der Suche: {str(e)}")
            return []

    def get_saved_results(self, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Lädt gespeicherte Suchergebnisse aus der Datenbank.
        
        Args:
            keyword: Optional - Suchbegriff zum Filtern
            
        Returns:
            Liste gespeicherter Suchergebnisse
        """
        try:
            return self.db_manager.get_search_results(self.shop_name, keyword) if keyword else []
        except Exception as e:
            logger.error(f"{self.shop_name}: Fehler beim Laden der Ergebnisse: {str(e)}")
            return []

    def add_proxy(self, proxy: str) -> None:
        """
        Fügt einen Proxy zur Proxy-Liste hinzu.
        
        Args:
            proxy: Proxy-URL
        """
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            logger.debug(f"{self.shop_name}: Proxy hinzugefügt: {proxy}")

    def clear_proxies(self) -> None:
        """Leert die Proxy-Liste."""
        self.proxies = []
        logger.debug(f"{self.shop_name}: Proxy-Liste geleert")

    def get_proxy_count(self) -> int:
        """
        Gibt die Anzahl der verfügbaren Proxies zurück.
        
        Returns:
            Anzahl der Proxies
        """
        return len(self.proxies)