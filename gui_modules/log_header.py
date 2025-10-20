"""
Log header widget displaying job/pipeline information
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from .styles import (HEADER_PROJECT_FONT_SIZE, HEADER_JOB_FONT_SIZE, 
                     HEADER_STATUS_FONT_SIZE, HEADER_ENV_FONT_SIZE, 
                     HEADER_DATE_FONT_SIZE)


class LogHeader(QWidget):
    """Header widget showing job/pipeline information"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the header UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        
        # Left side container for project/job info
        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Project name label (plus gros)
        self.project_label = QLabel("")
        self.project_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-weight: bold;
                font-size: {HEADER_PROJECT_FONT_SIZE}pt;
            }}
        """)
        
        # Job name label (plus gros)
        self.job_label = QLabel("")
        self.job_label.setStyleSheet(f"""
            QLabel {{
                color: #eceff1;
                font-weight: bold;
                font-size: {HEADER_JOB_FONT_SIZE}pt;
            }}
        """)
        
        # Environment pill (à droite du job)
        self.env_pill = QLabel("")
        self.env_pill.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                color: #99e5ff;
                border: 1px solid #99e5ff;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: {HEADER_ENV_FONT_SIZE}pt;
                font-weight: bold;
            }}
        """)
        self.env_pill.hide()
        
        # Status label (pill)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-weight: bold;
                font-size: {HEADER_STATUS_FONT_SIZE}pt;
                padding: 2px 8px;
                border-radius: 3px;
            }}
        """)
        
        left_layout.addWidget(self.project_label)
        left_layout.addWidget(self.job_label)
        left_layout.addWidget(self.env_pill)
        left_layout.addWidget(self.status_label)
        left_layout.addStretch()
        
        # Right side container for date/duration
        right_container = QWidget()
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        # Date label (plus gros, aligné à gauche)
        self.date_label = QLabel("")
        self.date_label.setStyleSheet(f"""
            QLabel {{
                color: #99e5ff;
                font-size: {HEADER_DATE_FONT_SIZE}pt;
            }}
        """)
        
        # Duration label (plus gros, aligné à gauche)
        self.duration_label = QLabel("")
        self.duration_label.setStyleSheet(f"""
            QLabel {{
                color: #99e5ff;
                font-size: {HEADER_DATE_FONT_SIZE}pt;
            }}
        """)
        
        right_layout.addWidget(self.date_label)
        right_layout.addWidget(self.duration_label)
        
        # Add containers to main layout
        layout.addWidget(left_container)
        layout.addStretch()
        layout.addWidget(right_container)
        
        # Set background
        self.setStyleSheet("""
            LogHeader {
                background-color: #455a64;
                border-bottom: 2px solid #0f3460;
            }
        """)
        
    def update_info(self, project_name="", env_name="", job_name="", status="", 
                    date="", duration="", is_pipeline=False):
        """Update header information"""
        # Project name
        if project_name:
            self.project_label.setText(project_name)
            self.project_label.show()
        else:
            self.project_label.hide()
        
        # Environment pill (sans crochets ASCII)
        if env_name:
            self.env_pill.setText(env_name)
            self.env_pill.show()
        else:
            self.env_pill.hide()
        
        # Job name
        if job_name and not is_pipeline:
            self.job_label.setText(f"• {job_name}")
            self.job_label.show()
        else:
            self.job_label.hide()
        
        # Status with color
        if status:
            status_colors = {
                'success': '#4caf50',
                'failed': '#f44336',
                'running': '#2196f3',
                'pending': '#ff9800',
                'canceled': '#9e9e9e',
                'skipped': '#607d8b',
                'manual': '#9c27b0'
            }
            bg_color = status_colors.get(status.lower(), '#607d8b')
            self.status_label.setText(status.upper())
            self.status_label.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    font-weight: bold;
                    font-size: {HEADER_STATUS_FONT_SIZE}pt;
                    padding: 2px 8px;
                    border-radius: 3px;
                    background-color: {bg_color};
                }}
            """)
            self.status_label.show()
        else:
            self.status_label.hide()
        
        # Date (alignée à gauche, plus grosse)
        if date:
            self.date_label.setText(date)
            self.date_label.show()
        else:
            self.date_label.hide()
        
        # Duration (alignée à gauche, plus grosse)
        if duration:
            self.duration_label.setText(f"⏱ {duration}")
            self.duration_label.show()
        else:
            self.duration_label.hide()
    
    def clear(self):
        """Clear all information"""
        self.update_info()
