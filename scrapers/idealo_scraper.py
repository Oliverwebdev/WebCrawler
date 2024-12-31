import logging
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
import re
from .base_scraper import BaseScraper

logger = logging.getLogger('IdealoScraper')

class IdealoScraper(BaseScraper):
    """Scraper für Idealo.de mit erweiterter Fehlerbehandlung und Robustheit"""
    
    def _init_(self, db_manager):
        """
        Initialisiert den IdealoScraper.
        
        Args:
            db_manager: Datenbankmanager-Instanz für die Datenpersistenz
        """
        super().__init__(db_manager, "ebay")  # Zuerst BaseScraper initialisieren

        self.retry_delay = 3
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1'
        })
        
        # Cache für bereits gesehene Produkt-IDs in einer Suchsession
        self._seen_products = set()
        
        # Kompilierte Regex-Patterns für bessere Performance
        self._price_pattern = re.compile(r'(\d+(?:\.\d{3})(?:,\d{2})?)\s€')
        self._product_id_pattern = re.compile(r'/([A-Za-z0-9-]+)\.html')

    @property
    def base_url(self) -> str:
        """Basis-URL für Idealo-Suche"""
        return "https://www.idealo.de/preisvergleich/MainSearchProductCategory.html"

    def _build_search_url(self, keyword: str, page: int = 1, min_price: Optional[float] = None, 
                         max_price: Optional[float] = None, condition: Optional[str] = None) -> str:
        """
        Erstellt die Such-URL mit allen Parametern.
        
        Args:
            keyword: Suchbegriff
            page: Seitennummer (1-basiert)
            min_price: Minimaler Preis
            max_price: Maximaler Preis
            condition: Artikelzustand (neu/gebraucht)
            
        Returns:
            Vollständige Such-URL
        """
        try:
            # Basis-Parameter
            params = [('q', keyword)]
            
            # Seitennummer (Idealo verwendet 0-basierte Paginierung)
            if page > 1:
                params.append(('p', str(page - 1)))
            
            # Preisbereich
            if min_price is not None:
                params.append(('price_min', str(min_price)))
            if max_price is not None:
                params.append(('price_max', str(max_price)))
                
            # Artikelzustand
            if condition:
                condition_map = {
                    'neu': 'new',
                    'gebraucht': 'used'
                }
                if condition.lower() in condition_map:
                    params.append(('condition', condition_map[condition.lower()]))
            
            # URL zusammenbauen
            param_str = '&'.join(f"{k}={v}" for k, v in params)
            url = f"{self.base_url}?{param_str}"
            
            logger.debug(f"Generierte Such-URL: {url}")
            return url
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Such-URL: {e}")
            # Fallback zur einfachen Suche
            return f"{self.base_url}?q={keyword}"

    def _extract_product_id(self, url: str) -> Optional[str]:
        """
        Extrahiert die Produkt-ID aus einer Idealo-URL.
        
        Args:
            url: Produkt-URL
            
        Returns:
            Produkt-ID oder None wenn nicht gefunden
        """
        try:
            match = self._product_id_pattern.search(url)
            return match.group(1) if match else None
        except Exception as e:
            logger.error(f"Fehler beim Extrahieren der Produkt-ID: {e}")
            return None

    def _normalize_price(self, price_text: str) -> str:
        """
        Normalisiert den Preis in ein einheitliches Format.
        
        Args:
            price_text: Roher Preistext
            
        Returns:
            Normalisierter Preis im Format "XX,XX€"
        """
        try:
            if not price_text or price_text.lower() == 'nicht verfügbar':
                return "Nicht verfügbar"

            # Entferne alle Whitespaces und "ab"
            price_text = price_text.strip().lower().replace('ab', '').strip()
            
            # Suche nach Preis mit regulärem Ausdruck
            match = self._price_pattern.search(price_text)
            if not match:
                return "Nicht verfügbar"
                
            price = match.group(1)
            
            # Normalisiere Tausendertrennzeichen
            if '.' in price and ',' in price:
                # Format: 1.234,56
                price = price.replace('.', '')
            elif '.' in price:
                # Format: 1234.56
                price = price.replace('.', ',')
                
            return f"{price}€"
            
        except Exception as e:
            logger.error(f"Fehler bei der Preisnormalisierung: {e}")
            return "Nicht verfügbar"

    def _extract_shipping(self, container: Tag) -> str:
        """
        Extrahiert die Versandinformationen.
        
        Args:
            container: BeautifulSoup Tag des Produktcontainers
            
        Returns:
            Versandinformation als String
        """
        try:
            shipping_selectors = [
                '.offerList-item-shipment',
                '.delivery-info',
                '[data-test="shipping-cost"]'
            ]
            
            for selector in shipping_selectors:
                shipping_elem = container.select_one(selector)
                if shipping_elem:
                    shipping_text = shipping_elem.get_text(strip=True)
                    if shipping_text:
                        return shipping_text
            
            return "Versand: siehe Website"
            
        except Exception as e:
            logger.error(f"Fehler beim Extrahieren der Versandinformation: {e}")
            return "Versand: siehe Website"

    def _parse_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extrahiert Produktinformationen aus der Idealo-Webseite.
        
        Args:
            soup: BeautifulSoup Objekt der Seite
            
        Returns:
            Liste von Produktdaten
        """
        items = []
        try:
            # Verschiedene Selektoren für Produktcontainer probieren
            selectors = [
                'div.offerList-item',
                'article.productList-box',
                '[data-test="product-row"]'
            ]
            
            product_list = []
            for selector in selectors:
                product_list = soup.select(selector)
                if product_list:
                    logger.debug(f"Produktliste gefunden mit Selector: {selector}")
                    break
                    
            if not product_list:
                logger.warning("Keine Produktliste gefunden")
                # Prüfe auf Captcha oder andere Blockaden
                if any(text in str(soup).lower() for text in ['captcha', 'blocked', 'access denied']):
                    logger.error("Möglicherweise durch Anti-Bot-Maßnahmen blockiert")
                return []

            for product in product_list:
                try:
                    # Extrahiere Link und ID
                    link_elem = product.select_one('a.offerList-item-description-title, [data-test="product-link"]')
                    if not link_elem or not link_elem.get('href'):
                        continue
                        
                    link = link_elem['href']
                    if not link.startswith('http'):
                        link = urljoin('https://www.idealo.de', link)
                        
                    product_id = self._extract_product_id(link)
                    if not product_id or product_id in self._seen_products:
                        continue
                    self._seen_products.add(product_id)
                    
                    # Extrahiere Titel
                    title = link_elem.get_text(strip=True)
                    if not title:
                        continue
                    
                    # Extrahiere Preis
                    price_elem = product.select_one('.offerList-item-priceMin, [data-test="price"]')
                    if not price_elem:
                        continue
                    price = self._normalize_price(price_elem.get_text(strip=True))
                    if price == "Nicht verfügbar":
                        continue
                    
                    # Extrahiere Versandinformation
                    shipping = self._extract_shipping(product)
                    
                    # Erstelle Artikel-Dictionary
                    item = {
                        'title': title,
                        'price': price,
                        'link': link,
                        'shipping': shipping,
                        'location': 'Idealo.de',
                        'timestamp': datetime.now().isoformat()
                    }
                    items.append(item)
                    
                except Exception as e:
                    logger.error(f"Fehler beim Parsen eines Produkts: {e}")
                    continue

        except Exception as e:
            logger.error(f"Fehler beim Parsen der Seite: {e}")
            
        finally:
            # Log Statistiken
            logger.info(f"Erfolgreich {len(items)} Produkte von Idealo extrahiert")
            
        return items

    def search(self, keyword: str, max_pages: int = 3, min_price: Optional[float] = None,
              max_price: Optional[float] = None, condition: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Führt eine Suche auf Idealo durch.
        
        Überschreibt die Basismethode um das Produkt-Cache zurückzusetzen.
        
        Args:
            keyword: Suchbegriff
            max_pages: Maximale Anzahl zu durchsuchender Seiten
            min_price: Minimaler Preis
            max_price: Maximaler Preis
            condition: Artikelzustand
            
        Returns:
            Liste gefundener Artikel
        """
        # Reset Produkt-Cache für neue Suche
        self._seen_products.clear()
        
        # Führe normale Suche durch
        return super().search(keyword, max_pages, min_price, max_price, condition)  