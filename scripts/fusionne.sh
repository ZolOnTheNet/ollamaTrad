#!/bin/bash
# Script de fusion automatique des branches Claude dans la branche de developpement
# Usage: ./fusionne.sh <branche-claude>

set -e  # Arreter en cas d'erreur

BRANCH_DEV="developpement"
BRANCH_CLAUDE="$1"

# Verifier qu'une branche est fournie
if [ -z "$BRANCH_CLAUDE" ]; then
    echo "[ERREUR] Veuillez specifier la branche Claude a fusionner"
    echo "Usage: ./fusionne.sh <branche-claude>"
    echo "Exemple: ./fusionne.sh claude/fix-safe-directory-warning-01MdoVv6j7to7ph4yW1cw7wf"
    exit 1
fi

echo "========================================="
echo "Fusion de $BRANCH_CLAUDE dans $BRANCH_DEV"
echo "========================================="
echo ""

# Sauvegarder la branche actuelle
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "[INFO] Branche actuelle: $CURRENT_BRANCH"

# Recuperer les dernieres modifications
echo "[INFO] Recuperation des modifications distantes..."
git fetch origin

# Basculer sur la branche de developpement
echo "[INFO] Basculement sur $BRANCH_DEV..."
git checkout "$BRANCH_DEV"

# Mettre a jour la branche de developpement
echo "[INFO] Mise a jour de la branche de developpement..."
git pull origin "$BRANCH_DEV" || echo "[WARN] Pas de nouvelles modifications distantes"

# Fusionner la branche Claude
echo "[INFO] Fusion de $BRANCH_CLAUDE..."
git merge "$BRANCH_CLAUDE" --no-edit

# Pousser les modifications
echo "[INFO] Envoi des modifications vers GitHub..."
git push origin "$BRANCH_DEV"

# Retourner a la branche d'origine
if [ "$CURRENT_BRANCH" != "$BRANCH_DEV" ]; then
    echo "[INFO] Retour a la branche $CURRENT_BRANCH..."
    git checkout "$CURRENT_BRANCH"
fi

echo ""
echo "========================================="
echo "[SUCCES] Fusion reussie !"
echo "  $BRANCH_CLAUDE"
echo "    --> $BRANCH_DEV"
echo "========================================="
