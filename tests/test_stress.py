# test_stress.py
import sys
import os

# Ajouter le répertoire parent au path pour importer gui
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QTimer
import random

from gui import MainWindow
import configparser
import shutil
from PyQt6.QtCore import QStandardPaths

@pytest.fixture
def test_config():
    """Fixture pour charger la configuration de test"""
    test_config_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'test_config.ini'
    )
    
    if not os.path.exists(test_config_file):
        pytest.skip("test_config.ini not found. Run ./copy_config_for_tests.sh first")
    
    # Copier la config de test vers l'emplacement attendu par l'app
    config_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
    os.makedirs(config_dir, exist_ok=True)
    
    app_config_file = os.path.join(config_dir, 'gitlab_pipelines_manager.ini')
    
    # Sauvegarder la config existante si elle existe
    backup_file = None
    if os.path.exists(app_config_file):
        backup_file = app_config_file + '.backup'
        shutil.copy(app_config_file, backup_file)
    
    # Copier la config de test
    shutil.copy(test_config_file, app_config_file)
    
    yield app_config_file
    
    # Restaurer la config originale
    if backup_file and os.path.exists(backup_file):
        shutil.move(backup_file, app_config_file)
    elif os.path.exists(app_config_file):
        os.remove(app_config_file)

def get_all_job_items(tree):
    """Récupère tous les items de job dans l'arbre"""
    job_items = []
    for i in range(tree.topLevelItemCount()):
        project_item = tree.topLevelItem(i)
        for j in range(project_item.childCount()):
            pipeline_item = project_item.child(j)
            for k in range(pipeline_item.childCount()):
                job_item = pipeline_item.child(k)
                if job_item:
                    job_items.append(job_item)
    return job_items

def test_rapid_close_after_startup(qtbot, test_config):
    """Fermer l'app immédiatement après le démarrage"""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Attendre juste 100ms puis fermer
    QTest.qWait(100)
    window.close()
    
    # Vérifier qu'aucun thread ne tourne encore
    assert len(window.project_workers) == 0
    assert len(window.job_status_workers) == 0

def test_rapid_job_switching(qtbot, test_config):
    """Changer de job très rapidement"""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Attendre le chargement initial
    QTest.qWait(2000)
    
    # Cliquer sur 10 jobs différents très rapidement
    for _ in range(10):
        items = get_all_job_items(window.tree)
        if items:
            item = random.choice(items)
            window.job_manager.on_item_clicked(item, 0)
            QTest.qWait(50)  # Seulement 50ms entre chaque clic
    
    # Fermer
    window.close()
    QTest.qWait(1000)
    
    # Vérifier qu'aucun worker ne tourne
    assert window.log_worker is None
    assert window.job_data_worker is None

def test_open_settings_during_loading(qtbot, test_config):
    """Ouvrir les settings pendant le chargement puis fermer"""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    
    # Attendre 500ms (pendant le chargement)
    QTest.qWait(500)
    
    # Essayer d'ouvrir les settings
    window.show_config()
    
    # Fermer immédiatement
    QTest.qWait(100)
    window.close()
    
    # Vérifier
    assert window.pending_config_dialog == False