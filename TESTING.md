# Guide de test - Mr. Pipe

## 🧪 Tests de stress QThread

### Installation des dépendances

```bash
# Installer pytest et pytest-qt
pip install pytest pytest-qt
```

### Configuration pour les tests

**IMPORTANT** : Les tests ont besoin de votre configuration GitLab.

```bash
# 1. Copier votre configuration actuelle pour les tests
./copy_config_for_tests.sh

# 2. Vérifier que test_config.ini a été créé
ls -l test_config.ini
```

**Note** : `test_config.ini` contient votre token GitLab et est automatiquement ajouté au `.gitignore` pour éviter de le commiter.

### Lancer les tests

#### 1. Tous les tests de stress

```bash
# Depuis la racine du projet
pytest tests/test_stress.py -v
```

#### 2. Un test spécifique

```bash
# Test de fermeture rapide
pytest tests/test_stress.py::test_rapid_close_after_startup -v

# Test de changement rapide de jobs
pytest tests/test_stress.py::test_rapid_job_switching -v

# Test d'ouverture de settings pendant le chargement
pytest tests/test_stress.py::test_open_settings_during_loading -v
```

#### 3. Avec plus de détails

```bash
# Afficher les prints et plus de détails
pytest tests/test_stress.py -v -s

# Arrêter au premier échec
pytest tests/test_stress.py -v -x

# Mode verbeux maximum
pytest tests/test_stress.py -vv
```

#### 4. Répéter les tests (pour détecter les problèmes intermittents)

```bash
# Répéter 10 fois
pytest tests/test_stress.py --count=10

# Ou avec une boucle bash
for i in {1..10}; do
    echo "=== Run $i/10 ==="
    pytest tests/test_stress.py -v || break
done
```

### Résultats attendus

✅ **Succès** : Tous les tests passent sans crash
```
tests/test_stress.py::test_rapid_close_after_startup PASSED
tests/test_stress.py::test_rapid_job_switching PASSED
tests/test_stress.py::test_open_settings_during_loading PASSED
```

❌ **Échec** : Un test échoue
```
tests/test_stress.py::test_rapid_close_after_startup FAILED
```

### Interpréter les erreurs

#### QThread destroyed while running
```
QThread: Destroyed while thread '' is still running
```
→ Un worker n'a pas été arrêté proprement

#### Assertion failed
```
AssertionError: assert 2 == 0
```
→ Des workers tournent encore après la fermeture

#### Timeout
```
TimeoutError: Worker did not finish in time
```
→ Un worker est bloqué

## 🔍 Debug des tests qui échouent

### Activer les logs Qt

```bash
# Avec les messages de debug Qt
QT_LOGGING_RULES="*.debug=true" pytest tests/test_stress.py -v -s
```

### Lancer avec un debugger

```bash
# Avec pdb (debugger Python)
pytest tests/test_stress.py --pdb

# Ou avec ipdb (meilleur)
pip install ipdb
pytest tests/test_stress.py --pdb --pdbcls=IPython.terminal.debugger:Pdb
```

### Capturer les warnings

```bash
# Afficher tous les warnings
pytest tests/test_stress.py -v -W all
```

## 📊 Tests en continu

### Lancer automatiquement à chaque modification

```bash
# Installer pytest-watch
pip install pytest-watch

# Lancer en mode watch
ptw tests/test_stress.py -- -v
```

### Intégration dans le workflow

Ajouter dans votre workflow de développement :

```bash
# Avant de commit
pytest tests/test_stress.py -v

# Si succès, commit
git add .
git commit -m "Fix: ..."
```

## 🎯 Bonnes pratiques

1. **Lancer les tests régulièrement** - Après chaque modification importante
2. **Répéter les tests** - Les problèmes de threads sont souvent intermittents
3. **Tester sur différents OS** - Les problèmes peuvent varier selon l'OS
4. **Ajouter des tests** - Quand un nouveau crash est découvert

## 🚀 Tests avancés

### Test de charge

```bash
# Lancer plusieurs instances en parallèle
pytest tests/test_stress.py -v -n 4  # 4 workers en parallèle
# (nécessite: pip install pytest-xdist)
```

### Profiling

```bash
# Mesurer le temps d'exécution
pytest tests/test_stress.py -v --durations=10

# Profiling mémoire
pip install pytest-memray
pytest tests/test_stress.py --memray
```

## 📝 Ajouter de nouveaux tests

Pour ajouter un nouveau test de stress :

1. Ouvrir `tests/test_stress.py`
2. Ajouter une nouvelle fonction `test_*`
3. Utiliser `qtbot` pour gérer la fenêtre
4. Simuler le scénario problématique
5. Vérifier l'état final

Exemple :
```python
def test_mon_nouveau_scenario(qtbot):
    """Description du test"""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Votre scénario ici
    # ...
    
    window.close()
    QTest.qWait(1000)
    
    # Vérifications
    assert condition
```

## 🆘 Aide

Si les tests échouent de manière persistante :

1. Vérifier les logs avec `-v -s`
2. Isoler le test qui échoue
3. Ajouter des `print()` pour tracer l'exécution
4. Vérifier que tous les workers sont bien arrêtés dans `closeEvent()`
5. Vérifier que tous les timers sont bien arrêtés

Bon testing ! 🎉
