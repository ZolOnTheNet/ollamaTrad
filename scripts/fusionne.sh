#!/bin/bash
# Script de fusion automatique des branches Claude dans la branche de développement
# Usage: ./fusionne.sh <branche-claude>

set -e  # Arrêter en cas d'erreur

BRANCH_DEV="claude/developpement-0157HNsrYJv3uYsHdcEi2fuL"
BRANCH_CLAUDE="$1"

# Vérifier qu'une branche est fournie
if [ -z "$BRANCH_CLAUDE" ]; then
    echo "❌ Erreur: Veuillez spécifier la branche Claude à fusionner"
    echo "Usage: ./fusionne.sh <branche-claude>"
    echo "Exemple: ./fusionne.sh claude/fix-safe-directory-warning-01MdoVv6j7to7ph4yW1cw7wf"
    exit 1
fi

echo "🔄 Fusion de $BRANCH_CLAUDE dans $BRANCH_DEV"
echo ""

# Sauvegarder la branche actuelle
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 Branche actuelle: $CURRENT_BRANCH"

# Récupérer les dernières modifications
echo "📥 Récupération des modifications distantes..."
git fetch origin

# Basculer sur la branche de développement
echo "🔀 Basculement sur $BRANCH_DEV..."
git checkout "$BRANCH_DEV"

# Mettre à jour la branche de développement
echo "⬇️  Mise à jour de la branche de développement..."
git pull origin "$BRANCH_DEV" || echo "⚠️  Pas de nouvelles modifications distantes"

# Fusionner la branche Claude
echo "🔗 Fusion de $BRANCH_CLAUDE..."
git merge "$BRANCH_CLAUDE" --no-edit

# Pousser les modifications
echo "⬆️  Envoi des modifications vers GitHub..."
git push origin "$BRANCH_DEV"

# Retourner à la branche d'origine
if [ "$CURRENT_BRANCH" != "$BRANCH_DEV" ]; then
    echo "↩️  Retour à la branche $CURRENT_BRANCH..."
    git checkout "$CURRENT_BRANCH"
fi

echo ""
echo "✅ Fusion réussie !"
echo "   $BRANCH_CLAUDE"
echo "   ⬇️"
echo "   $BRANCH_DEV"
