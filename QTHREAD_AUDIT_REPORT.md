# Audit complet des QThread dans l'application

## Liste des Workers (6 types)

1. **HttpWorker** - Requêtes HTTP génériques
2. **ProjectSyncWorker** - Synchronisation des projets
3. **LaunchWorker** - Lancement de jobs manuels
4. **LogWorker** - Récupération des logs en temps réel
5. **JobStatusWorker** - Surveillance du statut des jobs
6. **JobDataWorker** - Récupération des données de job

## Instances et leur gestion

### ✅ Bien gérés dans `gui.py` closeEvent

| Worker | Stocké dans | Nettoyage closeEvent | Status |
|--------|-------------|---------------------|---------|
| log_worker | self.log_worker | ✅ stop() + terminate() | OK |
| launch_worker | self.launch_worker | ✅ stop() + terminate() | OK |
| job_data_worker | self.job_data_worker | ✅ stop() + terminate() | OK |
| project_workers | self.project_workers{} | ✅ stop() + terminate() | OK |
| job_status_workers | self.job_status_workers{} | ✅ stop() + terminate() | OK |

### ✅ Bien géré dans `dialogs.py` closeEvent

| Worker | Stocké dans | Nettoyage closeEvent | Status |
|--------|-------------|---------------------|---------|
| sync_worker | self.sync_worker | ✅ stop() + terminate() | OK |

## ⚠️ Problèmes identifiés

### 1. ❌ `job_manager.py` - Arrêt sans terminate()

**Ligne 32-34 et 37-39** :
```python
if self.window.log_worker:
    self.window.log_worker.stop()
    self.window.log_worker.wait()  # ← Pas de timeout, pas de terminate()
    self.window.log_worker = None
```

**Problème** : Si le worker est bloqué, `wait()` sans timeout bloquera indéfiniment.

**Solution** : Ajouter timeout + terminate()

### 2. ❌ `job_manager.py` - Ligne 140-141

```python
self.window.log_worker.stop()
self.window.log_worker.wait()  # ← Pas de timeout, pas de terminate()
```

**Problème** : Même problème, pas de protection contre les blocages.

### 3. ⚠️ `project_manager.py` - Ligne 91-92

```python
worker.stop()
worker.wait()  # ← Pas de timeout, pas de terminate()
```

**Problème** : Lors du remplacement d'un worker, pas de protection.

### 4. ⚠️ `project_manager.py` - Ligne 136-144

```python
if worker.isRunning():
    worker.stop()
    worker.wait()  # ← Pas de timeout, pas de terminate()
```

**Problème** : Lors du nettoyage des projets supprimés, pas de protection.

## 🔧 Corrections nécessaires

### Correction 1 : `job_manager.py` - on_item_clicked()

**Avant** :
```python
if self.window.log_worker:
    self.window.log_worker.stop()
    self.window.log_worker.wait()
    self.window.log_worker = None

if self.window.job_data_worker:
    self.window.job_data_worker.stop()
    self.window.job_data_worker.wait()
    self.window.job_data_worker = None
```

**Après** :
```python
if self.window.log_worker:
    self.window.log_worker.stop()
    if self.window.log_worker.isRunning():
        self.window.log_worker.wait(500)
        if self.window.log_worker.isRunning():
            self.window.log_worker.terminate()
            self.window.log_worker.wait()
    self.window.log_worker = None

if self.window.job_data_worker:
    self.window.job_data_worker.stop()
    if self.window.job_data_worker.isRunning():
        self.window.job_data_worker.wait(500)
        if self.window.job_data_worker.isRunning():
            self.window.job_data_worker.terminate()
            self.window.job_data_worker.wait()
    self.window.job_data_worker = None
```

### Correction 2 : `job_manager.py` - on_job_finished()

**Avant** :
```python
self.window.log_worker.stop()
self.window.log_worker.wait()
```

