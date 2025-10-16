#!/bin/bash
# Script pour copier votre configuration actuelle vers test_config.ini

CONFIG_SOURCE="$HOME/Library/Preferences/Mr. Pipe/Mr. Pipe/gitlab_pipelines_manager.ini"
CONFIG_DEST="test_config.ini"

echo "📋 Copie de la configuration pour les tests"
echo "==========================================="
echo ""

# Vérifier si la config source existe
if [ ! -f "$CONFIG_SOURCE" ]; then
    echo "❌ Configuration source non trouvée: $CONFIG_SOURCE"
    echo ""
    echo "💡 Lancez l'application une fois et configurez-la dans Settings"
    echo "   puis relancez ce script."
    exit 1
fi

# Copier la configuration
cp "$CONFIG_SOURCE" "$CONFIG_DEST"

if [ $? -eq 0 ]; then
    echo "✅ Configuration copiée avec succès vers: $CONFIG_DEST"
    echo ""
    echo "📝 Contenu de la configuration:"
    echo "--------------------------------"
    cat "$CONFIG_DEST"
    echo ""
    echo "⚠️  ATTENTION: Cette configuration contient votre token GitLab"
    echo "   Ne la commitez PAS dans git!"
    echo ""
    echo "🔒 Ajout de test_config.ini au .gitignore..."
    
    # Ajouter au gitignore si pas déjà présent
    if ! grep -q "test_config.ini" .gitignore 2>/dev/null; then
        echo "test_config.ini" >> .gitignore
        echo "✅ test_config.ini ajouté au .gitignore"
    else
        echo "✅ test_config.ini déjà dans .gitignore"
    fi
else
    echo "❌ Erreur lors de la copie"
    exit 1
fi

echo ""
echo "🎉 Configuration prête pour les tests!"
echo "   Vous pouvez maintenant lancer: ./run_tests.sh"
