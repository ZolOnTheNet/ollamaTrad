# Commandes Internes - Guide d'utilisation

## Vue d'ensemble

OllamaFic supporte maintenant les **commandes internes** inspirées d'Ollama, accessibles via l'API et compatibles avec tous les providers AI (Ollama, OpenAI, Mistral, Anthropic).

## Commandes disponibles

### 📊 INFORMATION
```bash
/show                    # Affiche les informations détaillées du provider/modèle
/help                    # Aide sur les commandes internes
/? shortcuts            # Aide sur les raccourcis clavier
```

### ⚙️ CONFIGURATION
```bash
/set                     # Affiche toutes les variables de session
/set variable valeur     # Définit une variable de session
/set temperature 0.7     # Exemple: température de génération
/load                    # Liste les modèles disponibles
/load nom_modele         # Change le modèle actuel
```

### 🗂️ GESTION
```bash
/clear                   # Efface l'historique de conversation
/save nom_session        # Sauvegarde la session actuelle
/bye                     # Termine la session
```

## Spécificités par provider

### Ollama (Fonctionnalités complètes)
- `/show` : Informations détaillées du modèle via l'API Ollama
- `/load` : Liste dynamique des modèles installés avec tailles
- Variables de session complètement supportées
- Sauvegarde native des sessions

### OpenAI
- `/show` : Informations avec masquage partiel de la clé API
- `/load` : Liste des modèles GPT disponibles
- Variables simulées localement
- Coût estimé par message affiché

### Mistral AI
- `/show` : Informations basiques avec statut de connexion
- `/load` : Modèles Mistral disponibles
- Variables simulées localement

### Anthropic Claude
- `/show` : Informations basiques
- `/load` : Modèles Claude disponibles
- Variables simulées localement

## Variables de session courantes

### Variables générales
```bash
/set temperature 0.7      # Créativité (0.0 = déterministe, 1.0 = créatif)
/set max_tokens 2000      # Limite de réponse
/set context_length 4096  # Taille du contexte
/set system_prompt "..."  # Prompt système personnalisé
```

### Variables spécifiques Ollama
```bash
/set top_p 0.9           # Échantillonnage nucleus
/set top_k 40            # Échantillonnage top-k
/set repeat_penalty 1.1   # Pénalité de répétition
/set seed 42             # Graine aléatoire pour reproductibilité
```

### Variables métier
```bash
/set context "Livre fantasy"     # Contexte du projet
/set style "Soutenu"             # Style de traduction
/set target_audience "Adultes"   # Public cible
```

## Exemples d'utilisation

### Workflow de configuration
```bash
# Vérifier l'état actuel
/show

# Configurer la session pour un projet spécifique
/set temperature 0.3
/set context "Traduction de dialogues de jeu RPG médiéval"
/set style "Langage soutenu avec archaismes"

# Changer de modèle si nécessaire
/load aya

# Vérifier la configuration
/set

# Démarrer les traductions avec le contexte configuré
ia "Traduis ce dialogue en conservant le style médiéval"
```

### Comparaison de providers
```bash
# Provider Ollama
provider set ollama
/show
/set temperature 0.7
ia "Traduis: 'Hello brave knight'"

# Provider OpenAI
provider set openai
/show
/set temperature 0.7
ia "Traduis: 'Hello brave knight'"

# Comparer les résultats
```

### Optimisation par type de contenu

**Pour dialogues créatifs:**
```bash
/set temperature 0.8
/set top_p 0.9
/set context "Dialogues créatifs avec personnalité"
```

**Pour textes techniques:**
```bash
/set temperature 0.2
/set context "Documentation technique, précision requise"
/set max_tokens 1000
```

**Pour narration:**
```bash
/set temperature 0.6
/set context "Narration littéraire, style immersif"
/set style "Descriptif et évocateur"
```

### Session de travail complète
```bash
# 1. Configuration initiale
/show                                    # État du provider
provider set ollama                      # Choisir Ollama
/load aya                          # Modèle adapté
/set temperature 0.5                     # Équilibre créatif/précis
/set context "Roman fantasy YA"          # Contexte global

# 2. Traduction avec contexte
translate -fr book/chapter1/title        # Traduction standard
ia "Le titre semble trop adulte pour YA" # Dialogue pour ajustement
/set target_audience "Young Adult"       # Ajustement des variables
translate -fr book/chapter1/title        # Nouvelle traduction

# 3. Sauvegarde de session
/save roman_fantasy_ya_session          # Session réutilisable

# 4. Réutilisation ultérieure
/load roman_fantasy_ya_session          # Recharger la configuration
/show                                   # Vérifier la restauration
```

## Intégration avec le système

### Dans l'interface CLI
```bash
# Commandes standard
provider list
ia "Message standard"

# Commandes internes
/show
/set variable valeur
/clear
```

### Dans l'interface GUI
```bash
# Chat interface
/show                    # Commande interne
/ia Message standard     # Dialogue direct
translate -fr path       # Commande de traduction
```

### En sessions de traitement
- Les variables de session persistent durant toute la session
- Elles influencent les traductions automatiques
- Elles sont sauvegardées avec `/save`
- L'historique des commandes internes est tracé

## Avantages des commandes internes

### 🎯 Précision
- Ajustement fin des paramètres de génération
- Contexte persistant entre les traductions
- Configuration adaptée au type de contenu

### 🔄 Consistance
- Variables partagées entre tous les traitements
- Style cohérent sur l'ensemble du projet
- Reproductibilité avec les mêmes paramètres

### ⚡ Efficacité
- Configuration une fois, utilisation multiple
- Changement rapide de modèle
- Sessions sauvegardées et réutilisables

### 🔧 Flexibilité
- Adaptation en temps réel selon les résultats
- Test A/B de différentes configurations
- Optimisation progressive des paramètres

Cette approche transforme OllamaFic en un véritable **atelier de traduction intelligente** où chaque parameter peut être finement ajusté pour obtenir les meilleurs résultats selon le contexte spécifique du projet. 🎨