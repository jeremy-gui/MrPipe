from PyQt6.QtWidgets import QTreeWidgetItem, QMessageBox
from PyQt6.QtGui import QColor, QFont, QTextCursor
from PyQt6.QtCore import QTimer, Qt
from workers import HttpWorker, JobDataWorker, LogWorker, JobStatusWorker


class ProjectManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.log_processor = None

    def set_log_processor(self, log_processor):
        self.log_processor = log_processor

    def update_projects(self, force_update=False):
        # Ne rien faire si l'application est en cours de fermeture
        if self.main_window._closing:
            return

        if not self.main_window.gitlab_manager:
            return

        # Si c'est le premier chargement, on nettoie tout
        if not self.main_window.project_items:
            self.main_window.tree.clear()

        for proj_id in self.main_window.projects:
            # Si le projet existe déjà et qu'on ne force pas la mise à jour
            if proj_id in self.main_window.project_workers and not force_update:
                # Vérifier si le worker est toujours en cours d'exécution
                if self.main_window.project_workers[proj_id].isRunning():
                    continue

            # Créer un nouvel item si nécessaire
            if proj_id not in self.main_window.project_items:
                proj_item = QTreeWidgetItem(self.main_window.tree, [f"Chargement... (ID: {proj_id})"])
                self.main_window.project_items[proj_id] = proj_item
            else:
                proj_item = self.main_window.project_items[proj_id]

            # Arrêter le worker existant s'il y en a un
            if proj_id in self.main_window.project_workers:
                worker = self.main_window.project_workers[proj_id]
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

            self.main_window.project_workers[proj_id] = worker

        # Remove projects no longer selected
        to_remove = []
        for proj_id, item in self.main_window.project_items.items():
            if proj_id not in self.main_window.projects:
                self.main_window.tree.takeTopLevelItem(self.main_window.tree.indexOfTopLevelItem(item))
                to_remove.append(proj_id)

        for proj_id in to_remove:
            del self.main_window.project_items[proj_id]
            if proj_id in self.main_window.project_workers:
                worker = self.main_window.project_workers[proj_id]
                if worker.isRunning():
                    worker.stop()
                    worker.wait()
                del self.main_window.project_workers[proj_id]
            # Remove job workers for this project
            keys_to_remove = [k for k in self.main_window.job_status_workers if k[0] == proj_id]
            for k in keys_to_remove:
                worker = self.main_window.job_status_workers[k]
                if worker.isRunning():
                    worker.stop()
                    worker.wait()
                del self.main_window.job_status_workers[k]

    def _fetch_project_data(self, proj_id):
        """Fonction exécutée dans un thread pour récupérer les données du projet"""
        proj = self.main_window.gitlab_manager.get_project(proj_id)
        pipelines = self.main_window.gitlab_manager.get_latest_pipeline(proj_id)
        pipeline_data = []
        for pipeline in pipelines:
            jobs = self.main_window.gitlab_manager.get_pipeline_jobs(proj_id, pipeline.id)
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
        if proj_id not in self.main_window.project_items:
            return

        # Vérifier si le worker est toujours valide
        if proj_id not in self.main_window.project_workers:
            return

        proj_item = self.main_window.project_items[proj_id]
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

            # Vérifier si ce pipeline est déjà affichée
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
                    if key not in self.main_window.job_status_workers:
                        worker = JobStatusWorker(self.main_window.gitlab_manager, proj_id, job.id, job_item, key)
                        worker.status_updated.connect(self._on_job_status_updated)
                        worker.finished_signal.connect(self._on_job_status_worker_finished)
                        worker.start()
                        self.main_window.job_status_workers[key] = worker

                # Développer le pipeline
                pipeline_item.setExpanded(True)

                # Sélectionner automatiquement le premier job de la nouvelle pipeline pour afficher ses logs
                if jobs:
                    first_job_item = pipeline_item.child(0)
                    self.main_window.tree.setCurrentItem(first_job_item)
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
                if key not in self.main_window.job_status_workers:
                    worker = JobStatusWorker(self.main_window.gitlab_manager, proj_id, job.id, job_item, key)
                    worker.status_updated.connect(self._on_job_status_updated)
                    worker.finished_signal.connect(self._on_job_status_worker_finished)
                    worker.start()
                    self.main_window.job_status_workers[key] = worker

    def _on_project_error(self, error, proj_id):
        """Appelé en cas d'erreur lors du chargement d'un projet"""
        # Ne rien faire si l'application est en cours de fermeture
        if self.main_window._closing:
            return

        if proj_id in self.main_window.project_items:
            self.main_window.project_items[proj_id].setText(0, f"Erreur: {error}")

        # Réessayer après une minute en cas d'erreur
        QTimer.singleShot(60000, lambda: self.update_projects(force_update=True))

    def on_item_clicked(self, item, column):
        # Ne rien faire si l'application est en cours de fermeture
        if self.main_window._closing:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        # Reset to log view
        self.main_window.right_stack.setCurrentIndex(0)
        self.main_window.current_manual_job = None

        # Arrêter le worker précédent s'il existe
        if self.main_window.log_worker:
            self.main_window.log_worker.stop()
            self.main_window.log_worker.wait()
            self.main_window.log_worker = None

        if self.main_window.job_data_worker:
            self.main_window.job_data_worker.stop()
            self.main_window.job_data_worker.wait()
            self.main_window.job_data_worker = None

        proj_id, job_id = data
        self.main_window.current_job = (proj_id, job_id)

        # Afficher un message de chargement
        self.main_window.log_view.setPlainText("Chargement des logs en cours...")
        self.log_processor._update_loading_display()

        # Use worker to fetch job data
        self.main_window.job_data_worker = JobDataWorker(self.main_window.gitlab_manager, proj_id, job_id)
        self.main_window.job_data_worker.data_ready.connect(self._on_job_data_received)
        self.main_window.job_data_worker.start()

    def _on_job_data_received(self, job_data):
        """Called when job data (status and logs) is received"""
        # Nettoyer le worker
        if self.main_window.job_data_worker:
            self.main_window.job_data_worker.stop()
            self.main_window.job_data_worker.wait()
            self.main_window.job_data_worker = None

        if job_data is None:
            self.show_error("Impossible de récupérer les données du job")
            return

        proj_id, job_id = self.main_window.current_job
        job_status = job_data.get('status')
        # Récupérer les logs de manière plus robuste
        log_content = job_data.get('trace', '')
        if not log_content and job_status:
            try:
                # Essayer de récupérer les logs directement si non présents
                log_content = self.main_window.gitlab_manager.get_job_trace(proj_id, job_id)
            except Exception as e:
                log_content = f"Erreur lors de la récupération des logs: {e}"

        # Mise à jour de l'interface utilisateur
        if log_content:
            self.log_processor.update_log_display(log_content)
        else:
            # Afficher un message si pas de logs disponibles
            self.log_processor.update_log_display("Aucun log disponible pour ce job")

        if job_status == 'manual':
            self.main_window.current_manual_job = (proj_id, job_id)
            self.main_window.right_stack.setCurrentIndex(1)  # Afficher le widget de lancement
            return

        # Mettre à jour l'état de chargement en fonction du statut du job
        is_job_running = job_status not in ['success', 'failed', 'canceled', 'skipped']
        self.log_processor._loading_active = is_job_running

        print(f"Statut du job: {job_status}")
        print(f"Taille des logs: {len(log_content) if log_content else 0} caractères")

        # Mettre à jour l'affichage des logs
        if log_content:
            self.log_processor.update_log_display(log_content)
            
            # Démarrer le timer de chargement si le job est en cours
            if is_job_running:
                self.main_window.loading_timer.start(500)
            else:
                # Afficher un message si pas de logs disponibles
                self.log_processor.update_log_display("Aucun log disponible pour ce job")
            # Si le job est en cours, démarrer le suivi en temps réel
            if self.log_processor._loading_active:
                print("Démarrage du suivi en temps réel...")
                self.main_window.log_worker = LogWorker(self.main_window.gitlab_manager, proj_id, job_id)
                self.main_window.log_worker.log_ready.connect(self.log_processor.update_log_display)
                self.main_window.log_worker.error_occurred.connect(self.show_error)
                self.main_window.log_worker.job_finished.connect(self._on_job_finished)
                self.main_window.log_worker.start()
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
                    cursor = self.main_window.log_view.textCursor()
                    cursor.movePosition(QTextCursor.MoveOperation.End)
                    cursor.insertText('\n\n' + '='*80 + '\n')
                    cursor.insertText(status_messages[job_status] + '\n')
        else:
            # Si pas de logs initiaux, afficher un message selon le statut
            if job_status in ['success', 'failed', 'canceled', 'skipped']:
                self.show_error("Aucun log disponible pour ce job terminé")
            else:
                self.main_window.log_view.setPlainText("Logs en cours de chargement...")
                self.log_processor._update_loading_display()
                if self.log_processor._loading_active:
                    self.main_window.loading_timer.start(500)
                # Démarrer le suivi en temps réel même sans logs initiaux
                print("Démarrage du suivi en temps réel...")
                self.main_window.log_worker = LogWorker(self.main_window.gitlab_manager, proj_id, job_id)
                self.main_window.log_worker.log_ready.connect(self.log_processor.update_log_display)
                self.main_window.log_worker.error_occurred.connect(self.show_error)
                self.main_window.log_worker.job_finished.connect(self._on_job_finished)
                self.main_window.log_worker.start()

    def _on_job_finished(self):
        """Appelé quand un job est terminé (succès, échec, etc.)"""
        if self.main_window.log_worker:
            status = self.main_window.log_worker.get_job_status()
            if status:
                status_messages = {
                    'success': '✅ Le job s\'est terminé avec succès',
                    'failed': '❌ Le job a échoué',
                    'canceled': '⏹️ Le job a été annulé',
                    'skipped': '⏭️ Le job a été ignoré'
                }
                message = status_messages.get(status, f'Le job est terminé (statut: {status})')

                # Ajouter un message à la fin des logs
                cursor = self.main_window.log_view.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertText('\n\n' + '='*80 + '\n')
                cursor.insertText(message + '\n')
                self.log_processor._loading_active = False
                self.log_processor._update_loading_display()
                self.main_window.loading_timer.stop()
                # Arrêter le worker car le job est terminé
                self.main_window.log_worker.stop()
                self.main_window.log_worker.wait()

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
            if job_id_tuple in self.main_window.job_animations:
                timer, state = self.main_window.job_animations[job_id_tuple]
                timer.stop()
                timer.deleteLater()
                del self.main_window.job_animations[job_id_tuple]

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
                    current = self.main_window.job_animations[job_id_tuple][1]
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
                    self.main_window.job_animations[job_id_tuple] = (timer, next_state)
                timer = QTimer(self.main_window)
                timer.setInterval(250)  # 250 ms pour un clignotement plus perceptible
                timer.timeout.connect(toggle_color)
                # Initialiser avec la première couleur
                job_item.setForeground(0, color1)
                job_item.setBackground(0, bg1)
                font = job_item.font(0)
                font.setBold(True)
                job_item.setFont(0, font)
                self.main_window.job_animations[job_id_tuple] = (timer, 0)
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

    def _on_job_status_updated(self, status, worker):
        """Appelé quand le statut d'un job est mis à jour"""
        # Ne rien faire si l'application est en cours de fermeture
        if self.main_window._closing:
            return

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
                        self.main_window.tree.setCurrentItem(worker.job_item)
                        self.on_item_clicked(worker.job_item, 0)

                    # Hipster Pipe : célébration quand un job passe de running à success
                    if status == 'success' and current_status == 'running' and self.main_window.hipster_pipe_enabled:
                        print(f"Hipster Pipe triggered! Job {worker.job_id} went from {current_status} to {status}")
                        self.main_window._show_hipster_pipe_animation()

    def _on_job_status_worker_finished(self, key):
        """Called when a JobStatusWorker finishes"""
        if key in self.main_window.job_status_workers:
            del self.main_window.job_status_workers[key]

    def show_error(self, error_message):
        self.main_window.log_view.setPlainText(error_message)
