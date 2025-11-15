# Script de fusion automatique des branches Claude dans la branche de développement
# Usage: .\fusionne.ps1 <branche-claude>

param(
    [Parameter(Mandatory=$true)]
    [string]$BrancheClaude
)

$ErrorActionPreference = "Stop"

$BRANCH_DEV = "claude/developpement-0157HNsrYJv3uYsHdcEi2fuL"

Write-Host "🔄 Fusion de $BrancheClaude dans $BRANCH_DEV" -ForegroundColor Cyan
Write-Host ""

# Sauvegarder la branche actuelle
$CURRENT_BRANCH = git rev-parse --abbrev-ref HEAD
Write-Host "📍 Branche actuelle: $CURRENT_BRANCH" -ForegroundColor Yellow

# Récupérer les dernières modifications
Write-Host "📥 Récupération des modifications distantes..." -ForegroundColor Cyan
git fetch origin

# Basculer sur la branche de développement
Write-Host "🔀 Basculement sur $BRANCH_DEV..." -ForegroundColor Cyan
git checkout $BRANCH_DEV

# Mettre à jour la branche de développement
Write-Host "⬇️  Mise à jour de la branche de développement..." -ForegroundColor Cyan
try {
    git pull origin $BRANCH_DEV
} catch {
    Write-Host "⚠️  Pas de nouvelles modifications distantes" -ForegroundColor Yellow
}

# Fusionner la branche Claude
Write-Host "🔗 Fusion de $BrancheClaude..." -ForegroundColor Cyan
git merge $BrancheClaude --no-edit

# Pousser les modifications
Write-Host "⬆️  Envoi des modifications vers GitHub..." -ForegroundColor Cyan
git push origin $BRANCH_DEV

# Retourner à la branche d'origine
if ($CURRENT_BRANCH -ne $BRANCH_DEV) {
    Write-Host "↩️  Retour à la branche $CURRENT_BRANCH..." -ForegroundColor Cyan
    git checkout $CURRENT_BRANCH
}

Write-Host ""
Write-Host "✅ Fusion réussie !" -ForegroundColor Green
Write-Host "   $BrancheClaude"
Write-Host "   ⬇️"
Write-Host "   $BRANCH_DEV"
