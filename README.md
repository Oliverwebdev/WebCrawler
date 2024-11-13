# Smart Shopping Assistant 🛍️

Ein intelligenter Shopping-Assistant, der aktuell eBay-Produkte durchsucht und analysiert, mit dem langfristigen Ziel, eine umfassende Cross-Platform-Shopping-Lösung zu werden.

## 🌟 Features

### Aktuelle Funktionen
- **Intelligente eBay-Suche**
  - Parallele Verarbeitung mehrerer Suchanfragen
  - Fortschrittliche Fehlerbehandlung und Retry-Mechanismen
  - Dynamische User-Agent-Rotation für stabilere Anfragen
  - Proxy-Unterstützung für verbesserte Skalierbarkeit

- **Benutzerfreundliche GUI**
  - Moderne, responsive Benutzeroberfläche mit Tkinter
  - Echtzeit-Suchfortschrittsanzeige
  - Erweiterte Filteroptionen (Preis, Zustand)
  - Sortierungsmöglichkeiten nach verschiedenen Kriterien

- **Favoriten-System**
  - Speichern und Verwalten von interessanten Produkten
  - Persistente Speicherung der Favoriten
  - Kontextmenü für schnelle Aktionen
  - Doppelklick-Funktion für Produktdetails

- **Datenmanagement**
  - JSON-basierte Datenspeicherung
  - Thread-sichere Implementierung
  - Automatische Backup-Funktionalität
  - Konfigurierbare Einstellungen

## 🚀 Installation

```bash
# Repository klonen
git clone https://github.com/yourusername/smart-shopping-assistant.git
cd smart-shopping-assistant

# Virtuelle Umgebung erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt
```

## 🛠️ Technische Anforderungen

- Python 3.8+
- Required Packages:
  - tkinter
  - requests
  - beautifulsoup4
  - fake-useragent
  - threading
  - logging

## 📦 Projektstruktur

```
smart-shopping-assistant/
├── main.py              # Haupteinstiegspunkt
├── gui.py              # GUI-Implementierung
├── ebay_scraper.py     # eBay-Scraping-Logik
├── config.py           # Konfigurationseinstellungen
├── utils.py            # Hilfsfunktionen
├── data/               # Gespeicherte Daten
└── logs/               # Logging-Dateien
```

## 🎯 Roadmap

### Kurzfristige Ziele
- [ ] Integration weiterer E-Commerce-Plattformen (Amazon, Idealo)
- [ ] Preisvergleich zwischen verschiedenen Plattformen
- [ ] Preishistorie und Preiswarnungen
- [ ] Erweiterte Filtermöglichkeiten
- [ ] Export-Funktionen für Suchergebnisse

### Mittelfristige Ziele
- [ ] Machine Learning für Produktempfehlungen
- [ ] Automatische Kategorisierung von Produkten
- [ ] Browser-Extension für direktes Speichern
- [ ] Mobile App Integration
- [ ] API-Schnittstelle für externe Dienste

### Langfristige Vision
- [ ] Vollständige Shopping-Automatisierung
- [ ] KI-basierte Preisvorhersagen
- [ ] Soziale Shopping-Features
- [ ] Internationale Marktplatz-Integration
- [ ] Automatische Deal-Erkennung

## 🤝 Beitragen

Beiträge sind willkommen! Bitte beachten Sie folgende Schritte:

1. Fork des Repositories
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## ⚠️ Rechtliche Hinweise

- Dieses Tool ist nur für persönliche Verwendung gedacht
- Bitte beachten Sie die Nutzungsbedingungen der jeweiligen Plattformen
- Scraping-Aktivitäten sollten die Server-Ressourcen respektieren

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.

## 🙏 Danksagung

Besonderer Dank gilt:
- Der Python-Community für die großartigen Bibliotheken
- Allen Mitwirkenden und Unterstützern des Projekts
- Der Open-Source-Community für Inspiration und Ressourcen



