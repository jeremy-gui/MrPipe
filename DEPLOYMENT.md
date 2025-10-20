# 📦 Guide de Déploiement - Mr. Pipe

## 🍎 Déploiement macOS

### Prérequis

```bash
pip install pyinstaller
```

### Build de l'Application

```bash
# Nettoyer les builds précédents
rm -rf build dist

# Créer l'application macOS
pyinstaller MrPipe.spec

# L'application sera dans dist/Mr. Pipe.app
```

### Structure du Bundle macOS

```
Mr. Pipe.app/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   │   └── Mr. Pipe (exécutable)
│   ├── Resources/
│   │   ├── icon.icns
│   │   └── assets/
│   │       ├── image.png
│   │       ├── logo.icns
│   │       ├── ico.ico
│   │       └── animation.mp4
│   └── Frameworks/
```

### Configuration dans MrPipe.spec

```python
# Icône de l'application
icon='assets/logo.icns'

# Assets inclus
datas=[
    ('assets/image.png', 'assets'),
    ('assets/logo.icns', 'assets'),
    ('assets/logo.ico', 'assets'),
    ('assets/ico.ico', 'assets'),
    ('assets/animation.mp4', 'assets'),
]

# Bundle macOS
app = BUNDLE(
    exe,
    name='Mr. Pipe.app',
    icon='assets/logo.icns',
    bundle_identifier='com.mrpipe.app',
    version='1.1.0',
)
```

### Signature et Notarisation (optionnel)

```bash
# Signer l'application
codesign --deep --force --verify --verbose \
    --sign "Developer ID Application: YOUR_NAME" \
    "dist/Mr. Pipe.app"

# Créer un DMG
hdiutil create -volname "Mr. Pipe" \
    -srcfolder "dist/Mr. Pipe.app" \
    -ov -format UDZO "dist/MrPipe-1.1.0.dmg"

# Notariser (nécessite un compte Apple Developer)
xcrun notarytool submit "dist/MrPipe-1.1.0.dmg" \
    --apple-id "your@email.com" \
    --team-id "TEAM_ID" \
    --password "app-specific-password"
```

## 🪟 Déploiement Windows

### Prérequis

```bash
pip install pyinstaller
```

### Build de l'Application

```bash
# Nettoyer les builds précédents
rmdir /s /q build dist

# Créer l'exécutable Windows
pyinstaller MrPipe-Windows.spec

# L'exécutable sera dans dist/Mr. Pipe.exe
```

### Structure du Build Windows

```
dist/
├── Mr. Pipe.exe
├── _internal/
│   ├── assets/
│   │   ├── image.png
│   │   ├── ico.ico
│   │   ├── logo.ico
│   │   └── animation.mp4
│   ├── PyQt6/
│   └── ... (autres dépendances)
```

### Configuration dans MrPipe-Windows.spec

```python
# Icône de l'application
icon='assets/logo.ico'

# Version info
version_file='version_info.txt'

# Assets inclus
datas=[
    ('assets/image.png', 'assets'),
    ('assets/ico.ico', 'assets'),
    ('assets/logo.ico', 'assets'),
    ('version_info.txt', '.'),
    ('assets/animation.mp4', 'assets'),
]
```

### Créer un Installeur (optionnel)

#### Avec Inno Setup

1. Installer [Inno Setup](https://jrsoftware.org/isinfo.php)
2. Créer un script `installer.iss` :

```iss
[Setup]
AppName=Mr. Pipe
AppVersion=1.1.0
DefaultDirName={pf}\Mr. Pipe
DefaultGroupName=Mr. Pipe
OutputDir=dist
OutputBaseFilename=MrPipe-Setup-1.1.0
Compression=lzma2
SolidCompression=yes
SetupIconFile=assets\logo.ico

[Files]
Source: "dist\Mr. Pipe.exe"; DestDir: "{app}"
Source: "dist\_internal\*"; DestDir: "{app}\_internal"; Flags: recursesubdirs

[Icons]
Name: "{group}\Mr. Pipe"; Filename: "{app}\Mr. Pipe.exe"
Name: "{commondesktop}\Mr. Pipe"; Filename: "{app}\Mr. Pipe.exe"

[Run]
Filename: "{app}\Mr. Pipe.exe"; Description: "Launch Mr. Pipe"; Flags: postinstall nowait skipifsilent
```

3. Compiler : `iscc installer.iss`

## 🔧 Gestion des Assets

### Développement

En mode développement, les assets sont chargés depuis `assets/` :

```python
UIHelpers.get_resource_path("assets/image.png")
# → /path/to/project/assets/image.png
```

### Production (PyInstaller)

En mode production, PyInstaller copie les assets dans `_MEIPASS` :

```python
UIHelpers.get_resource_path("assets/image.png")
# macOS → /var/.../Mr. Pipe.app/Contents/Resources/assets/image.png
# Windows → C:\Users\...\AppData\Local\Temp\_MEI...\assets\image.png
```

## 📋 Checklist de Déploiement

### Avant le Build

- [ ] Tester l'application en mode développement
- [ ] Vérifier que tous les assets sont dans `assets/`
- [ ] Mettre à jour le numéro de version dans les `.spec`
- [ ] Vérifier `version_info.txt` (Windows)
- [ ] Tester sur la plateforme cible

### Build

- [ ] Nettoyer les builds précédents (`rm -rf build dist`)
- [ ] Exécuter PyInstaller avec le bon `.spec`
- [ ] Vérifier que l'application se lance
- [ ] Tester toutes les fonctionnalités
- [ ] Vérifier que les assets se chargent correctement

### Distribution

- [ ] Créer un DMG (macOS) ou installeur (Windows)
- [ ] Signer l'application (optionnel mais recommandé)
- [ ] Tester l'installation sur une machine propre
- [ ] Créer des notes de version
- [ ] Publier sur GitHub Releases ou autre

## 🐛 Dépannage

### Les assets ne se chargent pas

```python
# Vérifier le chemin
import sys
print(f"Running from: {sys._MEIPASS if hasattr(sys, '_MEIPASS') else 'dev mode'}")
```

### L'icône ne s'affiche pas (macOS)

```bash
# Vérifier l'icône dans le bundle
ls -la "dist/Mr. Pipe.app/Contents/Resources/"
```

### L'icône ne s'affiche pas (Windows)

```bash
# Vérifier que logo.ico est bien utilisé
# Parfois Windows met en cache les icônes
```

### Erreur de dépendances manquantes

```python
# Ajouter dans hiddenimports du .spec
hiddenimports=[
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtMultimedia',
    'PyQt6.QtMultimediaWidgets',
]
```

## 📚 Ressources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [macOS Code Signing](https://developer.apple.com/support/code-signing/)
- [Inno Setup](https://jrsoftware.org/isinfo.php)
- [Windows App Certification](https://docs.microsoft.com/en-us/windows/apps/desktop/)

## 🔄 Mise à Jour

Pour mettre à jour l'application :

1. Incrémenter le numéro de version dans les `.spec`
2. Mettre à jour `version_info.txt` (Windows)
3. Rebuild avec PyInstaller
4. Tester la mise à jour
5. Distribuer la nouvelle version
