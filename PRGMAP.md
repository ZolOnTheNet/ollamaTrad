# PRGMAP.md - Architecture du Programme OllamaFic

## Vue d'ensemble du projet

OllamaFic est une application Python sophistiquée conçue pour le traitement intelligent de fichiers JSON utilisant plusieurs fournisseurs d'IA (Ollama, OpenAI, Mistral, Anthropic). Elle propose des interfaces CLI et GUI avec un système de navigation similaire à un système de fichiers pour les structures JSON.

## Structure des répertoires

```
ollamaFic/
├── ollamaTrad.py              # Point d'entrée principal avec parsing d'arguments
├── core/                      # Modules centraux
│   ├── json_manager.py        # Gestionnaire JSON avec navigation filesystem
│   ├── ai_client.py           # Client IA unifié multi-providers
│   ├── ollama_client.py       # Client Ollama spécialisé (legacy)
│   ├── operation_history.py   # Système d'historique avancé avec undo/redo
│   ├── metadata.py            # Gestionnaire de métadonnées (legacy)
│   └── i18n.py                # Système d'internationalisation
├── cli/                       # Interface ligne de commande
│   └── commands.py            # Commandes CLI et logique d'interaction
├── gui/                       # Interface graphique
│   └── app.py                 # Application Tkinter avec configuration providers
├── config/                    # Configuration
│   └── settings.json          # Configuration multi-providers
├── translations/              # Fichiers de traduction
│   ├── fr.json, en.json, es.json, de.json, it.json
├── data/                      # Données utilisateur
│   ├── metadata/, sessions/, history/, snapshots/
└── conversations/             # Conversations sauvegardées
```

---

## Module: core/json_manager.py

### Classe: JsonPath
**Emplacement**: `core/json_manager.py:10-34`

**Attributs**:
- `path: str` - Chemin dans la structure JSON

**Méthodes**:
- `__post_init__()` - Nettoie le chemin en supprimant les '/' de début/fin
- `parts: List[str]` (property) - Divise le chemin en segments
- `parent: JsonPath` (property) - Retourne le chemin parent
- `name: str` (property) - Retourne le nom du dernier segment
- `__str__()` - Format d'affichage avec '/' initial

**Usage**: Représente un chemin dans un JSON comme un système de fichiers. Utilisé pour la navigation hiérarchique.

### Classe: JsonManager
**Emplacement**: `core/json_manager.py:35-493`

**Attributs principaux**:
- `file_path: Path` - Chemin du fichier JSON chargé
- `data: Dict[str, Any]` - Données JSON actuelles
- `original_data: Dict[str, Any]` - Sauvegarde des données originales
- `current_path: str` - Répertoire courant dans la structure JSON
- `modifications: List[Dict]` - Historique des modifications
- `modified_paths: Dict[str, str]` - État des modifications par chemin
- `pending_modifications: Dict[str, Any]` - Modifications en attente
- `operation_hook: Callable` - Hook pour le système d'historique

