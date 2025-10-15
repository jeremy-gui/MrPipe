# Configuration des Tailles de Font

## 📐 Tailles Centralisées

Toutes les tailles de font sont maintenant définies dans `gui_modules/styles.py` pour une configuration cohérente et facile à modifier.

### Constantes Disponibles

```python
# Dans gui_modules/styles.py
LOG_FONT_SIZE = 16              # Taille des logs (affichage principal)
TREE_FONT_SIZE_PROJECT = 12     # Taille des noms de projets dans l'arbre
TREE_FONT_SIZE_PIPELINE = 11    # Taille des noms de pipelines dans l'arbre
```

## 📍 Utilisation dans le Code

### 1. **Logs** (16pt)

#### `gui.py` - Configuration initiale
```python
from gui_modules.styles import LOG_FONT_SIZE

def configure_log_view_font(self):
    font.setPointSize(LOG_FONT_SIZE)  # ← Utilise la constante
```

#### `gui_modules/log_display.py` - Affichage des logs
```python
from .styles import LOG_FONT_SIZE

def update_log_display(self, log_content):
    current_font.setPointSize(LOG_FONT_SIZE)           # ← Utilise la constante
    default_format.setFontPointSize(LOG_FONT_SIZE)     # ← Utilise la constante
    LogFormatter.process_ansi_codes(..., LOG_FONT_SIZE) # ← Utilise la constante
```

#### `gui_modules/styles.py` - Stylesheet CSS
```python
def get_log_view_stylesheet():
    return f"""
    QTextEdit {{
        font-size: {LOG_FONT_SIZE}pt;  # ← Utilise la constante
    }}
    """
```

### 2. **Arbre de Projets** (12pt et 11pt)

#### `gui_modules/project_manager.py`
```python
from .styles import TREE_FONT_SIZE_PROJECT, TREE_FONT_SIZE_PIPELINE

# Pour les projets
font.setPointSize(TREE_FONT_SIZE_PROJECT)    # 12pt

# Pour les pipelines
font.setPointSize(TREE_FONT_SIZE_PIPELINE)   # 11pt
```

## 🔧 Comment Modifier les Tailles

Pour changer les tailles de font dans toute l'application, il suffit de modifier les constantes dans **un seul fichier** :

### Fichier : `gui_modules/styles.py`

```python
# Modifiez ces valeurs selon vos préférences
LOG_FONT_SIZE = 16              # Changez pour 14, 18, 20, etc.
TREE_FONT_SIZE_PROJECT = 12     # Changez pour 10, 14, etc.
TREE_FONT_SIZE_PIPELINE = 11    # Changez pour 10, 12, etc.
```

**Aucune autre modification n'est nécessaire** - tous les fichiers utilisent automatiquement ces constantes !

## ✅ Avantages de cette Approche

1. **Centralisation** : Une seule source de vérité pour les tailles
2. **Cohérence** : Toutes les parties de l'application utilisent les mêmes valeurs
3. **Maintenabilité** : Facile de changer les tailles globalement
4. **Lisibilité** : Les constantes ont des noms explicites
5. **Évolutivité** : Facile d'ajouter de nouvelles constantes

## 📊 Fichiers Modifiés

| Fichier | Utilisation |
|---------|-------------|
| `gui_modules/styles.py` | **Définition** des constantes |
| `gui.py` | Import et utilisation de `LOG_FONT_SIZE` |
| `gui_modules/log_display.py` | Import et utilisation de `LOG_FONT_SIZE` |
| `gui_modules/project_manager.py` | Import et utilisation de `TREE_FONT_SIZE_*` |

## 🎯 Résultat

- ✅ **Cohérence totale** : Plus d'incohérences entre 14pt, 16pt et 20pt
- ✅ **Configuration unique** : Toutes les tailles dans `styles.py`
- ✅ **Facile à modifier** : Changez une valeur, tout est mis à jour
- ✅ **Code propre** : Constantes nommées au lieu de valeurs magiques
