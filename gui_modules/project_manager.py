"""
Project management utilities
"""

from PyQt6.QtWidgets import QTreeWidgetItem, QPushButton, QWidget, QHBoxLayout, QLabel
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtCore import Qt, QTimer
from datetime import datetime

from .workers import HttpWorker, JobStatusWorker
from .styles import TREE_FONT_SIZE_PROJECT, TREE_FONT_SIZE_PIPELINE


def format_timestamp(timestamp_str):
    """Format a timestamp string to a readable format"""
    if not timestamp_str:
        return ""
    try:
        # Parse ISO format timestamp
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        # Format to readable format: DD/MM/YYYY HH:MM
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception as e:
        print(f"Error formatting timestamp {timestamp_str}: {e}")
        return ""


def format_job_tooltip(job):
    """Format tooltip for a job with creation and update dates"""
    try:
        tooltip_parts = []
        
        if hasattr(job, 'created_at') and job.created_at:
            created = format_timestamp(job.created_at)
            if created:
                tooltip_parts.append(f"Created: {created}")
        
        if hasattr(job, 'started_at') and job.started_at:
            started = format_timestamp(job.started_at)
            if started:
                tooltip_parts.append(f"Started: {started}")
        
        if hasattr(job, 'finished_at') and job.finished_at:
            finished = format_timestamp(job.finished_at)
            if finished:
                tooltip_parts.append(f"Finished: {finished}")
        
        if tooltip_parts:
            return "\n".join(tooltip_parts)
        return ""
    except Exception as e:
        print(f"Error formatting job tooltip: {e}")
        return ""


