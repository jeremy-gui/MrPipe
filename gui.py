from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QDialog, QLabel,
    QLineEdit, QDialogButtonBox, QCheckBox
)
from PyQt6.QtGui import QAction, QTextCharFormat, QColor, QTextCursor, QFont, QFontDatabase
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QStandardPaths, QEventLoop
import os, time
import configparser
from gitlab_manager import GitLabManager
from PyQt6 import sip

class HttpWorker(QThread):
    """Worker générique pour les appels HTTP"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self._is_running = True
    
    def run(self):
        if not self._is_running:
            return
            
        try:
            result = self.func(*self.args, **self.kwargs)
            if self._is_running:
                self.finished.emit(result)
        except Exception as e:
            if self._is_running:
                self.error.emit(f"Erreur: {str(e)}")
    
    def stop(self):
        self._is_running = False


class LogWorker(QThread):
    """Worker spécifique pour la récupération des logs"""
    log_ready = pyqtSignal(str)
    job_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)  # Signal pour les erreurs
    
    def __init__(self, gitlab_manager, project_id, job_id):
        super().__init__()
        self.gitlab_manager = gitlab_manager
        self.project_id = project_id
        self.job_id = job_id
        self._is_running = True
        self._job_status = None
        self.logs_loaded = False
    
    def run(self):
        # Variable pour suivre si on a déjà chargé les logs
        logs_loaded = False
        
        while self._is_running:
            if not self._is_running:
                return
            
            # Vérifier l'état actuel du job
            status = self._get_job_status(self.project_id, self.job_id)
            if status is None:
                self._is_running = False
                return
            
            # Charger les logs au moins une fois, même si le job est terminé
            if not logs_loaded or self._job_status not in ['success', 'failed', 'canceled', 'skipped']:
                try:
                    trace = self.gitlab_manager.get_job_trace(self.project_id, self.job_id)
                    self._on_log_received(trace)
                    logs_loaded = True
                except Exception as e:
                    self.error_occurred.emit(str(e))
                    logs_loaded = True  # Pour éviter de retry en boucle
            
            # Si le job est terminé, on arrête la boucle
            if self._job_status in ['success', 'failed', 'canceled', 'skipped']:
                self.job_finished.emit()
                self._is_running = False
                break
                
            # Attendre avant la prochaine itération
            self.msleep(500)  # Vérifier toutes les 0.5 secondes pour les logs
    
    def _on_log_received(self, log):
        if self._is_running:
            self.log_ready.emit(log)
    
    def stop(self):
        self._is_running = False
    
    def _get_job_status(self, project_id, job_id):
        """Récupère le statut d'un job spécifique"""
        try:
            project = self.gitlab_manager.get_project(project_id)
            job = project.jobs.get(job_id)
            self._job_status = job.status
            return self._job_status
        except Exception as e:
            print(f"Erreur lors de la récupération du statut du job: {e}")
            # Ne pas émettre ici, géré dans run()
            return None
    
    def get_job_status(self):
        return self._job_status


