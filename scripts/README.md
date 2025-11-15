# Scripts de gestion Git pour OllamaTrad

Ce répertoire contient des scripts pour faciliter la gestion des branches créées par Claude Code.

## 📋 Scripts disponibles

### 🔗 fusionne.sh / fusionne.ps1

Fusionne automatiquement une branche de session Claude dans la branche de développement principale.

**Caractéristiques**:
- Préserve votre branche actuelle
- Met à jour la branche de développement
- Fusionne les modifications
- Pousse vers GitHub
- Retourne à votre branche d'origine

**Usage Ubuntu/Linux**:
```bash
./scripts/fusionne.sh claude/fix-safe-directory-warning-01MdoVv6j7to7ph4yW1cw7wf
```

**Usage PowerShell**:
```powershell
.\scripts\fusionne.ps1 claude/fix-safe-directory-warning-01MdoVv6j7to7ph4yW1cw7wf
```

### 🧹 nettoyer-branches.sh / nettoyer-branches.ps1

Nettoie les branches Claude fusionnées et obsolètes (locales et distantes).

**Caractéristiques**:
- Détecte les branches déjà fusionnées
- Demande confirmation avant suppression
- Nettoie les branches locales
- Nettoie les branches distantes (optionnel)
- Préserve la branche de développement

**Usage Ubuntu/Linux**:
```bash
./scripts/nettoyer-branches.sh
```

**Usage PowerShell**:
```powershell
.\scripts\nettoyer-branches.ps1
```

## 🔄 Workflow recommandé

1. **Claude travaille** sur sa branche de session (ex: `claude/fix-xxx-sessionID`)
2. **Claude pousse** ses modifications vers GitHub
3. **Vous fusionnez** avec le script fusionne :
   ```bash
   ./scripts/fusionne.sh claude/fix-xxx-sessionID
   ```
4. **Après fusion**, nettoyez les anciennes branches :
   ```bash
   ./scripts/nettoyer-branches.sh
   ```

## 💡 Astuces

### Alias Git (optionnel)

Pour simplifier encore plus, ajoutez ces alias à votre `.gitconfig` :

```bash
git config --global alias.fusionne '!f() { ./scripts/fusionne.sh "$1"; }; f'
git config --global alias.nettoyer '!./scripts/nettoyer-branches.sh'
```

Puis utilisez simplement :
```bash
git fusionne claude/fix-xxx-sessionID
git nettoyer
```

### PowerShell Profile (optionnel)

Ajoutez à votre profil PowerShell (`$PROFILE`) :

```powershell
function Merge-ClaudeBranch {
    param([string]$Branch)
    .\scripts\fusionne.ps1 $Branch
}

function Clean-ClaudeBranches {
    .\scripts\nettoyer-branches.ps1
}

Set-Alias fusionne Merge-ClaudeBranch
Set-Alias nettoyer Clean-ClaudeBranches
```

Puis utilisez :
```powershell
fusionne claude/fix-xxx-sessionID
nettoyer
```

## ⚠️ Notes importantes

- La branche de développement est : `claude/developpement-0157HNsrYJv3uYsHdcEi2fuL`
- Les scripts préservent toujours votre branche actuelle
- Les suppressions de branches distantes nécessitent les droits appropriés
- En cas de conflit lors de la fusion, le script s'arrête pour vous laisser résoudre manuellement

## 🐛 Dépannage

### "Permission denied" sur Linux/Ubuntu

```bash
chmod +x scripts/*.sh
```

### "Execution policy" sur PowerShell

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Conflit lors de la fusion

Si un conflit survient :
1. Le script s'arrête automatiquement
2. Résolvez les conflits manuellement
3. Commitez les résolutions : `git commit`
4. Poussez : `git push origin claude/developpement-0157HNsrYJv3uYsHdcEi2fuL`
5. Retournez à votre branche : `git checkout <votre-branche>`