**Après** :
```python
self.window.log_worker.stop()
if self.window.log_worker.isRunning():
    self.window.log_worker.wait(500)
    if self.window.log_worker.isRunning():
        self.window.log_worker.terminate()
        self.window.log_worker.wait()
```

### Correction 3 : `job_manager.py` - on_job_data_received()

**Avant** :
```python
if self.window.job_data_worker:
    self.window.job_data_worker.stop()
    self.window.job_data_worker.wait()
    self.window.job_data_worker = None
```

**Après** :
```python
if self.window.job_data_worker:
    self.window.job_data_worker.stop()
    if self.window.job_data_worker.isRunning():
        self.window.job_data_worker.wait(500)
        if self.window.job_data_worker.isRunning():
            self.window.job_data_worker.terminate()
            self.window.job_data_worker.wait()
    self.window.job_data_worker = None
```

### Correction 4 : `project_manager.py` - _start_project_worker()

**Avant** :
```python
if proj_id in self.window.project_workers:
    worker = self.window.project_workers[proj_id]
    if worker and worker.isRunning():
        try:
            worker.finished.disconnect()
            worker.error.disconnect()
            worker.stop()
            worker.wait()
        except:
            pass
```

**Après** :
```python
if proj_id in self.window.project_workers:
    worker = self.window.project_workers[proj_id]
    if worker and worker.isRunning():
        try:
            worker.finished.disconnect()
            worker.error.disconnect()
            worker.stop()
            if worker.isRunning():
                worker.wait(500)
                if worker.isRunning():
                    worker.terminate()
                    worker.wait()
        except:
            pass
```

### Correction 5 : `project_manager.py` - _cleanup_removed_projects()

**Avant** :
```python
if worker.isRunning():
    worker.stop()
    worker.wait()
```

**Après** :
```python
if worker.isRunning():
    worker.stop()
    worker.wait(500)
    if worker.isRunning():
        worker.terminate()
        worker.wait()
```

## 📊 Résumé

| Fichier | Problèmes trouvés | Corrections nécessaires |
|---------|-------------------|------------------------|
| gui.py | 0 | ✅ Déjà corrigé |
| dialogs.py | 0 | ✅ Déjà corrigé |
| job_manager.py | 3 | ❌ À corriger |
| project_manager.py | 2 | ❌ À corriger |

## 🎯 Principe à appliquer partout

**Pattern standard pour arrêter un worker** :
```python
worker.stop()                    # 1. Signal d'arrêt
if worker.isRunning():           # 2. Vérifier s'il tourne encore
    worker.wait(500)             # 3. Attendre 500ms
    if worker.isRunning():       # 4. Vérifier à nouveau
        worker.terminate()       # 5. Forcer l'arrêt
        worker.wait()            # 6. Attendre la fin
```

## ⚠️ Cas particuliers

### JobStatusWorker - Auto-nettoyage

Ces workers s'arrêtent automatiquement quand le job est terminé :
```python
if status in ['success', 'failed', 'canceled', 'skipped']:
    self._is_running = False
    self.finished_signal.emit(self.key)
```

Mais ils doivent quand même être arrêtés proprement lors de la fermeture.

### LogWorker - Boucle infinie

```python
while self._is_running:
    # ... récupération des logs
    self.msleep(1000)
```

Peut être bloqué sur `get_job_trace()` → **Nécessite terminate()**

## 🔍 Points de vigilance

1. **Toujours utiliser timeout** : `wait()` → `wait(500)`
2. **Toujours vérifier isRunning()** avant et après wait()
3. **Toujours avoir terminate() en dernier recours**
4. **Toujours mettre dans try/except** pour éviter les crashs
5. **Toujours mettre à None** après nettoyage

## ✅ Checklist de vérification

- [ ] Tous les `wait()` ont un timeout
- [ ] Tous les `wait()` sont suivis d'un check `isRunning()`
- [ ] Tous les workers bloqués peuvent être `terminate()`
- [ ] Tous les workers sont mis à `None` après nettoyage
- [ ] Tous les nettoyages sont dans des `try/except`
