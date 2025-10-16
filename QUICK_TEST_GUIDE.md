# 🚀 Guide rapide - Tests de stress

## Setup (une seule fois)

```bash
# 1. Installer les dépendances
pip install pytest pytest-qt

# 2. Copier votre configuration GitLab
./copy_config_for_tests.sh
```

## Lancer les tests

```bash
# Méthode simple (recommandée)
./run_tests.sh

# Répéter 10 fois
./run_tests.sh repeat 10

# Mode debug
./run_tests.sh debug
```

## Résultats

✅ **Succès** : Tous les tests passent
```
========================= 3 passed in 15.23s =========================
```

❌ **Échec** : Un crash QThread a été détecté
```
QThread: Destroyed while thread '' is still running
FAILED
```

## Fichiers importants

- `tests/test_stress.py` - Les tests
- `test_config.ini` - Votre config (ne pas commiter!)
- `run_tests.sh` - Script de lancement
- `TESTING.md` - Documentation complète

## En cas de problème

1. Vérifier que `test_config.ini` existe
2. Vérifier que votre token GitLab est valide
3. Lancer en mode debug : `./run_tests.sh debug`
4. Consulter `TESTING.md` pour plus de détails

## Ajouter au workflow

```bash
# Avant chaque commit
./run_tests.sh && git commit -m "..."
```

C'est tout ! 🎉
