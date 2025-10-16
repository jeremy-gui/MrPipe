# Changements - Chargement Progressif des Projets

## Problème résolu
L'application bloquait complètement l'interface pendant le chargement initial des projets, ce qui pouvait causer des crashs si l'utilisateur cliquait dans le menu pendant ce temps.

## Solution implémentée

### 1. Chargement progressif des projets
- **Avant** : Tous les projets étaient chargés en parallèle, ce qui surchargeait l'interface
- **Après** : Les projets sont chargés un par un lors du premier démarrage
- Délai de 100ms entre chaque projet pour maintenir l'interface réactive
- Les mises à jour ultérieures continuent de charger en parallèle pour la rapidité

### 2. Indicateur visuel de chargement
- Message "Chargement des projets en cours..." affiché dans l'arbre pendant le chargement initial
- Chaque projet affiche "Chargement... (ID: xxx)" pendant son chargement individuel
- Le message disparaît automatiquement une fois tous les projets chargés

### 3. Protection contre les crashs
- Ajout d'un flag `is_initial_loading` pour suivre l'état du chargement
- Avertissement si l'utilisateur tente d'ouvrir les paramètres pendant le chargement
- Vérification que `gitlab_manager` est initialisé avant de charger les logs d'un job
- Gestion d'erreur améliorée dans les workers avec traceback complet pour le débogage

### 4. Gestion d'erreur robuste
- Les erreurs dans les workers sont maintenant loggées avec le traceback complet
- Les erreurs de chargement d'un projet n'empêchent pas le chargement des autres
- Messages d'erreur clairs pour l'utilisateur

## Fichiers modifiés

### `gui_modules/project_manager.py`
- Ajout de `loading_queue`, `is_loading`, et `initial_load_done`
- Nouvelle méthode `_load_next_project()` pour le chargement progressif
- Nouvelle méthode `_start_project_worker()` pour démarrer un worker de projet
- Nouvelles méthodes `_on_progressive_load_done()` et `_on_progressive_load_error()`
- Refactorisation de `_cleanup_removed_projects()`

### `gui.py`
- Ajout du flag `is_initial_loading`
- Modification de `show_config()` pour avertir pendant le chargement
- Reset du flag `initial_load_done` lors d'une nouvelle configuration

### `gui_modules/job_manager.py`
- Ajout de vérification que `gitlab_manager` est initialisé avant de charger un job
- Gestion d'erreur avec try/catch lors de la création du `JobDataWorker`

### `gui_modules/workers.py`
- Amélioration de la gestion d'erreur dans `HttpWorker.run()`
- Ajout du traceback complet pour le débogage

## Comportement attendu

### Au démarrage
1. L'application affiche le splash screen
2. La fenêtre principale s'ouvre
3. Message "Chargement des projets en cours..." apparaît
4. Les projets se chargent un par un (visible dans l'arbre)
5. Une fois terminé, le message disparaît et l'interface est pleinement réactive

### Pendant le chargement
- L'interface reste réactive
- L'utilisateur peut redimensionner la fenêtre
- Un avertissement s'affiche si l'utilisateur tente d'ouvrir les paramètres
- Les clics sur les projets déjà chargés fonctionnent normalement

### Après le chargement
- L'interface fonctionne normalement
- Les mises à jour automatiques continuent en arrière-plan
- Pas de blocage lors des rafraîchissements

## Tests recommandés

1. **Test de démarrage** : Vérifier que les projets se chargent progressivement
2. **Test d'interaction** : Cliquer dans le menu pendant le chargement
3. **Test de redimensionnement** : Redimensionner la fenêtre pendant le chargement
4. **Test d'erreur** : Simuler une erreur réseau pour vérifier la gestion d'erreur
5. **Test de configuration** : Changer la configuration pendant le chargement

## Correction du warning QThread (mise à jour)

### Problème supplémentaire identifié
Après les tests, un warning `QThread: Destroyed while thread is still running` apparaissait lors de la fermeture de l'application.

### Solution appliquée
- Amélioration du nettoyage des workers dans `closeEvent()`
- Ajout de `wait(1000)` pour attendre la fin des threads avant destruction
- Utilisation de `list()` pour itérer sur les workers en toute sécurité
- Appel de `deleteLater()` seulement après arrêt complet des threads
- Suppression du nettoyage automatique des workers pendant leur cycle de vie

### Résultat
- Plus de warning lors de la fermeture
- Fermeture propre de tous les threads
- Pas de fuite mémoire

Voir `FIX_QTHREAD_WARNING.md` pour plus de détails.

## Notes techniques

- Le chargement progressif n'est utilisé que pour le premier chargement
- Les mises à jour ultérieures utilisent le chargement parallèle pour la rapidité
- Le délai de 100ms entre chaque projet peut être ajusté si nécessaire
- Les workers sont correctement arrêtés pour éviter les fuites mémoire
- Timeout de 1 seconde pour l'arrêt des threads lors de la fermeture
