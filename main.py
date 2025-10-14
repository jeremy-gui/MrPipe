#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication
from gui import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("Mr. Pipe")
    app.setOrganizationDomain("mr-pipe.app")
    app.setApplicationName("Mr. Pipe")
    app.setApplicationDisplayName("Mr. Pipe")
    app.setApplicationVersion("1.0")
    app.setDesktopFileName("mr-pipe")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
