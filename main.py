#!/usr/bin/env python3
import sys
import os
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from gui import MainWindow

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # If not running as PyInstaller bundle, use the script's directory
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

def main():
    try:
        print("Creating QApplication")
        app = QApplication(sys.argv)
        
        # Désactiver l'utilisation des couleurs système natives
        app.setStyle('Fusion')

        app.setOrganizationName("Mr. Pipe")
        app.setOrganizationDomain("mr-pipe.app")
        app.setApplicationName("Mr. Pipe")
        app.setApplicationDisplayName("Mr. Pipe")
        app.setApplicationVersion("1.1")
        app.setDesktopFileName("mr-pipe")

        # Créer le splash screen
        print("Loading splash pix")
        splash_pix = QPixmap(get_resource_path("assets/image.png"))
        print(f"Splash pix is null: {splash_pix.isNull()}")
        if splash_pix.isNull():
            # Continuer sans splash screen
            print("No splash, creating window")
            window = MainWindow()
            window.show()
            print("Window shown")
            return app.exec()

        # Redimensionner l'image à 512x512 si elle est plus grande
        if splash_pix.width() > 512 or splash_pix.height() > 512:
            splash_pix = splash_pix.scaled(512, 512, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
        splash.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Ajouter un message sur le splash screen
        splash.showMessage("Démarrage de Mr. Pipe...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, Qt.GlobalColor.white)
        splash.show()

        # Forcer la mise à jour de l'affichage du splash screen
        app.processEvents()

        # Créer la fenêtre principale
        splash.showMessage("Initialisation des composants...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, Qt.GlobalColor.white)
        app.processEvents()

        print("Creating MainWindow")
        window = MainWindow()

        # Fermer le splash screen et afficher la fenêtre principale
        splash.showMessage("Lancement terminé !", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, Qt.GlobalColor.white)
        app.processEvents()

        # Délai minimum pour que le splash screen soit visible
        from PyQt6.QtCore import QTimer, QEventLoop
        loop = QEventLoop()
        QTimer.singleShot(2000, loop.quit)  # Attendre 2 secondes
        loop.exec()

        splash.finish(window)
        window.show()
        print("Window shown after splash")

        print("Starting app.exec()")
        result = app.exec()
        print(f"App exec returned: {result}")
        return result

    except Exception as e:
        print(f"Erreur lors du démarrage: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
