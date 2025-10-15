# Assets - Mr. Pipe

Ce dossier contient tous les fichiers médias (images, icônes, vidéos) utilisés par l'application.

## 📁 Structure

### Icônes d'Application

- **`logo.icns`** : Icône macOS (format ICNS)
- **`logo.ico`** : Icône Windows principale (format ICO)
- **`ico.ico`** : Icône de fenêtre Windows (format ICO)

### Images

- **`image.png`** : Splash screen (512x512px)
- **`ico.png`** : Image icône principale
- **`ico-complet.png`** : Image icône complète
- **`logo-1.png`** : Logo alternatif

### Vidéos

- **`animation.mp4`** : Animation "Hipster Pipe" (célébration de succès)

### Autres

- **`MrPipe_logo_vectorized.svg`** : Logo vectoriel (SVG)

## 🔧 Utilisation dans le Code

Tous les assets sont chargés via `UIHelpers.get_resource_path()` qui gère automatiquement :
- Le mode développement (chemin relatif)
- Le mode production PyInstaller (chemin dans `_MEIPASS`)

### Exemples

```python
# Icône de fenêtre
self.setWindowIcon(QIcon(UIHelpers.get_resource_path("assets/ico.ico")))

# Splash screen
splash_pix = QPixmap(get_resource_path("assets/image.png"))

# Animation Hipster Pipe
video_path = UIHelpers.get_resource_path("assets/animation.mp4")
```

## 📦 Déploiement

Les fichiers `.spec` (PyInstaller) incluent automatiquement ces assets :

### macOS (`MrPipe.spec`)
```python
datas=[
    ('assets/image.png', 'assets'),
    ('assets/logo.icns', 'assets'),
    ('assets/ico.ico', 'assets'),
    ('assets/animation.mp4', 'assets'),
]
```

### Windows (`MrPipe-Windows.spec`)
```python
datas=[
    ('assets/image.png', 'assets'),
    ('assets/ico.ico', 'assets'),
    ('assets/logo.ico', 'assets'),
    ('assets/animation.mp4', 'assets'),
]
```

## 🎨 Format des Icônes

### macOS (ICNS)
- Format : ICNS
- Tailles : 16x16, 32x32, 128x128, 256x256, 512x512, 1024x1024
- Fichier : `logo.icns`

### Windows (ICO)
- Format : ICO
- Tailles : 16x16, 32x32, 48x48, 256x256
- Fichiers : `logo.ico` (app), `ico.ico` (fenêtre)

## 📝 Notes

- Tous les assets doivent être placés dans ce dossier
- Les chemins dans le code utilisent toujours le préfixe `assets/`
- PyInstaller copie automatiquement ce dossier dans le bundle