**Méthodes principales**:
- `load_file(file_path: str)` - Charge un fichier JSON/JSON5
- `save_file(file_path: Optional[str])` - Sauvegarde le JSON
- `navigate_to_path(json_path)` - Navigation vers un chemin spécifique
- `list_contents(json_path)` - Liste le contenu (équivalent `ls`)
- `get_value(json_path)` - Récupère une valeur à un chemin
- `set_value(json_path, value)` - Définit une valeur avec historique
- `search(pattern, search_keys, search_values)` - Recherche par regex
- `_expand_wildcards(path)` - Expansion des jokers (*, ?, #)
- `set_pending_modification(path, value)` - Marque une modification en attente
- `commit_pending_modification(path)` - Applique une modification en attente

**Usage**: Gestionnaire central pour manipuler les données JSON avec un paradigme de navigation filesystem. Supporte les jokers et la gestion des modifications en attente.

---

## Module: core/ai_client.py

### Classe Abstraite: AIProvider
**Emplacement**: `core/ai_client.py:14-203`

**Attributs**:
- `config: Dict[str, Any]` - Configuration du provider
- `conversation_history: List[Dict]` - Historique des conversations
- `session_variables: Dict[str, Any]` - Variables de session (/set)
- `current_model: str` - Modèle actuel

**Méthodes abstraites**:
- `chat(message, system_prompt)` - Communication asynchrone avec l'IA
- `check_connection()` - Vérification de la connexion

**Méthodes de commandes internes**:
- `execute_internal_command(command)` - Exécute les commandes /
- `cmd_set(args)` - Gestion des variables (/set)
- `cmd_show(args)` - Affichage des informations (/show)
- `cmd_load(args)` - Changement de modèle (/load)
- `cmd_save(args)` - Sauvegarde de session (/save)
- `cmd_clear()` - Effacement de l'historique (/clear)
- `cmd_help(args)` - Aide des commandes internes (/help)

**Usage**: Interface commune pour tous les providers IA avec système de commandes internes unifié.

### Classe: OllamaProvider
**Emplacement**: `core/ai_client.py:205-384`
**Hérite de**: AIProvider

**Attributs spécifiques**:
- `host: str` - URL du serveur Ollama
- `timeout: int` - Timeout des requêtes

**Méthodes spécifiques**:
- `_update_preferred_model()` - Met à jour le modèle avec logique de préférence pour aya
- `cmd_show(args)` - Version étendue avec détails du modèle Ollama
- `cmd_load(args)` - Vérification de l'existence des modèles via API

**Usage**: Provider pour Ollama local avec gestion intelligente des modèles et intégration API native.

### Classe: OpenAIProvider
**Emplacement**: `core/ai_client.py:386-497`
**Hérite de**: AIProvider

**Attributs spécifiques**:
- `api_url: str` - URL de l'API OpenAI
- `api_key: str` - Clé API
- `model: str` - Modèle GPT

**Usage**: Provider pour OpenAI GPT avec gestion des clés API et modèles disponibles.

### Classe: MistralProvider
**Emplacement**: `core/ai_client.py:499-579`
**Hérite de**: AIProvider

**Usage**: Provider pour Mistral AI avec API compatible OpenAI.

### Classe: AnthropicProvider
**Emplacement**: `core/ai_client.py:582-664`
**Hérite de**: AIProvider

**Particularités**:
- Format d'API différent (system prompt séparé)
- Headers spécifiques (`x-api-key`, `anthropic-version`)

**Usage**: Provider pour Claude d'Anthropic avec format API spécifique.

### Classe: AIClient
**Emplacement**: `core/ai_client.py:666-794`

**Attributs**:
- `config_path: Path` - Chemin du fichier de configuration
- `config: Dict` - Configuration chargée
- `current_provider: AIProvider` - Provider actuel
- `providers: Dict[str, AIProvider]` - Tous les providers disponibles

**Méthodes**:
- `load_config()` - Charge la configuration depuis settings.json
- `init_providers()` - Initialise tous les providers configurés
- `set_provider(provider_name)` - Change le provider actuel
- `chat(message, system_prompt)` - Délègue au provider actuel
- `execute_internal_command(command)` - Exécute les commandes internes
- `update_provider_config(provider_name, config)` - Met à jour la config

**Usage**: Gestionnaire unifié pour tous les providers IA avec changement à chaud et persistance de configuration.

---

## Module: core/operation_history.py

### Classe: OperationSnapshot
**Emplacement**: `core/operation_history.py:15-22`

**Attributs**:
- `path: str` - Chemin modifié
- `value_before: Any` - Valeur avant modification
- `value_after: Any` - Valeur après modification
- `timestamp: str` - Timestamp de l'opération
- `operation_id: str` - ID de l'opération parente

**Usage**: Snapshot d'une modification pour système undo/redo.

### Classe: DetailedOperation
**Emplacement**: `core/operation_history.py:24-46`

**Attributs**:
- `operation_id: str` - Identifiant unique
- `operation_type: str` - Type (translate, process, ia_chat, etc.)
- `user_input: Dict` - Paramètres de l'opération
- `provider_info: Dict` - Informations du provider utilisé
- `session_variables: Dict` - Variables au moment de l'opération
- `affected_paths: List[OperationSnapshot]` - Données pour undo/redo
- `result: Any` - Résultat de l'opération
- `execution_time_ms: float` - Temps d'exécution

**Usage**: Opération complète avec toutes les métadonnées pour navigation et undo/redo.

### Classe: SessionHistory
**Emplacement**: `core/operation_history.py:48-71`

**Attributs**:
- `session_id: str` - Identifiant unique de session
- `file_path: str` - Fichier traité
- `operations: List[DetailedOperation]` - Historique ordonné
- `current_position: int` - Position actuelle (-1 = à jour)
- `tags: List[str]` - Tags de la session
- `context: str` - Contexte global

**Usage**: Historique complet d'une session avec navigation et métadonnées.

### Classe: OperationHistoryManager
**Emplacement**: `core/operation_history.py:72-542`

**Attributs**:
- `data_dir: Path` - Répertoire de données
- `history_dir: Path` - Répertoire des historiques
- `snapshots_dir: Path` - Répertoire des snapshots
- `current_session: SessionHistory` - Session active
- `max_operations_in_memory: int` - Limite mémoire

**Méthodes principales**:
- `start_session(file_path, session_id)` - Démarre une nouvelle session
- `record_operation(operation_type, user_input, affected_data, ...)` - Enregistre une opération
- `undo_last_operation()` - Annule la dernière opération
- `redo_next_operation()` - Refait une opération annulée
- `jump_to_operation(operation_id)` - Navigue à une opération spécifique
- `get_operation_history(limit)` - Récupère l'historique avec métadonnées

**Usage**: Gestionnaire avancé d'historique avec undo/redo complet et navigation temporelle.

---

## Module: core/i18n.py

### Classe: I18n
**Emplacement**: `core/i18n.py:12-223`

**Attributs**:
- `current_locale: str` - Langue actuelle
- `translations: Dict[str, Dict[str, str]]` - Traductions par langue
- `fallback_locale: str` - Langue de fallback

**Méthodes**:
- `load_translations()` - Charge traductions intégrées + fichiers externes
- `set_locale(locale)` - Change la langue actuelle
- `_(key, **kwargs)` - Traduit une clé avec interpolation
- `add_translation(locale, key, value)` - Ajoute une traduction dynamiquement

**Usage**: Système d'internationalisation sans dépendances externes avec support français, anglais, espagnol, allemand, italien.

---

## Module: cli/commands.py

### Classe: CLIInterface
**Emplacement**: `cli/commands.py:16-946`

**Attributs**:
- `json_manager: JsonManager` - Gestionnaire JSON
- `ollama_client: OllamaClient` - Client Ollama legacy
- `ai_client: AIClient` - Client IA unifié
- `history_manager: OperationHistoryManager` - Gestionnaire d'historique
- `current_session: str` - Session active
- `current_path: str` - Chemin courant CLI

**Méthodes de commandes**:
- `cmd_load(file_path)` - Charge un fichier JSON
- `cmd_ls(path)` - Liste le contenu (équivalent ls Unix)
- `cmd_cat(path)` - Affiche le contenu (équivalent cat Unix)
- `cmd_cd(path)` - Change le répertoire courant
- `cmd_search(pattern)` - Recherche par regex
- `cmd_translate(options, path, model)` - Traduction avec nouvelle syntaxe
- `cmd_validate(action)` - Gestion des modifications (list/commit/reject)
- `cmd_process(path, instruction, model)` - Traitement avec instruction
- `cmd_ia(message)` - Dialogue direct avec IA
- `cmd_provider(action, provider_name)` - Gestion des providers
- `cmd_internal(command)` - Commandes internes (/, /set, /show)
- `cmd_undo(steps)` - Annulation d'opérations
- `cmd_history(count)` - Affichage de l'historique

**Méthodes utilitaires**:
- `get_preferred_model()` - Récupère le modèle préféré (aya en priorité)
- `parse_and_execute(command_line)` - Parser de commandes avec support guillemets
- `run_interactive()` - Boucle interactive avec prompt contextuel

**Usage**: Interface CLI complète avec commandes Unix-like et intégration IA avancée.

---

## Module: gui/app.py

### Classe: OllamaTradGUI
**Emplacement**: `gui/app.py:25-fin`

**Attributs principaux**:
- `root: tk.Tk` - Fenêtre principale Tkinter
- `json_manager: JsonManager` - Gestionnaire JSON
- `ai_client: AIClient` - Client IA unifié
- `json_tree: ttk.Treeview` - Arbre de navigation JSON
- `path_states: Dict` - États des modifications avec tags visuels
- `batch_processing: bool` - État du traitement par lot

**Méthodes d'interface**:
- `setup_ui()` - Configuration complète de l'interface
- `setup_tree_colors()` - Configuration des couleurs d'état
- `open_file()` - Dialogue d'ouverture de fichier
- `save_file()` - Sauvegarde avec gestion des modifications
- `update_json_tree()` - Mise à jour de l'arbre avec coloration

**Méthodes de traitement**:
- `quick_translate(lang)` - Traduction rapide vers une langue
- `quick_process(instruction)` - Traitement avec instruction prédéfinie
- `execute_chat_command(command)` - Exécution de commandes chat
- `open_provider_config()` - Interface de configuration des providers

**Méthodes d'historique**:
- `undo_operation()` - Interface d'annulation
- `redo_operation()` - Interface de rétablissement
- `show_history()` - Dialogue d'historique avec navigation

**Usage**: Interface graphique complète avec workflow streamlined, configuration providers et système de coloration d'état.

---

## Module: core/ollama_client.py (Legacy)

### Classe: OllamaClient
**Emplacement**: `core/ollama_client.py:7-fin`

**Attributs**:
- `host: str` - URL du serveur Ollama
- `session: aiohttp.ClientSession` - Session HTTP asynchrone

**Méthodes**:
- `chat_sync(model, messages)` - Communication synchrone
- `chat_async(model, messages)` - Communication asynchrone
- `translate_text(text, source_lang, target_lang, model, context)` - Traduction
- `process_json_field(field_content, instruction, model, context)` - Traitement
- `get_available_models()` - Liste des modèles
- `check_connection()` - Vérification de connexion

**Usage**: Client Ollama spécialisé maintenu pour compatibilité. Utilisation recommandée via AIClient.

---

## Configuration et fichiers externes

### config/settings.json
**Structure**:
```json
{
  "ai_providers": {
    "default_provider": "ollama",
    "ollama": {
      "host": "http://localhost:11434",
      "default_model": "aya"
    },
    "openai": {
      "api_key": "sk-...",
      "default_model": "gpt-4"
    },
    "mistral": {
      "api_key": "...",
      "default_model": "mistral-large-latest"
    },
    "anthropic": {
      "api_key": "sk-ant-...",
      "default_model": "claude-3-sonnet-20240229"
    }
  }
}
```

### translations/*.json
**Structure**: Dictionnaires clé-valeur pour chaque langue supportée.

---

## Points d'entrée et utilisation

### main.py
**Usage CLI**:
```bash
python ollamaTrad.py                           # Mode interactif
python ollamaTrad.py --gui                     # Mode GUI
python ollamaTrad.py --file data.json          # Charger un fichier
python ollamaTrad.py --command "translate -fr /title"  # Commande directe
```

### Architecture générale

1. **Couche de données**: JsonManager pour navigation et modification
2. **Couche IA**: AIClient unifié avec providers multiples
3. **Couche historique**: OperationHistoryManager pour undo/redo avancé
4. **Couches interface**: CLI (commands.py) et GUI (app.py)
5. **Couche configuration**: settings.json et i18n
6. **Couche persistance**: data/ pour métadonnées et historiques

### Flux de données typique

1. Chargement JSON via JsonManager
2. Navigation filesystem dans la structure
3. Opérations IA via AIClient avec provider sélectionné
4. Enregistrement automatique dans OperationHistoryManager
5. Modifications en attente avec validation différée
6. Persistance avec historique complet

Cette architecture modulaire permet une extensibilité facile, un suivi complet des opérations, et une expérience utilisateur riche avec undo/redo avancé et multi-provider IA.