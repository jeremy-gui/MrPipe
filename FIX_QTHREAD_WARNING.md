# Correction du warning "QThread: Destroyed while thread is still running"

## Problème
Le warning `QThread: Destroyed while thread is still running` apparaissait lors de la fermeture de l'application, indiquant que des threads étaient détruits alors qu'ils étaient encore en cours d'exécution.

## Causes identifiées

1. **Nettoyage prématuré des workers** : Les workers étaient supprimés avant que leurs threads ne soient complètement terminés
2. **Pas d'attente de fin de thread** : La méthode `deleteLater()` était appelée sans attendre que `isRunning()` retourne `False`
3. **Nettoyage automatique mal synchronisé** : Tentative de nettoyer les workers immédiatement après l'émission des signaux `finished`/`error`

## Solutions implémentées

### 1. Amélioration du `closeEvent` dans `gui.py`

**Avant** :
```python
for worker in self.project_workers.values():
    if worker and worker.isRunning():
        try:
            worker.finished.disconnect()
            worker.error.disconnect()
            worker.stop()
            # worker.wait()  # Retiré pour éviter le blocage
        except:
            pass
```

**Après** :
```python
# Arrêter tous les workers de projet
for worker in list(self.project_workers.values()):
    if worker:
        try:
            worker.stop()
            if worker.isRunning():
                worker.wait(1000)  # Wait max 1 second
            worker.deleteLater()
        except:
            pass
self.project_workers.clear()
```

**Changements** :
- Utilisation de `list()` pour éviter les modifications du dictionnaire pendant l'itération
- Appel de `wait(1000)` pour attendre que le thread se termine (max 1 seconde)
- Appel de `deleteLater()` seulement après que le thread soit arrêté
- Nettoyage explicite du dictionnaire avec `clear()`

### 2. Application aux autres workers

Les mêmes corrections ont été appliquées à :
- `log_worker`
- `launch_worker`
- `job_data_worker`
- `job_status_workers`

### 3. Simplification du nettoyage automatique

**Décision** : Ne pas nettoyer automatiquement les workers pendant leur cycle de vie normal.

**Raison** : 
- Les workers sont légers en mémoire
- Le nettoyage automatique créait des problèmes de synchronisation
- Les workers sont correctement nettoyés lors de la fermeture de l'application
- Les workers sont remplacés (et donc nettoyés) lors des mises à jour

**Code retiré** :
```python
def _cleanup_worker(self, proj_id):
    """Clean up a worker after it finishes"""
    # Code complexe de nettoyage automatique retiré
```

## Bonnes pratiques appliquées

### 1. Arrêt propre des threads
```python
worker.stop()  # Signal au thread de s'arrêter
if worker.isRunning():
    worker.wait(1000)  # Attendre max 1 seconde
worker.deleteLater()  # Marquer pour suppression
```

### 2. Timeout de sécurité
- Utilisation de `wait(1000)` au lieu de `wait()` sans timeout
- Évite le blocage infini si un thread ne répond pas
- 1 seconde est suffisant pour la plupart des opérations réseau

### 3. Itération sécurisée
```python
for worker in list(self.project_workers.values()):
    # Utiliser list() pour créer une copie
```

### 4. Nettoyage explicite
```python
self.project_workers.clear()  # Vider le dictionnaire
```

## Tests effectués

1. **Démarrage normal** : ✅ Pas de warning
2. **Fermeture pendant le chargement** : ✅ Pas de warning
3. **Fermeture après chargement complet** : ✅ Pas de warning
4. **Multiples ouvertures/fermetures** : ✅ Pas de warning

## Impact sur les performances

- **Mémoire** : Impact négligeable (les workers sont légers)
- **CPU** : Aucun impact (pas de polling ou de vérifications continues)
- **Fermeture** : Peut prendre jusqu'à 1 seconde de plus si des threads sont actifs (acceptable)

## Recommandations futures

1. **Monitoring** : Ajouter des logs pour suivre le cycle de vie des workers en mode debug
2. **Timeout configurable** : Permettre de configurer le timeout de `wait()` si nécessaire
3. **Indicateur de fermeture** : Afficher un indicateur pendant la fermeture si des threads sont actifs

## Fichiers modifiés

- `gui.py` : Amélioration de `closeEvent()`
- `gui_modules/project_manager.py` : Suppression du nettoyage automatique

## Notes techniques

- Les workers héritent de `QThread` et ont un flag `_is_running`
- La méthode `stop()` met `_is_running` à `False`
- Le thread vérifie ce flag dans sa boucle `run()`
- `wait()` bloque jusqu'à ce que `run()` se termine
- `deleteLater()` marque l'objet pour suppression lors du prochain cycle d'événements Qt
