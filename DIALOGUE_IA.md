# Dialogue Direct avec l'IA - Guide d'utilisation

## Vue d'ensemble

OllamaFic supporte maintenant le **dialogue direct avec l'IA** via plusieurs providers (Ollama, OpenAI, Mistral, Anthropic). Cette fonctionnalité permet de corriger les modèles en dialoguant directement avec eux.

## Commandes disponibles

### Interface CLI

#### Dialogue direct
```bash
ia "Votre message ici"
# Exemple: ia "Comment améliorer cette traduction ?"
```

#### Gestion des providers
```bash
provider list                    # Liste tous les providers
provider set openai             # Change vers OpenAI
provider set ollama             # Change vers Ollama local
provider clear                  # Efface l'historique de conversation
provider history                # Affiche l'historique récent
```

### Interface GUI

#### Dialogue direct
```
/ia Votre message ici
ia Votre message ici
```

#### Configuration des providers
- Cliquez sur le bouton **🤖 Providers** dans la barre de navigation
- Interface à onglets pour configurer chaque provider
- Gestion de l'historique de conversation

## Configuration des providers

### 1. Ollama (Local)
```json
{
  "host": "http://localhost:11434",
  "default_model": "aya"
}
```

### 2. OpenAI
```json
{
  "api_key": "sk-...",
  "api_url": "https://api.openai.com/v1/chat/completions",
  "default_model": "gpt-4"
}
```

### 3. Mistral AI
```json
{
  "api_key": "...",
  "api_url": "https://api.mistral.ai/v1/chat/completions",
  "default_model": "mistral-large-latest"
}
```

### 4. Anthropic Claude
```json
{
  "api_key": "sk-ant-...",
  "api_url": "https://api.anthropic.com/v1/messages",
  "default_model": "claude-3-sonnet-20240229"
}
```

## Cas d'usage typiques

### 1. Correction de traduction récurrente
```bash
# Problème détecté lors d'une traduction
translate -fr book/title

# Dialogue pour comprendre et corriger
ia "Cette traduction semble incorrecte. Peux-tu expliquer pourquoi tu as traduit 'Adventure' par 'Aventure' au lieu de 'Expédition' dans ce contexte de livre fantasy ?"

# Continuer la conversation pour affiner
ia "Comment puis-je t'indiquer le contexte pour de meilleures traductions à l'avenir ?"
```

### 2. Amélioration continue du modèle
```bash
# Définir le contexte du fichier
context "Ce fichier contient les dialogues d'un jeu vidéo RPG médiéval"

# Dialoguer pour ajuster le style
ia "Peux-tu adapter ton style de traduction pour ce contexte spécifique ? Les personnages parlent dans un langage plus soutenu."

# Tester une nouvelle traduction
translate -fr dialogs/merchant/greeting
```

### 3. Gestion multi-provider
```bash
# Comparer les réponses de différents providers
provider set openai
ia "Traduis ce titre en gardant l'ambiance mystérieuse"

provider set mistral
ia "Traduis ce titre en gardant l'ambiance mystérieuse"

# Analyser les différences et choisir le meilleur provider
```

## Fonctionnalités avancées

### Historique de conversation persistant
- L'historique est maintenu par provider
- Maximum 50 messages par défaut
- Effacement possible via `provider clear`

### Contexte automatique
- Le contexte du fichier JSON est automatiquement injecté
- Les métadonnées sont utilisées comme contexte système

### Intégration avec les sessions
- Les dialogues IA sont enregistrés dans les sessions actives
- Traçabilité complète des interactions

## Interface de configuration

L'interface graphique propose un panneau complet de configuration accessible via le bouton **🤖 Providers** :

### Onglets disponibles
1. **Provider Actuel** - Statut et changement de provider
2. **Ollama** - Configuration du serveur local
3. **OpenAI** - Clé API et modèles
4. **Mistral** - Configuration Mistral AI
5. **Conversation** - Gestion de l'historique

### Sécurité
- Les clés API sont masquées lors de la saisie
- Configuration sauvegardée dans `config/settings.json`
- Pas de transmission des clés vers des services tiers non autorisés

## Exemples pratiques

### Workflow typique de correction
1. **Traduction initiale** : `translate -fr book/chapter1/title`
2. **Problème détecté** : Résultat insatisfaisant
3. **Dialogue direct** : `/ia Peux-tu expliquer pourquoi cette traduction ne semble pas appropriée ?`
4. **Contextualisation** : `/ia Le contexte est un livre pour enfants, adapte ton style`
5. **Nouvelle traduction** : `translate -fr book/chapter1/title`
6. **Validation** : Dialogue pour confirmer l'amélioration

### Optimisation multi-fichiers
```bash
# Charger un fichier de données
load game_dialogs.json

# Définir le contexte global
context "Dialogues d'un RPG médiéval-fantastique avec personnages nobles"

# Session de correction collaborative
session start
ia "Je vais traduire plusieurs dialogues. Peux-tu maintenir le style noble et médiéval pour tous ?"

# Traductions avec contexte persistant
translate -fr dialogs/king/speech1
translate -fr dialogs/wizard/prophecy
translate -fr dialogs/knight/oath

# Vérification finale
ia "Les traductions sont-elles cohérentes en style ?"
session end
```

Cette approche permet un véritable **apprentissage collaboratif** avec l'IA pour améliorer progressivement la qualité des traductions et traitements.