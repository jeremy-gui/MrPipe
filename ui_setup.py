from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QDialog, QLabel, QLineEdit, QPushButton, QMessageBox,
    QStackedWidget, QSizePolicy, QSplitter, QDialogButtonBox
)
from PyQt6.QtGui import QAction, QFont, QFontDatabase, QIcon, QPixmap
from PyQt6.QtCore import Qt


class UiSetup:
    def __init__(self, main_window):
        self.main_window = main_window

    def setup_ui(self):
        """Configure l'interface utilisateur principale"""
        # Widget central et layout principal
        central = QWidget()
        self.main_window.setCentralWidget(central)

        # Créer un splitter horizontal pour permettre le redimensionnement
        self.main_window.splitter = QSplitter(Qt.Orientation.Horizontal)
        layout = QVBoxLayout(central)
        layout.addWidget(self.main_window.splitter)

        # Définir la taille initiale de la fenêtre (largeur, hauteur)
        self.main_window.resize(2000, 1200)  # Taille augmentée pour une meilleure visibilité
        self.main_window.tree = QTreeWidget()
        self.main_window.tree.setHeaderLabel("Projects and Jobs")
        self.main_window.tree.itemClicked.connect(self.main_window.project_manager.on_item_clicked)
        self.main_window.tree.setMinimumWidth(200)  # Largeur minimale pour éviter que ce soit trop petit
        self.main_window.splitter.addWidget(self.main_window.tree)
        self.main_window.log_view = QTextEdit()
        self.main_window.log_view.setReadOnly(True)

        # Launch widget for manual jobs
        launch_widget = QWidget()
        launch_layout = QVBoxLayout(launch_widget)
        launch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        launch_label = QLabel("This job is manual and not started.")
        launch_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_window.launch_button = QPushButton("Launch Job")
        self.main_window.launch_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.main_window.launch_button.clicked.connect(self.main_window._launch_manual_job)
        launch_layout.addWidget(launch_label)
        launch_layout.addWidget(self.main_window.launch_button)

        # Stacked widget for right side
        self.main_window.right_stack = QStackedWidget()
        self.main_window.right_stack.addWidget(self.main_window.log_view)  # index 0
        self.main_window.right_stack.addWidget(launch_widget)  # index 1
        self.main_window.right_stack.setCurrentIndex(0)  # default to log_view
        self.main_window.right_stack.setMinimumWidth(400)  # Largeur minimale pour le panneau de droite

        self.main_window.splitter.addWidget(self.main_window.right_stack)

        # Définir les proportions par défaut du splitter (1/3 pour l'arbre, 2/3 pour les logs)
        self.main_window.splitter.setSizes([666, 1334])  # 2000 / 3 = 666.67, arrondi à 666 et 1334

        # Connecter le signal pour sauvegarder automatiquement quand on redimensionne
        self.main_window.splitter.splitterMoved.connect(self.main_window._auto_save_geometry)

        # Connecter les signaux de redimensionnement de la fenêtre
        self.main_window.resizeEvent = self.main_window._on_resize_event
        self.main_window.moveEvent = self.main_window._on_move_event

        # Menu for settings
        menubar = self.main_window.menuBar()
        settings_menu = menubar.addMenu("Settings")
        config_action = QAction("Configure", self.main_window)
        config_action.triggered.connect(self.main_window.show_config)
        settings_menu.addAction(config_action)

        # Quit action
        quit_action = QAction("Quit", self.main_window)
        quit_action.triggered.connect(self.main_window.close)
        settings_menu.addAction(quit_action)

        # About action
        about_action = QAction("About", self.main_window)
        about_action.triggered.connect(self.main_window.show_about)
        settings_menu.addAction(about_action)

        # Apply dark mode stylesheet
        self._apply_dark_mode_stylesheet()

    def _apply_dark_mode_stylesheet(self):
        """Apply comprehensive dark mode stylesheet to all widgets"""
        dark_stylesheet = """
        /* Main window background */
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }

        /* Tree widget */
        QTreeWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #555555;
            alternate-background-color: #333333;
        }

        QTreeWidget::item {
            background-color: transparent;
            border-bottom: 1px solid #444444;
            padding: 2px;
        }

        QTreeWidget::item:selected {
            background-color: #4a90d9;
            color: white;
        }

        QTreeWidget::item:hover {
            background-color: #404040;
        }

        /* Headers */
        QHeaderView::section {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 4px;
        }

        /* Buttons */
        QPushButton {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 12px;
        }

        QPushButton:hover {
            background-color: #555555;
        }

        QPushButton:pressed {
            background-color: #666666;
        }

        QPushButton:disabled {
            background-color: #333333;
            color: #888888;
        }

        /* Line edits */
        QLineEdit {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 6px;
            selection-background-color: #4a90d9;
        }

        QLineEdit:focus {
            border-color: #4a90d9;
        }

        /* Labels */
        QLabel {
            color: #ffffff;
        }

        /* Dialogs */
        QDialog {
            background-color: #2b2b2b;
            color: #ffffff;
        }

        /* List widgets */
        QListWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #555555;
            alternate-background-color: #333333;
        }

        QListWidget::item {
            background-color: transparent;
            color: #ffffff;
            border-bottom: 1px solid #444444;
            padding: 4px;
        }

        QListWidget::item:selected {
            background-color: #4a90d9;
            color: white;
        }

        QListWidget::item:hover {
            background-color: #404040;
        }

        /* Checkboxes */
        QCheckBox {
            color: #ffffff;
        }

        QCheckBox::indicator {
            background-color: #404040;
            border: 1px solid #555555;
            width: 16px;
            height: 16px;
        }

        QCheckBox::indicator:checked {
            background-color: #4a90d9;
            border: 1px solid #4a90d9;
        }

        /* Dialog button box */
        QDialogButtonBox {
            button-layout: 0;
        }

        /* Menu bar */
        QMenuBar {
            background-color: #404040;
            color: #ffffff;
            border-bottom: 1px solid #555555;
        }

        QMenuBar::item {
            background-color: transparent;
            color: #ffffff;
            padding: 4px 8px;
        }

        QMenuBar::item:selected {
            background-color: #555555;
        }

        /* Menus */
        QMenu {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
        }

        QMenu::item {
            background-color: transparent;
            color: #ffffff;
            padding: 4px 20px;
        }

        QMenu::item:selected {
            background-color: #555555;
        }

        /* Message boxes */
        QMessageBox {
            background-color: #2b2b2b;
            color: #ffffff;
        }

        QMessageBox QLabel {
            color: #ffffff;
        }

        /* Splitter */
        QSplitter::handle {
            background-color: #555555;
        }

        QSplitter::handle:horizontal {
            width: 2px;
        }

        QSplitter::handle:hover {
            background-color: #666666;
        }

        /* Text edit is handled separately in the code */
        """
        self.main_window.setStyleSheet(dark_stylesheet)
