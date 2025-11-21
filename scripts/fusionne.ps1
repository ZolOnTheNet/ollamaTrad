# Script de fusion automatique des branches Claude dans la branche de developpement
# Usage: .\fusionne.ps1 <branche-claude>

param(
    [Parameter(Mandatory=$true)]
    [string]$BrancheClaude
)

$ErrorActionPreference = "Stop"

$BRANCH_DEV = "developpement"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Fusion de $BrancheClaude dans $BRANCH_DEV" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Sauvegarder la branche actuelle
$CURRENT_BRANCH = git rev-parse --abbrev-ref HEAD
Write-Host "[INFO] Branche actuelle: $CURRENT_BRANCH" -ForegroundColor Yellow

# Recuperer les dernieres modifications
Write-Host "[INFO] Recuperation des modifications distantes..." -ForegroundColor Cyan
git fetch origin

# Basculer sur la branche de developpement
Write-Host "[INFO] Basculement sur $BRANCH_DEV..." -ForegroundColor Cyan
git checkout $BRANCH_DEV

# Mettre a jour la branche de developpement
Write-Host "[INFO] Mise a jour de la branche de developpement..." -ForegroundColor Cyan
try {
    git pull origin $BRANCH_DEV
} catch {
    Write-Host "[WARN] Pas de nouvelles modifications distantes" -ForegroundColor Yellow
}

# Fusionner la branche Claude
Write-Host "[INFO] Fusion de $BrancheClaude..." -ForegroundColor Cyan
git merge $BrancheClaude --no-edit

# Pousser les modifications
Write-Host "[INFO] Envoi des modifications vers GitHub..." -ForegroundColor Cyan
git push origin $BRANCH_DEV

# Retourner a la branche d'origine
if ($CURRENT_BRANCH -ne $BRANCH_DEV) {
    Write-Host "[INFO] Retour a la branche $CURRENT_BRANCH..." -ForegroundColor Cyan
    git checkout $CURRENT_BRANCH
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "[SUCCES] Fusion reussie !" -ForegroundColor Green
Write-Host "  $BrancheClaude" -ForegroundColor Green
Write-Host "    --> $BRANCH_DEV" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# Réinitialiser les couleurs de la console
[Console]::ResetColor()
