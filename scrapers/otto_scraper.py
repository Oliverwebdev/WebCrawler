from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import time
import json
import re

logger = logging.getLogger('OttoScraper')

class OttoScraper(BaseScraper):
    def __init__(self, db_manager):
        """
        Initialisiert den Otto-Scraper.
        
        Args:
            db_manager: Datenbankmanager-Instanz
        """
        self.additional_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'de-DE,de;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        }
        
        super().__init__(db_manager, "otto")
        self.retry_delay = 3

    @property
    def base_url(self) -> str:
        """Basis-URL für Otto-Suche"""
        return "https://www.otto.de/suche"

    def _build_search_url(self, keyword: str, page: int = 1, min_price: Optional[float] = None,
                         max_price: Optional[float] = None, condition: Optional[str] = None) -> str:
        """
        Erstellt die Such-URL für Otto.
        
        Args:
            keyword: Suchbegriff
            page: Seitennummer
            min_price: Minimaler Preis
            max_price: Maximaler Preis
            condition: Artikelzustand (wird bei Otto nicht verwendet)
            
        Returns:
            Vollständige Such-URL
        """
        # Basis-URL mit Suchbegriff
        keyword_formatted = keyword.replace(' ', '+').lower()
        url = f"{self.base_url}/{keyword_formatted}/"
        
        # Parameter hinzufügen
        params = []
        
        if page > 1:
            params.append(f"page={page}")
            
        if min_price is not None:
            params.append(f"priceMin={min_price}")
            
        if max_price is not None:
            params.append(f"priceMax={max_price}")
            
        # Parameter zur URL hinzufügen
        if params:
            url += "?" + "&".join(params)
            
        logger.debug(f"Generierte Otto-URL: {url}")
        return url

    def _get_headers(self) -> Dict[str, str]:
        """Erweiterte Headers für Otto-Anfragen."""
        base_headers = super()._get_headers()
        base_headers.update(self.additional_headers)
        return base_headers

    def _parse_price(self, price_text: str) -> str:
        """
        Extrahiert und formatiert den Preis.
        
        Args:
            price_text: Rohtext des Preises
            
        Returns:
            Formatierter Preis als String
        """
        try:
            if not price_text:
                return "Nicht verfügbar"

            # Suche nach Preismustern
            price_pattern = r'(\d+[.,]\d{2})'
            matches = re.findall(price_pattern, price_text)
            
            if matches:
                price = matches[0]
                if '.' in price:
                    price = price.replace('.', ',')
                return f"{price}€"
            
            # Alternative: Suche nach ganzen Zahlen
            price_pattern = r'(\d+)'
            matches = re.findall(price_pattern, price_text)
            
            if matches:
                return f"{matches[0]},00€"

            return "Nicht verfügbar"

        except Exception as e:
            logger.error(f"Fehler beim Parsen des Preises: {e}")
            return "Nicht verfügbar"

    def _parse_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extrahiert Produktinformationen aus der Otto-Webseite.
        
        Args:
            soup: BeautifulSoup Objekt der Seite
            
        Returns:
            Liste von Produktdaten
        """
        items = []
        try:
            # Debug-Ausgabe der ersten 1000 Zeichen des HTML
            html_sample = str(soup)[:1000]
            logger.debug(f"HTML Sample: {html_sample}")

            # Versuche verschiedene Container-Selektoren
            product_containers = []
            
            # Methode 1: Suche nach allen Artikeln
            products = soup.find_all('article')
            if products:
                logger.debug(f"Gefunden via article: {len(products)}")
                product_containers.extend(products)

            # Methode 2: Suche nach spezifischen Klassen
            products = soup.find_all(class_=lambda x: x and ('product' in x.lower() or 'article' in x.lower()))
            if products:
                logger.debug(f"Gefunden via class: {len(products)}")
                product_containers.extend(products)

            # Methode 3: Suche nach data-Attributen
            products = soup.find_all(lambda tag: any(attr for attr in tag.attrs if 'data-' in attr and 'product' in tag[attr].lower()))
            if products:
                logger.debug(f"Gefunden via data-attributes: {len(products)}")
                product_containers.extend(products)

            # Methode 4: Suche nach spezifischen Grid-Containern
            grid_container = soup.find('div', {'data-testid': 'grid-container'})
            if grid_container:
                products = grid_container.find_all('div', recursive=False)
                logger.debug(f"Gefunden via grid-container: {len(products)}")
                product_containers.extend(products)

            # Entferne Duplikate
            product_containers = list(set(product_containers))
            logger.debug(f"Gefundene Produkte nach Deduplizierung: {len(product_containers)}")

            for container in product_containers:
                try:
                    # Debug-Ausgabe des Container-HTML
                    container_html = str(container)[:200]
                    logger.debug(f"Container Sample: {container_html}")

                    # Titel suchen
                    title = None
                    title_candidates = [
                        container.find('h2'),
                        container.find('h3'),
                        container.find(class_=lambda x: x and 'title' in x.lower()),
                        container.find(attrs={'data-testid': lambda x: x and 'title' in x.lower()}),
                        container.find(attrs={'data-qa': lambda x: x and 'title' in x.lower()}),
                        container.find('a', class_=lambda x: x and 'product' in x.lower())
                    ]
                    for candidate in title_candidates:
                        if candidate:
                            title = candidate.get_text().strip()
                            break

                    if not title:
                        continue

                    # Link suchen
                    link = None
                    link_candidates = [
                        container.find('a', href=True),
                        container.find('a', class_=lambda x: x and 'product' in x.lower()),
                        container.find(attrs={'data-testid': lambda x: x and 'link' in x.lower()})
                    ]
                    for link_elem in link_candidates:
                        if link_elem and 'href' in link_elem.attrs:
                            link = link_elem['href']
                            if not link.startswith('http'):
                                link = 'https://www.otto.de' + link
                            break

                    if not link:
                        continue

                    # Preis suchen
                    price = None
                    price_candidates = [
                        container.find(class_=lambda x: x and 'price' in x.lower()),
                        container.find(attrs={'data-testid': lambda x: x and 'price' in x.lower()}),
                        container.find(attrs={'data-qa': lambda x: x and 'price' in x.lower()}),
                        container.find('span', string=lambda x: x and '€' in x)
                    ]
                    for candidate in price_candidates:
                        if candidate:
                            price_text = candidate.get_text().strip()
                            price = self._parse_price(price_text)
                            if price != "Nicht verfügbar":
                                break

                    if price == "Nicht verfügbar":
                        continue

                    # Versand suchen
                    shipping = "Versand: siehe Website"
                    shipping_candidates = [
                        container.find(class_=lambda x: x and 'shipping' in x.lower()),
                        container.find(attrs={'data-testid': lambda x: x and 'shipping' in x.lower()}),
                        container.find(attrs={'data-qa': lambda x: x and 'shipping' in x.lower()}),
                        container.find(string=lambda x: x and 'versand' in x.lower() if x else False)
                    ]
                    for candidate in shipping_candidates:
                        if candidate:
                            shipping = candidate.get_text().strip()
                            break

                    item = {
                        'title': title,
                        'price': price,
                        'link': link,
                        'shipping': shipping,
                        'location': 'Otto.de',
                        'timestamp': datetime.now().isoformat()
                    }
                    items.append(item)
                    logger.debug(f"Gefundenes Produkt: {title} - {price}")

                except Exception as e:
                    logger.error(f"Fehler beim Parsen eines Produkts: {e}")
                    continue

        except Exception as e:
            logger.error(f"Fehler beim Parsen der Seite: {e}")

        logger.debug(f"Erfolgreich {len(items)} Otto-Produkte geparst")
        return items