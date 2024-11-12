import os
import sys
import logging

logger = logging.getLogger('X11Config')

def configure_x11_environment():
    """Konfiguriert die X11-Umgebung für optimale Kompatibilität."""
    if not sys.platform.startswith('linux'):
        return

    try:
        # X11-spezifische Umgebungsvariablen
        x11_config = {
            'NO_AT_BRIDGE': '1',  # Deaktiviert Accessibility Bridge
            'XDG_SESSION_TYPE': 'x11',
            'GDK_BACKEND': 'x11',
            'QT_QPA_PLATFORM': 'xcb',  # Für Qt-Kompatibilität
            'DISPLAY': os.environ.get('DISPLAY', ':0'),  # Sicherstellen dass DISPLAY gesetzt ist
        }

        # Setze Umgebungsvariablen
        for key, value in x11_config.items():
            os.environ[key] = value

        # Überprüfe X11-Verbindung
        import subprocess
        try:
            subprocess.run(['xset', 'q'], capture_output=True, check=True)
        except subprocess.CalledProcessError:
            logger.warning("X11-Server möglicherweise nicht verfügbar")
            
        logger.info("X11-Umgebung erfolgreich konfiguriert")
        
    except Exception as e:
        logger.error(f"Fehler bei X11-Konfiguration: {e}")
        
def check_display_server():
    """Überprüft und gibt Informationen über den Display-Server zurück."""
    display_server = "unbekannt"
    
    try:
        if os.environ.get('WAYLAND_DISPLAY'):
            display_server = "Wayland"
        elif os.environ.get('DISPLAY'):
            display_server = "X11"
            
        logger.info(f"Erkannter Display-Server: {display_server}")
        
        # Überprüfe verfügbare Bildschirmauflösungen
        if sys.platform.startswith('linux'):
            try:
                import subprocess
                xrandr = subprocess.check_output(['xrandr']).decode()
                logger.info(f"Verfügbare Auflösungen: {xrandr.split('n')[0]}")
            except Exception as e:
                logger.warning(f"Konnte Bildschirmauflösungen nicht abrufen: {e}")
                
    except Exception as e:
        logger.error(f"Fehler bei Display-Server-Erkennung: {e}")
        
    return display_server