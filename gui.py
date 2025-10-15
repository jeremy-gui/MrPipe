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
from gui_modules.workers import (
    HttpWorker, ProjectSyncWorker, LaunchWorker, LogWorker,
    JobStatusWorker, JobDataWorker
)
from gui_modules.dialogs import ConfigDialog, AboutDialog
from gui_modules.styles import get_dark_mode_stylesheet, get_log_view_stylesheet
from gui_modules.log_formatter import LogFormatter


# Workers are now imported from gui.workers module


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mr. Pipe")
        # Définir l'icône de l'application
        self.setWindowIcon(QIcon(self.get_resource_path("ico.ico")))
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
        self._loading_active = False  # For loading animation
        self.setup_ui()

        # Configuration simple de la police
        try:
            # Essayer d'abord avec une police système courante
            font = QFont('Monaco')
            if not font.exactMatch():
                font = QFont('Consolas')
                if not font.exactMatch():
                    font = QFont('Courier New')
                    if not font.exactMatch():
                        font = QFont('monospace')

            # Configurer la police
            font.setPointSize(16)  # Taille de police augmentée
            font.setStyleHint(QFont.StyleHint.TypeWriter)
            font.setFixedPitch(True)

            # Configurer la zone de texte
            self.log_view.setFont(font)
            self.log_view.setAcceptRichText(True)

            # Utiliser une configuration CSS améliorée
            self.log_view.setStyleSheet(get_log_view_stylesheet())
        except Exception as e:
            print(f"Erreur lors de la configuration de la police: {e}")
            # Configuration minimale en cas d'échec
            self.log_view.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    font-family: monospace;
                }
            """)

        self.load_config()  # Doit être après setup_ui() pour pouvoir afficher les messages
        self.setup_timers()

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
        self.tree.itemClicked.connect(self.on_item_clicked)
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
        self.splitter.splitterMoved.connect(self._auto_save_geometry)

        # Connecter les signaux de redimensionnement de la fenêtre
        self.resizeEvent = self._on_resize_event
        self.moveEvent = self._on_move_event

        # Menu for settings
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        config_action = QAction("Configure", self)
        config_action.triggered.connect(self.show_config)
        settings_menu.addAction(config_action)

        # Quit action
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        settings_menu.addAction(quit_action)

        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        settings_menu.addAction(about_action)

        # Apply dark mode stylesheet
        self.setStyleSheet(get_dark_mode_stylesheet())

    # Stylesheet now imported from gui.styles module

    def _animate_loading_dots(self):
        states = ["·", "··", "···"]
        self._loading_state = (self._loading_state + 1) % len(states)
        self._loading_text = states[self._loading_state]
        self._update_loading_display()

    def _update_loading_display(self):
        # Utiliser QTextCursor pour modifier seulement les points de chargement sans casser le formatage
        cursor = self.log_view.textCursor()
        document = self.log_view.document()

        # Chercher le dernier bloc qui contient seulement des points de chargement
        block = document.lastBlock()
        while block.isValid():
            text = block.text().strip()
            if text in ['·', '··', '···']:
                # Trouver ce bloc et le remplacer
                block_start = block.position()
                block_end = block_start + len(block.text())

                # Créer un nouveau curseur pour la modification
                edit_cursor = self.log_view.textCursor()
                edit_cursor.setPosition(block_start)
                edit_cursor.setPosition(block_end, QTextCursor.MoveMode.KeepAnchor)
                edit_cursor.removeSelectedText()

                # Insérer les nouveaux points
                if hasattr(self, '_loading_active') and self._loading_active and hasattr(self, '_loading_text'):
                    edit_cursor.insertText(self._loading_text)

                # Repositionner le curseur principal à la fin
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.log_view.setTextCursor(cursor)
                return

            # Passer au bloc précédent
            block = block.previous()

        # Si aucun bloc de points trouvé, ajouter à la fin
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if hasattr(self, '_loading_active') and self._loading_active and hasattr(self, '_loading_text'):
            cursor.insertText(self._loading_text)
        self.log_view.setTextCursor(cursor)

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

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            if 'GitLab' in self.config:
                config = self.config['GitLab']
                url = config.get('url', 'https://gitlab.com')
                token = config.get('token', '')
                projects = config.get('projects', '')

                if token and projects:
                    try:
                        self.projects = [int(p.strip()) for p in projects.split(',') if p.strip()]
                        self.gitlab_manager = GitLabManager(url, token)
                        self.log_view.setPlainText("Chargement des projets...")
                        self.update_projects()
                    except Exception as e:
                        self.log_view.setPlainText(f"Erreur lors du chargement de la configuration : {str(e)}")
                else:
                    self.log_view.setPlainText("Veuillez configurer l'URL GitLab et le token dans les paramètres.")

            # Charger l'option UI
            if 'UI' in self.config:
                self.auto_select_updated = self.config.getboolean('UI', 'auto_select_updated', fallback=True)
                self.hipster_pipe_enabled = self.config.getboolean('UI', 'hipster_pipe_enabled', fallback=False)

                # Restaurer les proportions du splitter après un court délai pour s'assurer que l'UI est prête
                splitter_sizes = self.config.get('UI', 'splitter_sizes', fallback=None)
                QTimer.singleShot(100, lambda: self._restore_splitter_sizes(splitter_sizes))

                # Restaurer la géométrie de la fenêtre
                geometry_b64 = self.config.get('UI', 'window_geometry', fallback=None)
                if geometry_b64:
                    try:
                        import base64
                        geometry_data = base64.b64decode(geometry_b64)
                        from PyQt6.QtCore import QByteArray
                        geometry = QByteArray(geometry_data)
                        self.restoreGeometry(geometry)
                    except Exception as e:
                        print(f"Erreur lors de la restauration de la géométrie: {e}")
        else:
            self.log_view.setPlainText("Bienvenue ! Veuillez configurer l'application dans le menu Paramètres.")

    def save_config(self, url, token, projects):
        if not self.config.has_section('GitLab'):
            self.config.add_section('GitLab')

        self.config['GitLab']['url'] = url
        self.config['GitLab']['token'] = token
        self.config['GitLab']['projects'] = ','.join(str(p) for p in projects)

        # Sauvegarder l'option UI
        if not self.config.has_section('UI'):
            self.config.add_section('UI')
        self.config.set('UI', 'auto_select_updated', str(self.auto_select_updated))
        self.config.set('UI', 'hipster_pipe_enabled', str(self.hipster_pipe_enabled))

        # Sauvegarder les proportions du splitter
        splitter_sizes = self.splitter.sizes()
        if splitter_sizes:
            self.config.set('UI', 'splitter_sizes', ','.join(str(size) for size in splitter_sizes))

        # Sauvegarder la géométrie de la fenêtre
        geometry = self.saveGeometry()
        if geometry:
            import base64
            geometry_b64 = base64.b64encode(geometry.data()).decode('ascii')
            self.config.set('UI', 'window_geometry', geometry_b64)

        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def _restore_splitter_sizes(self, splitter_sizes_str):
        """Restaure les proportions du splitter depuis la configuration"""
        if splitter_sizes_str:
            try:
                sizes = [int(s.strip()) for s in splitter_sizes_str.split(',')]
                if len(sizes) >= 2:
                    # S'assurer que les tailles respectent les minimums
                    if sizes[0] < 200:
                        sizes[0] = 200
                    if sizes[1] < 400:
                        sizes[1] = 400
                    self.splitter.setSizes(sizes)
            except (ValueError, IndexError) as e:
                print(f"Erreur lors de la restauration des proportions du splitter: {e}")
                # Utiliser les proportions par défaut
                pass

    def _auto_save_geometry(self):
        """Sauvegarde automatique de la géométrie et des proportions du splitter"""
        try:
            # Créer la section UI si elle n'existe pas
            if not self.config.has_section('UI'):
                self.config.add_section('UI')

            # Sauvegarder les proportions du splitter
            splitter_sizes = self.splitter.sizes()
            if splitter_sizes:
                self.config.set('UI', 'splitter_sizes', ','.join(str(size) for size in splitter_sizes))

            # Sauvegarder la géométrie de la fenêtre
            geometry = self.saveGeometry()
            if geometry:
                import base64
                geometry_b64 = base64.b64encode(geometry.data()).decode('ascii')
                self.config.set('UI', 'window_geometry', geometry_b64)

            # Écrire dans le fichier
            with open(self.config_file, 'w') as f:
                self.config.write(f)

        except Exception as e:
            print(f"Erreur lors de la sauvegarde automatique: {e}")

    def _on_resize_event(self, event):
        """Appelé quand la fenêtre est redimensionnée"""
        # Délai pour éviter trop de sauvegardes pendant le redimensionnement
        if hasattr(self, '_resize_timer') and self._resize_timer.isActive():
            self._resize_timer.stop()

        if not hasattr(self, '_resize_timer'):
            self._resize_timer = QTimer(self)
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._auto_save_geometry)

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
            self._move_timer.timeout.connect(self._auto_save_geometry)

        self._move_timer.start(500)  # Sauvegarder 500ms après le dernier déplacement

        # Appeler la méthode parente
        super().moveEvent(event)

    def get_resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            # If not running as PyInstaller bundle, use the script's directory
            base_path = os.path.dirname(os.path.abspath(__file__))

        return os.path.join(base_path, relative_path)

    def _show_hipster_pipe_animation(self):
        """Affiche la vidéo de célébration Hipster Pipe"""
        print(f"_show_hipster_pipe_animation called. hipster_pipe_enabled: {self.hipster_pipe_enabled}")
        if hasattr(self, 'hipster_video_widget') and self.hipster_video_widget:
            print("Animation already in progress, skipping")
            return  # Animation déjà en cours

        # Vérifier si le fichier vidéo existe
        video_path = self.get_resource_path("animation.mp4")
        if not os.path.exists(video_path):
            print(f"Vidéo {video_path} non trouvée, pas d'animation Hipster Pipe")
            return

        print(f"Starting Hipster Pipe animation with video: {video_path}")

        # Créer le widget vidéo
        self.hipster_video_widget = QVideoWidget(self.right_stack)
        self.hipster_video_widget.setGeometry(50, 50, 500, 300)
        self.hipster_video_widget.raise_()  # S'assurer qu'il est au-dessus

        # Créer le media player
        self.hipster_media_player = QMediaPlayer()
        self.hipster_media_player.setVideoOutput(self.hipster_video_widget)
        self.hipster_media_player.setSource(QUrl.fromLocalFile(video_path))

        # Connecter le signal de fin de vidéo
        self.hipster_media_player.mediaStatusChanged.connect(self._on_video_finished)

        # Démarrer la vidéo
        self.hipster_video_widget.show()
        self.hipster_media_player.play()
        print("Hipster Pipe video started playing")

    def _on_video_finished(self, status):
        """Appelé quand la vidéo Hipster Pipe se termine"""
        from PyQt6.QtMultimedia import QMediaPlayer

        print(f"Hipster Pipe video status changed: {status}")
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("Hipster Pipe video finished, cleaning up")
            # Nettoyer la vidéo
            if hasattr(self, 'hipster_media_player') and self.hipster_media_player:
                self.hipster_media_player.stop()
                self.hipster_media_player.deleteLater()
                self.hipster_media_player = None

            if hasattr(self, 'hipster_video_widget') and self.hipster_video_widget:
                self.hipster_video_widget.hide()
                self.hipster_video_widget.deleteLater()
                self.hipster_video_widget = None

    def show_config(self):
        dialog = ConfigDialog(self, self.config, self.config_file)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            url = dialog.get_url()
            token = dialog.get_token()
            selected_projects = dialog.get_selected_projects()
            self.auto_select_updated = dialog.get_auto_select_updated()
            self.hipster_pipe_enabled = dialog.get_hipster_pipe_enabled()

            try:
                self.save_config(url, token, selected_projects)
                self.projects = selected_projects
                self.gitlab_manager = GitLabManager(url, token)
                self.update_projects()
            except Exception as e:
                self.log_view.setPlainText(f"Erreur de configuration : {str(e)}")

    # Old config dialog removed - now using ConfigDialog from gui.dialogs

    def show_about(self):
        """Affiche la fenêtre À propos"""
        dialog = AboutDialog(self, self.get_resource_path)
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
        self.update_projects(force_update=True)
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

    def update_projects(self, force_update=False):
        if not self.gitlab_manager:
            return

        # Si c'est le premier chargement, on nettoie tout
        if not self.project_items:
            self.tree.clear()


        for proj_id in self.projects:
            # Si le projet existe déjà et qu'on ne force pas la mise à jour
            if proj_id in self.project_workers and not force_update:
                # Vérifier si le worker est toujours en cours d'exécution
                if self.project_workers[proj_id].isRunning():
                    continue

            # Créer un nouvel item si nécessaire
            if proj_id not in self.project_items:
                proj_item = QTreeWidgetItem(self.tree, [f"Chargement... (ID: {proj_id})"])
                self.project_items[proj_id] = proj_item
            else:
                proj_item = self.project_items[proj_id]

            # Arrêter le worker existant s'il y en a un
            if proj_id in self.project_workers:
                worker = self.project_workers[proj_id]
                if worker and worker.isRunning():
                    try:
                        worker.finished.disconnect()
                        worker.error.disconnect()
                        worker.stop()
                        worker.wait()
                    except:
                        pass

            # Créer un nouveau worker pour ce projet
            worker = HttpWorker(
                self._fetch_project_data,
                proj_id
            )
            worker.finished.connect(lambda data, pid=proj_id: self._on_project_data_loaded(data, pid))
            worker.error.connect(lambda error, pid=proj_id: self._on_project_error(error, pid))
            worker.start()

            self.project_workers[proj_id] = worker

        # Remove projects no longer selected
        to_remove = []
        for proj_id, item in self.project_items.items():
            if proj_id not in self.projects:
                self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
                to_remove.append(proj_id)

        for proj_id in to_remove:
            del self.project_items[proj_id]
            if proj_id in self.project_workers:
                worker = self.project_workers[proj_id]
                if worker.isRunning():
                    worker.stop()
                    worker.wait()
                del self.project_workers[proj_id]
            # Remove job workers for this project
            keys_to_remove = [k for k in self.job_status_workers if k[0] == proj_id]
            for k in keys_to_remove:
                worker = self.job_status_workers[k]
                if worker.isRunning():
                    worker.stop()
                    worker.wait()
                del self.job_status_workers[k]

    def _fetch_project_data(self, proj_id):
        """Fonction exécutée dans un thread pour récupérer les données du projet"""
        proj = self.gitlab_manager.get_project(proj_id)
        pipelines = self.gitlab_manager.get_latest_pipeline(proj_id)
        pipeline_data = []
        for pipeline in pipelines:
            jobs = self.gitlab_manager.get_pipeline_jobs(proj_id, pipeline.id)
            # Déterminer l'ordre des stages basé sur l'ordre des jobs
            stage_order = {}
            for job in jobs:
                if job.stage not in stage_order:
                    stage_order[job.stage] = len(stage_order)
            # Trier les jobs par ordre des stages inverse puis par ID
            jobs.sort(key=lambda j: (-stage_order.get(j.stage, -1), j.id))
            # Filtrer pour exclure les jobs en "created", mais garder les "manual" et "created" si ils sont dans un stage après le stage courant
            # Pour l'instant, commenter le filtrage pour tester
            # jobs = [j for j in jobs if j.status != 'created']
            pipeline_data.append({
                'pipeline': pipeline,
                'jobs': jobs
            })
        return {
            'proj_id': proj_id,
            'proj_name': proj.name,
            'pipelines': pipeline_data
        }

    def _on_project_data_loaded(self, data, proj_id):
        """Appelé quand les données d'un projet sont chargées"""
        # Vérifier si le projet existe toujours dans notre liste
        if proj_id not in self.project_items:
            return

        # Vérifier si le worker est toujours valide
        if proj_id not in self.project_workers or self.project_workers[proj_id] != self.sender():
            return

        proj_item = self.project_items[proj_id]
        proj_name = data['proj_name']
        pipelines_data = data['pipelines']

        # Mettre à jour le texte du projet
        proj_item.setText(0, f"{proj_name} (ID: {proj_id})")

        # Police en gras et plus grosse pour les projets
        font = proj_item.font(0)
        font.setBold(True)
        font.setPointSize(12)  # Un peu plus gros
        proj_item.setFont(0, font)

        # Couleur blanche pour les projets
        proj_item.setForeground(0, QColor('white'))

        # Créer un ensemble des IDs de pipelines existants
        existing_pipeline_ids = set()
        for i in range(proj_item.childCount()):
            child = proj_item.child(i)
            text = child.text(0)
            if text.startswith("Pipeline "):
                try:
                    pipeline_id = int(text.split()[1])
                    existing_pipeline_ids.add(pipeline_id)
                except (ValueError, IndexError):
                    pass

        # Traiter chaque pipeline
        for pipeline_info in pipelines_data:
            pipeline = pipeline_info['pipeline']
            jobs = pipeline_info['jobs']

            # Ajouter seulement les pipelines qui ont des jobs
            if not jobs:
                continue

            # Vérifier si ce pipeline est déjà affiché
            if pipeline.id in existing_pipeline_ids:
                # Mettre à jour le statut si nécessaire
                for i in range(proj_item.childCount()):
                    child = proj_item.child(i)
                    if child.text(0).startswith(f"Pipeline {pipeline.id}"):
                        current_text = child.text(0)
                        expected_text = f"Pipeline {pipeline.id} - {pipeline.status}"
                        if current_text != expected_text:
                            child.setText(0, expected_text)
                            # Mettre à jour les jobs aussi
                            self._update_pipeline_jobs(child, jobs, proj_id)

                            # Police en gras pour les pipelines
                            font = child.font(0)
                            font.setBold(True)
                            font.setPointSize(11)
                            child.setFont(0, font)

                            # Couleur blanche pour les pipelines
                            child.setForeground(0, QColor('white'))

                            # Si l'option est activée, sélectionner le premier job de la pipeline mise à jour
                            # if self.auto_select_updated and child.childCount() > 0:
                            #     first_job_item = child.child(0)
                            #     self.tree.setCurrentItem(first_job_item)
                            #     self.on_item_clicked(first_job_item, 0)
                        break
            else:
                # Ajouter le nouveau pipeline
                pipeline_item = QTreeWidgetItem(proj_item, [f"Pipeline {pipeline.id} - {pipeline.status}"])

                # Police en gras pour les pipelines
                font = pipeline_item.font(0)
                font.setBold(True)
                font.setPointSize(11)
                pipeline_item.setFont(0, font)

                # Couleur blanche pour les pipelines
                pipeline_item.setForeground(0, QColor('white'))

                # Ajouter les jobs
                for job in jobs:
                    job_item = QTreeWidgetItem(pipeline_item, [f"{job.name} - {job.status}"])
                    job_item.setData(0, Qt.ItemDataRole.UserRole, (proj_id, job.id))

                    # Définir la couleur selon le statut
                    self._set_job_color(job_item, job.status)

                    # Démarrer un worker de statut pour ce job
                    key = (proj_id, job.id)
                    if key not in self.job_status_workers:
                        worker = JobStatusWorker(self.gitlab_manager, proj_id, job.id, job_item, key)
                        worker.status_updated.connect(self._on_job_status_updated)
                        worker.finished_signal.connect(self._on_job_status_worker_finished)
                        worker.start()
                        self.job_status_workers[key] = worker

                # Développer le pipeline
                pipeline_item.setExpanded(True)

                # Sélectionner automatiquement le premier job de la nouvelle pipeline pour afficher ses logs
                if jobs:
                    first_job_item = pipeline_item.child(0)
                    self.tree.setCurrentItem(first_job_item)
                    self.on_item_clicked(first_job_item, 0)

        # Développer le projet si nécessaire
        if not proj_item.isExpanded():
            proj_item.setExpanded(True)

    def _update_pipeline_jobs(self, pipeline_item, jobs, proj_id):
        """Met à jour les jobs d'un pipeline existant"""
        # Créer un ensemble des IDs de jobs existants
        existing_job_ids = set()
        for i in range(pipeline_item.childCount()):
            child = pipeline_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and len(data) == 2:
                _, job_id = data
                existing_job_ids.add(job_id)

        # Ajouter ou mettre à jour les jobs
        for job in jobs:
            if job.id in existing_job_ids:
                # Mettre à jour le statut
                for i in range(pipeline_item.childCount()):
                    child = pipeline_item.child(i)
                    data = child.data(0, Qt.ItemDataRole.UserRole)
                    if data and len(data) == 2 and data[1] == job.id:
                        expected_text = f"{job.name} - {job.status}"
                        if child.text(0) != expected_text:
                            child.setText(0, expected_text)
                            # Mettre à jour la couleur
                            self._set_job_color(child, job.status)
                        break
            else:
                # Ajouter le nouveau job
                job_item = QTreeWidgetItem(pipeline_item, [f"{job.name} - {job.status}"])
                job_item.setData(0, Qt.ItemDataRole.UserRole, (proj_id, job.id))

                # Définir la couleur selon le statut
                self._set_job_color(job_item, job.status)

                # Démarrer un worker de statut pour le nouveau job
                key = (proj_id, job.id)
                if key not in self.job_status_workers:
                    worker = JobStatusWorker(self.gitlab_manager, proj_id, job.id, job_item, key)
                    worker.status_updated.connect(self._on_job_status_updated)
                    worker.finished_signal.connect(self._on_job_status_worker_finished)
                    worker.start()
                    self.job_status_workers[key] = worker

    def _on_project_error(self, error, proj_id):
        """Appelé en cas d'erreur lors du chargement d'un projet"""
        if proj_id in self.project_items:
            self.project_items[proj_id].setText(0, f"Erreur: {error}")

        # Réessayer après une minute en cas d'erreur
        QTimer.singleShot(60000, lambda: self.update_projects(force_update=True))

    def on_item_clicked(self, item, column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        # Reset to log view
        self.right_stack.setCurrentIndex(0)
        self.current_manual_job = None

        # Arrêter le worker précédent s'il existe
        if self.log_worker:
            self.log_worker.stop()
            self.log_worker.wait()
            self.log_worker = None

        if self.job_data_worker:
            self.job_data_worker.stop()
            self.job_data_worker.wait()
            self.job_data_worker = None

        proj_id, job_id = data
        self.current_job = (proj_id, job_id)

        # Afficher un message de chargement
        self.log_view.setPlainText("Chargement des logs en cours...")
        self._update_loading_display()

        # Use worker to fetch job data
        self.job_data_worker = JobDataWorker(self.gitlab_manager, proj_id, job_id)
        self.job_data_worker.data_ready.connect(self._on_job_data_received)
        self.job_data_worker.start()

    def _on_job_data_received(self, job_data):
        """Called when job data (status and logs) is received"""
        # Clean up the worker
        if self.job_data_worker:
            self.job_data_worker.stop()
            self.job_data_worker.wait()
            self.job_data_worker = None

        if job_data is None:
            self.show_error("Impossible de récupérer les données du job")
            return

        proj_id, job_id = self.current_job
        job_status = job_data.get('status')
        log_content = job_data.get('trace')

        if job_status == 'manual':
            self.current_manual_job = (proj_id, job_id)
            self.right_stack.setCurrentIndex(1)  # show launch widget
            return

        self._loading_active = job_status not in ['success', 'failed', 'canceled', 'skipped']

        print(f"Statut du job: {job_status}")
        print(f"Taille des logs: {len(log_content) if log_content else 0} caractères")

        if log_content:
            self.update_log_display(log_content)
            if self._loading_active:
                self.loading_timer.start(500)
            # Si le job est en cours, démarrer le suivi en temps réel
            if self._loading_active:
                print("Démarrage du suivi en temps réel...")
                self.log_worker = LogWorker(self.gitlab_manager, proj_id, job_id)
                self.log_worker.log_ready.connect(self.update_log_display)
                self.log_worker.error_occurred.connect(self.show_error)
                self.log_worker.job_finished.connect(self._on_job_finished)
                self.log_worker.start()
            else:
                print("Le job est terminé, pas de suivi en temps réel nécessaire")

                # Afficher un message de statut si le job est terminé
                status_messages = {
                    'success': '✅ Le job s\'est terminé avec succès',
                    'failed': '❌ Le job a échoué',
                    'canceled': '⏹️ Le job a été annulé',
                    'skipped': '⏭️ Le job a été ignoré'
                }

                if job_status in status_messages:
                    cursor = self.log_view.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    cursor.insertText('\n\n' + '='*80 + '\n')
                    cursor.insertText(status_messages[job_status] + '\n')
        else:
            # Si pas de logs initiaux, afficher un message selon le statut
            if job_status in ['success', 'failed', 'canceled', 'skipped']:
                self.show_error("Aucun log disponible pour ce job terminé")
            else:
                self.log_view.setPlainText("Logs en cours de chargement...")
                self._update_loading_display()
                if self._loading_active:
                    self.loading_timer.start(500)
                # Démarrer le suivi en temps réel même sans logs initiaux
                print("Démarrage du suivi en temps réel...")
                self.log_worker = LogWorker(self.gitlab_manager, proj_id, job_id)
                self.log_worker.log_ready.connect(self.update_log_display)
                self.log_worker.error_occurred.connect(self.show_error)
                self.log_worker.job_finished.connect(self._on_job_finished)
                self.log_worker.start()

    def _on_job_finished(self):
        """Appelé quand un job est terminé (succès, échec, etc.)"""
        if self.log_worker:
            status = self.log_worker.get_job_status()
            if status:
                status_messages = {
                    'success': '✅ Le job s\'est terminé avec succès',
                    'failed': '❌ Le job a échoué',
                    'canceled': '⏹️ Le job a été annulé',
                    'skipped': '⏭️ Le job a été ignoré'
                }
                message = status_messages.get(status, f'Le job est terminé (statut: {status})')

                # Ajouter un message à la fin des logs
                cursor = self.log_view.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertText('\n\n' + '='*80 + '\n')
                cursor.insertText(message + '\n')
                self._loading_active = False
                self.loading_timer.stop()
                self._update_loading_display()
                # Arrêter le worker car le job est terminé
                self.log_worker.stop()
                self.log_worker.wait()

    def _set_job_color(self, job_item, status):
        """Définit la couleur (et l'animation) de l'item job selon son statut
        Pour 'running', fait clignoter la couleur du texte ET le fond, et alterne le gras."""
        # Gérer l'arrêt de l'animation précédente si elle existe
        job_id_tuple = None
        data = job_item.data(0, Qt.ItemDataRole.UserRole)
        if data and isinstance(data, tuple) and len(data) == 2:
            job_id_tuple = (data[0], data[1])

        # Arrêter et supprimer l'animation si le statut n'est plus "running"
        if job_id_tuple is not None:
            if job_id_tuple in self.job_animations:
                timer, state = self.job_animations[job_id_tuple]
                timer.stop()
                timer.deleteLater()
                del self.job_animations[job_id_tuple]

        if status == 'success':
            color = QColor(100, 255, 100)  # Vert clair
            job_item.setForeground(0, color)
            job_item.setBackground(0, QColor(0, 0, 0, 0))  # Transparent/no background
            font = job_item.font(0)
            font.setBold(False)
            job_item.setFont(0, font)
        elif status == 'running':
            # Animation de clignotement bleu + fond + gras
            if job_id_tuple is not None:
                # Deux teintes de bleu pour le texte
                color1 = QColor(100, 150, 255)  # Bleu clair 1
                color2 = QColor(30, 80, 200)    # Bleu plus foncé
                # Deux couleurs de fond (subtiles)
                bg1 = QColor(230, 240, 255)    # Fond bleu très clair
                bg2 = QColor(200, 220, 245)    # Fond bleu-gris
                # Timer pour alterner
                def toggle_color():
                    current = self.job_animations[job_id_tuple][1]
                    next_state = 1 - current
                    if next_state == 0:
                        fg = color1
                        bg = bg1
                        bold = True
                    else:
                        fg = color2
                        bg = bg2
                        bold = False
                    job_item.setForeground(0, fg)
                    job_item.setBackground(0, bg)
                    font = job_item.font(0)
                    font.setBold(bold)
                    job_item.setFont(0, font)
                    self.job_animations[job_id_tuple] = (timer, next_state)
                timer = QTimer(self)
                timer.setInterval(250)  # 250 ms pour un clignotement plus perceptible
                timer.timeout.connect(toggle_color)
                # Initialiser avec la première couleur
                job_item.setForeground(0, color1)
                job_item.setBackground(0, bg1)
                font = job_item.font(0)
                font.setBold(True)
                job_item.setFont(0, font)
                self.job_animations[job_id_tuple] = (timer, 0)
                timer.start()
            else:
                # Fallback sans animation si pas d'identifiant
                color = QColor(100, 150, 255)
                job_item.setForeground(0, color)
                job_item.setBackground(0, QColor(230, 240, 255))
                font = job_item.font(0)
                font.setBold(True)
                job_item.setFont(0, font)
        elif status == 'failed':
            color = QColor(255, 100, 100)  # Rouge clair
            job_item.setForeground(0, color)
            job_item.setBackground(0, QColor(0, 0, 0, 0))
            font = job_item.font(0)
            font.setBold(False)
            job_item.setFont(0, font)
        else:
            color = QColor('white')  # Blanc pour les autres statuts
            job_item.setForeground(0, color)
            job_item.setBackground(0, QColor(0, 0, 0, 0))
            font = job_item.font(0)
            font.setBold(False)
            job_item.setFont(0, font)

    def _on_job_status_updated(self, status):
        """Appelé quand le statut d'un job est mis à jour"""
        worker = self.sender()
        if worker and hasattr(worker, 'job_item'):
            current_text = worker.job_item.text(0)
            if ' - ' in current_text:
                parts = current_text.split(' - ')
                name = parts[0]
                current_status = parts[1] if len(parts) > 1 else ''
                new_text = f"{name} - {status}"
                if current_text != new_text:
                    worker.job_item.setText(0, new_text)
                    # Mettre à jour la couleur selon le nouveau statut
                    self._set_job_color(worker.job_item, status)
                    # Si le statut passe à "running" ou "failed", sélectionner automatiquement
                    if status in ['running', 'failed'] and current_status != status:
                        self.tree.setCurrentItem(worker.job_item)
                        self.on_item_clicked(worker.job_item, 0)

                    # Hipster Pipe : célébration quand un job passe de running à success
                    if status == 'success' and current_status == 'running' and self.hipster_pipe_enabled:
                        print(f"Hipster Pipe triggered! Job {worker.job_id} went from {current_status} to {status}")
                        self._show_hipster_pipe_animation()

    def update_log_display(self, log_content):
        # Éviter le scintillement en ne mettant à jour que si le contenu a changé
        if log_content == self.last_log_content:
            return
        self.last_log_content = log_content

        # Check if we can append incrementally
        current_plain = self.log_view.toPlainText()
        loading_suffix = '\n' + self._loading_text if self._loading_active else ''
        if current_plain.endswith(loading_suffix):
            current_plain = current_plain[:-len(loading_suffix)]

        if log_content.startswith(current_plain) and current_plain:
            # Append the new part incrementally
            new_part = log_content[len(current_plain):]
            cursor = self.log_view.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            # Remove loading if present
            document = self.log_view.document()
            last_block = document.lastBlock()
            if last_block.text() in ['·', '··', '···']:
                cursor.setPosition(last_block.position())
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
                if cursor.position() > 0:
                    cursor.setPosition(cursor.position() - 1)
                    if self.log_view.toPlainText()[cursor.position()] == '\n':
                        cursor.deleteChar()

            cursor.movePosition(QTextCursor.MoveOperation.End)

            # Process and append new part
            cleaned_new_part = self._clean_ansi_codes(new_part)
            self._process_ansi_codes(cleaned_new_part, cursor)

            # Scroll to bottom
            scrollbar = self.log_view.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            self._update_loading_display()
        else:
            # Full update
            self.log_view.clear()

            # Définir la police et la taille pour le contenu
            current_font = self.log_view.font()
            current_font.setPointSize(20)  # Taille de police augmentée pour les logs
            self.log_view.setFont(current_font)

            # Créer un curseur au début du document
            cursor = self.log_view.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)

            # Appliquer le format par défaut avec une police plus grande
            default_format = QTextCharFormat()
            default_format.setForeground(QColor("white"))
            default_format.setFontPointSize(20)  # Taille de police augmentée pour correspondre à l'interface
            cursor.setCharFormat(default_format)

            # Nettoyer le contenu des codes ANSI inutiles
            cleaned_content = self._clean_ansi_codes(log_content)

            # Traiter le contenu avec les codes ANSI
            self._process_ansi_codes(cleaned_content, cursor)

            # Défiler vers le bas pour voir les derniers logs
            scrollbar = self.log_view.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            self._update_loading_display()

    def _clean_ansi_codes(self, text):
        """Nettoie le texte des séquences de contrôle inutiles tout en préservant les couleurs"""
        return LogFormatter.clean_ansi_codes(text)

    def _process_ansi_codes(self, text, cursor):
        """Traite les codes ANSI et les convertit en format de texte Qt"""
        current_font = self.log_view.font()
        font_size = current_font.pointSize()
        LogFormatter.process_ansi_codes(text, cursor, font_size)

    def show_error(self, error_message):
        self.log_view.setPlainText(error_message)

    def setup_timers(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_projects)
        # Commencer avec un intervalle plus long après le chargement initial
        QTimer.singleShot(10000, lambda: self.timer.start(3000))  # Attendre 10s puis mettre à jour toutes les 2s

        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self._animate_loading_dots)

        # Planifier une première mise à jour différée pour laisser le temps à l'interface de se charger
        QTimer.singleShot(8000, self.update_projects)

    def closeEvent(self, event):
        # Sauvegarder automatiquement la géométrie et les proportions avant de fermer
        self._auto_save_geometry()

        # Arrêter tous les workers en cours d'exécution
        if self.log_worker:
            self.log_worker.stop()
            # self.log_worker.wait()  # Retiré pour éviter le blocage

        # sync_worker is now handled in ConfigDialog

        if self.launch_worker:
            self.launch_worker.stop()

        if self.job_data_worker:
            self.job_data_worker.stop()

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

        for worker in self.project_workers.values():
            if worker and worker.isRunning():
                try:
                    worker.finished.disconnect()
                    worker.error.disconnect()
                    worker.stop()
                    # worker.wait()  # Retiré pour éviter le blocage
                except:
                    pass

        # Arrêter tous les workers de statut des jobs
        for worker in self.job_status_workers.values():
            if worker and worker.isRunning():
                worker.stop()
                # worker.wait() optionnel

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
