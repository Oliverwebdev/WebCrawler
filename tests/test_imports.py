#!/usr/bin/env python3

def test_imports():
    """Test all required imports"""
    import sys
    from pathlib import Path
    
    print(f"Python Version: {sys.version}")
    print(f"Current Directory: {Path.cwd()}")
    print("\nTesting imports...")
    
    try:
        import requests
        print("✓ requests")
    except ImportError as e:
        print(f"✗ requests: {e}")
    
    try:
        from bs4 import BeautifulSoup
        print("✓ beautifulsoup4")
    except ImportError as e:
        print(f"✗ beautifulsoup4: {e}")
    
    try:
        from fake_useragent import UserAgent
        print("✓ fake-useragent")
    except ImportError as e:
        print(f"✗ fake-useragent: {e}")
    
    print("\nTesting local modules...")
    
    try:
        from config import CONFIG
        print("✓ config")
    except ImportError as e:
        print(f"✗ config: {e}")
    
    try:
        from scrapers.ebay_scraper import EbayScraper
        print("✓ ebay_scraper")
    except ImportError as e:
        print(f"✗ ebay_scraper: {e}")
    
    try:
        from gui.gui import EbayScraperGUI
        print("✓ gui")
    except ImportError as e:
        print(f"✗ gui: {e}")
    
    try:
        from utils.utils import save_to_json, load_from_json
        print("✓ utils")
    except ImportError as e:
        print(f"✗ utils: {e}")

if __name__ == "__main__":
    test_imports()