class JobStatusWorker(QThread):
    """Worker pour surveiller le statut d'un job spécifique"""
    status_updated = pyqtSignal(str)
    
    def __init__(self, gitlab_manager, proj_id, job_id, job_item):
        super().__init__()
        self.gitlab_manager = gitlab_manager
        self.proj_id = proj_id
        self.job_id = job_id
        self.job_item = job_item  # Référence à l'item QTreeWidgetItem pour mise à jour
        self._is_running = True
    
    def run(self):
        while self._is_running:
            try:
                project = self.gitlab_manager.get_project(self.proj_id)
                job = project.jobs.get(self.job_id)
                status = job.status
                self.status_updated.emit(status)
                
                # Si le job est terminé, arrêter le worker
                if status in ['success', 'failed', 'canceled', 'skipped']:
                    self._is_running = False
                    break
            except Exception as e:
                print(f"Erreur mise à jour statut job {self.job_id}: {e}")
                self._is_running = False
                break
            
            self.msleep(2000)  # Vérifier toutes les 2 secondes
    
    def stop(self):
        self._is_running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitLab Pipelines Manager")
        self.gitlab_manager = None
        self.projects = []  # list of project ids
        self.current_job = None
        self.log_worker = None
        self.project_workers = {}  # Dictionnaire pour suivre les workers par projet
        self.project_items = {}  # Pour garder une référence aux items de projet
        self.job_status_workers = {}  # Dictionnaire pour suivre les workers de statut par (proj_id, job_id)
        self.config = configparser.ConfigParser()
        self.config_file = os.path.join(
            QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation),
            'gitlab_pipelines_manager.ini'
        )
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        self.auto_select_updated = True  # Par défaut activé
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
            self.log_view.setStyleSheet("""
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    font-family: 'Courier New', monospace;
                    font-size: 16pt;
                    line-height: 1.5;
                    padding: 10px;
                    selection-background-color: #4a90d9;
                    selection-color: white;
                }
            """)
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
        layout = QHBoxLayout(central)
        
        # Définir la taille initiale de la fenêtre (largeur, hauteur)
        self.resize(2000, 1200)  # Taille augmentée pour une meilleure visibilité
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Projects and Jobs")
        self.tree.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.tree)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        layout.addWidget(self.log_view)
        # Menu for settings
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        config_action = QAction("Configure", self)
        config_action.triggered.connect(self.show_config)
        settings_menu.addAction(config_action)

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
        
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def show_config(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Configuration")
        layout = QVBoxLayout(dialog)
        
        # Récupérer les valeurs actuelles ou les valeurs par défaut
        current_url = self.config.get('GitLab', 'url', fallback='https://gitlab.com')
        current_token = self.config.get('GitLab', 'token', fallback='')
        current_projects = self.config.get('GitLab', 'projects', fallback='')
        
        url_label = QLabel("GitLab URL:")
        self.url_edit = QLineEdit(current_url)
        layout.addWidget(url_label)
        layout.addWidget(self.url_edit)
        
        token_label = QLabel("Private Token:")
        self.token_edit = QLineEdit(current_token)
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(token_label)
        layout.addWidget(self.token_edit)
        
        projects_label = QLabel("Project IDs (comma separated):")
        self.projects_edit = QLineEdit(current_projects)
        layout.addWidget(projects_label)
        layout.addWidget(self.projects_edit)
        
        # Option UI
        auto_select_label = QLabel("Sélectionner automatiquement les pipelines mises à jour:")
        self.auto_select_checkbox = QCheckBox()
        self.auto_select_checkbox.setChecked(self.auto_select_updated)
        layout.addWidget(auto_select_label)
        layout.addWidget(self.auto_select_checkbox)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            url = self.url_edit.text().strip()
            token = self.token_edit.text().strip()
            projects_str = self.projects_edit.text()
            projects = [p.strip() for p in projects_str.split(',') if p.strip()]
            
            self.auto_select_updated = self.auto_select_checkbox.isChecked()
            
            try:
                self.save_config(url, token, projects)
                self.projects = [int(p) for p in projects]
                self.gitlab_manager = GitLabManager(url, token)
                self.update_projects()
            except Exception as e:
                self.log_view.setPlainText(f"Erreur de configuration : {str(e)}")

    def update_projects(self, force_update=False):
        if not self.gitlab_manager:
            return
            
        # Si c'est le premier chargement, on nettoie tout
        if not self.project_items:
            self.tree.clear()
        
        current_time = int(time.time())
        
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
                            
                            # Si l'option est activée, sélectionner le premier job de la pipeline mise à jour
                            if self.auto_select_updated and child.childCount() > 0:
                                first_job_item = child.child(0)
                                self.tree.setCurrentItem(first_job_item)
                                self.on_item_clicked(first_job_item, 0)
                        break
            else:
                # Ajouter le nouveau pipeline
                pipeline_item = QTreeWidgetItem(proj_item, [f"Pipeline {pipeline.id} - {pipeline.status}"])
                
                # Police en gras pour les pipelines
                font = pipeline_item.font(0)
                font.setBold(True)
                font.setPointSize(11)
                pipeline_item.setFont(0, font)
                
                # Ajouter les jobs
                for job in jobs:
                    job_item = QTreeWidgetItem(pipeline_item, [f"{job.name} - {job.status}"])
                    job_item.setData(0, Qt.ItemDataRole.UserRole, (proj_id, job.id))
                    
                    # Définir la couleur selon le statut
                    self._set_job_color(job_item, job.status)
                    
                    # Démarrer un worker de statut pour ce job
                    key = (proj_id, job.id)
                    if key not in self.job_status_workers:
                        worker = JobStatusWorker(self.gitlab_manager, proj_id, job.id, job_item)
                        worker.status_updated.connect(self._on_job_status_updated)
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
                    worker = JobStatusWorker(self.gitlab_manager, proj_id, job.id, job_item)
                    worker.status_updated.connect(self._on_job_status_updated)
                    worker.start()
                    self.job_status_workers[key] = worker
                
                # Sélectionner automatiquement le nouveau job pour afficher ses logs
                self.tree.setCurrentItem(job_item)
                self.on_item_clicked(job_item, 0)
    
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
            
        # Arrêter le worker précédent s'il existe
        if self.log_worker:
            self.log_worker.stop()
            self.log_worker.wait()
            self.log_worker = None
            
        proj_id, job_id = data
        self.current_job = (proj_id, job_id)
        
        # Afficher un message de chargement
        self.log_view.setPlainText("Chargement des logs en cours...")
        
        # Récupérer les logs immédiatement
        try:
            # Récupérer d'abord le statut du job
            def get_job_status(project_id, job_id):
                try:
                    print(f"Récupération du statut du job {job_id}...")
                    project = self.gitlab_manager.get_project(project_id)
                    job = project.jobs.get(job_id)
                    status = job.status
                    print(f"Statut du job {job_id}: {status}")
                    
                    # Récupérer les logs directement ici
                    print(f"Récupération des logs pour le job {job_id}...")
                    try:
                        trace = job.trace().decode('utf-8')
                        print(f"Logs récupérés directement, longueur: {len(trace)}")
                        return status, trace
                    except Exception as e:
                        print(f"Erreur lors de la récupération directe des logs: {e}")
                        return status, None
                        
                except Exception as e:
                    error_msg = f"Erreur lors de la récupération du statut du job {job_id}: {e}"
                    print(error_msg)
                    self.show_error(error_msg)
                    return None, None
            
            print("Création du worker de statut et de logs...")
            
            # Utiliser un QEventLoop pour attendre la fin de l'opération
            loop = QEventLoop()
            
            # Fonction pour gérer la fin de la récupération
            def on_job_data_received():
                loop.quit()
            
            # Créer un worker pour récupérer les données du job
            def fetch_job_data():
                try:
                    project = self.gitlab_manager.get_project(proj_id)
                    job = project.jobs.get(job_id)
                    status = job.status
                    
                    # Essayer de récupérer les logs
                    try:
                        trace = job.trace().decode('utf-8')
                        return {'status': status, 'trace': trace}
                    except Exception as e:
                        print(f"Erreur lors de la récupération des logs: {e}")
                        return {'status': status, 'trace': None}
                        
                except Exception as e:
                    print(f"Erreur lors de la récupération des données du job: {e}")
                    return None
            
            job_data = None
            
            # Exécuter dans un thread pour ne pas bloquer l'interface
            def run_in_thread():
                nonlocal job_data
                job_data = fetch_job_data()
                loop.quit()
            
            import threading
            thread = threading.Thread(target=run_in_thread)
            thread.daemon = True
            thread.start()
            
            # Attendre la fin du thread avec un timeout
            QTimer.singleShot(10000, loop.quit)  # Timeout de 10 secondes
            loop.exec()
            
            if job_data is None:
                self.show_error("Impossible de récupérer les données du job")
                return
                
            job_status = job_data.get('status')
            log_content = job_data.get('trace')
            
            print(f"Statut du job: {job_status}")
            print(f"Taille des logs: {len(log_content) if log_content else 0} caractères")
            
            if log_content:
                self.update_log_display(log_content)
                
                # Si le job est en cours, démarrer le suivi en temps réel
                if job_status not in ['success', 'failed', 'canceled', 'skipped']:
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
                    # Démarrer le suivi en temps réel même sans logs initiaux
                    print("Démarrage du suivi en temps réel...")
                    self.log_worker = LogWorker(self.gitlab_manager, proj_id, job_id)
                    self.log_worker.log_ready.connect(self.update_log_display)
                    self.log_worker.error_occurred.connect(self.show_error)
                    self.log_worker.job_finished.connect(self._on_job_finished)
                    self.log_worker.start()
            
        except Exception as e:
            error_msg = f"Erreur lors du chargement des logs: {str(e)}"
            print(error_msg)
            self.show_error(error_msg)
            import traceback
            traceback.print_exc()
    
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
                
                # Arrêter le worker car le job est terminé
                self.log_worker.stop()
                self.log_worker.wait()

    def _set_job_color(self, job_item, status):
        """Définit la couleur de l'item job selon son statut"""
        if status == 'success':
            color = QColor(100, 255, 100)  # Vert clair
        elif status == 'running':
            color = QColor(100, 150, 255)  # Bleu clair
        elif status == 'failed':
            color = QColor(255, 100, 100)  # Rouge clair
        else:
            color = QColor('white')  # Blanc pour les autres statuts
        job_item.setForeground(0, color)

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

    def update_log_display(self, log_content):
        # Vider le contenu actuel
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
    
    def _clean_ansi_codes(self, text):
        """Nettoie le texte des séquences de contrôle inutiles tout en préservant les couleurs"""
        import re
        
        # Liste des séquences de contrôle à supprimer (sauf les couleurs qui se terminent par 'm')
        control_sequences = [
            r'\x1b\[\d*[JK]',  # Effacement d'écran et de lignes
            r'\x1b\[\d*;*\d*[Hf]',  # Positionnement du curseur
            r'\x1b\[\d*[ABCD]',  # Déplacements du curseur
            r'\x1b\[\?\d*[hl]',  # Paramètres d'affichage
            r'\x1b\[\d*[ST]',  # Défilement et tabulation
            r'\x1b\[\?1[hl]',  # Mode curseur
            r'\x1b\[\?25[hl]',  # Curseur visible/invisible
            r'\x1b\[2J',  # Effacer l'écran
            r'\x1b\[K',  # Effacer jusqu'à la fin de la ligne
            r'\x1b\[\?7[hl]',  # Mode retour à la ligne automatique
            r'\x1b\[\?1h\=7h',  # Mode VT100
            r'\x1b\[\?1l\>',  # Désactiver le mode VT100
            r'\x1b\[\?\d*[hl]',  # Codes de configuration d'écran
            # Ne pas inclure les codes de couleur qui se terminent par 'm'
        ]
        
        # Supprimer les séquences de contrôle une par une
        for pattern in control_sequences:
            text = re.sub(pattern, '', text)
            
        # Nettoyer les séquences de contrôle orphelines qui ne sont pas des codes de couleur
        text = re.sub(r'\x1b\[(?![\d;]*m)[^a-zA-Z]', '', text)
        
        # Supprimer les séquences de contrôle résiduelles qui ne sont pas des codes de couleur
        text = re.sub(r'\x1b\[(?![\d;]*m)[\d;]*[a-zA-Z]', '', text)
        
        return text
    
    def _process_ansi_codes(self, text, cursor):
        """Traite les codes ANSI et les convertit en format de texte Qt"""
        import re
        
        # Ne pas nettoyer le texte ici pour conserver les codes couleur
        
        # Expression régulière pour les codes ANSI
        ansi_escape = re.compile(r'(\x1b\[[0-9;]*m)')
        
        # Définition des styles ANSI
        ansi_styles = {
            '0': lambda f: f,  # Reset
            '1': lambda f: f.setFontWeight(75),  # Bold
            '3': lambda f: f.setFontItalic(True),  # Italic
            '4': lambda f: f.setFontUnderline(True),  # Underline
            '30': lambda f: f.setForeground(QColor('black')),  # Black
            '31': lambda f: f.setForeground(QColor(255, 85, 85)),  # Red (plus visible sur fond sombre)
            '32': lambda f: f.setForeground(QColor(85, 255, 85)),  # Green
            '33': lambda f: f.setForeground(QColor(255, 255, 85)),  # Yellow
            '34': lambda f: f.setForeground(QColor(85, 85, 255)),  # Blue
            '35': lambda f: f.setForeground(QColor(255, 85, 255)),  # Magenta
            '36': lambda f: f.setForeground(QColor(85, 255, 255)),  # Cyan
            '37': lambda f: f.setForeground(QColor('white')),  # White
            '90': lambda f: f.setForeground(QColor(127, 127, 127)),  # Bright Black (gray)
            '91': lambda f: f.setForeground(QColor(255, 85, 85)),  # Bright Red
            '92': lambda f: f.setForeground(QColor(85, 255, 85)),  # Bright Green
            '93': lambda f: f.setForeground(QColor(255, 255, 85)),  # Bright Yellow
            '94': lambda f: f.setForeground(QColor(85, 85, 255)),  # Bright Blue
            '95': lambda f: f.setForeground(QColor(255, 85, 255)),  # Bright Magenta
            '96': lambda f: f.setForeground(QColor(85, 255, 255)),  # Bright Cyan
            '97': lambda f: f.setForeground(QColor('white')),  # Bright White
            '40': lambda f: f.setBackground(QColor('black')),  # Background black
            '41': lambda f: f.setBackground(QColor('darkRed')),  # Background red
            '42': lambda f: f.setBackground(QColor('darkGreen')),  # Background green
            '43': lambda f: f.setBackground(QColor('darkYellow')),  # Background yellow
            '44': lambda f: f.setBackground(QColor('darkBlue')),  # Background blue
            '45': lambda f: f.setBackground(QColor('darkMagenta')),  # Background magenta
            '46': lambda f: f.setBackground(QColor('darkCyan')),  # Background cyan
            '47': lambda f: f.setBackground(QColor('lightGray')),  # Background white
        }
        
        # Récupérer la taille de police actuelle du widget
        current_font = self.log_view.font()
        font_size = current_font.pointSize()
        
        # Format de texte par défaut avec la police actuelle
        default_format = QTextCharFormat()
        default_format.setForeground(QColor('white'))
        default_format.setFontPointSize(font_size)
        current_format = QTextCharFormat(default_format)
        
        # Diviser le texte en segments en utilisant les codes ANSI comme séparateurs
        segments = ansi_escape.split(text)
        
        for segment in segments:
            if not segment:
                continue
                
            # Vérifier si c'est un code ANSI
            if segment.startswith('\x1b[') and segment.endswith('m'):
                codes = segment[2:-1].split(';')  # Enlever '\x1b[' et 'm', puis séparer par ';'
                
                for code in codes:
                    if not code:  # Code vide signifie réinitialisation
                        current_format = QTextCharFormat(default_format)
                    elif code in ansi_styles:
                        ansi_styles[code](current_format)
                    # Gestion des codes 256 couleurs (simplifiée)
                    elif code.startswith('38;5;') and len(code.split(';')) == 3:
                        # Code de couleur 256 (simplifié)
                        pass  # On ignore pour l'instant
                    else:
                        # Code inconnu, on réinitialise
                        current_format = QTextCharFormat(default_format)
                        
                # Appliquer le format mis à jour
                cursor.setCharFormat(current_format)
            else:
                # C'est du texte à afficher
                cursor.insertText(segment, current_format)
        
    def show_error(self, error_message):
        self.log_view.setPlainText(error_message)

    def setup_timers(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_projects)
        self.timer.start(2000)  # Vérifier les mises à jour toutes les 1 seconde
        
        # Planifier une première mise à jour différée pour laisser le temps à l'interface de se charger
        QTimer.singleShot(500, self.update_projects)
        
    def closeEvent(self, event):
        # Arrêter tous les workers en cours d'exécution
        if self.log_worker:
            self.log_worker.stop()
            # self.log_worker.wait()  # Retiré pour éviter le blocage
            
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
                
        event.accept()
