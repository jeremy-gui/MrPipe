"""
Job management utilities
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QTextCursor

from .workers import JobDataWorker, LogWorker


class JobManager:
    """Manages job selection and log display"""
    
    def __init__(self, main_window):
        self.window = main_window
    
    def on_item_clicked(self, item, column):
        """Handle tree item click"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        
        # Check if gitlab_manager is initialized
        if not self.window.gitlab_manager:
            self.window.log_view.setPlainText("GitLab non configuré. Veuillez configurer l'application dans le menu Settings.")
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

        self.window.log_view.setPlainText("Chargement des logs en cours...")
        self.window.loading_animation.update_display()

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
            return

        proj_id, job_id = self.window.current_job
        job_status = job_data.get('status')
        log_content = job_data.get('trace')

        if job_status == 'manual':
            self.window.current_manual_job = (proj_id, job_id)
            self.window.right_stack.setCurrentIndex(1)
            return

        self.window._loading_active = job_status not in ['success', 'failed', 'canceled', 'skipped']

        print(f"Statut du job: {job_status}")
        print(f"Taille des logs: {len(log_content) if log_content else 0} caractères")

        if log_content:
            self.window.log_display.update_log_display(log_content)
            if self.window._loading_active:
                self.window.loading_timer.start(500)
            if self.window._loading_active:
                print("Démarrage du suivi en temps réel...")
                self.window.log_worker = LogWorker(self.window.gitlab_manager, proj_id, job_id)
                self.window.log_worker.log_ready.connect(self.window.log_display.update_log_display)
                self.window.log_worker.error_occurred.connect(lambda msg: self.window.log_view.setPlainText(msg))
                self.window.log_worker.job_finished.connect(self.on_job_finished)
                self.window.log_worker.start()
            else:
                print("Le job est terminé, pas de suivi en temps réel nécessaire")

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
                    if status == 'success' and current_status == 'running' and window.hipster_pipe_enabled:
                        print(f"Hipster Pipe triggered! Job {worker.job_id} went from {current_status} to {status}")
                        window.hipster_animation.show_animation()
