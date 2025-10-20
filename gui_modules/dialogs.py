"""
Dialog windows for configuration and about
"""

import json
import configparser
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QDialogButtonBox,
    QCheckBox, QMessageBox, QTextEdit, QWidget, QSpinBox, QRadioButton, QButtonGroup
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from .workers import ProjectSyncWorker
from .styles import get_dialog_stylesheet, get_license_text_stylesheet


class ConfigDialog(QDialog):
    """Configuration dialog for GitLab settings"""

    def __init__(self, parent, config, config_file):
        super().__init__(parent)
        self.parent_window = parent
        self.config = config
        self.config_file = config_file
        self.sync_worker = None
        
        self.setWindowTitle("Configuration")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Récupérer les valeurs actuelles
        current_url = self.config.get('GitLab', 'url', fallback='https://gitlab.com')
        current_token = self.config.get('GitLab', 'token', fallback='')
        current_projects = self.config.get('GitLab', 'projects', fallback='')

        # URL
        url_label = QLabel("GitLab URL:")
        self.url_edit = QLineEdit(current_url)
        layout.addWidget(url_label)
        layout.addWidget(self.url_edit)

        # Token
        token_label = QLabel("Private Token:")
        self.token_edit = QLineEdit(current_token)
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(token_label)
        layout.addWidget(self.token_edit)

        # Sync button
        self.sync_button = QPushButton("Sync Projects")
        self.sync_button.clicked.connect(self._sync_projects)
        layout.addWidget(self.sync_button)

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

        # Auto-select option
        auto_select_layout = QHBoxLayout()
        auto_select_label = QLabel("Automatically select updated popped projects:")
        self.auto_select_checkbox = QCheckBox()
        self.auto_select_checkbox.setChecked(
            self.parent_window.auto_select_updated if hasattr(self.parent_window, 'auto_select_updated') else True
        )
        auto_select_layout.addWidget(auto_select_label)
        auto_select_layout.addWidget(self.auto_select_checkbox)
        auto_select_layout.addStretch()
        layout.addLayout(auto_select_layout)

        # Hipster Pipe option
        hipster_layout = QHBoxLayout()
        hipster_label = QLabel("Hipster Pipe:")
        hipster_layout.addWidget(hipster_label)
        
        # Radio buttons for Hipster Pipe mode
        self.hipster_button_group = QButtonGroup()
        self.hipster_no_radio = QRadioButton("No")
        self.hipster_yes_radio = QRadioButton("Yes")
        self.hipster_yes_sound_radio = QRadioButton("Yes with sound")
        
        self.hipster_button_group.addButton(self.hipster_no_radio, 0)
        self.hipster_button_group.addButton(self.hipster_yes_radio, 1)
        self.hipster_button_group.addButton(self.hipster_yes_sound_radio, 2)
        
        # Set current value
        current_mode = self.parent_window.hipster_pipe_mode if hasattr(self.parent_window, 'hipster_pipe_mode') else 0
        if current_mode == 0:
            self.hipster_no_radio.setChecked(True)
        elif current_mode == 1:
            self.hipster_yes_radio.setChecked(True)
        else:
            self.hipster_yes_sound_radio.setChecked(True)
        
        hipster_layout.addWidget(self.hipster_no_radio)
        hipster_layout.addWidget(self.hipster_yes_radio)
        hipster_layout.addWidget(self.hipster_yes_sound_radio)
        hipster_layout.addStretch()
        layout.addLayout(hipster_layout)

        # Log font size option
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("Taille du texte des logs:")
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setMinimum(8)
        self.font_size_spinbox.setMaximum(32)
        self.font_size_spinbox.setSuffix(" pt")
        self.font_size_spinbox.setValue(
            self.parent_window.log_font_size if hasattr(self.parent_window, 'log_font_size') else 16
        )
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_spinbox)
        font_size_layout.addStretch()
        layout.addLayout(font_size_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _sync_projects(self):
        if self.sync_worker and self.sync_worker.isRunning():
            return
        token = self.token_edit.text().strip()
        url = self.url_edit.text().strip()
        if not token:
            QMessageBox.warning(self, "Warning", "Enter token first")
            return
        
        self.sync_button.setText("Syncing...")
        self.sync_button.setEnabled(False)
        
        saved_projects = set(int(p.strip()) for p in self.config.get('GitLab', 'projects', fallback='').split(',') if p.strip())
        self.sync_worker = ProjectSyncWorker(url, token)
        self.sync_worker.sync_done.connect(lambda projects: self._on_sync_done(projects, saved_projects))
        self.sync_worker.sync_error.connect(self._on_sync_error)
        self.sync_worker.start()

    def _on_sync_done(self, projects, saved_projects):
        # Cache the projects
        if not self.config.has_section('GitLab'):
            self.config.add_section('GitLab')
        self.config['GitLab']['available_projects'] = json.dumps([{'name': p.name, 'id': p.id} for p in projects])
        with open(self.config_file, 'w') as f:
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
        self.sync_button.setText("Sync Projects")
        self.sync_button.setEnabled(True)

    def _on_sync_error(self, error):
        QMessageBox.warning(self, "Sync Error", f"Failed to sync projects: {error}")
        self.sync_worker = None
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
        """Retourne la liste des projets sélectionnés"""
        selected_projects = []
        for i in range(self.projects_list.count()):
            item = self.projects_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_projects.append(item.data(Qt.ItemDataRole.UserRole))
        return selected_projects

    def get_url(self):
        return self.url_edit.text().strip()

    def get_token(self):
        return self.token_edit.text().strip()

    def get_auto_select_updated(self):
        return self.auto_select_checkbox.isChecked()

    def get_hipster_pipe_mode(self):
        """Returns 0 for No, 1 for Yes, 2 for Yes with sound"""
        return self.hipster_button_group.checkedId()

    def get_log_font_size(self):
        return self.font_size_spinbox.value()
    
    def closeEvent(self, event):
        """Clean up sync worker before closing"""
        if self.sync_worker and self.sync_worker.isRunning():
            self.sync_worker.stop()
            self.sync_worker.wait(500)
            if self.sync_worker.isRunning():
                self.sync_worker.terminate()
                self.sync_worker.wait()
            self.sync_worker = None
        event.accept()


class AboutDialog(QDialog):
    """About dialog showing application information"""

    def __init__(self, parent, get_resource_path_func):
        super().__init__(parent)
        self.get_resource_path = get_resource_path_func
        self.setWindowTitle("À propos de Mr. Pipe")
        self.setFixedSize(600, 400)
        self.media_player = None
        self.audio_output = None
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)

        # Left side: text information
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(10)

        # Author
        author_label = QLabel("Auteur:")
        author_label.setStyleSheet("font-weight: bold; color: white;")
        author_value = QLabel("Jérémy Couderc Guillaume")
        author_value.setStyleSheet("color: white;")
        left_layout.addWidget(author_label)
        left_layout.addWidget(author_value)

        # Email
        email_label = QLabel("Email:")
        email_label.setStyleSheet("font-weight: bold; color: white;")
        email_value = QLabel("jeremy.guillau@gmail.com")
        email_value.setStyleSheet("color: white;")
        left_layout.addWidget(email_label)
        left_layout.addWidget(email_value)

        # License (clickable)
        license_label = QLabel("Licence:")
        license_label.setStyleSheet("font-weight: bold; color: white;")
        license_value = QLabel('<a href="#" style="color: #4a90d9;">MIT</a>')
        license_value.setStyleSheet("color: #4a90d9;")
        license_value.setOpenExternalLinks(False)
        license_value.linkActivated.connect(self.show_license)
        left_layout.addWidget(license_label)
        left_layout.addWidget(license_value)

        # Version
        version_label = QLabel("Version:")
        version_label.setStyleSheet("font-weight: bold; color: white;")
        version_value = QLabel("v1.1.0")
        version_value.setStyleSheet("color: white;")
        left_layout.addWidget(version_label)
        left_layout.addWidget(version_value)

        left_layout.addStretch()

        # Right side: video
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Create video widget
        video_widget = QVideoWidget()
        video_widget.setFixedSize(252, 252)
        right_layout.addWidget(video_widget)

        # Create media player
        self.audio_output = QAudioOutput()
        self.audio_output.setMuted(True)  # Mute the video
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(video_widget)
        
        # Load and play video
        video_path = self.get_resource_path("assets/about.mp4")
        self.media_player.setSource(QUrl.fromLocalFile(video_path))
        self.media_player.setLoops(QMediaPlayer.Loops.Infinite)  # Loop indefinitely
        self.media_player.play()

        layout.addWidget(left_widget)
        layout.addWidget(right_widget)

        self.setStyleSheet(get_dialog_stylesheet())

    def show_license(self):
        """Affiche la licence MIT dans une nouvelle fenêtre"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Licence MIT")
        dialog.setFixedSize(500, 400)
        layout = QVBoxLayout(dialog)

        license_text = QTextEdit()
        license_text.setPlainText("""MIT License

Copyright (c) 2024 Jérémy Couderc Guillaume

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""")
        license_text.setReadOnly(True)
        license_text.setStyleSheet(get_license_text_stylesheet())
        layout.addWidget(license_text)

        dialog.exec()
