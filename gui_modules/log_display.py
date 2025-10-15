"""
Log display utilities
"""

from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor

from .log_formatter import LogFormatter
from .styles import LOG_FONT_SIZE


class LogDisplay:
    """Manages log display and formatting"""
    
    def __init__(self, main_window):
        self.window = main_window
    
    def update_log_display(self, log_content):
        """Update the log display with new content"""
        # Avoid flickering by only updating if content changed
        if log_content == self.window.last_log_content:
            return
        self.window.last_log_content = log_content

        # Check if we can append incrementally
        current_plain = self.window.log_view.toPlainText()
        loading_suffix = '\n' + self.window._loading_text if self.window._loading_active else ''
        if current_plain.endswith(loading_suffix):
            current_plain = current_plain[:-len(loading_suffix)]

        if log_content.startswith(current_plain) and current_plain:
            # Append the new part incrementally
            new_part = log_content[len(current_plain):]
            cursor = self.window.log_view.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            # Remove loading if present
            document = self.window.log_view.document()
            last_block = document.lastBlock()
            if last_block.text() in ['·', '··', '···']:
                cursor.setPosition(last_block.position())
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
                if cursor.position() > 0:
                    cursor.setPosition(cursor.position() - 1)
                    if self.window.log_view.toPlainText()[cursor.position()] == '\n':
                        cursor.deleteChar()

            cursor.movePosition(QTextCursor.MoveOperation.End)

            # Process and append new part
            cleaned_new_part = LogFormatter.clean_ansi_codes(new_part)
            current_font = self.window.log_view.font()
            font_size = current_font.pointSize()
            LogFormatter.process_ansi_codes(cleaned_new_part, cursor, font_size)

            # Scroll to bottom
            scrollbar = self.window.log_view.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            self.window._update_loading_display()
        else:
            # Full update
            self.window.log_view.clear()

            # Set font and size for content
            current_font = self.window.log_view.font()
            current_font.setPointSize(LOG_FONT_SIZE)
            self.window.log_view.setFont(current_font)

            # Create cursor at document start
            cursor = self.window.log_view.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)

            # Apply default format with larger font
            default_format = QTextCharFormat()
            default_format.setForeground(QColor("white"))
            default_format.setFontPointSize(LOG_FONT_SIZE)
            cursor.setCharFormat(default_format)

            # Clean ANSI codes
            cleaned_content = LogFormatter.clean_ansi_codes(log_content)

            # Process content with ANSI codes
            LogFormatter.process_ansi_codes(cleaned_content, cursor, LOG_FONT_SIZE)

            # Scroll to bottom
            scrollbar = self.window.log_view.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            self.window._update_loading_display()
