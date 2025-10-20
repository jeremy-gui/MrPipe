"""
UI helper utilities
"""

import os
import sys
import random
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget


class UIHelpers:
    """Helper functions for UI operations"""
    
    @staticmethod
    def get_resource_path(relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)


class HipsterPipeAnimation:
    """Manages the Hipster Pipe celebration animation"""
    
    def __init__(self, main_window):
        self.window = main_window
        self.audio_output = None
    
    def show_animation(self, video_type='success'):
        """Display the Hipster Pipe video
        
        Args:
            video_type: 'success' for success videos, 'fail' for fail video
        """
        print(f"show_animation called. hipster_pipe_mode: {self.window.hipster_pipe_mode}, video_type: {video_type}")
        
        # Check if Hipster Pipe is enabled (mode > 0), except for 'etonne' which plays on activation
        if self.window.hipster_pipe_mode == 0 and video_type != 'etonne':
            print("Hipster Pipe disabled, skipping animation")
            return
            
        if hasattr(self.window, 'hipster_video_widget') and self.window.hipster_video_widget:
            print("Animation already in progress, skipping")
            return

        # Select video based on type
        if video_type == 'success':
            # Randomly select one of the success videos
            success_videos = ['success-1.mp4', 'success-2.mp4', 'success-3.mp4']
            video_file = random.choice(success_videos)
        elif video_type == 'fail':
            video_file = 'fail.mp4'
        elif video_type == 'etonne':
            video_file = 'etonne.mp4'
        else:
            print(f"Unknown video type: {video_type}")
            return
        
        video_path = UIHelpers.get_resource_path(f"assets/{video_file}")
        if not os.path.exists(video_path):
            print(f"Vidéo {video_path} non trouvée, pas d'animation Hipster Pipe")
            return

        print(f"Starting Hipster Pipe animation with video: {video_path}")

        self.window.hipster_video_widget = QVideoWidget(self.window.right_stack)
        self.window.hipster_video_widget.setGeometry(50, 50, 500, 300)
        self.window.hipster_video_widget.raise_()

        # Setup audio output
        self.audio_output = QAudioOutput()
        # Mute if mode is 1 (Yes without sound), unmute if mode is 2 (Yes with sound)
        self.audio_output.setMuted(self.window.hipster_pipe_mode == 1)
        
        self.window.hipster_media_player = QMediaPlayer()
        self.window.hipster_media_player.setAudioOutput(self.audio_output)
        self.window.hipster_media_player.setVideoOutput(self.window.hipster_video_widget)
        self.window.hipster_media_player.setSource(QUrl.fromLocalFile(video_path))

        self.window.hipster_media_player.mediaStatusChanged.connect(self.on_video_finished)

        self.window.hipster_video_widget.show()
        self.window.hipster_media_player.play()
        print("Hipster Pipe video started playing")

    def on_video_finished(self, status):
        """Called when the Hipster Pipe video finishes"""
        from PyQt6.QtMultimedia import QMediaPlayer

        print(f"Hipster Pipe video status changed: {status}")
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("Hipster Pipe video finished, cleaning up")
            if hasattr(self.window, 'hipster_media_player') and self.window.hipster_media_player:
                self.window.hipster_media_player.stop()
                self.window.hipster_media_player.deleteLater()
                self.window.hipster_media_player = None

            if hasattr(self.window, 'hipster_video_widget') and self.window.hipster_video_widget:
                self.window.hipster_video_widget.hide()
                self.window.hipster_video_widget.deleteLater()
                self.window.hipster_video_widget = None
            
            if self.audio_output:
                self.audio_output.deleteLater()
                self.audio_output = None


class LoadingAnimation:
    """Manages the loading dots animation"""
    
    def __init__(self, main_window):
        self.window = main_window
    
    def animate_dots(self):
        """Animate the loading dots"""
        states = ["·", "··", "···"]
        self.window._loading_state = (self.window._loading_state + 1) % len(states)
        self.window._loading_text = states[self.window._loading_state]
        self.update_display()

    def update_display(self):
        """Update the loading display in the log view"""
        from PyQt6.QtGui import QTextCursor
        
        cursor = self.window.log_view.textCursor()
        document = self.window.log_view.document()

        block = document.lastBlock()
        while block.isValid():
            text = block.text().strip()
            if text in ['·', '··', '···']:
                block_start = block.position()
                block_end = block_start + len(block.text())

                edit_cursor = self.window.log_view.textCursor()
                edit_cursor.setPosition(block_start)
                edit_cursor.setPosition(block_end, QTextCursor.MoveMode.KeepAnchor)
                edit_cursor.removeSelectedText()

                if hasattr(self.window, '_loading_active') and self.window._loading_active and hasattr(self.window, '_loading_text'):
                    edit_cursor.insertText(self.window._loading_text)

                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.window.log_view.setTextCursor(cursor)
                return

            block = block.previous()

        cursor.movePosition(QTextCursor.MoveOperation.End)
        if hasattr(self.window, '_loading_active') and self.window._loading_active and hasattr(self.window, '_loading_text'):
            cursor.insertText(self.window._loading_text)
        self.window.log_view.setTextCursor(cursor)
