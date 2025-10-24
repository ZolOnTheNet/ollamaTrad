# Fonctionnalité : Commandes Console dans le Chat

## Description

Le chat intègre maintenant un système de commandes console inspiré de l'interface CLI. Les commandes commencent par `/` et permettent de contrôler l'application directement depuis le chat.

## Utilisation

### Syntaxe des commandes

```
/<commande> [arguments]
```

### Commande par défaut

Si vous tapez un message **sans** le préfixe `/`, il est automatiquement traité comme `/ia <votre message>`.

**Exemples** :
- `Coucou, c'est moi` → Équivalent à `/ia Coucou, c'est moi`
- `Comment améliorer cette traduction ?` → Équivalent à `/ia Comment améliorer cette traduction ?`

## Commandes disponibles

### 1. Navigation : `/cd`

Change le chemin actuel et met à jour la sélection dans l'arbre.

#### Syntaxe

```
/cd <chemin>
/cd
```

#### Exemples

```
# Naviguer vers un chemin spécifique
/cd app/title

# Naviguer avec "/" initial (également accepté)
/cd /entries/monster1/name

# Afficher le chemin actuel
/cd
```

#### Comportement

1. **Avec un chemin** :
   - Vérifie que le chemin existe dans le fichier .got.json
   - Trouve l'item correspondant dans l'arbre
   - Sélectionne l'item dans l'arbre (avec scroll automatique)
   - Met à jour le formulaire de traduction
   - Met à jour le contexte du chat

2. **Sans argument** :
   - Affiche le chemin actuel dans le chat

#### Messages

##### Succès
```
[10:30:15] > /cd app/title
[10:30:15] < ✓ Navigué vers: app/title
```

##### Erreurs
```
# Chemin inexistant
[10:31:00] > /cd app/wrong
[10:31:00] < ❌ Erreur: Chemin non trouvé: app/wrong

# Aucun fichier chargé
[10:32:00] > /cd app/title
[10:32:00] < ❌ Erreur: Aucun fichier chargé
```

### 2. Dialogue avec l'IA : `/ia`

Dialogue direct avec le provider IA actuel (Ollama, OpenAI, Mistral, Anthropic).

#### Syntaxe

```
/ia <message>
<message>  # Sans "/" = commande par défaut
```

#### Exemples

```
# Explicite
/ia Comment améliorer cette traduction ?

# Implicite (recommandé)
Comment améliorer cette traduction ?

# Questions contextuelles
Peux-tu me suggérer une meilleure formulation ?
Quelle est la différence entre ces deux traductions ?
```

#### Comportement

1. Affiche un message "💭 Réflexion en cours..."
2. Envoie le message au provider IA actuel
3. Affiche la réponse complète dans le chat
4. Utilise un timeout de 60 secondes

#### Messages

##### Dialogue normal
```
[10:40:00] > Comment améliorer cette traduction ?
[10:40:00] < 💭 Réflexion en cours...
[10:40:03] < Pour améliorer cette traduction, je suggère...
```

##### Erreur
```
[10:41:00] > Dis-moi quelque chose
[10:41:00] < 💭 Réflexion en cours...
[10:41:30] < ❌ Erreur: Erreur de dialogue: Connection timeout
```

### 3. Commandes internes : `/show`, `/set`, `/load`, etc.

Commandes internes du provider IA (Ollama-style).

#### Syntaxe

```
/<commande_interne> [arguments]
```

#### Commandes supportées

| Commande | Description | Exemple |
|----------|-------------|---------|
| `/show` | Affiche les informations du provider/modèle actuel | `/show` |
| `/set` | Définit ou affiche les variables de session | `/set temperature 0.7` |
| `/load` | Change le modèle actuel | `/load aya` |
| `/clear` | Efface l'historique de conversation | `/clear` |
| `/save` | Sauvegarde la session | `/save session_name` |
| `/help` | Aide sur les commandes internes | `/help` |

#### Exemples

```
# Afficher le provider actuel
/show

# Changer la température
/set temperature 0.8

# Charger un autre modèle
/load mistral

# Effacer l'historique
/clear

# Aide
/help
```

#### Comportement

1. Affiche un message "🔧 Exécution: <commande>"
2. Envoie la commande au provider IA
3. Affiche la réponse dans le chat

#### Messages

