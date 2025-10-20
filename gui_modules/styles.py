"""
Styles and themes for the application
"""

import sys
import platform

def get_font_scale():
    """
    Retourne un facteur d'échelle pour les polices selon la plateforme.
    macOS (Retina) : 1.0 (tailles normales)
    Windows/Linux : 0.85 (tailles réduites de 15%)
    """
    if platform.system() == 'Darwin':  # macOS
        return 1.0
    else:  # Windows, Linux
        return 0.85

# Font size constants for consistency (ajustés selon la plateforme)
_SCALE = get_font_scale()
LOG_FONT_SIZE = int(16 * _SCALE)  # Main log display font size
TREE_FONT_SIZE_PROJECT = int(12 * _SCALE)  # Project names in tree
TREE_FONT_SIZE_PIPELINE = int(11 * _SCALE)  # Pipeline names in tree

# Header font sizes
HEADER_PROJECT_FONT_SIZE = int(14 * _SCALE)
HEADER_JOB_FONT_SIZE = int(13 * _SCALE)
HEADER_STATUS_FONT_SIZE = int(10 * _SCALE)
HEADER_ENV_FONT_SIZE = int(9 * _SCALE)
HEADER_DATE_FONT_SIZE = int(11 * _SCALE)


def get_dark_mode_stylesheet():
    """Retourne le stylesheet Material Design avec couleurs Mr. Pipe"""
    return """
    /* Main window background - Material Design */
    QMainWindow {
        background-color: #263238;
        color: #eceff1;
    }

    /* Tree widget - Material Design */
    QTreeWidget {
        background-color: #37474f;
        color: #eceff1;
        border: none;
        alternate-background-color: #263238;
        font-size: 10pt;
        outline: none;
        selection-background-color: rgba(153, 229, 255, 0.4);
        selection-color: white;
    }

    QTreeWidget::branch:selected {
        background-color: rgba(153, 229, 255, 0.4);
    }

    QTreeWidget::branch:hover {
        background-color: rgba(52, 152, 219, 0.2);
    }

    QTreeWidget::item {
        background-color: transparent;
        border: none;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding: 4px 8px;
        min-height: 20px;
        border-radius: 2px;
    }

    QTreeWidget::item:selected {
        background-color: rgba(153, 229, 255, 0.4) !important;
        color: white !important;
    }

    QTreeWidget::item:selected:active {
        background-color: rgba(153, 229, 255, 0.4) !important;
        color: white !important;
    }

    QTreeWidget::item:selected:!active {
        background-color: rgba(153, 229, 255, 0.3) !important;
        color: white !important;
    }

    QTreeWidget::item:hover {
        background-color: rgba(52, 152, 219, 0.2);
    }

    /* Headers - Material Design */
    QHeaderView::section {
        background-color: #455a64;
        color: #eceff1;
        border: none;
        padding: 8px;
        font-weight: 500;
        font-size: 11pt;
    }

    /* Buttons - Material Design */
    QPushButton {
        background-color: rgba(153, 229, 255, 0.4);
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-size: 11pt;
        font-weight: 500;
    }

    QPushButton:hover {
        background-color: #fca326;
    }

    QPushButton:pressed {
        background-color: #db5b23;
    }

    QPushButton:disabled {
        background-color: #546e7a;
        color: #90a4ae;
    }

    /* Line edits - Material Design */
    QLineEdit {
        background-color: #455a64;
        color: #eceff1;
        border: none;
        border-bottom: 2px solid #546e7a;
        border-radius: 2px;
        padding: 8px;
        selection-background-color: rgba(153, 229, 255, 0.4);
        font-size: 10pt;
    }

    QLineEdit:focus {
        border-bottom: 2px solid #3498db;
        background-color: #455a64;
    }

    /* Labels - Material Design */
    QLabel {
        color: #eceff1;
        font-weight: 400;
    }

    /* Dialogs - Material Design */
    QDialog {
        background-color: #263238;
        color: #eceff1;
        border: none;
    }

    /* List widgets - Material Design */
    QListWidget {
        background-color: #37474f;
        color: #eceff1;
        border: none;
        alternate-background-color: #263238;
        outline: none;
    }

    QListWidget::item {
        background-color: transparent;
        color: #eceff1;
        border: none;
        padding: 8px;
        min-height: 20px;
        border-radius: 2px;
    }

    QListWidget::item:selected {
        background-color: rgba(153, 229, 255, 0.4);
        color: white;
    }

    QListWidget::item:hover {
        background-color: rgba(52, 152, 219, 0.2);
    }

    /* Checkboxes - Material Design */
    QListWidget::indicator {
        background-color: #455a64;
        border: 2px solid #546e7a;
        border-radius: 2px;
        width: 18px;
        height: 18px;
    }

    QListWidget::indicator:checked {
        background-color: rgba(153, 229, 255, 0.6);
        border: 2px solid rgba(153, 229, 255, 0.6);
        image: url(none);
    }
    
    QCheckBox {
        color: #eceff1;
        font-weight: 400;
    }

    QCheckBox::indicator {
        background-color: #455a64;
        border: 2px solid #546e7a;
        border-radius: 2px;
        width: 18px;
        height: 18px;
    }

    QCheckBox::indicator:checked {
        background-color: rgba(153, 229, 255, 0.6);
        border: 2px solid rgba(153, 229, 255, 0.6);
    }

    /* Dialog button box */
    QDialogButtonBox {
        button-layout: 0;
    }

    /* Menu bar - Material Design */
    QMenuBar {
        background-color: #455a64;
        color: #eceff1;
        border: none;
        font-weight: 500;
        font-size: 10pt;
    }

    QMenuBar::item {
        background-color: transparent;
        color: #eceff1;
        padding: 8px 12px;
        border-radius: 2px;
    }

    QMenuBar::item:selected {
        background-color: rgba(153, 229, 255, 0.2);
    }

    /* Menus - Material Design */
    QMenu {
        background-color: #37474f;
        color: #eceff1;
        border: none;
        border-radius: 4px;
    }

    QMenu::item {
        background-color: transparent;
        color: #eceff1;
        padding: 8px 24px;
        border-radius: 2px;
    }

    QMenu::item:selected {
        background-color: rgba(153, 229, 255, 0.4);
        color: white;
    }

    /* Message boxes - Material Design */
    QMessageBox {
        background-color: #263238;
        color: #eceff1;
        border: none;
    }

    QMessageBox QLabel {
        color: #eceff1;
        font-weight: 400;
    }

    /* Splitter - Material Design */
    QSplitter::handle {
        background-color: #455a64;
    }

    QSplitter::handle:horizontal {
        width: 2px;
    }

    QSplitter::handle:hover {
        background-color: rgba(153, 229, 255, 0.4);
    }
    """


