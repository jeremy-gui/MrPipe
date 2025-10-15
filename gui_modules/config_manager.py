"""
Configuration management utilities
"""

import os
import configparser
from PyQt6.QtCore import QTimer


class ConfigManager:
    """Handles configuration loading, saving, and geometry management"""
    
    def __init__(self, main_window):
        self.window = main_window
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.window.config_file):
            self.window.config.read(self.window.config_file)
            if 'GitLab' in self.window.config:
                config = self.window.config['GitLab']
                url = config.get('url', 'https://gitlab.com')
                token = config.get('token', '')
                projects = config.get('projects', '')

                if token and projects:
                    try:
                        from gitlab_manager import GitLabManager
                        self.window.projects = [int(p.strip()) for p in projects.split(',') if p.strip()]
                        self.window.gitlab_manager = GitLabManager(url, token)
                        self.window.log_view.setPlainText("Chargement des projets...")
                        self.window.update_projects()
                    except Exception as e:
                        self.window.log_view.setPlainText(f"Erreur lors du chargement de la configuration : {str(e)}")
                else:
                    self.window.log_view.setPlainText("Veuillez configurer l'URL GitLab et le token dans les paramètres.")

            if 'UI' in self.window.config:
                self.window.auto_select_updated = self.window.config.getboolean('UI', 'auto_select_updated', fallback=True)
                self.window.hipster_pipe_enabled = self.window.config.getboolean('UI', 'hipster_pipe_enabled', fallback=False)

                splitter_sizes = self.window.config.get('UI', 'splitter_sizes', fallback=None)
                QTimer.singleShot(100, lambda: self.restore_splitter_sizes(splitter_sizes))

                geometry_b64 = self.window.config.get('UI', 'window_geometry', fallback=None)
                if geometry_b64:
                    try:
                        import base64
                        from PyQt6.QtCore import QByteArray
                        geometry_data = base64.b64decode(geometry_b64)
                        geometry = QByteArray(geometry_data)
                        self.window.restoreGeometry(geometry)
                    except Exception as e:
                        print(f"Erreur lors de la restauration de la géométrie: {e}")
        else:
            self.window.log_view.setPlainText("Bienvenue ! Veuillez configurer l'application dans le menu Paramètres.")

    def save_config(self, url, token, projects):
        """Save configuration to file"""
        if not self.window.config.has_section('GitLab'):
            self.window.config.add_section('GitLab')

        self.window.config['GitLab']['url'] = url
        self.window.config['GitLab']['token'] = token
        self.window.config['GitLab']['projects'] = ','.join(str(p) for p in projects)

        if not self.window.config.has_section('UI'):
            self.window.config.add_section('UI')
        self.window.config.set('UI', 'auto_select_updated', str(self.window.auto_select_updated))
        self.window.config.set('UI', 'hipster_pipe_enabled', str(self.window.hipster_pipe_enabled))

        splitter_sizes = self.window.splitter.sizes()
        if splitter_sizes:
            self.window.config.set('UI', 'splitter_sizes', ','.join(str(size) for size in splitter_sizes))

        geometry = self.window.saveGeometry()
        if geometry:
            import base64
            geometry_b64 = base64.b64encode(geometry.data()).decode('ascii')
            self.window.config.set('UI', 'window_geometry', geometry_b64)

        with open(self.window.config_file, 'w') as f:
            self.window.config.write(f)

    def restore_splitter_sizes(self, splitter_sizes_str):
        """Restore splitter proportions from configuration"""
        if splitter_sizes_str:
            try:
                sizes = [int(s.strip()) for s in splitter_sizes_str.split(',')]
                if len(sizes) >= 2:
                    if sizes[0] < 200:
                        sizes[0] = 200
                    if sizes[1] < 400:
                        sizes[1] = 400
                    self.window.splitter.setSizes(sizes)
            except (ValueError, IndexError) as e:
                print(f"Erreur lors de la restauration des proportions du splitter: {e}")

    def auto_save_geometry(self):
        """Auto-save geometry and splitter proportions"""
        try:
            if not self.window.config.has_section('UI'):
                self.window.config.add_section('UI')

            splitter_sizes = self.window.splitter.sizes()
            if splitter_sizes:
                self.window.config.set('UI', 'splitter_sizes', ','.join(str(size) for size in splitter_sizes))

            geometry = self.window.saveGeometry()
            if geometry:
                import base64
                geometry_b64 = base64.b64encode(geometry.data()).decode('ascii')
                self.window.config.set('UI', 'window_geometry', geometry_b64)

            with open(self.window.config_file, 'w') as f:
                self.window.config.write(f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde automatique: {e}")
