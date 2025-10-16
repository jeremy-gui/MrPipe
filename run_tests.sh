#!/bin/bash
# Script pour lancer les tests de stress

echo "🧪 Mr. Pipe - Tests de stress QThread"
echo "======================================"
echo ""

# Vérifier si pytest est installé
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "⚠️  pytest n'est pas installé"
    echo "📦 Installation de pytest et pytest-qt..."
    pip install pytest pytest-qt
    echo ""
fi

# Vérifier si pytest-qt est installé
if ! python3 -c "import pytestqt" 2>/dev/null; then
    echo "⚠️  pytest-qt n'est pas installé"
    echo "📦 Installation de pytest-qt..."
    pip install pytest-qt
    echo ""
fi

echo "✅ Dépendances installées"
echo ""

# Lancer les tests
echo "🚀 Lancement des tests de stress..."
echo ""

# Mode par défaut : tous les tests
if [ "$1" == "" ]; then
    pytest tests/test_stress.py -v
    
# Mode répétition
elif [ "$1" == "repeat" ]; then
    TIMES=${2:-10}
    echo "🔁 Répétition des tests $TIMES fois..."
    for i in $(seq 1 $TIMES); do
        echo ""
        echo "=== Run $i/$TIMES ==="
        pytest tests/test_stress.py -v || {
            echo ""
            echo "❌ Test échoué à l'itération $i"
            exit 1
        }
    done
    echo ""
    echo "✅ Tous les tests ont réussi ($TIMES itérations)"
    
# Mode debug
elif [ "$1" == "debug" ]; then
    echo "🐛 Mode debug activé"
    pytest tests/test_stress.py -v -s
    
# Mode spécifique
elif [ "$1" == "test" ]; then
    TEST_NAME=$2
    echo "🎯 Lancement du test: $TEST_NAME"
    pytest "tests/test_stress.py::$TEST_NAME" -v
    
# Aide
else
    echo "Usage:"
    echo "  ./run_tests.sh              # Lancer tous les tests"
    echo "  ./run_tests.sh repeat [N]   # Répéter N fois (défaut: 10)"
    echo "  ./run_tests.sh debug        # Mode debug avec output"
    echo "  ./run_tests.sh test <name>  # Lancer un test spécifique"
    echo ""
    echo "Exemples:"
    echo "  ./run_tests.sh"
    echo "  ./run_tests.sh repeat 20"
    echo "  ./run_tests.sh test test_rapid_close_after_startup"
fi
