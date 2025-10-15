# GUI Modules - Refactored Components

Ce dossier contient les modules refactorisés de l'interface graphique de Mr. Pipe.

## Structure

### `workers.py`
Contient tous les workers QThread pour les opérations asynchrones :
- **HttpWorker** : Worker générique pour les requêtes HTTP
- **ProjectSyncWorker** : Synchronisation de la liste des projets
- **LaunchWorker** : Lancement des jobs manuels
- **LogWorker** : Récupération des logs en temps réel
- **JobStatusWorker** : Surveillance du statut d'un job
- **JobDataWorker** : Récupération des données d'un job (statut + logs)

### `dialogs.py`
Contient les fenêtres de dialogue :
- **ConfigDialog** : Dialogue de configuration (URL GitLab, token, projets)
- **AboutDialog** : Dialogue "À propos" avec informations sur l'application

### `styles.py`
Contient les feuilles de style CSS :
- **get_dark_mode_stylesheet()** : Stylesheet dark mode pour toute l'application
- **get_log_view_stylesheet()** : Stylesheet spécifique pour la vue des logs
- **get_dialog_stylesheet()** : Stylesheet pour les dialogues
- **get_license_text_stylesheet()** : Stylesheet pour le texte de licence

### `log_formatter.py`
Contient les utilitaires de formatage des logs :
- **LogFormatter.clean_ansi_codes()** : Nettoie les codes ANSI inutiles
- **LogFormatter.process_ansi_codes()** : Convertit les codes ANSI en format Qt

## Utilisation

Ces modules sont importés dans `gui.py` :

```python
from gui_modules.workers import HttpWorker, ProjectSyncWorker, ...
from gui_modules.dialogs import ConfigDialog, AboutDialog
from gui_modules.styles import get_dark_mode_stylesheet, get_log_view_stylesheet
from gui_modules.log_formatter import LogFormatter
```

## Avantages de la refactorisation

1. **Séparation des responsabilités** : Chaque module a une fonction claire
2. **Maintenabilité** : Plus facile de trouver et modifier du code
3. **Réutilisabilité** : Les composants peuvent être réutilisés ailleurs
4. **Testabilité** : Plus facile de tester chaque module individuellement
5. **Lisibilité** : Le fichier principal `gui.py` est plus court et plus clair
