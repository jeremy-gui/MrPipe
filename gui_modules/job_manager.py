"""
Job management utilities
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QTextCursor, QIcon
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton

from .workers import JobDataWorker, LogWorker


class JobManager:
    """Manages job selection and log display"""
    
    def __init__(self, main_window):
        self.window = main_window
    
    def create_job_buttons(self, proj_id, job_id, job_status):
        """Create action buttons widget for a job (retry, cancel)"""
        container = QWidget()
        container.setFixedWidth(50)  # Largeur fixe pour 2 boutons
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        from .ui_helpers import UIHelpers
        
        # Retry button
        retry_button = QPushButton()
        retry_button.setFixedSize(20, 20)
        retry_icon_path = UIHelpers.get_resource_path("assets/start.svg")
        retry_button.setIcon(QIcon(retry_icon_path))
        retry_button.setIconSize(retry_button.size())
        retry_button.setCursor(Qt.CursorShape.PointingHandCursor)
        retry_button.setStyleSheet("""
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
        retry_button.setToolTip("Relancer le job")
        retry_button.clicked.connect(lambda: self.retry_job(proj_id, job_id))
        layout.addWidget(retry_button)
        
        # Cancel button - show if job is running or pending
        if job_status in ['running', 'pending']:
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
            cancel_button.setToolTip("Annuler le job")
            cancel_button.clicked.connect(lambda: self.cancel_job(proj_id, job_id))
            layout.addWidget(cancel_button)
        
        return container
    
    def retry_job(self, proj_id, job_id):
        """Retry a job"""
        try:
            project = self.window.gitlab_manager.get_project(proj_id)
            job = project.jobs.get(job_id)
            
            # Retry returns a dict, not a job object
            new_job_data = job.retry()
            
            # Get the new job ID from the dict
            if isinstance(new_job_data, dict):
                new_job_id = new_job_data.get('id', job_id)
            else:
                new_job_id = new_job_data.id
            
            print(f"Job {job_id} relancé, nouveau job: {new_job_id}")
            
            # Show success message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self.window, "Job relancé", f"Le job a été relancé avec succès.")
            
            # Store the new job ID to select it after refresh
            self.window.pending_selection = ('job', proj_id, new_job_id)
            
            # Refresh will happen automatically
        except Exception as e:
            error_msg = str(e)
            print(f"Erreur lors du relancement du job: {error_msg}")
            # Show error message to user
            from PyQt6.QtWidgets import QMessageBox
            if "403" in error_msg or "Forbidden" in error_msg or "not retryable" in error_msg:
                QMessageBox.warning(self.window, "Job non relançable", 
                                   "Ce job ne peut pas être relancé.\n\n"
                                   "Raisons possibles:\n"
                                   "- Le job est déjà en cours d'exécution\n"
                                   "- Le job est manuel et n'a pas encore été démarré\n"
                                   "- Le job n'est pas dans un état permettant le relancement")
            else:
                QMessageBox.critical(self.window, "Erreur", f"Erreur lors du relancement du job:\n{error_msg}")
    
    def cancel_job(self, proj_id, job_id):
        """Cancel a job"""
        try:
            project = self.window.gitlab_manager.get_project(proj_id)
            job = project.jobs.get(job_id)
            job.cancel()
            print(f"Job {job_id} annulé")
            # Show success message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self.window, "Job annulé", f"Le job a été annulé avec succès.")
            # Refresh will happen automatically
        except Exception as e:
            error_msg = str(e)
            print(f"Erreur lors de l'annulation du job: {error_msg}")
            # Show error message to user
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self.window, "Erreur", f"Erreur lors de l'annulation du job:\n{error_msg}")
    
    def _update_header_for_job(self, proj_id, job_id, job_status):
        """Update the log header with job information"""
        try:
            # Get project info
            project = self.window.gitlab_manager.get_project(proj_id)
            project_name = project.name
            
            # Get job info
            job = project.jobs.get(job_id)
            job_name = job.name
            
            # Get environment (ref)
            env_name = ""
            if hasattr(job, 'ref') and job.ref:
                env_name = job.ref
            
            # Get date
            date = ""
            if hasattr(job, 'created_at') and job.created_at:
                from gui_modules.project_manager import format_timestamp
                date = format_timestamp(job.created_at)
            
            # Get duration
            duration = ""
            if hasattr(job, 'duration') and job.duration:
                duration = self._format_duration(job.duration)
            
            # Update header
            self.window.log_header.update_info(
                project_name=project_name,
                env_name=env_name,
                job_name=job_name,
                status=job_status,
                date=date,
                duration=duration,
                is_pipeline=False
            )
        except Exception as e:
            print(f"Error updating header: {e}")
            self.window.log_header.clear()
    
    def _format_duration(self, seconds):
        """Format duration in seconds to human readable format"""
        if seconds is None:
            return ""
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def _handle_project_click(self, item):
        """Handle click on a project item"""
        # Clear logs and show project info in header
        self.window.log_view.setPlainText("")
        
        # Parse project name from item text
        item_text = item.text(0)
        # Format is: "Project Name (ID: 12345)"
        if " (ID: " in item_text:
            project_name = item_text.split(" (ID: ")[0]
        else:
            project_name = item_text
        
        # Update header with project info only
        self.window.log_header.update_info(
            project_name=project_name,
            env_name="",
            job_name="",
            status="",
            date="",
            duration="",
            is_pipeline=False
        )
    
    def _handle_pipeline_click(self, item, pipeline_id):
        """Handle click on a pipeline item"""
        # Clear logs and show pipeline info in header
        self.window.log_view.setPlainText("")
        
        # Get project info from parent
        parent = item.parent()
        if parent:
            parent_text = parent.text(0)
            if " (ID: " in parent_text:
                project_name = parent_text.split(" (ID: ")[0]
            else:
                project_name = parent_text
        else:
            project_name = ""
        
        # Parse pipeline info from item text
        item_text = item.text(0)
        # Format can be: "Pipeline 123 • status • time" or "[env]Pipeline 123 • status • time"
        
        # Extract environment if present
        env_name = ""
        if item_text.startswith("[") and "]" in item_text:
            env_name = item_text[1:item_text.index("]")]
            item_text = item_text[item_text.index("]")+1:]
        
        # Extract status and time
        parts = item_text.split(" • ")
        pipeline_info = parts[0] if parts else item_text  # "Pipeline 123"
        status = parts[1] if len(parts) > 1 else ""
        date = parts[2] if len(parts) > 2 else ""
        
        # Update header with pipeline info
        self.window.log_header.update_info(
            project_name=project_name,
            env_name=env_name,
            job_name="",
            status=status,
            date=date,
            duration="",
            is_pipeline=True
        )
    
    def on_item_clicked(self, item, column):
        """Handle tree item click"""
        # Check if gitlab_manager is initialized
        if not self.window.gitlab_manager:
            self.window.log_view.setPlainText("GitLab non configuré. Veuillez configurer l'application dans le menu Settings.")
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Check if this is a pipeline item (has pipeline_id in UserRole + 1)
        pipeline_id = item.data(0, Qt.ItemDataRole.UserRole + 1)
        
        # If no job data but has pipeline_id, it's a pipeline
        if not data and pipeline_id:
            self._handle_pipeline_click(item, pipeline_id)
            return
        
        # If no data at all, it's a project
        if not data:
            self._handle_project_click(item)
            return

        self.window.right_stack.setCurrentIndex(0)
        self.window.current_manual_job = None

        if self.window.log_worker:
            self.window.log_worker.stop()
            if self.window.log_worker.isRunning():
                self.window.log_worker.wait(500)
                if self.window.log_worker.isRunning():
                    self.window.log_worker.terminate()
                    self.window.log_worker.wait()
            self.window.log_worker = None

        if self.window.job_data_worker:
            self.window.job_data_worker.stop()
            if self.window.job_data_worker.isRunning():
                self.window.job_data_worker.wait(500)
                if self.window.job_data_worker.isRunning():
                    self.window.job_data_worker.terminate()
                    self.window.job_data_worker.wait()
            self.window.job_data_worker = None

        proj_id, job_id = data
        self.window.current_job = (proj_id, job_id)

        # Réinitialiser le contenu des logs pour forcer la mise à jour
        self.window.last_log_content = ""
        self.window.log_view.setPlainText("Chargement des logs en cours...")
        self.window.loading_animation.update_display()
        
        # Update header immediately with available info from tree item
        try:
            project = self.window.gitlab_manager.get_project(proj_id)
            project_name = project.name
            
            # Parse job info from tree item text
            item_text = item.text(0)
            # Format is: "job_name - status"
            if " - " in item_text:
                job_name, job_status = item_text.rsplit(" - ", 1)
            else:
                job_name = item_text
                job_status = "unknown"
            
            # Update header with basic info immediately
            self.window.log_header.update_info(
                project_name=project_name,
                env_name="",  # Will be updated when data loads
                job_name=job_name,
                status=job_status,
                date="",  # Will be updated when data loads
                duration="",  # Will be updated when data loads
                is_pipeline=False
            )
        except Exception as e:
            print(f"Error updating header immediately: {e}")

        try:
            self.window.job_data_worker = JobDataWorker(self.window.gitlab_manager, proj_id, job_id)
            self.window.job_data_worker.data_ready.connect(self.on_job_data_received)
            self.window.job_data_worker.start()
        except Exception as e:
            self.window.log_view.setPlainText(f"Erreur lors du chargement du job: {str(e)}")

    def on_job_data_received(self, job_data):
        """Called when job data (status and logs) is received"""
        if self.window.job_data_worker:
            self.window.job_data_worker.stop()
            if self.window.job_data_worker.isRunning():
                self.window.job_data_worker.wait(500)
                if self.window.job_data_worker.isRunning():
                    self.window.job_data_worker.terminate()
                    self.window.job_data_worker.wait()
            self.window.job_data_worker = None

        if job_data is None:
            self.window.log_view.setPlainText("Impossible de récupérer les données du job")
            self.window.log_header.clear()
            return

        proj_id, job_id = self.window.current_job
        job_status = job_data.get('status')
        log_content = job_data.get('trace')
        
        # Update header with job information
        self._update_header_for_job(proj_id, job_id, job_status)

        if job_status == 'manual':
            self.window.current_manual_job = (proj_id, job_id)
            self.window.right_stack.setCurrentIndex(1)
            return

        self.window._loading_active = job_status not in ['success', 'failed', 'canceled', 'skipped']

        print(f"Statut du job: {job_status}")
        print(f"Taille des logs: {len(log_content) if log_content else 0} caractères")

        if log_content:
            # Afficher les logs
            self.window.log_display.update_log_display(log_content)
            
            if self.window._loading_active:
                # Job en cours - démarrer le suivi en temps réel
                self.window.loading_timer.start(500)
                print("Démarrage du suivi en temps réel...")
                self.window.log_worker = LogWorker(self.window.gitlab_manager, proj_id, job_id)
                self.window.log_worker.log_ready.connect(self.window.log_display.update_log_display)
                self.window.log_worker.error_occurred.connect(lambda msg: self.window.log_view.setPlainText(msg))
                self.window.log_worker.job_finished.connect(self.on_job_finished)
                self.window.log_worker.start()
            else:
                # Job terminé - ajouter le message de statut
                print("Le job est terminé, pas de suivi en temps réel nécessaire")
                # Arrêter l'animation de chargement
                self.window.loading_timer.stop()
                self.window.loading_animation.update_display()

                status_messages = {
                    'success': '✅ Le job s\'est terminé avec succès',
                    'failed': '❌ Le job a échoué',
                    'canceled': '⏹️ Le job a été annulé',
                    'skipped': '⏭️ Le job a été ignoré'
                }

                if job_status in status_messages:
                    cursor = self.window.log_view.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    cursor.insertText('\n\n' + '='*80 + '\n')
                    cursor.insertText(status_messages[job_status] + '\n')
        else:
            if job_status in ['success', 'failed', 'canceled', 'skipped']:
                self.window.log_view.setPlainText("Aucun log disponible pour ce job terminé")
                # Arrêter l'animation de chargement
                self.window.loading_timer.stop()
                self.window.loading_animation.update_display()
            else:
                self.window.log_view.setPlainText("Logs en cours de chargement...")
                self.window.loading_animation.update_display()
                if self.window._loading_active:
                    self.window.loading_timer.start(500)
                print("Démarrage du suivi en temps réel...")
                self.window.log_worker = LogWorker(self.window.gitlab_manager, proj_id, job_id)
                self.window.log_worker.log_ready.connect(self.window.log_display.update_log_display)
                self.window.log_worker.error_occurred.connect(lambda msg: self.window.log_view.setPlainText(msg))
                self.window.log_worker.job_finished.connect(self.on_job_finished)
                self.window.log_worker.start()

    def on_job_finished(self):
        """Called when a job is finished (success, failure, etc.)"""
        if self.window.log_worker:
            status = self.window.log_worker.get_job_status()
            if status:
                status_messages = {
                    'success': '✅ Le job s\'est terminé avec succès',
                    'failed': '❌ Le job a échoué',
                    'canceled': '⏹️ Le job a été annulé',
                    'skipped': '⏭️ Le job a été ignoré'
                }
                message = status_messages.get(status, f'Le job est terminé (statut: {status})')

                cursor = self.window.log_view.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertText('\n\n' + '='*80 + '\n')
                cursor.insertText(message + '\n')
                self.window._loading_active = False
                self.window.loading_timer.stop()
                self.window.loading_animation.update_display()
                self.window.log_worker.stop()
                if self.window.log_worker.isRunning():
                    self.window.log_worker.wait(500)
                    if self.window.log_worker.isRunning():
                        self.window.log_worker.terminate()
                        self.window.log_worker.wait()


