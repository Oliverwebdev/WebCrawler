from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import time

logger = logging.getLogger('KleinanzeigenScraper')

class KleinanzeigenScraper:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.base_url = "https://www.kleinanzeigen.de/s-suche"
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Browser im Hintergrund ausführen
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)


    def _simulate_human_behavior(self):
        delay = random.uniform(1, 3)
        logger.debug(f"Simuliere menschliches Verhalten: Wartezeit {delay:.2f} Sekunden")
        time.sleep(delay)

    def _build_search_url(self, keyword, page=1):
        keyword_formatted = keyword.replace(" ", "-").lower()
        return f"{self.base_url}/{keyword_formatted}/seite:{page}"

    def _parse_page(self, soup):
        items = []
        for ad in soup.find_all("article", class_="aditem"):
            try:
                title_elem = ad.find("a", class_="ellipsis")
                title = title_elem.get_text(strip=True) if title_elem else "Kein Titel"

                price_elem = ad.find("p", class_="aditem-main--price")
                price = price_elem.get_text(strip=True) if price_elem else "Nicht verfügbar"

                link_elem = ad.find("a", href=True)
                link = link_elem["href"] if link_elem and "href" in link_elem.attrs else None
                if link and not link.startswith("http"):
                    link = f"https://www.kleinanzeigen.de{link}"

                location_elem = ad.find("div", class_="aditem-main--top--left")
                location = location_elem.get_text(strip=True) if location_elem else "Unbekannter Standort"

                if not link:
                    logger.warning("Artikel ohne gültigen Link übersprungen.")
                    continue

                item = {
                    "title": title,
                    "price": price,
                    "link": link,
                    "location": location,
                    "source": "kleinanzeigen",
                    "timestamp": datetime.now().isoformat(),
                }
                items.append(item)
            except Exception as e:
                logger.warning(f"Fehler beim Parsen eines Artikels: {e}")
        return items

    def search(self, keyword, max_pages=3, min_price=None, max_price=None, condition=None):
        try:
            url = self._build_search_url(keyword, page)
            self.driver.get(url)
            self._simulate_human_behavior()

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            results = self._parse_page(soup)

            if results:
                self.db_manager.save_search_results(results)

            return results
        except Exception as e:
            logger.error(f"Fehler bei der Suche: {e}")
            return []
        finally:
            self.driver.quit()
