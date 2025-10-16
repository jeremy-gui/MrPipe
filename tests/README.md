# Tests - Mr. Pipe

Ce dossier contient tous les tests automatisés de l'application.

## 📁 Structure

```
tests/
├── __init__.py           # Package Python
├── test_stress.py        # Tests de stress QThread
└── README.md            # Ce fichier
```

## 🧪 Tests disponibles

### test_stress.py - Tests de stress QThread

Tests pour détecter les crashs QThread et les problèmes de concurrence :

- **test_rapid_close_after_startup** - Ferme l'app 100ms après le démarrage
- **test_rapid_job_switching** - Change de job toutes les 50ms
- **test_open_settings_during_loading** - Ouvre Settings pendant le chargement

## 🚀 Lancer les tests

Depuis la racine du projet :

```bash
# Tous les tests
./run_tests.sh

# Répéter 10 fois
./run_tests.sh repeat 10

# Mode debug
./run_tests.sh debug

# Un test spécifique
./run_tests.sh test test_rapid_close_after_startup
```

Ou directement avec pytest :

```bash
# Tous les tests
pytest tests/ -v

# Un fichier spécifique
pytest tests/test_stress.py -v

# Un test spécifique
pytest tests/test_stress.py::test_rapid_close_after_startup -v
```

## 📝 Ajouter de nouveaux tests

1. Créer un nouveau fichier `test_*.py` dans ce dossier
2. Importer les dépendances nécessaires
3. Utiliser le fixture `test_config` pour la configuration GitLab
4. Utiliser `qtbot` pour gérer les widgets Qt
5. Écrire vos tests avec des assertions

Exemple :

```python
import pytest
from PyQt6.QtTest import QTest

def test_mon_scenario(qtbot, test_config):
    """Description du test"""
    from gui import MainWindow
    
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Votre scénario de test
    QTest.qWait(1000)
    
    # Vérifications
    assert window.isVisible()
    
    window.close()
```

## 📚 Documentation

- **TESTING.md** - Guide complet des tests
- **QUICK_TEST_GUIDE.md** - Guide rapide

## 🔧 Configuration

Les tests utilisent `test_config.ini` à la racine du projet.
Pour créer ce fichier : `./copy_config_for_tests.sh`
