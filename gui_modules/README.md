# GUI Modules - Refactored Components

Ce dossier contient les modules refactorisés de l'interface graphique de Mr. Pipe.

## Structure

### Phase 1 - Composants de base

#### `workers.py`
Contient tous les workers QThread pour les opérations asynchrones :
- **HttpWorker** : Worker générique pour les requêtes HTTP
- **ProjectSyncWorker** : Synchronisation de la liste des projets
- **LaunchWorker** : Lancement des jobs manuels
- **LogWorker** : Récupération des logs en temps réel
- **JobStatusWorker** : Surveillance du statut d'un job
- **JobDataWorker** : Récupération des données d'un job (statut + logs)

#### `dialogs.py`
Contient les fenêtres de dialogue :
- **ConfigDialog** : Dialogue de configuration (URL GitLab, token, projets)
- **AboutDialog** : Dialogue "À propos" avec informations sur l'application

#### `styles.py`
Contient les feuilles de style CSS :
- **get_dark_mode_stylesheet()** : Stylesheet dark mode pour toute l'application
- **get_log_view_stylesheet()** : Stylesheet spécifique pour la vue des logs
- **get_dialog_stylesheet()** : Stylesheet pour les dialogues
- **get_license_text_stylesheet()** : Stylesheet pour le texte de licence

#### `log_formatter.py`
Contient les utilitaires de formatage des logs :
- **LogFormatter.clean_ansi_codes()** : Nettoie les codes ANSI inutiles
- **LogFormatter.process_ansi_codes()** : Convertit les codes ANSI en format Qt

### Phase 2 - Managers et helpers

#### `config_manager.py`
Gestion de la configuration :
- **ConfigManager** : Charge, sauvegarde et restaure la configuration
  - `load_config()` : Charge la configuration depuis le fichier
  - `save_config()` : Sauvegarde la configuration
  - `restore_splitter_sizes()` : Restaure les proportions du splitter
  - `auto_save_geometry()` : Sauvegarde automatique de la géométrie

#### `project_manager.py`
Gestion des projets :
- **ProjectManager** : Gère l'affichage et la mise à jour des projets
  - `update_projects()` : Met à jour tous les projets dans l'arbre
  - `fetch_project_data()` : Récupère les données d'un projet
  - `on_project_data_loaded()` : Appelé quand les données sont chargées
  - `update_pipeline_jobs()` : Met à jour les jobs d'un pipeline
  - `on_project_error()` : Gère les erreurs de chargement

#### `job_manager.py`
Gestion des jobs :
- **JobManager** : Gère la sélection des jobs et l'affichage des logs
  - `on_item_clicked()` : Gère le clic sur un item de l'arbre
  - `on_job_data_received()` : Appelé quand les données du job sont reçues
  - `on_job_finished()` : Appelé quand un job est terminé
- **JobColorManager** : Gère les couleurs et animations des jobs
  - `set_job_color()` : Définit la couleur d'un job selon son statut
  - `on_job_status_updated()` : Appelé quand le statut d'un job change

#### `log_display.py`
Affichage des logs :
- **LogDisplay** : Gère l'affichage et le formatage des logs
  - `update_log_display()` : Met à jour l'affichage des logs

#### `ui_helpers.py`
Utilitaires UI :
- **UIHelpers** : Fonctions helper pour l'UI
  - `get_resource_path()` : Obtient le chemin absolu d'une ressource
- **HipsterPipeAnimation** : Gère l'animation de célébration
  - `show_animation()` : Affiche la vidéo de célébration
  - `on_video_finished()` : Appelé quand la vidéo se termine
- **LoadingAnimation** : Gère l'animation de chargement
  - `animate_dots()` : Anime les points de chargement
  - `update_display()` : Met à jour l'affichage du chargement

## Utilisation

Ces modules sont importés dans `gui.py` :

```python
from gui_modules.workers import LaunchWorker
from gui_modules.dialogs import ConfigDialog, AboutDialog
from gui_modules.styles import get_dark_mode_stylesheet, get_log_view_stylesheet
from gui_modules.config_manager import ConfigManager
from gui_modules.project_manager import ProjectManager
from gui_modules.job_manager import JobManager, JobColorManager
from gui_modules.log_display import LogDisplay
from gui_modules.ui_helpers import UIHelpers, HipsterPipeAnimation, LoadingAnimation
```

## Statistiques de refactorisation

### Phase 1
- **Avant** : 1 fichier de ~1966 lignes
- **Après Phase 1** : 1 fichier principal (~1274 lignes) + 4 modules (~850 lignes)
- **Réduction** : ~700 lignes de code dupliqué supprimées

### Phase 2
- **Avant Phase 2** : 1 fichier de ~1274 lignes
- **Après Phase 2** : 1 fichier principal (~997 lignes) + 9 modules (~1650 lignes)
- **Réduction supplémentaire** : ~277 lignes (~22%)
- **Réduction totale** : ~977 lignes (~50% du fichier original)

## Avantages de la refactorisation

1. **Séparation des responsabilités** : Chaque module a une fonction claire
2. **Maintenabilité** : Plus facile de trouver et modifier du code
3. **Réutilisabilité** : Les composants peuvent être réutilisés ailleurs
4. **Testabilité** : Plus facile de tester chaque module individuellement
5. **Lisibilité** : Le fichier principal `gui.py` est plus court et plus clair
6. **Modularité** : Architecture en couches (Workers → Managers → MainWindow)