def get_log_view_stylesheet(font_size=16):
    """Retourne le stylesheet pour la vue des logs - Material Design
    
    Args:
        font_size: Taille de la police en points (défaut: 16)
    """
    return f"""
    QTextEdit {{
        background-color: #263238;
        color: #00ff41;
        font-family: 'Courier New', 'Consolas', monospace;
        font-size: {font_size}pt;
        line-height: 1.5;
        padding: 12px;
        border: none;
        selection-background-color: rgba(153, 229, 255, 0.4);
        selection-color: white;
        font-weight: normal;
    }}
    """


def get_dialog_stylesheet():
    """Retourne le stylesheet pour les dialogues - Material Design"""
    return """
    QDialog {
        background-color: #263238;
        color: #eceff1;
        border: none;
    }

    /* QListWidget check indicators */
    QListWidget::indicator {
        background-color: #455a64;
        border: 2px solid #546e7a;
        border-radius: 2px;
        width: 18px;
        height: 18px;
    }

    QListWidget::indicator:checked {
        background-color: rgba(153, 229, 255, 0.4);
        border: 2px solid rgba(153, 229, 255, 0.4);
    }
    """


def get_license_text_stylesheet():
    """Retourne le stylesheet pour le texte de licence - Material Design"""
    return """
    QTextEdit {
        background-color: #263238;
        color: #eceff1;
        font-family: 'Courier New', monospace;
        font-size: 10pt;
        border: none;
        font-weight: 400;
    }
    """