```
[10:50:00] > /show
[10:50:00] < 🔧 Exécution: /show
[10:50:01] < Model: aya
             Provider: ollama
             Temperature: 0.7
             Context: 4096

[10:51:00] > /set temperature 0.9
[10:51:00] < 🔧 Exécution: /set temperature 0.9
[10:51:01] < ✓ Temperature set to 0.9
```

## Cas d'usage

### 1. Navigation rapide

**Scénario** : Vous travaillez sur plusieurs entrées et voulez naviguer rapidement.

```
/cd entries/monster1
# Traduire quelque chose...
/cd entries/monster2
# Traduire quelque chose...
/cd app/title
```

### 2. Dialogue contextuel

**Scénario** : Vous avez une question sur la traduction actuelle.

```
# Sélectionner une entrée dans l'arbre
# Puis dans le chat:
Cette traduction est-elle idiomatique en français ?
Peux-tu suggérer une alternative plus naturelle ?
```

### 3. Configuration du modèle

**Scénario** : Ajuster les paramètres de l'IA pour une traduction spécifique.

```
/show
# Voir les paramètres actuels

/set temperature 0.3
# Plus déterministe pour traductions techniques

# Traduire...

/set temperature 0.9
# Plus créatif pour traductions littéraires
```

### 4. Workflow mixte

**Scénario** : Combiner navigation, traduction et dialogue.

```
/cd entries/spell1/description
# Formulaire se met à jour automatiquement

# Cliquer sur 🪄 pour traduire

# Vérifier le résultat dans le chat
Est-ce que cette traduction préserve le sens magique du sort ?

# Ajuster si nécessaire
/cd entries/spell2/description
```

## Architecture technique

### Flux de commande

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Utilisateur tape dans le chat                           │
│    Exemple: "/cd app/title"                                │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. chat_panel._on_send_message()                           │
│    - Affiche le message dans le chat                       │
│    - Appelle on_user_message callback                      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. app_v2._on_user_chat_message()                          │
│    - Détecte le "/" au début                               │
│    - Parse la commande et les arguments                    │
│    - Route vers le handler approprié                       │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┴────────────┬────────────────┐
    │                         │                │
    ▼                         ▼                ▼
┌─────────────┐  ┌──────────────────┐  ┌────────────────┐
│ _handle_cd  │  │ _handle_ia       │  │ _handle_internal│
│ _command()  │  │ _command()       │  │ _command()     │
└─────────────┘  └──────────────────┘  └────────────────┘
    │                         │                │
    ▼                         ▼                ▼
┌─────────────┐  ┌──────────────────┐  ┌────────────────┐
│ - Valide    │  │ - Thread async   │  │ - Thread async │
│   le chemin │  │ - ai_client.chat │  │ - execute_     │
│ - Sélectionne│  │ - Affiche       │  │   internal_    │
│   dans arbre│  │   réponse       │  │   command()    │
│ - Met à jour│  └──────────────────┘  └────────────────┘
│   formulaire│
└─────────────┘
```

### Détection de commande

```python
def _on_user_chat_message(self, message: str):
    if message.startswith("/"):
        # Parser la commande
        parts = message.split(None, 1)
        command = parts[0][1:].lower()  # Enlever "/" et minuscules
        args = parts[1] if len(parts) > 1 else ""

        # Router
        if command == "cd":
            self._handle_cd_command(args)
        elif command == "ia":
            self._handle_ia_command(args)
        else:
            self._handle_internal_command(message)
    else:
        # Default: /ia
        self._handle_ia_command(message)
```

### Navigation (/cd)

```python
def _handle_cd_command(self, path: str):
    # Nettoyer le chemin
    path = path.strip().lstrip("/")

    # Vérifier existence
    entry = self.got_manager._get_entry_by_path(path)

    # Trouver item d'arbre
    tree_item = self.path_to_tree_item.get(path)

    # Sélectionner
    self.tree.selection_set(tree_item)
    self.tree.see(tree_item)

    # _on_tree_select() est déclenché automatiquement
    # → Met à jour formulaire et contexte
```

### Dialogue (/ia)

```python
def _handle_ia_command(self, message: str):
    def run_chat():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            self.ai_client.chat(message, timeout=60)
        )

        loop.close()
        self.root.after(0, lambda r=result:
            self._on_chat_response_success(r))

    thread = threading.Thread(target=run_chat, daemon=True)
    thread.start()
