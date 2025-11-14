# OllamaTrad

**OllamaTrad** est une application Python de traduction intelligente utilisant plusieurs fournisseurs d'IA (Ollama, OpenAI, Mistral, Anthropic, DeepL). Elle permet de traduire et gérer des fichiers JSON complexes avec un format spécial `.got.json` qui conserve l'original, les traductions, l'historique et l'état de validation.

## 🌟 Fonctionnalités principales

### Interface graphique moderne
- **Formulaire de traduction** : Édition multi-lignes avec auto-ajustement de hauteur
- **Arbre JSON** : Navigation hiérarchique avec code couleur par état de validation
- **Recherche dans l'arbre** : Recherche en temps réel avec navigation entre occurrences (< et >)
- **Chat contextuel** : Dialogue direct avec l'IA pour améliorer les traductions
- **Traduction par lot** : Sélection de champs et traduction en masse
- **Boutons DeepL intelligents** : Affichage du coût en caractères avant traduction

### Support multi-providers IA
- **Ollama** : Modèles locaux (gratuit)
- **OpenAI** : GPT-3.5, GPT-4, etc.
- **Mistral AI** : Mistral Large, etc.
- **Anthropic** : Claude 3 (Sonnet, Opus, Haiku)
- **DeepL** : Traduction professionnelle (gratuit jusqu'à 500K caractères/mois)

### Gestion avancée des traductions
- **Validation** : Marquer les traductions comme validées (protégées contre la retraduction)
- **Historique** : Rollback pour annuler les modifications
- **Amélioration IA** : Baguette magique pour améliorer une traduction existante
- **Détection HTML** : Préservation automatique des balises HTML
- **Traduction partielle** : Garder une partie de la traduction IA

### Format .got.json v2.0
```json
{
  "some": {
    "nested": {
      "field": {
        "ori": "Original text",
        "fr": {
          "text": "Texte traduit",
          "valid": true,
          "history": ["Ancienne traduction"]
        },
        "en": {
          "text": "Translated text",
          "valid": false
        }
      }
    }
  }
}
```

## 🚀 Installation

### Prérequis
- Python 3.8+
- tkinter (généralement inclus avec Python)

### Dépendances
```bash
pip install json5 requests aiohttp
```

### Installation d'Ollama (optionnel, pour IA locale)
```bash
# Télécharger depuis https://ollama.com
# Puis installer un modèle, par exemple :
ollama pull aya
```

## 💻 Utilisation

### Mode GUI (interface graphique)
```bash
python ollamaTrad.py --gui
```

Ou charger directement un fichier :
```bash
python ollamaTrad.py --gui --file mon_fichier.json
```

### Mode CLI (ligne de commande)
```bash
python ollamaTrad.py
```

## ⚙️ Configuration

### Première utilisation
1. Lancez l'application en mode GUI
2. Cliquez sur **⚙️ Options**
3. Configurez :
   - **Langues** : Ajoutez les langues que vous voulez gérer
   - **Configuration IA** : Sélectionnez votre provider et configurez les clés API
   - **DeepL** : Activez DeepL et ajoutez votre clé API (optionnel)
   - **Prompts** : Personnalisez les prompts envoyés à l'IA

### Fichiers de configuration
- `config/translation_config.json` : Langues, prompts, options
- `config/settings.json` : Configuration des providers IA (généré automatiquement)

## 📖 Guide d'utilisation

### 1. Charger un fichier
- **Menu Fichier → Ouvrir** ou glisser-déposer
- Formats supportés : `.json`, `.got.json`
- Conversion automatique en `.got.json` si nécessaire

### 2. Naviguer dans l'arbre JSON
- Cliquez sur une entrée traduisible (icône 📝)
- Le formulaire de traduction s'affiche à droite

### 3. Traduire
- **Bouton langue (ex: FR)** : Traduction automatique avec l'IA configurée
- **Bouton DeepL** : Traduction professionnelle avec DeepL
- **Baguette magique (✨)** : Améliorer une traduction existante
- **Édition manuelle** : Modifier directement le texte traduit

### 4. Validation
- Cliquez sur **✓** pour valider une traduction
- Les traductions validées sont **protégées** contre la retraduction automatique
- Permet de préserver les traductions humaines ou validées

### 5. Traduction par lot
- Sélectionnez une branche dans l'arbre (pas une feuille)
- Le panneau **📦 Traitements par lot** s'affiche
- Cochez les champs à traduire
- Cliquez sur le bouton de langue souhaité
- Le compteur DeepL affiche le nombre de caractères qui seront traduits (excluant les champs validés)

### 6. Rechercher dans l'arbre
- Tapez au moins **3 caractères** dans la zone de recherche
- L'arbre se positionne automatiquement sur la première occurrence
- Utilisez **<** et **>** pour naviguer entre les occurrences
- Le compteur affiche "X / Y" (occurrence actuelle / total)
- Recherche **insensible à la casse** dans le texte de toutes les entrées

### 7. Sauvegarder
- **Menu Fichier → Sauvegarder** ou `Ctrl+S`
- Option **sauvegarde automatique** à la fermeture dans Options → Avancé

## 🎨 Code couleur de l'arbre

- **🔵 Bleu** : Champ vide (non traduit)
- **🟢 Vert** : Champ validé (✓)
- **🟡 Jaune** : Champ traduit mais non validé
- **Gras** : Modification en cours (non sauvegardée)

## 🔧 Structure du projet

```
ollamaTrad/
├── ollamaTrad.py              # Point d'entrée
├── core/
│   ├── got_json_manager.py    # Gestion du format .got.json
│   ├── ai_client.py           # Client IA multi-providers
│   └── i18n.py                # Internationalisation
├── gui/
│   ├── app.py                 # Interface graphique principale
│   ├── translation_form.py    # Formulaire de traduction
│   ├── options_dialog.py      # Fenêtre d'options
│   ├── chat_panel.py          # Panneau de chat avec l'IA
│   ├── batch_translation_form.py  # Formulaire de traduction par lot
│   └── batch_tabs/            # Onglets du formulaire par lot
├── cli/
│   └── commands.py            # Interface CLI
├── utils/
│   └── file_loader.py         # Chargement intelligent de fichiers
└── config/
    ├── translation_config.json  # Configuration utilisateur
    └── settings.json            # Configuration providers IA
```

## 🆘 Aide et dépannage

### L'IA ne répond pas
- **Ollama** : Vérifiez qu'Ollama est lancé (`ollama serve`)
- **OpenAI/Mistral/Anthropic** : Vérifiez votre clé API dans Options
- **DeepL** : Vérifiez votre clé API et votre quota de caractères

### Messages d'erreur détaillés
L'application affiche maintenant des messages d'erreur **ultra-détaillés** dans la console avec :
- URL appelée et modèle utilisé
- Timeout configuré
- Payload JSON complet
- Réponse exacte du serveur
- Traceback complet pour le débogage

Exemple :
```
============================================================
❌ ERREUR OLLAMA - DÉTAILS COMPLETS
============================================================
📍 URL appelée: http://localhost:11434/api/chat
🔧 Modèle: aya
📊 Status HTTP: 404
📋 Réponse serveur: {"error":"model not found"}
============================================================
```

### Les traductions validées sont retraduits
- ✅ **Corrigé** : Les champs validés sont maintenant **protégés** contre la retraduction automatique

### Le compteur DeepL affiche un nombre incorrect
- ✅ **Corrigé** : Le compteur exclut maintenant les champs validés et déjà traduits

### Interface ne s'affiche pas
- Vérifiez que tkinter est installé : `python -m tkinter`
- Sur Linux : `sudo apt-get install python3-tk`

## 📝 Licence

Projet personnel - Libre d'utilisation

## 🙏 Crédits

- Interface graphique : tkinter
- IA : Ollama, OpenAI, Mistral AI, Anthropic, DeepL
- Développé avec l'aide de **Claude Code** (Anthropic)
