# 🚀 Guide de Lancement d'OllamaTrad

Ce document explique comment lancer OllamaTrad sur différents systèmes d'exploitation en utilisant les scripts fournis.

---

## 📋 Table des Matières

1. [Linux](#-linux)
2. [macOS](#-macos)
3. [Windows](#-windows)
4. [Installation du Menu (Linux)](#-installation-du-menu-linux)
5. [Résolution de Problèmes](#-résolution-de-problèmes)

---

## 🐧 Linux

### Méthode 1 : Lancement via Script

```bash
# Rendre le script exécutable (une seule fois)
chmod +x ollamaTrad.sh

# Lancer l'application
./ollamaTrad.sh
```

### Méthode 2 : Double-clic (Gestionnaire de fichiers)

1. Faites un **clic droit** sur `ollamaTrad.sh`
2. Sélectionnez **Propriétés** → **Permissions**
3. Cochez **"Autoriser l'exécution du fichier comme un programme"**
4. **Double-cliquez** sur `ollamaTrad.sh`

### Méthode 3 : Terminal Direct

```bash
python3 ollamaTrad.py --gui
```

---

## 🍎 macOS

### Méthode 1 : Double-clic sur le fichier .command

1. **Double-cliquez** sur `ollamaTrad-macos.command`
2. Si macOS bloque l'exécution :
   - Allez dans **Préférences Système** → **Sécurité et confidentialité**
   - Cliquez sur **"Ouvrir quand même"**

### Méthode 2 : Via Terminal

```bash
# Rendre le script exécutable (une seule fois)
chmod +x ollamaTrad-macos.command

# Lancer l'application
./ollamaTrad-macos.command
```

### Méthode 3 : Python Direct

```bash
python3 ollamaTrad.py --gui
```

---

## 🪟 Windows

### Méthode 1 : Double-clic sur le fichier .bat

1. **Double-cliquez** sur `ollamaTrad.bat`
2. Une fenêtre de terminal s'ouvre et vérifie les dépendances
3. L'application se lance automatiquement

### Méthode 2 : Via l'Explorateur

1. Faites un **clic droit** sur `ollamaTrad.bat`
2. Sélectionnez **"Exécuter en tant qu'administrateur"** (si nécessaire)

### Méthode 3 : Invite de Commandes

```batch
REM Se placer dans le répertoire
cd C:\chemin\vers\ollamaFic

REM Lancer l'application
ollamaTrad.bat
```

### Méthode 4 : Python Direct

```batch
python ollamaTrad.py --gui
```

---

## 🎯 Installation du Menu (Linux)

Pour ajouter OllamaTrad au menu d'applications de votre bureau Linux :

### Installation Utilisateur (Recommandé)

```bash
# Copier le fichier .desktop dans le répertoire local
cp ollamaTrad.desktop ~/.local/share/applications/

# Mettre à jour le cache du menu
update-desktop-database ~/.local/share/applications/
```

### Installation Système (Nécessite sudo)

```bash
# Copier le fichier .desktop dans le répertoire système
sudo cp ollamaTrad.desktop /usr/share/applications/

# Mettre à jour le cache du menu
sudo update-desktop-database /usr/share/applications/
```

### Personnalisation du Chemin

Si vous avez déplacé OllamaTrad ailleurs que `/mnt/foundryvtt/FoundryOG/python/ollamaFic`, éditez le fichier `.desktop` :

```bash
nano ollamaTrad.desktop
```

Modifiez les lignes :
- `Exec=/bin/bash -c "cd NOUVEAU_CHEMIN && ./ollamaTrad.sh"`
- `Path=NOUVEAU_CHEMIN`
- `Icon=NOUVEAU_CHEMIN/icon.png`

---

## 🔧 Résolution de Problèmes

### ❌ "Python n'est pas installé"

**Linux/macOS**:
```bash
# Debian/Ubuntu
sudo apt install python3 python3-tk python3-pip

# Fedora
sudo dnf install python3 python3-tkinter python3-pip

# macOS (avec Homebrew)
brew install python-tk@3.12
```

**Windows**:
1. Téléchargez Python depuis https://www.python.org/downloads/windows/
2. **IMPORTANT** : Cochez "Add Python to PATH" pendant l'installation
3. Installez Python 3.9 ou supérieur

---

### ❌ "tkinter n'est pas disponible"

**Linux**:
```bash
sudo apt install python3-tk  # Debian/Ubuntu
sudo dnf install python3-tkinter  # Fedora
```

**macOS**:
```bash
brew install python-tk@3.12
```

**Windows**:
- Réinstallez Python en cochant l'option **"tcl/tk and IDLE"**

---

### ❌ "Dépendances manquantes" (json5, requests, aiohttp)

Les scripts tentent d'installer automatiquement ces dépendances. Si cela échoue :

```bash
# Linux/macOS
python3 -m pip install --user json5 requests aiohttp

# Windows
python -m pip install --user json5 requests aiohttp
```

---

### ❌ "Permission refusée" (Linux/macOS)

```bash
# Rendre les scripts exécutables
chmod +x ollamaTrad.sh
chmod +x ollamaTrad-macos.command
```

---

### ❌ "Le script ne se lance pas en double-clic" (macOS)

1. Faites un **clic droit** sur le fichier `.command`
2. Sélectionnez **"Ouvrir avec"** → **"Terminal"**
3. Cochez **"Toujours ouvrir avec"**

---

### ❌ Windows bloque l'exécution du .bat

1. Faites un **clic droit** sur `ollamaTrad.bat`
2. Sélectionnez **"Propriétés"**
3. Si vous voyez "Ce fichier provient d'un autre ordinateur", cochez **"Débloquer"**
4. Cliquez **"Appliquer"** puis **"OK"**

---

## 📊 Que font les Scripts ?

Tous les scripts effectuent les mêmes vérifications :

### 1. 🔍 Vérification de Python
- Cherche Python 3 sur le système
- Affiche la version trouvée
- Guide l'installation si absent

### 2. 📦 Vérification des Dépendances
- Vérifie `tkinter` (interface graphique)
- Vérifie `json5`, `requests`, `aiohttp`
- Installe automatiquement les dépendances manquantes

### 3. 🚀 Lancement de l'Application
- Change le répertoire courant
- Lance `python ollamaTrad.py --gui`
- Affiche les erreurs éventuelles

---

## 💡 Astuces

### Créer un Raccourci Bureau (Windows)

1. **Clic droit** sur `ollamaTrad.bat`
2. **Envoyer vers** → **Bureau (créer un raccourci)**
3. Renommez le raccourci en "OllamaTrad"

### Créer un Alias (Linux/macOS)

Ajoutez à votre `~/.bashrc` ou `~/.zshrc` :

```bash
alias ollamaTrad='cd /chemin/vers/ollamaFic && ./ollamaTrad.sh'
```

Puis :
```bash
source ~/.bashrc  # ou ~/.zshrc
ollamaTrad  # Lance l'application de n'importe où
```

### Lancement avec un Fichier

Passez le chemin du fichier en argument :

```bash
# Linux/macOS
./ollamaTrad.sh --file mon_fichier.got.json

# Windows
ollamaTrad.bat --file mon_fichier.got.json
```

---

## 📝 Options de Ligne de Commande

```bash
# Mode GUI (par défaut)
python3 ollamaTrad.py --gui

# Mode CLI
python3 ollamaTrad.py

# Charger un fichier directement
python3 ollamaTrad.py --file data.json

# Exécuter une commande
python3 ollamaTrad.py --command "translate /title fr"
```

---

## 🆘 Support

Si vous rencontrez des problèmes non résolus par ce guide :

1. Vérifiez les **messages d'erreur** affichés dans le terminal
2. Consultez les fichiers **`.md`** dans le répertoire pour plus de détails
3. Assurez-vous que **Python 3.9+** est installé
4. Vérifiez que **tkinter** est disponible
5. Essayez de lancer manuellement : `python3 ollamaTrad.py --gui`

---

## ✨ Prochaines Étapes

Une fois l'application lancée :

1. **Fichier** → **Ouvrir** pour charger un `.got.json`
2. **Fichier** → **Options** pour configurer les langues et l'IA
3. Sélectionnez une entrée dans l'arbre
4. Utilisez le formulaire de traduction avec la baguette magique 🪄

---

**Version**: OllamaTrad v3.0
**Date**: 2025-10-16
**Auteur**: Claude (Anthropic)

Bon travail avec OllamaTrad ! 🚀
