"""
Log formatting utilities for ANSI codes and text processing
"""

import re
from PyQt6.QtGui import QTextCharFormat, QColor


class LogFormatter:
    """Handles ANSI code processing and log formatting"""

    @staticmethod
    def clean_ansi_codes(text):
        """Nettoie le texte des séquences de contrôle inutiles tout en préservant les couleurs"""
        control_sequences = [
            r'\x1b\[\d*[JK]',
            r'\x1b\[\d*;*\d*[Hf]',
            r'\x1b\[\d*[ABCD]',
            r'\x1b\[\?\d*[hl]',
            r'\x1b\[\d*[ST]',
            r'\x1b\[\?1[hl]',
            r'\x1b\[\?25[hl]',
            r'\x1b\[2J',
            r'\x1b\[K',
            r'\x1b\[\?7[hl]',
            r'\x1b\[\?1h\=7h',
            r'\x1b\[\?1l\>',
            r'\x1b\[\?\d*[hl]',
        ]

        for pattern in control_sequences:
            text = re.sub(pattern, '', text)

        text = re.sub(r'\x1b\[(?![\d;]*m)[^a-zA-Z]', '', text)
        text = re.sub(r'\x1b\[(?![\d;]*m)[\d;]*[a-zA-Z]', '', text)

        return text

    @staticmethod
    def get_ansi_styles():
        """Retourne le dictionnaire des styles ANSI"""
        return {
            '0': lambda f: f,
            '1': lambda f: f.setFontWeight(75),
            '3': lambda f: f.setFontItalic(True),
            '4': lambda f: f.setFontUnderline(True),
            '30': lambda f: f.setForeground(QColor('black')),
            '31': lambda f: f.setForeground(QColor(255, 85, 85)),
            '32': lambda f: f.setForeground(QColor(85, 255, 85)),
            '33': lambda f: f.setForeground(QColor(255, 255, 85)),
            '34': lambda f: f.setForeground(QColor(85, 85, 255)),
            '35': lambda f: f.setForeground(QColor(255, 85, 255)),
            '36': lambda f: f.setForeground(QColor(85, 255, 255)),
            '37': lambda f: f.setForeground(QColor('white')),
            '90': lambda f: f.setForeground(QColor(127, 127, 127)),
            '91': lambda f: f.setForeground(QColor(255, 85, 85)),
            '92': lambda f: f.setForeground(QColor(85, 255, 85)),
            '93': lambda f: f.setForeground(QColor(255, 255, 85)),
            '94': lambda f: f.setForeground(QColor(85, 85, 255)),
            '95': lambda f: f.setForeground(QColor(255, 85, 255)),
            '96': lambda f: f.setForeground(QColor(85, 255, 255)),
            '97': lambda f: f.setForeground(QColor('white')),
            '40': lambda f: f.setBackground(QColor('black')),
            '41': lambda f: f.setBackground(QColor('darkRed')),
            '42': lambda f: f.setBackground(QColor('darkGreen')),
            '43': lambda f: f.setBackground(QColor('darkYellow')),
            '44': lambda f: f.setBackground(QColor('darkBlue')),
            '45': lambda f: f.setBackground(QColor('darkMagenta')),
            '46': lambda f: f.setBackground(QColor('darkCyan')),
            '47': lambda f: f.setBackground(QColor('lightGray')),
        }

    @staticmethod
    def process_ansi_codes(text, cursor, font_size):
        """Traite les codes ANSI et les convertit en format de texte Qt"""
        ansi_escape = re.compile(r'(\x1b\[[0-9;]*m)')
        ansi_styles = LogFormatter.get_ansi_styles()

        default_format = QTextCharFormat()
        default_format.setForeground(QColor('white'))
        default_format.setFontPointSize(font_size)
        current_format = QTextCharFormat(default_format)

        segments = ansi_escape.split(text)

        for segment in segments:
            if not segment:
                continue

            if segment.startswith('\x1b[') and segment.endswith('m'):
                codes = segment[2:-1].split(';')

                for code in codes:
                    if not code:
                        current_format = QTextCharFormat(default_format)
                    elif code in ansi_styles:
                        ansi_styles[code](current_format)
                    elif code.startswith('38;5;') and len(code.split(';')) == 3:
                        pass
                    else:
                        current_format = QTextCharFormat(default_format)

                cursor.setCharFormat(current_format)
            else:
                cursor.insertText(segment, current_format)
