"""
Project management utilities
"""

from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QTimer

from .workers import HttpWorker, JobStatusWorker
from .styles import TREE_FONT_SIZE_PROJECT, TREE_FONT_SIZE_PIPELINE


class ProjectManager:
    """Manages project display and updates"""
    
    def __init__(self, main_window):
        self.window = main_window
    
    def update_projects(self, force_update=False):
        """Update all projects in the tree"""
        if not self.window.gitlab_manager:
            return

        if not self.window.project_items:
            self.window.tree.clear()

        for proj_id in self.window.projects:
            if proj_id in self.window.project_workers and not force_update:
                if self.window.project_workers[proj_id].isRunning():
                    continue

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
                        worker.wait()
                    except:
                        pass

            worker = HttpWorker(self.fetch_project_data, proj_id)
            worker.finished.connect(lambda data, pid=proj_id: self.on_project_data_loaded(data, pid))
            worker.error.connect(lambda error, pid=proj_id: self.on_project_error(error, pid))
            worker.start()

            self.window.project_workers[proj_id] = worker

        # Remove projects no longer selected
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
                    worker.wait()
                del self.window.project_workers[proj_id]
            keys_to_remove = [k for k in self.window.job_status_workers if k[0] == proj_id]
            for k in keys_to_remove:
                worker = self.window.job_status_workers[k]
                if worker.isRunning():
                    worker.stop()
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

        for pipeline_info in pipelines_data:
            pipeline = pipeline_info['pipeline']
            jobs = pipeline_info['jobs']

            if not jobs:
                continue

            if pipeline.id in existing_pipeline_ids:
                for i in range(proj_item.childCount()):
                    child = proj_item.child(i)
                    if child.text(0).startswith(f"Pipeline {pipeline.id}"):
                        current_text = child.text(0)
                        expected_text = f"Pipeline {pipeline.id} - {pipeline.status}"
                        if current_text != expected_text:
                            child.setText(0, expected_text)
                            self.update_pipeline_jobs(child, jobs, proj_id)

                            font = child.font(0)
                            font.setBold(True)
                            font.setPointSize(TREE_FONT_SIZE_PIPELINE)
                            child.setFont(0, font)
                            child.setForeground(0, QColor('white'))
                        break
            else:
                pipeline_item = QTreeWidgetItem(proj_item, [f"Pipeline {pipeline.id} - {pipeline.status}"])

                font = pipeline_item.font(0)
                font.setBold(True)
                font.setPointSize(TREE_FONT_SIZE_PIPELINE)
                pipeline_item.setFont(0, font)
                pipeline_item.setForeground(0, QColor('white'))

                for job in jobs:
                    job_item = QTreeWidgetItem(pipeline_item, [f"{job.name} - {job.status}"])
                    job_item.setData(0, Qt.ItemDataRole.UserRole, (proj_id, job.id))

                    # Import job_manager to set color
                    from .job_manager import JobColorManager
                    JobColorManager.set_job_color(self.window, job_item, job.status)

                    key = (proj_id, job.id)
                    if key not in self.window.job_status_workers:
                        worker = JobStatusWorker(self.window.gitlab_manager, proj_id, job.id, job_item, key)
                        worker.status_updated.connect(self.window._on_job_status_updated)
                        worker.finished_signal.connect(self.window._on_job_status_worker_finished)
                        worker.start()
                        self.window.job_status_workers[key] = worker

                pipeline_item.setExpanded(True)

                if jobs:
                    first_job_item = pipeline_item.child(0)
                    self.window.tree.setCurrentItem(first_job_item)
                    self.window.on_item_clicked(first_job_item, 0)

        if not proj_item.isExpanded():
            proj_item.setExpanded(True)

    def update_pipeline_jobs(self, pipeline_item, jobs, proj_id):
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
                        break
            else:
                job_item = QTreeWidgetItem(pipeline_item, [f"{job.name} - {job.status}"])
                job_item.setData(0, Qt.ItemDataRole.UserRole, (proj_id, job.id))

                from .job_manager import JobColorManager
                JobColorManager.set_job_color(self.window, job_item, job.status)

                key = (proj_id, job.id)
                if key not in self.window.job_status_workers:
                    worker = JobStatusWorker(self.window.gitlab_manager, proj_id, job.id, job_item, key)
                    worker.status_updated.connect(self.window._on_job_status_updated)
                    worker.finished_signal.connect(self.window._on_job_status_worker_finished)
                    worker.start()
                    self.window.job_status_workers[key] = worker

    def on_project_error(self, error, proj_id):
        """Called on project loading error"""
        if proj_id in self.window.project_items:
            self.window.project_items[proj_id].setText(0, f"Erreur: {error}")
        QTimer.singleShot(60000, lambda: self.update_projects(force_update=True))
