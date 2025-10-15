from PyQt6.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QLabel, QTextEdit, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("À propos de Mr. Pipe")
        self.setFixedSize(600, 400)  # Taille fixe pour la fenêtre
        layout = QHBoxLayout(self)

        # Partie gauche : informations texte
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(10)

        # Auteur
        author_label = QLabel("Auteur:")
        author_label.setStyleSheet("font-weight: bold; color: white;")
        author_value = QLabel("Jérémy Couderc Guillaume")
        author_value.setStyleSheet("color: white;")
        left_layout.addWidget(author_label)
        left_layout.addWidget(author_value)

        # Email
        email_label = QLabel("Email:")
        email_label.setStyleSheet("font-weight: bold; color: white;")
        email_value = QLabel("jeremy.guillau@gmail.com")
        email_value.setStyleSheet("color: white;")
        left_layout.addWidget(email_label)
        left_layout.addWidget(email_value)

        # Licence (cliquable)
        license_label = QLabel("Licence:")
        license_label.setStyleSheet("font-weight: bold; color: white;")
        license_value = QLabel('<a href="#" style="color: #4a90d9;">MIT</a>')
        license_value.setStyleSheet("color: #4a90d9;")
        license_value.setOpenExternalLinks(False)
        license_value.linkActivated.connect(self.show_license)
        left_layout.addWidget(license_label)
        left_layout.addWidget(license_value)

        # Version
        version_label = QLabel("Version:")
        version_label.setStyleSheet("font-weight: bold; color: white;")
        version_value = QLabel("v1.0.2")
        version_value.setStyleSheet("color: white;")
        left_layout.addWidget(version_label)
        left_layout.addWidget(version_value)

        # Espacement
        left_layout.addStretch()

        # Partie droite : image du splash screen
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Charger l'image du splash screen
        splash_pixmap = QPixmap(self.parent().get_resource_path("image.png"))
        splash_label = QLabel()
        splash_label.setPixmap(splash_pixmap.scaled(252, 252, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(splash_label)

        # Ajouter les widgets au layout principal
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)

        # Appliquer le style sombre
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
        """)

    def show_license(self):
        """Affiche la licence MIT dans une nouvelle fenêtre"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Licence MIT")
        dialog.setFixedSize(500, 400)
        layout = QVBoxLayout(dialog)

        license_text = QTextEdit()
        license_text.setPlainText("""MIT License

Copyright (c) 2024 Jérémy Couderc Guillaume

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""")
        license_text.setReadOnly(True)
        license_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                font-family: monospace;
                font-size: 10pt;
            }
        """)
        layout.addWidget(license_text)

        dialog.exec()
