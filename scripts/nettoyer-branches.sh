#!/bin/bash
# Script de nettoyage des anciennes branches Claude
# Usage: ./nettoyer-branches.sh

set -e

BRANCH_DEV="developpement"

echo "🧹 Nettoyage des branches Claude fusionnées"
echo ""

# Sauvegarder la branche actuelle
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 Branche actuelle: $CURRENT_BRANCH"

# Récupérer les dernières informations
echo "📥 Récupération des informations distantes..."
git fetch origin --prune

# Basculer temporairement sur la branche de développement
git checkout "$BRANCH_DEV" > /dev/null 2>&1

# Lister les branches Claude (locales) déjà fusionnées
echo ""
echo "🔍 Recherche des branches fusionnées..."
MERGED_BRANCHES=$(git branch --merged | grep "claude/" | grep -v "$BRANCH_DEV" | sed 's/^[ *]*//' || true)

if [ -z "$MERGED_BRANCHES" ]; then
    echo "✨ Aucune branche fusionnée à nettoyer"
else
    echo "📋 Branches fusionnées trouvées:"
    echo "$MERGED_BRANCHES" | while read branch; do
        echo "   - $branch"
    done

    echo ""
    read -p "❓ Voulez-vous supprimer ces branches locales ? (o/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Oo]$ ]]; then
        echo "$MERGED_BRANCHES" | while read branch; do
            if [ -n "$branch" ]; then
                echo "🗑️  Suppression de $branch..."
                git branch -d "$branch"
            fi
        done
        echo "✅ Branches locales nettoyées"
    else
        echo "⏭️  Nettoyage annulé"
    fi
fi

# Lister les branches distantes
echo ""
echo "🌐 Branches distantes Claude:"
git branch -r | grep "origin/claude/" | grep -v "$BRANCH_DEV" | sed 's|origin/||' | sed 's/^[ ]*//' || echo "   Aucune"

echo ""
read -p "❓ Voulez-vous supprimer des branches distantes ? (o/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Oo]$ ]]; then
    REMOTE_BRANCHES=$(git branch -r | grep "origin/claude/" | grep -v "$BRANCH_DEV" | sed 's|origin/||' | sed 's/^[ ]*//')

    if [ -n "$REMOTE_BRANCHES" ]; then
        echo "$REMOTE_BRANCHES" | while read branch; do
            if [ -n "$branch" ]; then
                echo "🗑️  Suppression distante de $branch..."
                git push origin --delete "$branch" || echo "⚠️  Impossible de supprimer $branch"
            fi
        done
        echo "✅ Branches distantes nettoyées"
    fi
else
    echo "⏭️  Nettoyage des branches distantes annulé"
fi

# Retourner à la branche d'origine
if [ "$CURRENT_BRANCH" != "$BRANCH_DEV" ]; then
    git checkout "$CURRENT_BRANCH" > /dev/null 2>&1
fi

echo ""
echo "✅ Nettoyage terminé !"
