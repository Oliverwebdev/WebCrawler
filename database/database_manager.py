import sqlite3
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger('DatabaseManager')


class DatabaseManager:
    def __init__(self, db_path: str = 'utils/scraper.db'):
        """Initialisiert die Datenbankverbindung."""
        self.db_path = db_path
        self.conn = None
        self.setup_database()

    def setup_database(self):
        """Erstellt die Datenbankverbindung und initialisiert Tabellen."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row

            # Lese SQL-Schema aus Datei
            schema_path = Path('database/schema.sql')
            if schema_path.exists():
                with open(schema_path, 'r', encoding='utf-8') as f:
                    self.conn.executescript(f.read())

            self.conn.commit()
            logger.info("Datenbank erfolgreich initialisiert")
        except Exception as e:
            logger.error(f"Fehler bei Datenbankinitialisierung: {e}")
            raise

    def migrate_from_json(self):
        """Migriert Daten von JSON-Dateien in die SQL-Datenbank."""
        try:
            # Migriere Einstellungen
            settings_path = Path('utils/user_settings.json')
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                    self.save_settings(settings_data.get('settings', {}))
                    self.save_favorites(settings_data.get('favorites', []))

            # Migriere eBay-Ergebnisse
            self._migrate_results('utils/ebay_results.json', 'ebay')

            # Migriere Amazon-Ergebnisse
            self._migrate_results('utils/amazon_results.json', 'amazon')

            logger.info("Migration erfolgreich abgeschlossen")
        except Exception as e:
            logger.error(f"Fehler bei der Migration: {e}")

    def _migrate_results(self, file_path: str, source: str):
        """Migriert Suchergebnisse von JSON in die Datenbank."""
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                results_data = json.load(f)
                for result in results_data:
                    self.save_search_results(
                        source,
                        result['keyword'],
                        result['items']
                    )

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Speichert oder aktualisiert Einstellungen."""
        try:
            sql = '''INSERT OR REPLACE INTO settings 
                    (max_pages, default_search_period) 
                    VALUES (?, ?)'''
            self.conn.execute(sql, (
                settings.get('max_pages', 3),
                settings.get('default_search_period', 30)
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Einstellungen: {e}")
            return False

    def get_settings(self) -> Dict[str, Any]:
        """Lädt die gespeicherten Einstellungen."""
        try:
            cursor = self.conn.execute('SELECT * FROM settings LIMIT 1')
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {
                'max_pages': 3,
                'default_search_period': 30
            }
        except Exception as e:
            logger.error(f"Fehler beim Laden der Einstellungen: {e}")
            return {}

    def save_favorites(self, favorites: List[Dict[str, Any]]) -> bool:
        """Speichert Favoriten in der Datenbank."""
        try:
            sql = '''INSERT OR REPLACE INTO favorites 
                    (title, price, link, source) 
                    VALUES (?, ?, ?, ?)'''
            for fav in favorites:
                self.conn.execute(sql, (
                    fav['title'],
                    fav['price'],
                    fav['link'],
                    fav['source']
                ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Favoriten: {e}")
            return False

    def get_favorites(self) -> List[Dict[str, Any]]:
        """Lädt alle gespeicherten Favoriten."""
        try:
            cursor = self.conn.execute(
                'SELECT * FROM favorites ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Fehler beim Laden der Favoriten: {e}")
            return []

    def delete_favorite(self, link: str) -> bool:
        """Löscht einen Favoriten anhand des Links."""
        try:
            self.conn.execute('DELETE FROM favorites WHERE link = ?', (link,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen des Favoriten: {e}")
            return False

    def clear_favorites(self):
        """Löscht alle Favoriten aus der Datenbank."""
        try:
            self.conn.execute('DELETE FROM favorites')
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen aller Favoriten: {e}")
            return False

    def save_search_results(self, source: str, keyword: str, items: List[Dict[str, Any]]) -> bool:
        """Speichert Suchergebnisse in der Datenbank."""
        try:
            sql = '''INSERT INTO search_results 
                    (source, keyword, title, price, link, shipping, location) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)'''
            for item in items:
                self.conn.execute(sql, (
                    source,
                    keyword,
                    item['title'],
                    item['price'],
                    item['link'],
                    item.get('shipping', ''),
                    item.get('location', '')
                ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Suchergebnisse: {e}")
            return False

    def get_search_results(self, source: str, keyword: str, order_by: str = None) -> List[Dict[str, Any]]:
        """Lädt Suchergebnisse für eine bestimmte Quelle und Keyword."""
        try:
            sql = '''SELECT * FROM search_results 
                    WHERE source = ? AND keyword = ?'''
            if order_by:
                sql += f' ORDER BY {order_by}'
            cursor = self.conn.execute(sql, (source, keyword))
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Fehler beim Laden der Suchergebnisse: {e}")
            return []

    def export_search_results_to_csv(self, filename: str, keyword: str = None) -> bool:
        """Exportiert Suchergebnisse in eine CSV-Datei."""
        try:
            import csv

            sql = 'SELECT * FROM search_results'
            params = []

            if keyword:
                sql += ' WHERE keyword = ?'
                params.append(keyword)

            cursor = self.conn.execute(sql, params)
            results = cursor.fetchall()

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'source', 'keyword', 'title', 'price', 'link',
                    'shipping', 'location', 'timestamp'
                ])
                writer.writeheader()
                writer.writerows([dict(row) for row in results])

            return True
        except Exception as e:
            logger.error(f"Fehler beim CSV-Export: {e}")
            return False

    def __del__(self):
        """Schließt die Datenbankverbindung beim Beenden."""
        if self.conn:
            self.conn.close()
