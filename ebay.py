import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from bs4 import BeautifulSoup
import random
import time
import json
from fake_useragent import UserAgent
import pandas as pd
from datetime import datetime
import threading


class EbayScraper:
    def __init__(self):
        # Liste von gängigen User Agents für Rotation
        self.ua = UserAgent()

        # Basis-URL für eBay Suche
        self.base_url = "https://www.ebay.de/sch/i.html?_nkw={}"

        # Verschiedene Proxy-Server (hier müssten Sie Ihre eigenen einfügen)
        self.proxies = [
            # Fügen Sie hier Ihre Proxy-Server ein
            # Format: "http://ip:port"
        ]

        # Speicherort für Ergebnisse
        self.results_file = "ebay_results.json"

    def _get_headers(self):
        """Generiert zufällige Headers für jede Anfrage"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def _get_random_delay(self):
        """Generiert eine zufällige Verzögerung zwischen Anfragen"""
        return random.uniform(2, 5)

    def search(self, keyword, max_pages=3):
        """Durchsucht eBay nach einem Suchbegriff"""
        all_items = []

        for page in range(1, max_pages + 1):
            # Zufällige Verzögerung zwischen Anfragen
            time.sleep(self._get_random_delay())

            # URL für aktuelle Seite
            url = self.base_url.format(keyword)
            if page > 1:
                url += f"&_pgn={page}"

            try:
                # Proxy rotieren (falls vorhanden)
                proxy = random.choice(self.proxies) if self.proxies else None

                # Anfrage senden
                response = requests.get(
                    url,
                    headers=self._get_headers(),
                    proxies={'http': proxy, 'https': proxy} if proxy else None,
                    timeout=10
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    items = self._parse_page(soup)
                    all_items.extend(items)
                else:
                    print(f"Fehler bei Seite {page}: Status Code {
                          response.status_code}")

            except Exception as e:
                print(f"Fehler beim Scraping von Seite {page}: {str(e)}")
                continue

        # Ergebnisse speichern
        self._save_results(keyword, all_items)
        return all_items

    def _parse_page(self, soup):
        """Extrahiert Artikel-Informationen von einer Seite"""
        items = []

        # Suche nach Artikeln auf der Seite
        listings = soup.find_all('div', class_='s-item__wrapper')

        for listing in listings:
            try:
                # Basis-Informationen extrahieren
                title = listing.find('div', class_='s-item__title')
                price = listing.find('span', class_='s-item__price')
                link = listing.find('a', class_='s-item__link')

                if title and price and link:
                    item = {
                        'title': title.get_text(strip=True),
                        'price': price.get_text(strip=True),
                        'link': link.get('href'),
                        'timestamp': datetime.now().isoformat()
                    }
                    items.append(item)
            except Exception as e:
                print(f"Fehler beim Parsen eines Artikels: {str(e)}")
                continue

        return items

    def _save_results(self, keyword, items):
        """Speichert die Ergebnisse in einer JSON-Datei"""
        data = {
            'keyword': keyword,
            'timestamp': datetime.now().isoformat(),
            'items': items
        }

        try:
            # Existierende Daten laden
            existing_data = []
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except FileNotFoundError:
                pass

            # Neue Daten hinzufügen
            existing_data.append(data)

            # Daten speichern
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Fehler beim Speichern der Ergebnisse: {str(e)}")

    def get_saved_results(self, keyword=None):
        """Lädt gespeicherte Ergebnisse"""
        try:
            with open(self.results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if keyword:
                # Filtern nach Suchbegriff
                data = [d for d in data if d['keyword'].lower() ==
                        keyword.lower()]

            return data
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"Fehler beim Laden der Ergebnisse: {str(e)}")
            return []


class EbayScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("eBay Artikel-Suche")
        self.root.geometry("800x600")
        self.scraper = EbayScraper()

        # Style konfigurieren
        self.style = ttk.Style()
        self.style.configure('TButton', padding=6)
        self.style.configure('TLabel', padding=6)
        self.style.configure('TFrame', padding=10)

        self.create_widgets()

    def create_widgets(self):
        # Hauptcontainer
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Suchbereich
        search_frame = ttk.LabelFrame(main_frame, text="Suche", padding=10)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        # Suchfeld und Button
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(
            search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)

        self.pages_var = tk.StringVar(value="3")
        ttk.Label(search_frame, text="Seiten:").pack(side=tk.LEFT, padx=5)
        pages_entry = ttk.Entry(
            search_frame, textvariable=self.pages_var, width=5)
        pages_entry.pack(side=tk.LEFT, padx=5)

        self.search_button = ttk.Button(
            search_frame, text="Suchen", command=self.start_search)
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.progress_var = tk.StringVar(value="Bereit")
        progress_label = ttk.Label(
            search_frame, textvariable=self.progress_var)
        progress_label.pack(side=tk.LEFT, padx=5)

        # Ergebnisbereich
        results_frame = ttk.LabelFrame(
            main_frame, text="Ergebnisse", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Treeview für Ergebnisse
        columns = ('Titel', 'Preis', 'Link')
        self.tree = ttk.Treeview(
            results_frame, columns=columns, show='headings')

        # Scrollbars für Treeview
        vsb = ttk.Scrollbar(results_frame, orient="vertical",
                            command=self.tree.yview)
        hsb = ttk.Scrollbar(
            results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Treeview-Spalten konfigurieren
        self.tree.heading('Titel', text='Titel')
        self.tree.heading('Preis', text='Preis')
        self.tree.heading('Link', text='Link')

        self.tree.column('Titel', width=300)
        self.tree.column('Preis', width=100)
        self.tree.column('Link', width=300)

        # Treeview und Scrollbars packen
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)

        # Status-Leiste
        self.status_var = tk.StringVar(
            value="Willkommen! Geben Sie einen Suchbegriff ein.")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, padx=5, pady=5)

        # Buttons für gespeicherte Ergebnisse
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="Gespeicherte Ergebnisse laden",
                   command=self.load_saved_results).pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Ergebnisse speichern",
                   command=self.save_current_results).pack(side=tk.LEFT, padx=5)

        # Ergebniszähler
        self.count_var = tk.StringVar(value="Gefundene Artikel: 0")
        count_label = ttk.Label(button_frame, textvariable=self.count_var)
        count_label.pack(side=tk.RIGHT, padx=5)

    def start_search(self):
        """Startet die Suche in einem separaten Thread"""
        keyword = self.search_var.get().strip()
        if not keyword:
            messagebox.showwarning(
                "Warnung", "Bitte geben Sie einen Suchbegriff ein!")
            return

        try:
            max_pages = int(self.pages_var.get())
        except ValueError:
            messagebox.showwarning(
                "Warnung", "Bitte geben Sie eine gültige Seitenzahl ein!")
            return

        self.search_button.state(['disabled'])
        self.progress_var.set("Suche läuft...")
        self.status_var.set(f"Suche nach '{keyword}'...")

        # Treeview leeren
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Suche in separatem Thread starten
        thread = threading.Thread(
            target=self.perform_search, args=(keyword, max_pages))
        thread.daemon = True
        thread.start()

    def perform_search(self, keyword, max_pages):
        """Führt die Suche aus und aktualisiert die GUI"""
        try:
            results = self.scraper.search(keyword, max_pages)
            self.root.after(0, self.update_results, results)
        except Exception as e:
            self.root.after(0, self.show_error, str(e))
        finally:
            self.root.after(0, self.search_completed)

    def update_results(self, results):
        """Aktualisiert die Treeview mit den Suchergebnissen"""
        for item in results:
            self.tree.insert('', tk.END, values=(
                item['title'],
                item['price'],
                item['link']
            ))
        self.count_var.set(f"Gefundene Artikel: {len(results)}")

    def show_error(self, error_message):
        """Zeigt eine Fehlermeldung an"""
        messagebox.showerror(
            "Fehler", f"Fehler bei der Suche: {error_message}")

    def search_completed(self):
        """Wird aufgerufen, wenn die Suche abgeschlossen ist"""
        self.search_button.state(['!disabled'])
        self.progress_var.set("Bereit")
        self.status_var.set("Suche abgeschlossen")

    def load_saved_results(self):
        """Lädt gespeicherte Suchergebnisse"""
        try:
            results = self.scraper.get_saved_results()
            if not results:
                messagebox.showinfo(
                    "Info", "Keine gespeicherten Ergebnisse gefunden.")
                return

            # Treeview leeren
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Alle gespeicherten Ergebnisse anzeigen
            total_items = 0
            for search in results:
                for item in search['items']:
                    self.tree.insert('', tk.END, values=(
                        item['title'],
                        item['price'],
                        item['link']
                    ))
                    total_items += 1

            self.count_var.set(f"Gefundene Artikel: {total_items}")
            self.status_var.set("Gespeicherte Ergebnisse geladen")

        except Exception as e:
            messagebox.showerror(
                "Fehler", f"Fehler beim Laden der Ergebnisse: {str(e)}")

    def save_current_results(self):
        """Speichert die aktuellen Ergebnisse"""
        items = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            items.append({
                'title': values[0],
                'price': values[1],
                'link': values[2],
                'timestamp': datetime.now().isoformat()
            })

        if not items:
            messagebox.showwarning(
                "Warnung", "Keine Ergebnisse zum Speichern vorhanden!")
            return

        try:
            self.scraper._save_results(self.search_var.get(), items)
            messagebox.showinfo("Erfolg", "Ergebnisse wurden gespeichert!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")
        items = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            items.append({
                'title': values[0],
                'price': values[1],
                'link': values[2],
                'timestamp': datetime.now().isoformat()
            })

        if not items:
            messagebox.showwarning(
                "Warnung", "Keine Ergebnisse zum Speichern vorhanden!")
            return

        try:
            self.scraper._save_results(self.search_var.get(), items)
            messagebox.showinfo("Erfolg", "Ergebnisse wurden gespeichert!")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {str(e)}")


def main():
    root = tk.Tk()
    app = EbayScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