class ProjectManager:
    """Manages project display and updates"""
    
    def __init__(self, main_window):
        self.window = main_window
        self.loading_queue = []  # Queue for progressive loading
        self.is_loading = False  # Flag to prevent concurrent loading
        self.initial_load_done = False  # Flag to track initial load
        self.manually_collapsed_projects = set()  # Track projects manually collapsed by user
        self.hidden_pipelines = set()  # Track hidden pipelines (proj_id, pipeline_id)
    
    def create_env_pill(self, env_name):
        """Create a pill widget for environment name"""
        pill = QLabel(env_name)
        pill.setStyleSheet("""
            QLabel {
                background-color: transparent;
                color: #99e5ff;
                border: 1px solid #99e5ff;
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 9pt;
                font-weight: bold;
            }
        """)
        return pill
    
    def create_pipeline_buttons(self, proj_id, pipeline_id, pipeline_item, pipeline_status):
        """Create action buttons widget for a pipeline (restart, cancel, hide)"""
        # Create a container widget with minimal padding
        container = QWidget()
        container.setFixedWidth(70)  # Largeur fixe pour 3 boutons (3x20 + padding)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 0, 0, 0)  # Padding 5px à gauche seulement
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        from .ui_helpers import UIHelpers
        
        # Restart button
        restart_button = QPushButton()
        restart_button.setFixedSize(20, 20)
        restart_icon_path = UIHelpers.get_resource_path("assets/start.svg")
        restart_button.setIcon(QIcon(restart_icon_path))
        restart_button.setIconSize(restart_button.size())
        restart_button.setCursor(Qt.CursorShape.PointingHandCursor)
        restart_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 0.2);
                border-radius: 3px;
            }
        """)
        restart_button.setToolTip("Relancer la pipeline")
        restart_button.clicked.connect(lambda: self.restart_pipeline(proj_id, pipeline_id))
        layout.addWidget(restart_button)
        
        # Cancel button - show if pipeline is running or pending
        if pipeline_status in ['running', 'pending']:
            cancel_button = QPushButton()
            cancel_button.setFixedSize(20, 20)
            cancel_icon_path = UIHelpers.get_resource_path("assets/stop.svg")
            cancel_button.setIcon(QIcon(cancel_icon_path))
            cancel_button.setIconSize(cancel_button.size())
            cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
            cancel_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 152, 0, 0.2);
                    border-radius: 3px;
                }
            """)
            cancel_button.setToolTip("Annuler la pipeline")
            cancel_button.clicked.connect(lambda: self.cancel_pipeline(proj_id, pipeline_id))
            layout.addWidget(cancel_button)
        
        # Hide button
        hide_button = QPushButton()
        hide_button.setFixedSize(20, 20)
        trash_icon_path = UIHelpers.get_resource_path("assets/trash.svg")
        hide_button.setIcon(QIcon(trash_icon_path))
        hide_button.setIconSize(hide_button.size())
        hide_button.setCursor(Qt.CursorShape.PointingHandCursor)
        hide_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 68, 68, 0.1);
                border-radius: 3px;
            }
        """)
        hide_button.setToolTip("Masquer cette pipeline")
        hide_button.clicked.connect(lambda: self.delete_pipeline(proj_id, pipeline_id, pipeline_item))
        layout.addWidget(hide_button)
        
        return container
    
    def restart_pipeline(self, proj_id, pipeline_id):
        """Restart a pipeline - creates a new pipeline with same parameters"""
        try:
            project = self.window.gitlab_manager.get_project(proj_id)
            pipeline = project.pipelines.get(pipeline_id)
            
            # Get the ref (branch) from the current pipeline
            ref = pipeline.ref
            
            # Create a new pipeline with the same ref
            new_pipeline = project.pipelines.create({'ref': ref})
            print(f"Nouvelle pipeline {new_pipeline.id} créée à partir de la pipeline {pipeline_id} (ref: {ref})")
            
            # Show success message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self.window, "Pipeline créée", 
                                   f"Nouvelle pipeline #{new_pipeline.id} créée avec succès sur la branche '{ref}'.")
            
            # Store the new pipeline ID to select it after refresh
            self.window.pending_selection = ('pipeline', proj_id, new_pipeline.id)
            
            # Refresh the project data
            self._start_project_worker(proj_id, progressive=False)
        except Exception as e:
            error_msg = str(e)
            print(f"Erreur lors du relancement de la pipeline: {error_msg}")
            # Show error message to user
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self.window, "Erreur", f"Erreur lors de la création de la pipeline:\n{error_msg}")
    
    def cancel_pipeline(self, proj_id, pipeline_id):
        """Cancel a pipeline"""
        try:
            project = self.window.gitlab_manager.get_project(proj_id)
            pipeline = project.pipelines.get(pipeline_id)
            pipeline.cancel()
            print(f"Pipeline {pipeline_id} annulée")
            
            # Show success message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self.window, "Pipeline annulée", f"La pipeline a été annulée avec succès.")
            
            # Refresh the project data
            self._start_project_worker(proj_id, progressive=False)
        except Exception as e:
            error_msg = str(e)
            print(f"Erreur lors de l'annulation de la pipeline: {error_msg}")
            # Show error message to user
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self.window, "Erreur", f"Erreur lors de l'annulation de la pipeline:\n{error_msg}")
    
    def delete_pipeline(self, proj_id, pipeline_id, pipeline_item):
        """Delete (hide) a pipeline from the display"""
        # Add to hidden pipelines
        self.hidden_pipelines.add((proj_id, pipeline_id))
        
        # Remove the item from the tree
        parent = pipeline_item.parent()
        if parent:
            parent.removeChild(pipeline_item)
            
            # If the project has no more visible pipelines, show a message
            if parent.childCount() == 0:
                placeholder = QTreeWidgetItem(parent, ["Toutes les pipelines sont masquées"])
                placeholder.setForeground(0, QColor('#888'))
        
        print(f"Pipeline {pipeline_id} du projet {proj_id} masquée")
    
    def update_projects(self, force_update=False):
        """Update all projects in the tree"""
        if not self.window.gitlab_manager:
            return

        if not self.window.project_items:
            self.window.tree.clear()

        # Build the loading queue
        projects_to_load = []
        for proj_id in self.window.projects:
            if proj_id in self.window.project_workers and not force_update:
                if self.window.project_workers[proj_id].isRunning():
                    continue
            projects_to_load.append(proj_id)

        # If this is the initial load, use progressive loading
        if not self.initial_load_done and projects_to_load:
            self.loading_queue = projects_to_load
            self.initial_load_done = True
            self.window.is_initial_loading = True
            # Show loading message in tree
            if not self.window.project_items:
                loading_item = QTreeWidgetItem(self.window.tree, ["Chargement des projets en cours..."])
                loading_item.setForeground(0, QColor('yellow'))
            self._load_next_project()
        else:
            # For subsequent updates, load all at once (but still async)
            for proj_id in projects_to_load:
                self._start_project_worker(proj_id)

        # Remove projects no longer selected
        self._cleanup_removed_projects()

    def _load_next_project(self):
        """Load the next project in the queue progressively"""
        # Check if window is still valid
        if not hasattr(self, 'window') or not self.window:
            return
            
        if not self.loading_queue:
            self.is_loading = False
            # Remove loading message
            try:
                for i in range(self.window.tree.topLevelItemCount()):
                    item = self.window.tree.topLevelItem(i)
                    if item and item.text(0) == "Chargement des projets en cours...":
                        self.window.tree.takeTopLevelItem(i)
                        break
            except:
                pass
            
            # Signal that initial loading is complete
            self.window.is_initial_loading = False
            
            # Select and load the most recent job
            if not hasattr(self.window, 'select_job_timer'):
                self.window.select_job_timer = QTimer(self.window)
                self.window.select_job_timer.setSingleShot(True)
                self.window.select_job_timer.timeout.connect(self._select_most_recent_job)
            self.window.select_job_timer.start(200)
            
            # Open config dialog if it was requested during loading
            if hasattr(self.window, 'pending_config_dialog') and self.window.pending_config_dialog:
                self.window.pending_config_dialog = False
                # Use QTimer to open dialog after event loop processes
                if not hasattr(self.window, 'open_config_timer'):
                    self.window.open_config_timer = QTimer(self.window)
                    self.window.open_config_timer.setSingleShot(True)
                    self.window.open_config_timer.timeout.connect(self._safe_open_config_dialog)
                self.window.open_config_timer.start(300)
            return

        if self.is_loading:
            return

        self.is_loading = True
        proj_id = self.loading_queue.pop(0)
        self._start_project_worker(proj_id, progressive=True)

    def _start_project_worker(self, proj_id, progressive=False):
        """Start a worker to load a single project"""
        if proj_id not in self.window.project_items:
            proj_item = QTreeWidgetItem(self.window.tree, [f"Chargement... (ID: {proj_id})"])
            self.window.project_items[proj_id] = proj_item
        else:
            proj_item = self.window.project_items[proj_id]

        if proj_id in self.window.project_workers:
            worker = self.window.project_workers[proj_id]
            if worker and worker.isRunning():
                try:
                    worker.finished.disconnect()
                    worker.error.disconnect()
                    worker.stop()
                    if worker.isRunning():
                        worker.wait(500)
                        if worker.isRunning():
                            worker.terminate()
                            worker.wait()
                except:
                    pass

        worker = HttpWorker(self.fetch_project_data, proj_id)
        
        if progressive:
            worker.finished.connect(lambda data, pid=proj_id: self._on_progressive_load_done(data, pid))
            worker.error.connect(lambda error, pid=proj_id: self._on_progressive_load_error(error, pid))
        else:
            worker.finished.connect(lambda data, pid=proj_id: self.on_project_data_loaded(data, pid))
            worker.error.connect(lambda error, pid=proj_id: self.on_project_error(error, pid))
        
        self.window.project_workers[proj_id] = worker
        worker.start()

    def _on_progressive_load_done(self, data, proj_id):
        """Called when a project loads during progressive loading"""
        try:
            self.on_project_data_loaded(data, proj_id)
        except Exception as e:
            print(f"Error in _on_progressive_load_done: {e}")
        finally:
            self.is_loading = False
            # Load next project after a short delay to keep UI responsive
            if hasattr(self.window, 'project_manager'):
                if not hasattr(self.window, 'next_project_timer'):
                    self.window.next_project_timer = QTimer(self.window)
                    self.window.next_project_timer.setSingleShot(True)
                    self.window.next_project_timer.timeout.connect(self._load_next_project)
                self.window.next_project_timer.start(100)

    def _on_progressive_load_error(self, error, proj_id):
        """Called when a project fails during progressive loading"""
        try:
            self.on_project_error(error, proj_id)
        except Exception as e:
            print(f"Error in _on_progressive_load_error: {e}")
        finally:
            self.is_loading = False
            # Continue with next project
            if hasattr(self.window, 'project_manager'):
                if not hasattr(self.window, 'next_project_timer'):
                    self.window.next_project_timer = QTimer(self.window)
                    self.window.next_project_timer.setSingleShot(True)
                    self.window.next_project_timer.timeout.connect(self._load_next_project)
                self.window.next_project_timer.start(100)
    
    def _safe_open_config_dialog(self):
        """Safely open config dialog with checks"""
        if hasattr(self.window, '_open_config_dialog') and self.window.isVisible():
            self.window._open_config_dialog()
    
    def _select_most_recent_job(self):
        """Select and load the most recent job after initial loading"""
        try:
            # Find the first project with jobs
            for i in range(self.window.tree.topLevelItemCount()):
                project_item = self.window.tree.topLevelItem(i)
                if project_item and project_item.childCount() > 0:
                    # Get the first pipeline (most recent)
                    pipeline_item = project_item.child(0)
                    if pipeline_item and pipeline_item.childCount() > 0:
                        # Get the first job in the pipeline
                        first_job_item = pipeline_item.child(0)
                        if first_job_item:
                            # Select and load this job
                            self.window.tree.setCurrentItem(first_job_item)
                            self.window.job_manager.on_item_clicked(first_job_item, 0)
                            print("Selected most recent job after initial loading")
                            return
        except Exception as e:
            print(f"Error selecting most recent job: {e}")

    def _cleanup_removed_projects(self):
        """Remove projects that are no longer selected"""
        to_remove = []
        for proj_id, item in self.window.project_items.items():
            if proj_id not in self.window.projects:
                self.window.tree.takeTopLevelItem(self.window.tree.indexOfTopLevelItem(item))
                to_remove.append(proj_id)

        for proj_id in to_remove:
            del self.window.project_items[proj_id]
            if proj_id in self.window.project_workers:
                worker = self.window.project_workers[proj_id]
                if worker.isRunning():
                    worker.stop()
                    worker.wait(500)
                    if worker.isRunning():
                        worker.terminate()
                        worker.wait()
                del self.window.project_workers[proj_id]
            keys_to_remove = [k for k in self.window.job_status_workers if k[0] == proj_id]
            for k in keys_to_remove:
                worker = self.window.job_status_workers[k]
                if worker.isRunning():
                    worker.stop()
                    worker.wait(500)
                    if worker.isRunning():
                        worker.terminate()
                        worker.wait()
                del self.window.job_status_workers[k]

    def fetch_project_data(self, proj_id):
        """Fetch project data in a thread"""
        proj = self.window.gitlab_manager.get_project(proj_id)
        pipelines = self.window.gitlab_manager.get_latest_pipeline(proj_id)
        pipeline_data = []
        for pipeline in pipelines:
            jobs = self.window.gitlab_manager.get_pipeline_jobs(proj_id, pipeline.id)
            stage_order = {}
            for job in jobs:
                if job.stage not in stage_order:
                    stage_order[job.stage] = len(stage_order)
            jobs.sort(key=lambda j: (-stage_order.get(j.stage, -1), j.id))
            pipeline_data.append({
                'pipeline': pipeline,
                'jobs': jobs
            })
        return {
            'proj_id': proj_id,
            'proj_name': proj.name,
            'pipelines': pipeline_data
        }

    def on_project_data_loaded(self, data, proj_id):
        """Called when project data is loaded"""
        if proj_id not in self.window.project_items:
            return

        if proj_id not in self.window.project_workers or self.window.project_workers[proj_id] != self.window.sender():
            return

        proj_item = self.window.project_items[proj_id]
        proj_name = data['proj_name']
        pipelines_data = data['pipelines']

        proj_item.setText(0, f"{proj_name} (ID: {proj_id})")

        font = proj_item.font(0)
        font.setBold(True)
        font.setPointSize(TREE_FONT_SIZE_PROJECT)
        proj_item.setFont(0, font)
        proj_item.setForeground(0, QColor('white'))
        existing_pipeline_ids = {}  # Changed to dict to map id -> item
        for i in range(proj_item.childCount()):
            child = proj_item.child(i)
            # Get pipeline ID from item data
            pipeline_id = child.data(0, Qt.ItemDataRole.UserRole + 1)
            if pipeline_id is not None:
                existing_pipeline_ids[pipeline_id] = child

        for pipeline_info in pipelines_data:
            pipeline = pipeline_info['pipeline']
            jobs = pipeline_info['jobs']

            if not jobs:
                continue
            
            # Skip hidden pipelines
            if (proj_id, pipeline.id) in self.hidden_pipelines:
                continue

            # Format pipeline environment target (ref/branch) as a pill
            pipeline_env = ""
            if hasattr(pipeline, 'ref') and pipeline.ref:
                # Utiliser des caractères Unicode pour créer un encadrement
                pipeline_env = f"【{pipeline.ref}】"
            
            # Format pipeline timestamp
            pipeline_time = ""
            if hasattr(pipeline, 'created_at') and pipeline.created_at:
                pipeline_time = format_timestamp(pipeline.created_at)
                pipeline_time = f"【{pipeline_time}】" if pipeline_time else ""

            if pipeline.id in existing_pipeline_ids:
                child = existing_pipeline_ids[pipeline.id]
                current_text = child.text(0)
                expected_text = f"{pipeline_env}Pipeline {pipeline.id} • {pipeline.status} • {pipeline_time}"
                if current_text != expected_text:
                    child.setText(0, expected_text)
                    self.update_pipeline_jobs(child, jobs, proj_id, pipeline)

                    font = child.font(0)
                    font.setBold(True)
                    font.setPointSize(TREE_FONT_SIZE_PIPELINE)
                    child.setFont(0, font)
                    
                    # Appliquer une couleur différente si environnement présent
                    if pipeline_env:
                        child.setForeground(0, QColor('#99e5ff'))  # Bleu clair pour la pill
                    else:
                        child.setForeground(0, QColor('white'))
                
                # Update action buttons (recreate to reflect current status)
                buttons = self.create_pipeline_buttons(proj_id, pipeline.id, child, pipeline.status)
                self.window.tree.setItemWidget(child, 1, buttons)
            else:
                pipeline_item = QTreeWidgetItem(proj_item,
                                                [f"{pipeline_env}Pipeline {pipeline.id} - {pipeline.status}{pipeline_time}"])

                # Store pipeline ID in item data
                pipeline_item.setData(0, Qt.ItemDataRole.UserRole + 1, pipeline.id)

                font = pipeline_item.font(0)
                font.setBold(True)
                font.setPointSize(TREE_FONT_SIZE_PIPELINE)
                pipeline_item.setFont(0, font)
                
                # Appliquer une couleur différente si environnement présent
                if pipeline_env:
                    pipeline_item.setForeground(0, QColor('#99e5ff'))  # Bleu clair pour la pill
                else:
                    pipeline_item.setForeground(0, QColor('white'))
                
                # Add action buttons widget
                buttons = self.create_pipeline_buttons(proj_id, pipeline.id, pipeline_item, pipeline.status)
                self.window.tree.setItemWidget(pipeline_item, 1, buttons)

                for job in jobs:
                    job_item = QTreeWidgetItem(pipeline_item, [f"{job.name} - {job.status}"])
                    job_item.setData(0, Qt.ItemDataRole.UserRole, (proj_id, job.id))

                    # Set tooltip with job timestamps
                    tooltip = format_job_tooltip(job)
                    if tooltip:
                        job_item.setToolTip(0, tooltip)

                    # Import job_manager to set color
                    from .job_manager import JobColorManager
                    JobColorManager.set_job_color(self.window, job_item, job.status)
                    
                    # Add action buttons for jobs
                    job_buttons = self.window.job_manager.create_job_buttons(proj_id, job.id, job.status)
                    self.window.tree.setItemWidget(job_item, 1, job_buttons)

                    key = (proj_id, job.id)
                    if key not in self.window.job_status_workers:
                        worker = JobStatusWorker(self.window.gitlab_manager, proj_id, job.id, job_item, key)
                        worker.status_updated.connect(
                            lambda status: JobColorManager.on_job_status_updated(self.window, status))
                        worker.finished_signal.connect(self.window._on_job_status_worker_finished)
                        worker.start()
                        self.window.job_status_workers[key] = worker

                pipeline_item.setExpanded(True)

                # Ne charger les logs que si ce n'est pas le chargement initial
                if jobs and not self.window.is_initial_loading:
                    first_job_item = pipeline_item.child(0)
                    self.window.tree.setCurrentItem(first_job_item)
                    self.window.job_manager.on_item_clicked(first_job_item, 0)
        # Only expand if not manually collapsed by user
        if proj_id not in self.manually_collapsed_projects:
            if not proj_item.isExpanded():
                proj_item.setExpanded(True)
        
        # Check if we need to select a specific pipeline or job after refresh
        if hasattr(self.window, 'pending_selection') and self.window.pending_selection:
            sel_type, sel_proj_id, sel_id = self.window.pending_selection
            if sel_proj_id == proj_id:
                if sel_type == 'pipeline':
                    # Find and select the pipeline
                    for i in range(proj_item.childCount()):
                        child = proj_item.child(i)
                        pipeline_id = child.data(0, Qt.ItemDataRole.UserRole + 1)
                        if pipeline_id == sel_id:
                            # Expand the pipeline and select its first job
                            child.setExpanded(True)
                            if child.childCount() > 0:
                                first_job = child.child(0)
                                self.window.tree.setCurrentItem(first_job)
                                self.window.job_manager.on_item_clicked(first_job, 0)
                            break
                elif sel_type == 'job':
                    # Find and select the job
                    for i in range(proj_item.childCount()):
                        pipeline_child = proj_item.child(i)
                        for j in range(pipeline_child.childCount()):
                            job_child = pipeline_child.child(j)
                            data = job_child.data(0, Qt.ItemDataRole.UserRole)
                            if data and len(data) == 2 and data[1] == sel_id:
                                self.window.tree.setCurrentItem(job_child)
                                self.window.job_manager.on_item_clicked(job_child, 0)
                                break
                # Clear the pending selection
                self.window.pending_selection = None

    def update_pipeline_jobs(self, pipeline_item, jobs, proj_id, pipeline=None):
        """Update jobs in an existing pipeline"""
        existing_job_ids = set()
        for i in range(pipeline_item.childCount()):
            child = pipeline_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and len(data) == 2:
                _, job_id = data
                existing_job_ids.add(job_id)

        for job in jobs:
            if job.id in existing_job_ids:
                for i in range(pipeline_item.childCount()):
                    child = pipeline_item.child(i)
                    data = child.data(0, Qt.ItemDataRole.UserRole)
                    if data and len(data) == 2 and data[1] == job.id:
                        expected_text = f"{job.name} - {job.status}"
                        if child.text(0) != expected_text:
                            child.setText(0, expected_text)
                        
                        from .job_manager import JobColorManager
                        JobColorManager.set_job_color(self.window, child, job.status)
                        
                        # Update tooltip with job timestamps
                        tooltip = format_job_tooltip(job)
                        if tooltip:
                            child.setToolTip(0, tooltip)
                        
                        # Always update action buttons to reflect current status
                        job_buttons = self.window.job_manager.create_job_buttons(proj_id, job.id, job.status)
                        self.window.tree.setItemWidget(child, 1, job_buttons)
                        break
            else:
                job_item = QTreeWidgetItem(pipeline_item, [f"{job.name} - {job.status}"])
                job_item.setData(0, Qt.ItemDataRole.UserRole, (proj_id, job.id))
                
                # Set tooltip with job timestamps
                tooltip = format_job_tooltip(job)
                if tooltip:
                    job_item.setToolTip(0, tooltip)

                from .job_manager import JobColorManager
                JobColorManager.set_job_color(self.window, job_item, job.status)
                
                # Add action buttons for new jobs
                job_buttons = self.window.job_manager.create_job_buttons(proj_id, job.id, job.status)
                self.window.tree.setItemWidget(job_item, 1, job_buttons)

                key = (proj_id, job.id)
                if key not in self.window.job_status_workers:
                    worker = JobStatusWorker(self.window.gitlab_manager, proj_id, job.id, job_item, key)
                    worker.status_updated.connect(lambda status: JobColorManager.on_job_status_updated(self.window, status))
                    worker.finished_signal.connect(self.window._on_job_status_worker_finished)
                    worker.start()
                    self.window.job_status_workers[key] = worker

    def on_project_error(self, error, proj_id):
        """Called on project loading error"""
        # Ne pas afficher l'erreur dans le tree, juste logger
        print(f"Erreur chargement projet {proj_id}: {error}")
        
        # Optionnel: masquer temporairement le projet en erreur
        if proj_id in self.window.project_items:
            proj_item = self.window.project_items[proj_id]
            # Garder le nom du projet mais indiquer qu'il est temporairement indisponible
            current_text = proj_item.text(0)
            if not current_text.endswith("(indisponible)"):
                proj_item.setText(0, f"{current_text} (indisponible)")
            # Griser le texte
            proj_item.setForeground(0, QColor('#666'))
        
        # Retry after 60 seconds
        if not hasattr(self.window, 'retry_update_timer'):
            self.window.retry_update_timer = QTimer(self.window)
            self.window.retry_update_timer.setSingleShot(True)
            self.window.retry_update_timer.timeout.connect(lambda: self.update_projects(force_update=True))
        self.window.retry_update_timer.start(6000)

    def on_project_collapsed(self, item):
        """Track when user manually collapses a project"""
        # Check if this is a project item (top level)
        if self.window.tree.indexOfTopLevelItem(item) != -1:
            # Find the project ID
            for proj_id, proj_item in self.window.project_items.items():
                if proj_item == item:
                    self.manually_collapsed_projects.add(proj_id)
                    break

    def on_project_expanded(self, item):
        """Track when user manually expands a project"""
        # Check if this is a project item (top level)
        if self.window.tree.indexOfTopLevelItem(item) != -1:
            # Find the project ID
            for proj_id, proj_item in self.window.project_items.items():
                if proj_item == item:
                    # Remove from collapsed set when user expands it
                    self.manually_collapsed_projects.discard(proj_id)
                    break
