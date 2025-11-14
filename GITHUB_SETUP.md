# Instructions pour créer le dépôt GitHub

Ce guide explique comment créer le dépôt GitHub et pousser le code.

## Prérequis

Installer GitHub CLI si ce n'est pas déjà fait :
- Windows : `winget install GitHub.cli` ou télécharger depuis https://cli.github.com/
- Linux/Mac : Voir https://github.com/cli/cli#installation

## Étapes

### 1. Se connecter à GitHub

```bash
gh auth login
```

Suivez les instructions pour vous authentifier avec votre compte GitHub.

### 2. Créer le dépôt GitHub

```bash
cd "V:\FoundryOG\python\ollamaFic"

# Créer un nouveau dépôt public sur GitHub
gh repo create ollamaTrad --public --description "Application Python de traduction intelligente avec support multi-providers IA (Ollama, OpenAI, Mistral, Anthropic, DeepL)" --source=. --remote=origin
```

Ou pour un dépôt **privé** :

```bash
gh repo create ollamaTrad --private --description "Application Python de traduction intelligente avec support multi-providers IA (Ollama, OpenAI, Mistral, Anthropic, DeepL)" --source=. --remote=origin
```

### 3. Créer le premier commit

```bash
# Les fichiers sont déjà staged, créer le commit
git commit -m "Initial commit: OllamaTrad - Traduction intelligente multi-providers

Fonctionnalités principales:
- Interface graphique moderne avec tkinter
- Support multi-providers IA (Ollama, OpenAI, Mistral, Anthropic, DeepL)
- Format .got.json v2.0 avec historique et validation
- Traduction par lot avec sélection de champs
- Recherche dans l'arbre JSON
- Boutons DeepL avec compteur de caractères
- Messages d'erreur détaillés pour débogage
- Chat contextuel avec l'IA
- Système de validation des traductions

🤖 Généré avec Claude Code (Anthropic)"
```

### 4. Pousser vers GitHub

```bash
# Pousser la branche actuelle (ollomatrad) vers GitHub
git push -u origin ollomatrad
```

### 5. (Optionnel) Créer la branche main et la définir comme par défaut

Si vous voulez que `main` soit la branche par défaut :

```bash
# Créer la branche main depuis ollomatrad
git checkout -b main
git push -u origin main

# Définir main comme branche par défaut sur GitHub
gh repo edit --default-branch main

# Retourner à ollomatrad si nécessaire
git checkout ollomatrad
```

## Vérification

Vérifiez que le dépôt a été créé :

```bash
gh repo view --web
```

Cette commande ouvrira le dépôt dans votre navigateur.

## Fichiers exclus (dans .gitignore)

Les fichiers suivants sont automatiquement exclus du dépôt :
- `config/settings.json` (contient les clés API)
- `config/translation_config.json` (configuration utilisateur)
- `.claude/settings.local.json` (paramètres Claude Code)
- `*.got.json` (fichiers de données utilisateur)
- `data/` (données utilisateur)
- `conversations/` (conversations sauvegardées)
- `*.log` (logs)
- Fichiers Python compilés (`__pycache__/`, `*.pyc`)
- Environnements virtuels (`venv/`, `env/`)

## Fichiers d'exemple fournis

Les utilisateurs pourront copier ces fichiers pour démarrer :
- `config/settings.example.json` → `config/settings.json`
- `config/translation_config.example.json` → `config/translation_config.json`

## Alternative : Création manuelle sur GitHub.com

Si vous préférez créer le dépôt manuellement :

1. Allez sur https://github.com/new
2. Nommez le dépôt : `ollamaTrad`
3. Ajoutez la description : "Application Python de traduction intelligente avec support multi-providers IA"
4. Choisissez Public ou Private
5. **NE PAS** initialiser avec README, .gitignore ou license (on les a déjà)
6. Cliquez sur "Create repository"
7. Suivez les instructions affichées pour pousser le code existant :

```bash
git remote add origin https://github.com/VOTRE_USERNAME/ollamaTrad.git
git push -u origin ollomatrad
```

## Collaboration

Pour permettre à d'autres de contribuer :

```bash
# Ajouter un collaborateur
gh repo add-collaborator USERNAME

# Créer une invitation de collaboration
gh repo invite USERNAME
```

## Mettre à jour le dépôt après des modifications

```bash
# Ajouter les modifications
git add -A

# Créer un commit
git commit -m "Description des modifications"

# Pousser vers GitHub
git push
```

---

**Note** : Assurez-vous de **JAMAIS** commiter de fichiers contenant des clés API ou des mots de passe !
