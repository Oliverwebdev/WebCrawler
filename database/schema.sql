-- Einstellungen Tabelle bleibt unverändert
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    max_pages INTEGER DEFAULT 3,
    default_search_period INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Aktualisierte Suchergebnisse Tabelle mit Kaufland als mögliche Quelle
CREATE TABLE IF NOT EXISTS search_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source VARCHAR(10) NOT NULL CHECK (source IN ('ebay', 'amazon', 'otto', 'kaufland')),
    keyword VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    price VARCHAR(50) NOT NULL,
    link TEXT NOT NULL,
    shipping VARCHAR(100),
    location VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Aktualisierte Favoriten Tabelle mit Kaufland als mögliche Quelle
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    price VARCHAR(50) NOT NULL,
    link TEXT UNIQUE NOT NULL,
    source VARCHAR(10) NOT NULL CHECK (source IN ('ebay', 'amazon', 'otto', 'kaufland')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Aktualisierte Archivtabelle mit Kaufland als mögliche Quelle
CREATE TABLE IF NOT EXISTS search_results_archive (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source VARCHAR(10) NOT NULL CHECK (source IN ('ebay', 'amazon', 'otto', 'kaufland')),
    keyword VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    price VARCHAR(50) NOT NULL,
    link TEXT NOT NULL,
    shipping VARCHAR(100),
    location VARCHAR(255),
    timestamp TIMESTAMP,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger bleiben unverändert
CREATE TRIGGER IF NOT EXISTS update_settings_timestamp 
AFTER UPDATE ON settings
BEGIN
    UPDATE settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS archive_old_results 
AFTER INSERT ON search_results
BEGIN
    INSERT INTO search_results_archive 
    SELECT id, source, keyword, title, price, link, shipping, location, timestamp, CURRENT_TIMESTAMP 
    FROM search_results 
    WHERE timestamp < datetime('now', '-30 day');
    
    DELETE FROM search_results 
    WHERE timestamp < datetime('now', '-30 day');
END;