# Script de nettoyage des anciennes branches Claude
# Usage: .\nettoyer-branches.ps1

$ErrorActionPreference = "Stop"

$BRANCH_DEV = "developpement"

Write-Host "🧹 Nettoyage des branches Claude fusionnées" -ForegroundColor Cyan
Write-Host ""

# Sauvegarder la branche actuelle
$CURRENT_BRANCH = git rev-parse --abbrev-ref HEAD
Write-Host "📍 Branche actuelle: $CURRENT_BRANCH" -ForegroundColor Yellow

# Récupérer les dernières informations
Write-Host "📥 Récupération des informations distantes..." -ForegroundColor Cyan
git fetch origin --prune

# Basculer temporairement sur la branche de développement
git checkout $BRANCH_DEV | Out-Null

# Lister les branches Claude (locales) déjà fusionnées
Write-Host ""
Write-Host "🔍 Recherche des branches fusionnées..." -ForegroundColor Cyan
$MERGED_BRANCHES = git branch --merged | Where-Object { $_ -match "claude/" -and $_ -notmatch $BRANCH_DEV } | ForEach-Object { $_.Trim(' *') }

if ($MERGED_BRANCHES.Count -eq 0) {
    Write-Host "✨ Aucune branche fusionnée à nettoyer" -ForegroundColor Green
} else {
    Write-Host "📋 Branches fusionnées trouvées:" -ForegroundColor Cyan
    $MERGED_BRANCHES | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }

    Write-Host ""
    $response = Read-Host "❓ Voulez-vous supprimer ces branches locales ? (o/N)"

    if ($response -match "^[Oo]$") {
        $MERGED_BRANCHES | ForEach-Object {
            Write-Host "🗑️  Suppression de $_..." -ForegroundColor Red
            git branch -d $_
        }
        Write-Host "✅ Branches locales nettoyées" -ForegroundColor Green
    } else {
        Write-Host "⏭️  Nettoyage annulé" -ForegroundColor Yellow
    }
}

# Lister les branches distantes
Write-Host ""
Write-Host "🌐 Branches distantes Claude:" -ForegroundColor Cyan
$REMOTE_BRANCHES = git branch -r | Where-Object { $_ -match "origin/claude/" -and $_ -notmatch $BRANCH_DEV } | ForEach-Object { $_ -replace "origin/", "" -replace "^\s+", "" }

if ($REMOTE_BRANCHES.Count -eq 0) {
    Write-Host "   Aucune" -ForegroundColor Gray
} else {
    $REMOTE_BRANCHES | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
}

Write-Host ""
$response = Read-Host "❓ Voulez-vous supprimer des branches distantes ? (o/N)"

if ($response -match "^[Oo]$") {
    if ($REMOTE_BRANCHES.Count -gt 0) {
        $REMOTE_BRANCHES | ForEach-Object {
            Write-Host "🗑️  Suppression distante de $_..." -ForegroundColor Red
            try {
                git push origin --delete $_
            } catch {
                Write-Host "⚠️  Impossible de supprimer $_" -ForegroundColor Yellow
            }
        }
        Write-Host "✅ Branches distantes nettoyées" -ForegroundColor Green
    }
} else {
    Write-Host "⏭️  Nettoyage des branches distantes annulé" -ForegroundColor Yellow
}

# Retourner à la branche d'origine
if ($CURRENT_BRANCH -ne $BRANCH_DEV) {
    git checkout $CURRENT_BRANCH | Out-Null
}

Write-Host ""
Write-Host "✅ Nettoyage terminé !" -ForegroundColor Green

# Réinitialiser les couleurs de la console
[Console]::ResetColor()
