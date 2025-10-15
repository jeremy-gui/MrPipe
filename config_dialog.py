from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QDialogButtonBox, QListWidget, QListWidgetItem, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import json


class ConfigDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Configuration")
        layout = QVBoxLayout(self)

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

        # Sync button
        sync_button = QPushButton("Sync Projects")
        self.sync_button = sync_button
        sync_button.clicked.connect(self._sync_projects)
        layout.addWidget(sync_button)

        # Projects list
        projects_label = QLabel("Select projects to monitor (max 10):")
        layout.addWidget(projects_label)

        # Search field
        search_label = QLabel("Search projects:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter by name or ID...")
        self.search_edit.textChanged.connect(self._filter_projects)
        layout.addWidget(search_label)
        layout.addWidget(self.search_edit)

        self.projects_list = QListWidget()
        self.projects_list.itemChanged.connect(self._limit_selection)
        layout.addWidget(self.projects_list)

        # Load saved projects
        saved_projects = set(int(p.strip()) for p in current_projects.split(',') if p.strip())

        # Load cached available projects
        cached_projects = self.config.get('GitLab', 'available_projects', fallback=None)
        if cached_projects:
            try:
                available = json.loads(cached_projects)
                self.projects_list.clear()
                for p in available:
                    item = QListWidgetItem(f"{p['name']} (ID: {p['id']})")
                    item.setData(Qt.ItemDataRole.UserRole, p['id'])
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    if p['id'] in saved_projects:
                        item.setCheckState(Qt.CheckState.Checked)
                    else:
                        item.setCheckState(Qt.CheckState.Unchecked)
                    self.projects_list.addItem(item)
            except Exception as e:
                print(f"Error loading cached projects: {e}")

        # Auto-sync removed to prevent freezing

        # Option UI - layout horizontal pour aligner le texte et la checkbox
        auto_select_layout = QHBoxLayout()
        auto_select_label = QLabel("Automatically select updated popped projects:")
        self.auto_select_checkbox = QCheckBox()
        auto_select_checkbox_state = self.config.getboolean('UI', 'auto_select_updated', fallback=True)
        self.auto_select_checkbox.setChecked(auto_select_checkbox_state)
        auto_select_layout.addWidget(auto_select_label)
        auto_select_layout.addWidget(self.auto_select_checkbox)
        auto_select_layout.addStretch()  # Pour pousser la checkbox à droite du texte
        layout.addLayout(auto_select_layout)

        # Option Hipster Pipe
        hipster_layout = QHBoxLayout()
        hipster_label = QLabel("Hipster Pipe (celebration animation on success):")
        self.hipster_checkbox = QCheckBox()
        hipster_checkbox_state = self.config.getboolean('UI', 'hipster_pipe_enabled', fallback=False)
        self.hipster_checkbox.setChecked(hipster_checkbox_state)
        hipster_layout.addWidget(hipster_label)
        hipster_layout.addWidget(self.hipster_checkbox)
        hipster_layout.addStretch()
        layout.addLayout(hipster_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _sync_projects(self):
        if self.sync_worker and self.sync_worker.isRunning():
            return  # Already syncing
        token = self.token_edit.text().strip()
        url = self.url_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Warning", "Enter token first")
            return
        # Update UI
        self.sync_button.setText("Syncing...")
        self.sync_button.setEnabled(False)
        # Use worker for sync
        saved_projects = set(int(p.strip()) for p in self.config.get('GitLab', 'projects', fallback='').split(',') if p.strip())
        from workers import ProjectSyncWorker
        self.sync_worker = ProjectSyncWorker(url, token)
        print("Starting sync worker")
        self.sync_worker.sync_done.connect(lambda projects: self._on_sync_done(projects, saved_projects))
        self.sync_worker.sync_error.connect(lambda error: self._on_sync_error(error))
        self.sync_worker.start()

    def _on_sync_done(self, projects, saved_projects):
        print(f"Sync done, got {len(projects)} projects")
        # Cache the projects
        if not self.config.has_section('GitLab'):
            self.config.add_section('GitLab')
        self.config['GitLab']['available_projects'] = json.dumps([{'name': p.name, 'id': p.id} for p in projects])
        with open(self.parent().config_file, 'w') as f:
            self.config.write(f)
        self.projects_list.clear()
        for proj in projects:
            item = QListWidgetItem(f"{proj.name} (ID: {proj.id})")
            item.setData(Qt.ItemDataRole.UserRole, proj.id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if proj.id in saved_projects:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            self.projects_list.addItem(item)
        self.sync_worker = None
        # Restore UI
        self.sync_button.setText("Sync Projects")
        self.sync_button.setEnabled(True)

    def _on_sync_error(self, error):
        print(f"Sync error: {error}")
        QMessageBox.warning(self, "Sync Error", f"Failed to sync projects: {error}")
        self.sync_worker = None
        # Restore UI
        self.sync_button.setText("Sync Projects")
        self.sync_button.setEnabled(True)

    def _filter_projects(self, text):
        text = text.lower()
        for i in range(self.projects_list.count()):
            item = self.projects_list.item(i)
            visible = text in item.text().lower()
            item.setHidden(not visible)

    def _limit_selection(self, item):
        checked_count = 0
        for i in range(self.projects_list.count()):
            if self.projects_list.item(i).checkState() == Qt.CheckState.Checked:
                checked_count += 1
        if checked_count > 10:
            item.setCheckState(Qt.CheckState.Unchecked)
            QMessageBox.information(self, "Limit", "Maximum 10 projects can be selected")

    def get_selected_projects(self):
        selected_projects = []
        for i in range(self.projects_list.count()):
            item = self.projects_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_projects.append(item.data(Qt.ItemDataRole.UserRole))
        return selected_projects

    def get_auto_select_updated(self):
        return self.auto_select_checkbox.isChecked()

    def get_hipster_pipe_enabled(self):
        return self.hipster_checkbox.isChecked()
