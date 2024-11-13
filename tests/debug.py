import sys
import tkinter as tk
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def check_dependencies():
    required_packages = [
        'requests',
        'beautifulsoup4',
        'fake-useragent',
        'tkinter'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✓ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"✗ {package} is missing")
    
    return missing_packages

def check_gui():
    try:
        root = tk.Tk()
        root.title("GUI Test")
        logger.info("✓ Tkinter GUI can be initialized")
        root.destroy()
        return True
    except Exception as e:
        logger.error(f"✗ GUI initialization failed: {str(e)}")
        return False

def main():
    logger.info("Starting diagnostics...")
    
    # Check Python version
    logger.info(f"Python version: {sys.version}")
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        logger.error(f"Missing packages: {', '.join(missing)}")
        logger.error("Please install missing packages using:")
        logger.error(f"pip install {' '.join(missing)}")
        return False
    
    # Check GUI
    if not check_gui():
        return False
    
    # Check file structure
    required_files = ['main.py', 'gui.py', 'ebay.py', 'config.py', 'utils.py']
    for file in required_files:
        try:
            with open(file, 'r') as f:
                logger.info(f"✓ {file} found and readable")
        except FileNotFoundError:
            logger.error(f"✗ {file} is missing")
            return False
    
    logger.info("All checks passed! The application should work.")
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        logger.error("Some checks failed. Please fix the issues above.")
    else:
        logger.info("You can now run 'python main.py' to start the application")