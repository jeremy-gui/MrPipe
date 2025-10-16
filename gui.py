from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QDialog, QLabel,
    QLineEdit, QDialogButtonBox, QCheckBox, QPushButton, QMessageBox, QListWidget, QListWidgetItem, QStackedWidget, QSizePolicy, QSplitter
)
from PyQt6.QtGui import QAction, QTextCharFormat, QColor, QTextCursor, QFont, QFontDatabase, QIcon, QPixmap
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QStandardPaths, QEventLoop, QUrl
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
import os, time
import configparser
import json
import sys
from gitlab_manager import GitLabManager
from PyQt6 import sip

# Import refactored modules
from gui_modules.workers import LaunchWorker
from gui_modules.dialogs import ConfigDialog, AboutDialog
from gui_modules.styles import get_dark_mode_stylesheet, get_log_view_stylesheet, LOG_FONT_SIZE
from gui_modules.config_manager import ConfigManager
from gui_modules.project_manager import ProjectManager
from gui_modules.job_manager import JobManager, JobColorManager
from gui_modules.log_display import LogDisplay
from gui_modules.ui_helpers import UIHelpers, HipsterPipeAnimation, LoadingAnimation


# Workers are now imported from gui.workers module


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mr. Pipe")
        # Définir l'icône de l'application
        self.setWindowIcon(QIcon(UIHelpers.get_resource_path("assets/ico.ico")))
        self.gitlab_manager = None
        self.projects = []  # list of project ids
        self.current_job = None
        self.log_worker = None
        self.project_workers = {}  # Dictionnaire pour suivre les workers par projet
        self.project_items = {}  # Pour garder une référence aux items de projet
        self.job_status_workers = {}  # Dictionnaire pour suivre les workers de statut par (proj_id, job_id)
        self.last_log_content = ""  # Pour éviter le scintillement des logs
        self.config = configparser.ConfigParser()
        self.config_file = os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation),
            'gitlab_pipelines_manager.ini'
        )
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        self.auto_select_updated = True  # Par défaut activé
        self.hipster_pipe_enabled = False  # Hipster Pipe désactivé par défaut
        self.job_animations = {}  # Pour gérer les timers d'animation des jobs "running"
        self.hipster_video_widget = None  # Pour la vidéo Hipster Pipe
        self.hipster_media_player = None  # Pour le lecteur vidéo Hipster Pipe
        self.sync_worker = None  # For project sync worker
        self.launch_worker = None  # For launching manual jobs
        self.job_data_worker = None  # For fetching job data
        self.launch_button = None  # For launch button feedback
        self.current_manual_job = None  # For launching manual jobs
        self._loading_state = 0  # For loading animation
        self._loading_text = "·"  # For loading animation
        self.hipster_pipe_enabled = False
        self.is_initial_loading = False  # Flag to track initial loading state
        
        # Initialize managers
        self.config_manager = ConfigManager(self)
        self.project_manager = ProjectManager(self)
        self.job_manager = JobManager(self)
        self.log_display = LogDisplay(self)
        self.hipster_animation = HipsterPipeAnimation(self)
        self.loading_animation = LoadingAnimation(self)
        
        # Setup UI
        self.setup_ui()
        self.configure_log_view_font()
        self.config_manager.load_config()
        self.setup_timers()

    def configure_log_view_font(self):
        """Configure la police pour la vue des logs"""
        try:
            font = QFont('Monaco')
            if not font.exactMatch():
                font = QFont('Consolas')
                if not font.exactMatch():
                    font = QFont('Courier New')
                    if not font.exactMatch():
                        font = QFont('monospace')

            font.setPointSize(LOG_FONT_SIZE)
            font.setStyleHint(QFont.StyleHint.TypeWriter)
            font.setFixedPitch(True)

            self.log_view.setFont(font)
            self.log_view.setAcceptRichText(True)
            self.log_view.setStyleSheet(get_log_view_stylesheet())
        except Exception as e:
            print(f"Erreur lors de la configuration de la police: {e}")
            self.log_view.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    font-family: monospace;
                }
            """)

    def setup_ui(self):
        """Configure l'interface utilisateur principale"""
        # Widget central et layout principal
        central = QWidget()
        self.setCentralWidget(central)

        # Créer un splitter horizontal pour permettre le redimensionnement
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        layout = QVBoxLayout(central)
        layout.addWidget(self.splitter)

        # Définir la taille initiale de la fenêtre (largeur, hauteur)
        self.resize(2000, 1200)  # Taille augmentée pour une meilleure visibilité
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Projects and Jobs")
        self.tree.itemClicked.connect(lambda item, col: self.job_manager.on_item_clicked(item, col))
        self.tree.setMinimumWidth(200)  # Largeur minimale pour éviter que ce soit trop petit
        self.splitter.addWidget(self.tree)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        # Launch widget for manual jobs
        launch_widget = QWidget()
        launch_layout = QVBoxLayout(launch_widget)
        launch_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        launch_label = QLabel("This job is manual and not started.")
        launch_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.launch_button = QPushButton("Launch Job")
        self.launch_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.launch_button.clicked.connect(self._launch_manual_job)
        launch_layout.addWidget(launch_label)
        launch_layout.addWidget(self.launch_button)

        # Stacked widget for right side
        self.right_stack = QStackedWidget()
        self.right_stack.addWidget(self.log_view)  # index 0
        self.right_stack.addWidget(launch_widget)  # index 1
        self.right_stack.setCurrentIndex(0)  # default to log_view
        self.right_stack.setMinimumWidth(400)  # Largeur minimale pour le panneau de droite

        self.splitter.addWidget(self.right_stack)

        # Définir les proportions par défaut du splitter (1/3 pour l'arbre, 2/3 pour les logs)
        self.splitter.setSizes([666, 1334])  # 2000 / 3 = 666.67, arrondi à 666 et 1334

        # Connecter le signal pour sauvegarder automatiquement quand on redimensionne
        self.splitter.splitterMoved.connect(self.config_manager.auto_save_geometry)

        # Connecter les signaux de redimensionnement de la fenêtre
        self.resizeEvent = self._on_resize_event
        self.moveEvent = self._on_move_event

        # Menu for settings
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        config_action = QAction("Configure", self)
        config_action.triggered.connect(self.show_config)
        settings_menu.addAction(config_action)

        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        settings_menu.addAction(about_action)

        # Separator
        settings_menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        settings_menu.addAction(quit_action)

        # Apply dark mode stylesheet
        self.setStyleSheet(get_dark_mode_stylesheet())

    # Stylesheet now imported from gui.styles module

    def _launch_manual_job(self):
        if not self.current_manual_job:
            return
        proj_id, job_id = self.current_manual_job
        # Check if already launching
        if self.launch_worker and self.launch_worker.isRunning():
            return
        # Update button to show launching state
        if self.launch_button:
            self.launch_button.setText("Launching...")
            self.launch_button.setEnabled(False)
        # Use worker to launch
        self.launch_worker = LaunchWorker(self.gitlab_manager, proj_id, job_id)
        self.launch_worker.launch_done.connect(self._on_launch_done)
        self.launch_worker.launch_error.connect(self._on_launch_error)
        self.launch_worker.start()

    # Moved to ConfigManager

    def _on_resize_event(self, event):
        """Appelé quand la fenêtre est redimensionnée"""
        # Délai pour éviter trop de sauvegardes pendant le redimensionnement
        if hasattr(self, '_resize_timer') and self._resize_timer.isActive():
            self._resize_timer.stop()

        if not hasattr(self, '_resize_timer'):
            self._resize_timer = QTimer(self)
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self.config_manager.auto_save_geometry)

        self._resize_timer.start(500)  # Sauvegarder 500ms après le dernier redimensionnement

        # Appeler la méthode parente
        super().resizeEvent(event)

    def _on_move_event(self, event):
        """Appelé quand la fenêtre est déplacée"""
        # Délai pour éviter trop de sauvegardes pendant le déplacement
        if hasattr(self, '_move_timer') and self._move_timer.isActive():
            self._move_timer.stop()

        if not hasattr(self, '_move_timer'):
            self._move_timer = QTimer(self)
            self._move_timer.setSingleShot(True)
            self._move_timer.timeout.connect(self.config_manager.auto_save_geometry)

        self._move_timer.start(500)  # Sauvegarder 500ms après le dernier déplacement

        # Appeler la méthode parente
        super().moveEvent(event)

    def show_config(self):
        # Warn if loading is in progress
        if self.is_initial_loading:
            reply = QMessageBox.question(
                self,
                "Chargement en cours",
                "Un chargement de projets est en cours. Voulez-vous continuer ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        dialog = ConfigDialog(self, self.config, self.config_file)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            url = dialog.get_url()
            token = dialog.get_token()
            selected_projects = dialog.get_selected_projects()
            self.auto_select_updated = dialog.get_auto_select_updated()
            self.hipster_pipe_enabled = dialog.get_hipster_pipe_enabled()

            try:
                self.config_manager.save_config(url, token, selected_projects)
                self.projects = selected_projects
                self.gitlab_manager = GitLabManager(url, token)
                # Reset initial load flag to trigger progressive loading again
                self.project_manager.initial_load_done = False
                self.is_initial_loading = True
                self.project_manager.update_projects()
            except Exception as e:
                self.log_view.setPlainText(f"Erreur de configuration : {str(e)}")

    # Old config dialog removed - now using ConfigDialog from gui.dialogs

    def show_about(self):
        """Affiche la fenêtre À propos"""
        dialog = AboutDialog(self, UIHelpers.get_resource_path)
        dialog.exec()

    # Sync methods removed - now handled in ConfigDialog

    def _on_launch_done(self):
        """Called when a manual job launch succeeds"""
        print("Job launched successfully")
        self.launch_worker = None
        # Reset button
        if self.launch_button:
            self.launch_button.setText("Launch Job")
            self.launch_button.setEnabled(True)
        # Refresh projects to update status
        self.project_manager.update_projects(force_update=True)
        # Switch back to log view and show message
        self.right_stack.setCurrentIndex(0)
        self.log_view.setPlainText("Job launched successfully. Refreshing...")

    def _on_launch_error(self, error):
        """Called when a manual job launch fails"""
        print(f"Launch error: {error}")
        self.launch_worker = None
        # Reset button
        if self.launch_button:
            self.launch_button.setText("Launch Job")
            self.launch_button.setEnabled(True)
        QMessageBox.warning(self, "Launch Error", f"Failed to launch job: {error}")
        # Switch back to log view
        self.right_stack.setCurrentIndex(0)

    def _on_job_status_worker_finished(self, key):
        """Called when a JobStatusWorker finishes"""
        if key in self.job_status_workers:
            del self.job_status_workers[key]

    # Filter and limit methods removed - now handled in ConfigDialog

    def setup_timers(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.project_manager.update_projects)
        # Commencer avec un intervalle plus long après le chargement initial
        QTimer.singleShot(10000, lambda: self.timer.start(3000))  # Attendre 10s puis mettre à jour toutes les 2s

        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.loading_animation.animate_dots)

        # Planifier une première mise à jour différée pour laisser le temps à l'interface de se charger
        QTimer.singleShot(8000, self.project_manager.update_projects)

    def closeEvent(self, event):
        # Sauvegarder automatiquement la géométrie et les proportions avant de fermer
        self.config_manager.auto_save_geometry()

        # Arrêter tous les workers en cours d'exécution
        if self.log_worker:
            self.log_worker.stop()
            if self.log_worker.isRunning():
                self.log_worker.wait(1000)
            self.log_worker.deleteLater()
            self.log_worker = None

        # sync_worker is now handled in ConfigDialog

        if self.launch_worker:
            self.launch_worker.stop()
            if self.launch_worker.isRunning():
                self.launch_worker.wait(1000)
            self.launch_worker.deleteLater()
            self.launch_worker = None

        if self.job_data_worker:
            self.job_data_worker.stop()
            if self.job_data_worker.isRunning():
                self.job_data_worker.wait(1000)
            self.job_data_worker.deleteLater()
            self.job_data_worker = None

        # Arrêter les timers
        if hasattr(self, 'timer') and self.timer:
            self.timer.stop()
        if hasattr(self, 'loading_timer') and self.loading_timer:
            self.loading_timer.stop()

        # Arrêter les timers de sauvegarde automatique
        if hasattr(self, '_resize_timer') and self._resize_timer:
            self._resize_timer.stop()
        if hasattr(self, '_move_timer') and self._move_timer:
            self._move_timer.stop()

        # Arrêter tous les workers de projet
        for worker in list(self.project_workers.values()):
            if worker:
                try:
                    worker.stop()
                    if worker.isRunning():
                        worker.wait(1000)  # Wait max 1 second
                    worker.deleteLater()
                except:
                    pass
        self.project_workers.clear()

        # Arrêter tous les workers de statut des jobs
        for worker in list(self.job_status_workers.values()):
            if worker:
                try:
                    worker.stop()
                    if worker.isRunning():
                        worker.wait(1000)  # Wait max 1 second
                    worker.deleteLater()
                except:
                    pass
        self.job_status_workers.clear()

        # Arrêter toutes les animations de jobs
        for timer, _ in self.job_animations.values():
            timer.stop()
            timer.deleteLater()
        self.job_animations.clear()

        # Arrêter l'animation Hipster Pipe si elle existe
        if (hasattr(self, 'hipster_video_widget') and self.hipster_video_widget) or (hasattr(self, 'hipster_media_player') and self.hipster_media_player):
            if hasattr(self, 'hipster_media_player') and self.hipster_media_player:
                self.hipster_media_player.stop()
                self.hipster_media_player.deleteLater()
            if hasattr(self, 'hipster_video_widget') and self.hipster_video_widget:
                self.hipster_video_widget.hide()
                self.hipster_video_widget.deleteLater()
            self.hipster_video_widget = None
            self.hipster_media_player = None

        event.accept()