```

## Fichiers modifiés

### gui/app_v2.py

**Ajouts** :
- `_on_user_chat_message()` : Détection et routing des commandes
- `_handle_cd_command()` : Navigation dans l'arbre
- `_handle_ia_command()` : Dialogue avec l'IA
- `_handle_internal_command()` : Commandes internes
- `_on_command_response_success()` : Affichage réponse commandes

**Lignes** : 853-1019

### gui/chat_panel.py

**Modifications** :
- Callback `on_user_message` déjà présent (ligne 27, 275)
- Aucune modification nécessaire

## Avantages

✅ **Interface unifiée** : Console et GUI partagent les mêmes commandes

✅ **Productivité** : Navigation rapide sans cliquer dans l'arbre

✅ **Flexibilité** : Dialogue contextuel pendant la traduction

✅ **Découvrabilité** : Les utilisateurs CLI se sentent à l'aise

✅ **Cohérence** : Même syntaxe qu'en mode console

## Limitations

1. **Autocomplétion** : Pas d'autocomplétion des chemins (à implémenter)
2. **Historique** : Pas de navigation dans l'historique des commandes (↑/↓)
3. **Alias** : Pas de raccourcis pour les commandes fréquentes
4. **Validation** : Pas de validation des chemins avant d'envoyer

## Améliorations futures

### 1. Autocomplétion

```python
# Dans chat_panel.py
def _on_tab_key(self, event):
    """Autocomplete les chemins et commandes"""
    text = self.input_entry.get()
    if text.startswith("/cd "):
        # Proposer les chemins disponibles
        suggestions = self._get_path_suggestions(text[4:])
        # Afficher popup avec suggestions
```

### 2. Historique de commandes

```python
# Dans chat_panel.py
self.command_history = []
self.history_index = -1

def _on_arrow_up(self, event):
    """Naviguer dans l'historique (↑)"""
    if self.history_index < len(self.command_history) - 1:
        self.history_index += 1
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, self.command_history[self.history_index])
```

### 3. Alias

```python
# Dans app_v2.py
COMMAND_ALIASES = {
    "ls": "cd",      # ls = afficher chemin actuel
    "goto": "cd",    # goto = alias pour cd
    "ask": "ia",     # ask = alias pour ia
}

def _resolve_alias(self, command: str) -> str:
    return COMMAND_ALIASES.get(command, command)
```

### 4. Commandes supplémentaires

| Commande | Description |
|----------|-------------|
| `/ls` | Liste les enfants du nœud actuel |
| `/parent` | Remonte au parent |
| `/save` | Sauvegarde le fichier |
| `/undo` | Annule la dernière opération |
| `/redo` | Refait l'opération annulée |

## Comparaison Console vs Chat

| Aspect | Console CLI | Chat GUI |
|--------|-------------|----------|
| **Commandes** | ✅ Toutes supportées | ✅ Sous-ensemble + navigation |
| **Navigation** | `cd <path>` | `/cd <path>` |
| **Dialogue IA** | `ia "message"` | `/ia message` ou `message` |
| **Feedback** | Texte console | Messages colorés dans chat |
| **Contexte** | Chemin courant affiché | Contexte du chat + arbre |
| **Interface** | Ligne de commande | Champ de saisie + historique |

## Exemples de workflows

### Workflow 1 : Traduction batch

```
/cd entries/monster1
# Traduire avec 🪄

/cd entries/monster2
# Traduire avec 🪄

/cd entries/monster3
# Traduire avec 🪄

# Demander une révision globale
Peux-tu vérifier la cohérence des traductions entre monster1, 2 et 3 ?
```

### Workflow 2 : Dialogue et ajustement

```
# Sélectionner une entrée dans l'arbre

# Cliquer sur 🪄 FR pour traduire

# Vérifier dans le chat
La traduction préserve-t-elle le ton original ?

# Si réponse négative, réessayer avec paramètres différents
/set temperature 0.5
# Cliquer à nouveau sur 🪄
```

### Workflow 3 : Exploration et traduction

```
/cd app
# Voir le formulaire pour app

Est-ce que je devrais traduire le nom de l'app ?

# Selon la réponse, traduire ou pas

/cd app/description
# Traduire la description
```

Cette fonctionnalité rend le chat beaucoup plus puissant et transforme l'interface en un véritable environnement de travail interactif !
