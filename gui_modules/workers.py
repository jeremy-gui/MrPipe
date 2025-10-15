"""
Worker threads for asynchronous operations
"""

from PyQt6.QtCore import QThread, pyqtSignal


class HttpWorker(QThread):
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


class ProjectSyncWorker(QThread):
    """Worker for synchronizing project list"""
    sync_done = pyqtSignal(list)
    sync_error = pyqtSignal(str)

    def __init__(self, url, token):
        super().__init__()
        self.url = url
        self.token = token
        self._is_running = True

    def run(self):
        if not self._is_running:
            return
        try:
            print(f"Syncing projects for {self.url}")
            from gitlab_manager import GitLabManager
            manager = GitLabManager(self.url, self.token)
            projects = manager.get_all_projects()
            print(f"Synced {len(projects)} projects")
            if self._is_running:
                self.sync_done.emit(projects)
        except Exception as e:
            print(f"Sync error: {e}")
            if self._is_running:
                self.sync_error.emit(str(e))

    def stop(self):
        self._is_running = False


class LaunchWorker(QThread):
    """Worker for launching manual jobs"""
    launch_done = pyqtSignal()
    launch_error = pyqtSignal(str)

    def __init__(self, gitlab_manager, proj_id, job_id):
        super().__init__()
        self.gitlab_manager = gitlab_manager
        self.proj_id = proj_id
        self.job_id = job_id
        self._is_running = True

    def run(self):
        if not self._is_running:
            return
        try:
            project = self.gitlab_manager.get_project(self.proj_id)
            job = project.jobs.get(self.job_id)
            job.play()
            if self._is_running:
                self.launch_done.emit()
        except Exception as e:
            if self._is_running:
                self.launch_error.emit(str(e))

    def stop(self):
        self._is_running = False


class LogWorker(QThread):
    """Worker spécifique pour la récupération des logs"""
    log_ready = pyqtSignal(str)
    job_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, gitlab_manager, project_id, job_id):
        super().__init__()
        self.gitlab_manager = gitlab_manager
        self.project_id = project_id
        self.job_id = job_id
        self._is_running = True
        self._job_status = None
        self.logs_loaded = False

    def run(self):
        logs_loaded = False

        while self._is_running:
            if not self._is_running:
                return

            status = self._get_job_status(self.project_id, self.job_id)
            if status is None:
                self._is_running = False
                return

            if not logs_loaded or self._job_status not in ['success', 'failed', 'canceled', 'skipped']:
                try:
                    trace = self.gitlab_manager.get_job_trace(self.project_id, self.job_id)
                    self._on_log_received(trace)
                    logs_loaded = True
                except Exception as e:
                    self.error_occurred.emit(str(e))
                    logs_loaded = True

            if self._job_status in ['success', 'failed', 'canceled', 'skipped']:
                self.job_finished.emit()
                self._is_running = False
                break

            self.msleep(1000)

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
            return None

    def get_job_status(self):
        return self._job_status


class JobStatusWorker(QThread):
    """Worker pour surveiller le statut d'un job spécifique"""
    status_updated = pyqtSignal(str)
    finished_signal = pyqtSignal(tuple)

    def __init__(self, gitlab_manager, proj_id, job_id, job_item, key):
        super().__init__()
        self.gitlab_manager = gitlab_manager
        self.proj_id = proj_id
        self.job_id = job_id
        self.job_item = job_item
        self.key = key
        self._is_running = True

    def run(self):
        while self._is_running:
            try:
                project = self.gitlab_manager.get_project(self.proj_id)
                job = project.jobs.get(self.job_id)
                status = job.status
                self.status_updated.emit(status)

                if status in ['success', 'failed', 'canceled', 'skipped']:
                    self._is_running = False
                    self.finished_signal.emit(self.key)
                    break
            except Exception as e:
                print(f"Erreur mise à jour statut job {self.job_id}: {e}")
                self._is_running = False
                self.finished_signal.emit(self.key)
                break

            self.msleep(2000)

    def stop(self):
        self._is_running = False


class JobDataWorker(QThread):
    """Worker for fetching job data (status and logs)"""
    data_ready = pyqtSignal(dict)

    def __init__(self, gitlab_manager, proj_id, job_id):
        super().__init__()
        self.gitlab_manager = gitlab_manager
        self.proj_id = proj_id
        self.job_id = job_id
        self._is_running = True

    def run(self):
        if not self._is_running:
            return
        try:
            project = self.gitlab_manager.get_project(self.proj_id)
            job = project.jobs.get(self.job_id)
            status = job.status

            try:
                trace = job.trace().decode('utf-8')
                data = {'status': status, 'trace': trace}
            except Exception as e:
                print(f"Erreur lors de la récupération des logs: {e}")
                data = {'status': status, 'trace': None}

            if self._is_running:
                self.data_ready.emit(data)
        except Exception as e:
            print(f"Erreur lors de la récupération des données du job: {e}")
            if self._is_running:
                self.data_ready.emit(None)

    def stop(self):
        self._is_running = False
