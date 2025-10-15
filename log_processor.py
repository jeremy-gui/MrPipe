from PyQt6.QtGui import QTextCharFormat, QColor, QTextCursor
from PyQt6.QtWidgets import QTextEdit


class LogProcessor:
    def __init__(self, log_view):
        self.log_view = log_view
        self.last_log_content = ""
        self._loading_state = 0
        self._loading_text = "·"
        self._loading_active = False

    def _animate_loading_dots(self):
        states = ["·", "··", "···"]
        self._loading_state = (self._loading_state + 1) % len(states)
        self._loading_text = states[self._loading_state]
        self._update_loading_display()

    def _update_loading_display(self):
        # Utiliser QTextCursor pour modifier seulement les points de chargement sans casser le formatage
        cursor = self.log_view.textCursor()
        document = self.log_view.document()

        # Chercher le dernier bloc qui contient seulement des points de chargement
        block = document.lastBlock()
        while block.isValid():
            text = block.text().strip()
            if text in ['·', '··', '···']:
                # Trouver ce bloc et le remplacer
                block_start = block.position()
                block_end = block_start + len(block.text())

                # Créer un nouveau curseur pour la modification
                edit_cursor = self.log_view.textCursor()
                edit_cursor.setPosition(block_start)
                edit_cursor.setPosition(block_end, QTextCursor.MoveMode.KeepAnchor)
                edit_cursor.removeSelectedText()

                # Insérer les nouveaux points
                if hasattr(self, '_loading_active') and self._loading_active and hasattr(self, '_loading_text'):
                    edit_cursor.insertText(self._loading_text)

                # Repositionner le curseur principal à la fin
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.log_view.setTextCursor(cursor)
                return

            # Passer au bloc précédent
            block = block.previous()

        # Si aucun bloc de points trouvé, ajouter à la fin
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if hasattr(self, '_loading_active') and self._loading_active and hasattr(self, '_loading_text'):
            cursor.insertText(self._loading_text)
        self.log_view.setTextCursor(cursor)

    def update_log_display(self, log_content):
        # Éviter le scintillement en ne mettant à jour que si le contenu a changé
        if log_content == self.last_log_content:
            return
        self.last_log_content = log_content

        # Check if we can append incrementally
        current_plain = self.log_view.toPlainText()
        loading_suffix = '\n' + self._loading_text if self._loading_active else ''
        if current_plain.endswith(loading_suffix):
            current_plain = current_plain[:-len(loading_suffix)]

        if log_content.startswith(current_plain) and current_plain:
            # Append the new part incrementally
            new_part = log_content[len(current_plain):]
            cursor = self.log_view.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            # Remove loading if present
            document = self.log_view.document()
            last_block = document.lastBlock()
            if last_block.text() in ['·', '··', '···']:
                cursor.setPosition(last_block.position())
                cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
                if cursor.position() > 0:
                    cursor.setPosition(cursor.position() - 1)
                    if self.log_view.toPlainText()[cursor.position()] == '\n':
                        cursor.deleteChar()

            cursor.movePosition(QTextCursor.MoveOperation.End)

            # Process and append new part
            cleaned_new_part = self._clean_ansi_codes(new_part)
            self._process_ansi_codes(cleaned_new_part, cursor)

            # Scroll to bottom
            scrollbar = self.log_view.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            self._update_loading_display()
        else:
            # Full update
            self.log_view.clear()

            # Définir la police et la taille pour le contenu
            current_font = self.log_view.font()
            current_font.setPointSize(20)  # Taille de police augmentée pour les logs
            self.log_view.setFont(current_font)

            # Créer un curseur au début du document
            cursor = self.log_view.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)

            # Appliquer le format par défaut avec une police plus grande
            default_format = QTextCharFormat()
            default_format.setForeground(QColor("white"))
            default_format.setFontPointSize(20)  # Taille de police augmentée pour correspondre à l'interface
            cursor.setCharFormat(default_format)

            # Nettoyer le contenu des codes ANSI inutiles
            cleaned_content = self._clean_ansi_codes(log_content)

            # Traiter le contenu avec les codes ANSI
            self._process_ansi_codes(cleaned_content, cursor)

            # Défiler vers le bas pour voir les derniers logs
            scrollbar = self.log_view.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

            self._update_loading_display()

    def _clean_ansi_codes(self, text):
        """Nettoie le texte des séquences de contrôle inutiles tout en préservant les couleurs"""
        import re

        # Liste des séquences de contrôle à supprimer (sauf les couleurs qui se terminent par 'm')
        control_sequences = [
            r'\x1b\[\d*[JK]',  # Effacement d'écran et de lignes
            r'\x1b\[\d*;*\d*[Hf]',  # Positionnement du curseur
            r'\x1b\[\d*[ABCD]',  # Déplacements du curseur
            r'\x1b\[\?\d*[hl]',  # Paramètres d'affichage
            r'\x1b\[\d*[ST]',  # Défilement et tabulation
            r'\x1b\[\?1[hl]',  # Mode curseur
            r'\x1b\[\?25[hl]',  # Curseur visible/invisible
            r'\x1b\[2J',  # Effacer l'écran
            r'\x1b\[K',  # Effacer jusqu'à la fin de la ligne
            r'\x1b\[\?7[hl]',  # Mode retour à la ligne automatique
            r'\x1b\[\?1h\=7h',  # Mode VT100
            r'\x1b\[\?1l\>',  # Désactiver le mode VT100
            r'\x1b\[\?\d*[hl]',  # Codes de configuration d'écran
            # Ne pas inclure les codes de couleur qui se terminent par 'm'
        ]

        # Supprimer les séquences de contrôle une par une
        for pattern in control_sequences:
            text = re.sub(pattern, '', text)

        # Nettoyer les séquences de contrôle orphelines qui ne sont pas des codes de couleur
        text = re.sub(r'\x1b\[(?![\d;]*m)[^a-zA-Z]', '', text)

        # Supprimer les séquences de contrôle résiduelles qui ne sont pas des codes de couleur
        text = re.sub(r'\x1b\[(?![\d;]*m)[\d;]*[a-zA-Z]', '', text)

        return text

    def _process_ansi_codes(self, text, cursor):
        """Traite les codes ANSI et les convertit en format de texte Qt"""
        import re

        # Ne pas nettoyer le texte ici pour conserver les codes couleur

        # Expression régulière pour les codes ANSI
        ansi_escape = re.compile(r'(\x1b\[[0-9;]*m)')

        # Définition des styles ANSI
        ansi_styles = {
            '0': lambda f: f,  # Reset
            '1': lambda f: f.setFontWeight(75),  # Bold
            '3': lambda f: f.setFontItalic(True),  # Italic
            '4': lambda f: f.setFontUnderline(True),  # Underline
            '30': lambda f: f.setForeground(QColor('black')),  # Black
            '31': lambda f: f.setForeground(QColor(255, 85, 85)),  # Red (plus visible sur fond sombre)
            '32': lambda f: f.setForeground(QColor(85, 255, 85)),  # Green
            '33': lambda f: f.setForeground(QColor(255, 255, 85)),  # Yellow
            '34': lambda f: f.setForeground(QColor(85, 85, 255)),  # Blue
            '35': lambda f: f.setForeground(QColor(255, 85, 255)),  # Magenta
            '36': lambda f: f.setForeground(QColor(85, 255, 255)),  # Cyan
            '37': lambda f: f.setForeground(QColor('white')),  # White
            '90': lambda f: f.setForeground(QColor(127, 127, 127)),  # Bright Black (gray)
            '91': lambda f: f.setForeground(QColor(255, 85, 85)),  # Bright Red
            '92': lambda f: f.setForeground(QColor(85, 255, 85)),  # Bright Green
            '93': lambda f: f.setForeground(QColor(255, 255, 85)),  # Bright Yellow
            '94': lambda f: f.setForeground(QColor(85, 85, 255)),  # Bright Blue
            '95': lambda f: f.setForeground(QColor(255, 85, 255)),  # Bright Magenta
            '96': lambda f: f.setForeground(QColor(85, 255, 255)),  # Bright Cyan
            '97': lambda f: f.setForeground(QColor('white')),  # Bright White
            '40': lambda f: f.setBackground(QColor('black')),  # Background black
            '41': lambda f: f.setBackground(QColor('darkRed')),  # Background red
            '42': lambda f: f.setBackground(QColor('darkGreen')),  # Background green
            '43': lambda f: f.setBackground(QColor('darkYellow')),  # Background yellow
            '44': lambda f: f.setBackground(QColor('darkBlue')),  # Background blue
            '45': lambda f: f.setBackground(QColor('darkMagenta')),  # Background magenta
            '46': lambda f: f.setBackground(QColor('darkCyan')),  # Background cyan
            '47': lambda f: f.setBackground(QColor('lightGray')),  # Background white
        }

        # Récupérer la taille de police actuelle du widget
        current_font = self.log_view.font()
        font_size = current_font.pointSize()

        # Format de texte par défaut avec la police actuelle
        default_format = QTextCharFormat()
        default_format.setForeground(QColor('white'))
        default_format.setFontPointSize(font_size)
        current_format = QTextCharFormat(default_format)

        # Diviser le texte en segments en utilisant les codes ANSI comme séparateurs
        segments = ansi_escape.split(text)

        for segment in segments:
            if not segment:
                continue

            # Vérifier si c'est un code ANSI
            if segment.startswith('\x1b[') and segment.endswith('m'):
                codes = segment[2:-1].split(';')  # Enlever '\x1b[' et 'm', puis séparer par ';'

                for code in codes:
                    if not code:  # Code vide signifie réinitialisation
                        current_format = QTextCharFormat(default_format)
                    elif code in ansi_styles:
                        ansi_styles[code](current_format)
                    # Gestion des codes 256 couleurs (simplifiée)
                    elif code.startswith('38;5;') and len(code.split(';')) == 3:
                        # Code de couleur 256 (simplifiée)
                        pass  # On ignore pour l'instant
                    else:
                        # Code inconnu, on réinitialise
                        current_format = QTextCharFormat(default_format)

                # Appliquer le format mis à jour
                cursor.setCharFormat(current_format)
            else:
                # C'est du texte à afficher
                cursor.insertText(segment, current_format)