class JobColorManager:
    """Manages job item colors and animations"""
    
    @staticmethod
    def set_job_color(window, job_item, status):
        """Set job item color (and animation) based on status"""
        job_id_tuple = None
        data = job_item.data(0, Qt.ItemDataRole.UserRole)
        if data and isinstance(data, tuple) and len(data) == 2:
            job_id_tuple = (data[0], data[1])

        # Stop and remove animation if status is no longer "running"
        if job_id_tuple is not None:
            if job_id_tuple in window.job_animations:
                timer, state = window.job_animations[job_id_tuple]
                timer.stop()
                timer.deleteLater()
                del window.job_animations[job_id_tuple]

        if status == 'success':
            color = QColor(100, 255, 100)
            job_item.setForeground(0, color)
            job_item.setBackground(0, QColor(0, 0, 0, 0))
            font = job_item.font(0)
            font.setBold(False)
            job_item.setFont(0, font)
        elif status == 'running':
            if job_id_tuple is not None:
                color1 = QColor(100, 150, 255)
                color2 = QColor(30, 80, 200)
                bg1 = QColor(230, 240, 255)
                bg2 = QColor(200, 220, 245)
                
                def toggle_color():
                    current = window.job_animations[job_id_tuple][1]
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
                    window.job_animations[job_id_tuple] = (timer, next_state)
                
                timer = QTimer(window)
                timer.setInterval(250)
                timer.timeout.connect(toggle_color)
                job_item.setForeground(0, color1)
                job_item.setBackground(0, bg1)
                font = job_item.font(0)
                font.setBold(True)
                job_item.setFont(0, font)
                window.job_animations[job_id_tuple] = (timer, 0)
                timer.start()
            else:
                color = QColor(100, 150, 255)
                job_item.setForeground(0, color)
                job_item.setBackground(0, QColor(230, 240, 255))
                font = job_item.font(0)
                font.setBold(True)
                job_item.setFont(0, font)
        elif status == 'failed':
            color = QColor(255, 100, 100)
            job_item.setForeground(0, color)
            job_item.setBackground(0, QColor(0, 0, 0, 0))
            font = job_item.font(0)
            font.setBold(False)
            job_item.setFont(0, font)
        else:
            color = QColor('white')
            job_item.setForeground(0, color)
            job_item.setBackground(0, QColor(0, 0, 0, 0))
            font = job_item.font(0)
            font.setBold(False)
            job_item.setFont(0, font)

    @staticmethod
    def on_job_status_updated(window, status):
        """Called when job status is updated"""
        worker = window.sender()
        if worker and hasattr(worker, 'job_item'):
            current_text = worker.job_item.text(0)
            if ' - ' in current_text:
                parts = current_text.split(' - ')
                name = parts[0]
                current_status = parts[1] if len(parts) > 1 else ''
                new_text = f"{name} - {status}"
                if current_text != new_text:
                    worker.job_item.setText(0, new_text)
                    JobColorManager.set_job_color(window, worker.job_item, status)
                    if status in ['running', 'failed'] and current_status != status:
                        window.tree.setCurrentItem(worker.job_item)
                        window.job_manager.on_item_clicked(worker.job_item, 0)

                    # Hipster Pipe: celebration when job goes from running to success
                    # Only trigger if this is the currently selected job
                    if status == 'success' and current_status == 'running' and window.hipster_pipe_enabled:
                        # Check if this is the currently selected job
                        current_item = window.tree.currentItem()
                        if current_item == worker.job_item:
                            print(f"Hipster Pipe triggered! Job {worker.job_id} went from {current_status} to {status}")
                            window.hipster_animation.show_animation()
                        else:
                            print(f"Hipster Pipe skipped: Job {worker.job_id} succeeded but is not currently selected")
