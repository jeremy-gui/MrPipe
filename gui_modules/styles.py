"""
Styles and themes for the application
"""

# Font size constants for consistency
LOG_FONT_SIZE = 16  # Main log display font size
TREE_FONT_SIZE_PROJECT = 12  # Project names in tree
TREE_FONT_SIZE_PIPELINE = 11  # Pipeline names in tree


def get_dark_mode_stylesheet():
    """Retourne le stylesheet dark mode complet"""
    return """
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

    /* QListWidget check indicators */
    QListWidget::indicator {
        background-color: #404040;
        border: 1px solid #555555;
        width: 16px;
        height: 16px;
    }

    QListWidget::indicator:checked {
        background-color: #5cb3ff;
        border: 1px solid #5cb3ff;
    }
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
    """


def get_log_view_stylesheet(font_size=16):
    """Retourne le stylesheet pour la vue des logs
    
    Args:
        font_size: Taille de la police en points (défaut: 16)
    """
    return f"""
    QTextEdit {{
        background-color: #1e1e1e;
        color: #ffffff;
        font-family: 'Courier New', monospace;
        font-size: {font_size}pt;
        line-height: 1.5;
        padding: 10px;
        selection-background-color: #4a90d9;
        selection-color: white;
    }}
    """


def get_dialog_stylesheet():
    """Retourne le stylesheet pour les dialogues"""
    return """
    QDialog {
        background-color: #2b2b2b;
        color: white;
    }

    /* QListWidget check indicators */
    QListWidget::indicator {
        background-color: #404040;
        border: 1px solid #555555;
        width: 16px;
        height: 16px;
    }

    QListWidget::indicator:checked {
        background-color: #5cb3ff;
        border: 1px solid #5cb3ff;
    }
    """


def get_license_text_stylesheet():
    """Retourne le stylesheet pour le texte de licence"""
    return """
    QTextEdit {
        background-color: #1e1e1e;
        color: white;
        font-family: monospace;
        font-size: 10pt;
    }
    """
