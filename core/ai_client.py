"""
Client AI unifié pour gérer multiple providers (Ollama, OpenAI, Mistral, Anthropic)
"""

import json
import aiohttp
import asyncio
import requests
from typing import Dict, List, Optional, Any
from pathlib import Path
import time
import traceback
from abc import ABC, abstractmethod


def format_error_details(provider_name: str, error_type: str, url: str, model: str,
                         timeout: int, message: str, payload: dict, error_info: str,
                         status_code: int = None, api_key: str = None) -> str:
    """
    Formate un message d'erreur détaillé pour le débogage.

    Args:
        provider_name: Nom du provider (Ollama, OpenAI, etc.)
        error_type: Type d'erreur (HTTP, TIMEOUT, EXCEPTION)
        url: URL appelée
        model: Modèle utilisé
        timeout: Timeout configuré
        message: Message utilisateur
        payload: Payload JSON envoyé
        error_info: Informations supplémentaires sur l'erreur
        status_code: Code HTTP (si applicable)
        api_key: Clé API (sera masquée, optionnelle)

    Returns:
        Message d'erreur formaté
    """
    separator = "=" * 60
    error_details = f"\n{separator}\n"

    if error_type == "HTTP":
        error_details += f"❌ ERREUR {provider_name.upper()} - DÉTAILS COMPLETS\n"
    elif error_type == "TIMEOUT":
        error_details += f"⏱️  TIMEOUT {provider_name.upper()} - DÉTAILS\n"
    else:
        error_details += f"💥 EXCEPTION {provider_name.upper()} - DÉTAILS\n"

    error_details += f"{separator}\n"
    error_details += f"📍 URL appelée: {url}\n"
    error_details += f"🔧 Modèle: {model}\n"
    error_details += f"⏱️  Timeout: {timeout}s\n"

    if status_code:
        error_details += f"📊 Status HTTP: {status_code}\n"

    if api_key:
        masked_key = '*' * 10 + api_key[-4:] if len(api_key) > 4 else '***'
        error_details += f"🔑 API Key: {masked_key}\n"

    error_details += f"📝 Message utilisateur (premiers 200 car.): {message[:200]}{'...' if len(message) > 200 else ''}\n"
    error_details += f"📦 Payload JSON envoyé:\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n"
    error_details += f"📋 Informations d'erreur:\n{error_info}\n"
    error_details += f"{separator}\n"

    return error_details

class AIProvider(ABC):
    """Interface abstraite pour les providers AI"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.conversation_history: List[Dict[str, str]] = []
        self.session_variables: Dict[str, Any] = {}  # Variables de session (/set)
        self.current_model = config.get("default_model", "")
        self.character_count = 0  # Compteur de caractères pour APIs payantes

    @abstractmethod
    async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
        """Envoie un message de chat et retourne la réponse"""
        pass

    @abstractmethod
    def check_connection(self) -> bool:
        """Vérifie la connexion au provider"""
        pass

    async def execute_internal_command(self, command: str) -> str:
        """Exécute une commande interne (/, /set, /show, etc.)"""
        if not command.startswith('/'):
            raise ValueError("Les commandes internes doivent commencer par /")

        parts = command[1:].split()
        cmd = parts[0].lower() if parts else ""

        if cmd == "set":
            return await self.cmd_set(parts[1:])
        elif cmd == "show":
            return await self.cmd_show(parts[1:])
        elif cmd == "load":
            return await self.cmd_load(parts[1:])
        elif cmd == "save":
            return await self.cmd_save(parts[1:])
        elif cmd == "clear":
            return await self.cmd_clear()
        elif cmd == "bye":
            return await self.cmd_bye()
        elif cmd in ["help", "?"]:
            return await self.cmd_help(parts[1:])
        else:
            return f"❌ Commande interne inconnue: /{cmd}\nTapez /help pour voir les commandes disponibles."

    async def cmd_set(self, args: List[str]) -> str:
        """Gère les variables de session /set"""
        if not args:
            # Afficher toutes les variables
            if self.session_variables:
                result = "📝 Variables de session:\n"
                for key, value in self.session_variables.items():
                    result += f"  {key} = {value}\n"
                return result
            else:
                return "📝 Aucune variable de session définie"

        if len(args) == 1:
            # Afficher une variable spécifique
            key = args[0]
            if key in self.session_variables:
                return f"📝 {key} = {self.session_variables[key]}"
            else:
                return f"❌ Variable '{key}' non définie"

        if len(args) >= 2:
            # Définir une variable
            key = args[0]
            value = " ".join(args[1:])

            # Conversion automatique de type
            if value.lower() in ["true", "false"]:
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "").isdigit():
                value = float(value)

            self.session_variables[key] = value
            return f"✅ Variable '{key}' définie: {value}"

    async def cmd_show(self, args: List[str]) -> str:
        """Affiche les informations du modèle/provider"""
        result = f"🤖 Provider: {self.__class__.__name__.replace('Provider', '')}\n"
        result += f"📋 Modèle actuel: {self.current_model}\n"
        result += f"🔗 Statut: {'✅ Connecté' if self.check_connection() else '❌ Déconnecté'}\n"
        result += f"💬 Messages en mémoire: {len(self.conversation_history)}\n"
        result += f"⚙️  Variables de session: {len(self.session_variables)}\n"
        return result

    async def cmd_load(self, args: List[str]) -> str:
        """Charge un modèle"""
        if not args:
            return "❌ Usage: /load <nom_du_modele>"

        model_name = args[0]
        old_model = self.current_model
        self.current_model = model_name
        self.config["default_model"] = model_name

        return f"✅ Modèle changé de '{old_model}' vers '{model_name}'"

    async def cmd_save(self, args: List[str]) -> str:
        """Sauvegarde la session/conversation"""
        if not args:
            return "❌ Usage: /save <nom_de_session>"

        session_name = args[0]
        # Cette méthode sera implémentée différemment selon le provider
        return f"💾 Session sauvegardée sous le nom '{session_name}'"

    async def cmd_clear(self) -> str:
        """Efface le contexte de la conversation"""
        messages_count = len(self.conversation_history)
        self.clear_conversation()
        return f"🗑️  Contexte effacé ({messages_count} messages supprimés)"

    async def cmd_bye(self) -> str:
        """Commande de sortie"""
        return "👋 Session terminée"

    async def cmd_help(self, args: List[str]) -> str:
        """Affiche l'aide des commandes internes"""
        if args and args[0] == "shortcuts":
            return """
⌨️  Raccourcis clavier (si supportés par l'interface):
  Ctrl+C        Interrompre la génération
  ↑/↓           Naviguer dans l'historique des commandes
  Tab           Auto-complétion
  Ctrl+L        Effacer l'écran
  Ctrl+D        Quitter
            """

        return """
🔧 Commandes internes disponibles:

📊 INFORMATION:
  /show           Affiche les informations du provider/modèle
  /help           Affiche cette aide
  /? shortcuts    Aide sur les raccourcis clavier

⚙️  CONFIGURATION:
  /set [var] [val]  Définit/affiche les variables de session
  /load <model>     Change le modèle actuel
  /save <nom>       Sauvegarde la session actuelle

🗂️  GESTION:
  /clear          Efface l'historique de conversation
  /bye            Termine la session

💡 EXEMPLES:
  /set temperature 0.7
  /set context_length 4096
  /show
  /load llama3.2
  /clear
        """

    def add_to_conversation(self, role: str, content: str):
        """Ajoute un message à l'historique de conversation"""
        self.conversation_history.append({"role": role, "content": content})

        # Limiter l'historique
        max_history = 50
        if len(self.conversation_history) > max_history:
            self.conversation_history = self.conversation_history[-max_history:]

    def clear_conversation(self):
        """Efface l'historique de conversation"""
        self.conversation_history = []

    def get_conversation_context(self) -> str:
        """Retourne le contexte de la conversation"""
        if not self.conversation_history:
            return ""

        context = []
        for msg in self.conversation_history[-10:]:  # Derniers 10 messages
            context.append(f"{msg['role']}: {msg['content']}")

        return "\n".join(context)

    def get_current_provider_info(self) -> Dict[str, Any]:
        """Retourne les informations du provider actuel pour l'historique"""
        return {
            "provider_name": self.__class__.__name__.replace('Provider', ''),
            "model": self.current_model,
            "session_variables": dict(self.session_variables),
            "connected": self.check_connection()
        }

    def get_character_count(self) -> int:
        """Retourne le nombre de caractères envoyés durant la session"""
        return self.character_count

    def reset_character_count(self):
        """Remet à zéro le compteur de caractères"""
        self.character_count = 0

    def _count_characters(self, text: str) -> int:
        """Compte les caractères dans un texte et l'ajoute au compteur"""
        char_count = len(text)
        self.character_count += char_count
        return char_count


class OllamaProvider(AIProvider):
    """Provider pour Ollama local"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "http://localhost:11434")

        # Chercher "model" puis "default_model" pour compatibilité
        self.model = config.get("model", config.get("default_model", "aya:8b"))
        self.current_model = self.model  # Synchroniser avec parent
        self.timeout = config.get("timeout", 120)  # Augmenté à 120s pour textes longs

    def check_connection(self) -> bool:
        """Vérifie la connexion à Ollama"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
        """
        Chat avec Ollama

        Args:
            message: Message à envoyer
            system_prompt: Prompt système optionnel
            timeout: Timeout en secondes (si None, utilise self.timeout)
        """
        # Variables pour le débogage
        url = None
        payload = None
        effective_timeout = None

        try:
            # Utiliser le timeout fourni ou celui par défaut
            effective_timeout = timeout if timeout is not None else self.timeout

            # Préparer les messages
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Ajouter le contexte de conversation
            messages.extend(self.conversation_history)
            messages.append({"role": "user", "content": message})

            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False
            }

            url = f"{self.host}/api/chat"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=effective_timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        assistant_message = result["message"]["content"]

                        # Ajouter à l'historique
                        self.add_to_conversation("user", message)
                        self.add_to_conversation("assistant", assistant_message)

                        return assistant_message
                    else:
                        # Lire le corps de la réponse pour plus de détails
                        error_body = await response.text()

                        error_details = (
                            f"\n{'='*60}\n"
                            f"❌ ERREUR OLLAMA - DÉTAILS COMPLETS\n"
                            f"{'='*60}\n"
                            f"📍 URL appelée: {url}\n"
                            f"🔧 Modèle: {self.model}\n"
                            f"⏱️  Timeout: {effective_timeout}s\n"
                            f"📊 Status HTTP: {response.status}\n"
                            f"📝 Message utilisateur (premiers 200 car.): {message[:200]}{'...' if len(message) > 200 else ''}\n"
                            f"📦 Payload JSON envoyé:\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n"
                            f"📋 Réponse serveur:\n{error_body}\n"
                            f"{'='*60}\n"
                        )
                        print(error_details)  # Afficher dans la console
                        raise Exception(f"Erreur Ollama HTTP {response.status}: {error_body}")

        except asyncio.TimeoutError:
            error_details = (
                f"\n{'='*60}\n"
                f"⏱️  TIMEOUT OLLAMA - DÉTAILS\n"
                f"{'='*60}\n"
                f"📍 URL: {url}\n"
                f"🔧 Modèle: {self.model}\n"
                f"⏱️  Timeout configuré: {effective_timeout}s\n"
                f"📝 Message (premiers 200 car.): {message[:200]}{'...' if len(message) > 200 else ''}\n"
                f"💡 Suggestion: Augmentez le timeout ou vérifiez que le serveur Ollama répond\n"
                f"{'='*60}\n"
            )
            print(error_details)
            raise Exception(f"Timeout après {effective_timeout}s lors de l'appel à Ollama")

        except Exception as e:
            # Si c'est déjà notre exception formatée, la relever telle quelle
            if "ERREUR OLLAMA - DÉTAILS COMPLETS" in str(e) or "TIMEOUT OLLAMA" in str(e):
                raise

            # Sinon, formater une nouvelle erreur détaillée
            import traceback
            error_details = (
                f"\n{'='*60}\n"
                f"💥 EXCEPTION OLLAMA - DÉTAILS\n"
                f"{'='*60}\n"
                f"📍 URL: {url or 'Non définie'}\n"
                f"🔧 Modèle: {self.model}\n"
                f"⏱️  Timeout: {effective_timeout}s\n"
                f"📝 Message (premiers 200 car.): {message[:200] if message else 'N/A'}{'...' if message and len(message) > 200 else ''}\n"
                f"📦 Payload: {json.dumps(payload, indent=2, ensure_ascii=False) if payload else 'Non défini'}\n"
                f"🐛 Type d'erreur: {type(e).__name__}\n"
                f"📄 Message d'erreur: {str(e)}\n"
                f"📚 Traceback complet:\n{traceback.format_exc()}\n"
                f"{'='*60}\n"
            )
            print(error_details)
            raise Exception(f"Erreur inattendue Ollama ({type(e).__name__}): {str(e)}")

    async def cmd_show(self, args: List[str]) -> str:
        """Version Ollama de /show avec informations détaillées du modèle"""
        base_info = await super().cmd_show(args)

        try:
            # Récupérer les informations détaillées du modèle via l'API Ollama
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.host}/api/show",
                    json={"name": self.current_model},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        model_info = await response.json()
                        base_info += f"💾 Taille du modèle: {model_info.get('size', 'Inconnue')}\n"
                        base_info += f"📅 Modifié: {model_info.get('modified_at', 'Inconnu')[:10]}\n"

                        # Paramètres du modèle si disponibles
                        if 'parameters' in model_info:
                            base_info += f"⚙️  Paramètres: {model_info['parameters']}\n"
                    else:
                        base_info += "⚠️ Impossible de récupérer les détails du modèle\n"
        except Exception as e:
            base_info += f"⚠️ Erreur lors de la récupération des détails: {e}\n"

        return base_info

    async def cmd_load(self, args: List[str]) -> str:
        """Version Ollama de /load qui vérifie l'existence du modèle"""
        if not args:
            # Lister les modèles disponibles
            try:
                response = requests.get(f"{self.host}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json()
                    if models.get('models'):
                        result = "📋 Modèles Ollama disponibles:\n"
                        for model in models['models']:
                            name = model['name']
                            size = model.get('size', 'Taille inconnue')
                            marker = "➤ " if name == self.current_model else "  "
                            result += f"{marker}{name} ({size})\n"
                        result += f"\n💡 Usage: /load <nom_du_modele>"
                        return result
                    else:
                        return "❌ Aucun modèle Ollama trouvé"
                else:
                    return "❌ Impossible de récupérer la liste des modèles"
            except Exception as e:
                return f"❌ Erreur lors de la récupération des modèles: {e}"

        model_name = args[0]

        # Vérifier que le modèle existe
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json()
                model_names = [m['name'] for m in models.get('models', [])]
                if model_name not in model_names:
                    return f"❌ Modèle '{model_name}' non trouvé.\nModèles disponibles: {', '.join(model_names)}"
        except Exception as e:
            return f"⚠️ Impossible de vérifier l'existence du modèle: {e}\nTentative de chargement..."

        # Changer le modèle
        old_model = self.current_model
        self.current_model = model_name
        self.config["default_model"] = model_name

        return f"✅ Modèle Ollama changé de '{old_model}' vers '{model_name}'"

    async def cmd_save(self, args: List[str]) -> str:
        """Version Ollama de /save utilisant l'API native"""
        if not args:
            return "❌ Usage: /save <nom_de_session>"

        session_name = args[0]

        # Sauvegarder via l'API Ollama (si supporté dans le futur)
        # Pour l'instant, sauvegarde locale de la conversation
        try:
            conversations_dir = Path("conversations")
            conversations_dir.mkdir(exist_ok=True)

            session_data = {
                "model": self.current_model,
                "provider": "ollama",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "session_variables": self.session_variables,
                "conversation": self.conversation_history
            }

            session_file = conversations_dir / f"{session_name}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            return f"💾 Session Ollama '{session_name}' sauvegardée ({len(self.conversation_history)} messages)"

        except Exception as e:
            return f"❌ Erreur lors de la sauvegarde: {e}"


class OpenAIProvider(AIProvider):
    """Provider pour OpenAI GPT"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_url = config.get("api_url", "https://api.openai.com/v1/chat/completions")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", config.get("default_model", "gpt-4"))
        self.current_model = self.model  # Synchroniser avec parent
        self.timeout = config.get("timeout", 30)

    def check_connection(self) -> bool:
        """Vérifie la connexion à OpenAI"""
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=5)
            return response.status_code == 200
        except:
            return False

    async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
        """Chat avec OpenAI"""
        if not self.api_key:
            raise Exception("Clé API OpenAI non configurée")

        # Variables pour le débogage
        url = None
        payload = None
        effective_timeout = None

        try:
            effective_timeout = timeout if timeout is not None else self.timeout

            # Compter les caractères envoyés
            self._count_characters(message)
            if system_prompt:
                self._count_characters(system_prompt)

            # Préparer les messages
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Ajouter le contexte de conversation
            messages.extend(self.conversation_history)
            messages.append({"role": "user", "content": message})

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.7
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            url = self.api_url

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=effective_timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        assistant_message = result["choices"][0]["message"]["content"]

                        # Ajouter à l'historique
                        self.add_to_conversation("user", message)
                        self.add_to_conversation("assistant", assistant_message)

                        return assistant_message
                    else:
                        error_body = await response.text()

                        error_details = (
                            f"\n{'='*60}\n"
                            f"❌ ERREUR OPENAI - DÉTAILS COMPLETS\n"
                            f"{'='*60}\n"
                            f"📍 URL appelée: {url}\n"
                            f"🔧 Modèle: {self.model}\n"
                            f"⏱️  Timeout: {effective_timeout}s\n"
                            f"📊 Status HTTP: {response.status}\n"
                            f"🔑 API Key: {'*' * 10 + self.api_key[-4:] if self.api_key else 'Non définie'}\n"
                            f"📝 Message utilisateur (premiers 200 car.): {message[:200]}{'...' if len(message) > 200 else ''}\n"
                            f"📦 Payload JSON envoyé:\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n"
                            f"📋 Réponse serveur:\n{error_body}\n"
                            f"{'='*60}\n"
                        )
                        print(error_details)
                        raise Exception(f"Erreur OpenAI HTTP {response.status}: {error_body}")

        except asyncio.TimeoutError:
            error_details = (
                f"\n{'='*60}\n"
                f"⏱️  TIMEOUT OPENAI - DÉTAILS\n"
                f"{'='*60}\n"
                f"📍 URL: {url}\n"
                f"🔧 Modèle: {self.model}\n"
                f"⏱️  Timeout configuré: {effective_timeout}s\n"
                f"📝 Message (premiers 200 car.): {message[:200]}{'...' if len(message) > 200 else ''}\n"
                f"💡 Suggestion: Augmentez le timeout ou vérifiez votre connexion réseau\n"
                f"{'='*60}\n"
            )
            print(error_details)
            raise Exception(f"Timeout après {effective_timeout}s lors de l'appel à OpenAI")

        except Exception as e:
            if "ERREUR OPENAI - DÉTAILS COMPLETS" in str(e) or "TIMEOUT OPENAI" in str(e):
                raise

            import traceback
            error_details = (
                f"\n{'='*60}\n"
                f"💥 EXCEPTION OPENAI - DÉTAILS\n"
                f"{'='*60}\n"
                f"📍 URL: {url or 'Non définie'}\n"
                f"🔧 Modèle: {self.model}\n"
                f"⏱️  Timeout: {effective_timeout}s\n"
                f"📝 Message (premiers 200 car.): {message[:200] if message else 'N/A'}{'...' if message and len(message) > 200 else ''}\n"
                f"📦 Payload: {json.dumps(payload, indent=2, ensure_ascii=False) if payload else 'Non défini'}\n"
                f"🐛 Type d'erreur: {type(e).__name__}\n"
                f"📄 Message d'erreur: {str(e)}\n"
                f"📚 Traceback complet:\n{traceback.format_exc()}\n"
                f"{'='*60}\n"
            )
            print(error_details)
            raise Exception(f"Erreur inattendue OpenAI ({type(e).__name__}): {str(e)}")

    async def cmd_show(self, args: List[str]) -> str:
        """Version OpenAI de /show avec informations spécifiques"""
        base_info = await super().cmd_show(args)

        # Ajouter des informations spécifiques OpenAI
        if self.api_key:
            base_info += f"🔑 API Key: {'*' * 10 + self.api_key[-4:]}\n"
        else:
            base_info += f"🔑 API Key: ❌ Non configurée\n"

        base_info += f"🌐 URL API: {self.api_url}\n"
        base_info += f"💰 Coût estimé par message: ~$0.002-0.03\n"

        return base_info

    async def cmd_load(self, args: List[str]) -> str:
        """Version OpenAI de /load pour changer de modèle"""
        if not args:
            available_models = [
                "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo",
                "gpt-4o", "gpt-4o-mini"
            ]
            result = "📋 Modèles OpenAI disponibles:\n"
            for model in available_models:
                marker = "➤ " if model == self.current_model else "  "
                result += f"{marker}{model}\n"
            result += f"\n💡 Usage: /load <nom_du_modele>"
            return result

        model_name = args[0]
        old_model = self.current_model
        self.current_model = model_name
        self.config["default_model"] = model_name

        return f"✅ Modèle OpenAI changé de '{old_model}' vers '{model_name}'"


class MistralProvider(AIProvider):
    """Provider pour Mistral AI"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_url = config.get("api_url", "https://api.mistral.ai/v1/chat/completions")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", config.get("default_model", "mistral-large-latest"))
        self.current_model = self.model  # Synchroniser avec parent
        self.timeout = config.get("timeout", 30)

    def check_connection(self) -> bool:
        """Vérifie la connexion à Mistral"""
        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            # Test avec un petit payload
            test_payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1
            }
            response = requests.post(self.api_url, json=test_payload, headers=headers, timeout=5)
            return response.status_code in [200, 400]  # 400 OK car c'est juste un test
        except:
            return False

    async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
        """Chat avec Mistral"""
        if not self.api_key:
            raise Exception("Clé API Mistral non configurée")

        try:
            # Compter les caractères envoyés
            self._count_characters(message)
            if system_prompt:
                self._count_characters(system_prompt)

            # Préparer les messages
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Ajouter le contexte de conversation
            messages.extend(self.conversation_history)
            messages.append({"role": "user", "content": message})

            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.7
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        assistant_message = result["choices"][0]["message"]["content"]

                        # Ajouter à l'historique
                        self.add_to_conversation("user", message)
                        self.add_to_conversation("assistant", assistant_message)

                        return assistant_message
                    else:
                        error_text = await response.text()
                        raise Exception(f"Erreur Mistral: {response.status} - {error_text}")

        except Exception as e:
            raise Exception(f"Erreur lors du chat Mistral: {e}")


class AnthropicProvider(AIProvider):
    """Provider pour Anthropic Claude"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_url = config.get("api_url", "https://api.anthropic.com/v1/messages")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", config.get("default_model", "claude-3-sonnet-20240229"))
        self.current_model = self.model  # Synchroniser avec parent
        self.timeout = config.get("timeout", 30)

    def check_connection(self) -> bool:
        """Vérifie la connexion à Anthropic"""
        if not self.api_key:
            return False

        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            # Test minimal
            test_payload = {
                "model": self.model,
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "test"}]
            }
            response = requests.post(self.api_url, json=test_payload, headers=headers, timeout=5)
            return response.status_code in [200, 400]
        except:
            return False

    async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
        """Chat avec Anthropic"""
        if not self.api_key:
            raise Exception("Clé API Anthropic non configurée")

        try:
            # Compter les caractères envoyés
            self._count_characters(message)
            if system_prompt:
                self._count_characters(system_prompt)

            # Préparer les messages (Anthropic a un format différent)
            messages = []

            # Ajouter le contexte de conversation
            messages.extend(self.conversation_history)
            messages.append({"role": "user", "content": message})

            payload = {
                "model": self.model,
                "max_tokens": 2000,
                "messages": messages
            }

            if system_prompt:
                payload["system"] = system_prompt

            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        assistant_message = result["content"][0]["text"]

                        # Ajouter à l'historique
                        self.add_to_conversation("user", message)
                        self.add_to_conversation("assistant", assistant_message)

                        return assistant_message
                    else:
                        error_text = await response.text()
                        raise Exception(f"Erreur Anthropic: {response.status} - {error_text}")

        except Exception as e:
            raise Exception(f"Erreur lors du chat Anthropic: {e}")


class DeepLProvider(AIProvider):
    """Provider pour DeepL (traduction uniquement)"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_url = config.get("api_url", "https://api-free.deepl.com/v2/translate")
        self.api_key = config.get("api_key", "")
        self.timeout = config.get("timeout", 30)
        self.is_pro = config.get("is_pro", False)  # Free ou Pro account

        # DeepL n'utilise pas de modèle
        self.current_model = "DeepL API"

        # Si compte Pro, utiliser l'URL Pro
        if self.is_pro:
            self.api_url = config.get("api_url", "https://api.deepl.com/v2/translate")

    def check_connection(self) -> bool:
        """Vérifie la connexion à DeepL"""
        if not self.api_key:
            return False

        try:
            # Test avec l'endpoint usage pour vérifier l'API key
            usage_url = self.api_url.replace("/translate", "/usage")
            headers = {"Authorization": f"DeepL-Auth-Key {self.api_key}"}
            response = requests.get(usage_url, headers=headers, timeout=5)
            return response.status_code == 200
        except:
            return False

    async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
        """
        DeepL n'est pas un chatbot, mais on peut l'utiliser pour traduire.
        Cette méthode est disponible pour compatibilité mais n'est pas recommandée.
        Utilisez translate() à la place.
        """
        raise NotImplementedError("DeepL est un service de traduction, pas un chatbot. Utilisez translate() à la place.")

    async def translate(self, text: str, target_lang: str, source_lang: str = "auto", timeout: Optional[int] = None) -> str:
        """
        Traduit un texte avec DeepL.

        Args:
            text: Texte à traduire
            target_lang: Langue cible (ex: "FR", "EN", "ES")
            source_lang: Langue source (ex: "EN", "FR" ou "auto" pour détection automatique)
            timeout: Timeout en secondes (si None, utilise self.timeout)

        Returns:
            Texte traduit
        """
        if not self.api_key:
            raise Exception("Clé API DeepL non configurée")

        if not text or not text.strip():
            return ""

        try:
            # Compter les caractères envoyés
            self._count_characters(text)

            # Convertir les codes langue en format DeepL (majuscules)
            # DeepL utilise des codes spéciaux pour certaines langues
            target_lang_upper = target_lang.upper()

            # Mapping des codes langue spéciaux DeepL
            lang_mapping = {
                "EN": "EN-US",  # Anglais américain par défaut
                "PT": "PT-BR"   # Portugais brésilien par défaut
            }

            # Appliquer le mapping si nécessaire (sauf si déjà spécifié)
            if target_lang_upper in lang_mapping and "-" not in target_lang_upper:
                target_lang_upper = lang_mapping[target_lang_upper]

            # Préparer les paramètres
            params = {
                "text": text,
                "target_lang": target_lang_upper,
                "preserve_formatting": "1",  # Préserver le formatage (dont HTML)
                "tag_handling": "html"  # Gérer les balises HTML
            }

            # Ajouter la langue source si spécifiée (pas pour auto)
            if source_lang and source_lang.lower() != "auto":
                params["source_lang"] = source_lang.upper()

            headers = {
                "Authorization": f"DeepL-Auth-Key {self.api_key}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    data=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout or self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        translated_text = result["translations"][0]["text"]
                        return translated_text
                    else:
                        error_text = await response.text()
                        raise Exception(f"Erreur DeepL: {response.status} - {error_text}")

        except Exception as e:
            raise Exception(f"Erreur lors de la traduction DeepL: {e}")

    async def cmd_show(self, args: List[str]) -> str:
        """Version DeepL de /show avec informations spécifiques"""
        base_info = f"🤖 Provider: DeepL\n"
        base_info += f"📋 Service: Traduction professionnelle\n"
        base_info += f"🔗 Statut: {'✅ Connecté' if self.check_connection() else '❌ Déconnecté'}\n"
        base_info += f"💳 Type de compte: {'Pro' if self.is_pro else 'Free'}\n"
        base_info += f"📊 Caractères envoyés: {self.character_count:,}\n"

        # Ajouter des informations spécifiques DeepL
        if self.api_key:
            base_info += f"🔑 API Key: {'*' * 10 + self.api_key[-4:]}\n"
        else:
            base_info += f"🔑 API Key: ❌ Non configurée\n"

        base_info += f"🌐 URL API: {self.api_url}\n"

        # Ajouter les limites selon le type de compte
        if self.is_pro:
            base_info += f"💰 Coût: Selon volume (facturé)\n"
        else:
            base_info += f"💰 Limite gratuite: 500,000 caractères/mois\n"

        # Essayer d'obtenir l'utilisation actuelle
        try:
            usage_url = self.api_url.replace("/translate", "/usage")
            headers = {"Authorization": f"DeepL-Auth-Key {self.api_key}"}
            response = requests.get(usage_url, headers=headers, timeout=5)
            if response.status_code == 200:
                usage_data = response.json()
                char_count = usage_data.get("character_count", 0)
                char_limit = usage_data.get("character_limit", 0)
                if char_limit > 0:
                    percentage = (char_count / char_limit) * 100
                    base_info += f"📈 Utilisation API: {char_count:,} / {char_limit:,} ({percentage:.1f}%)\n"
        except:
            pass

        return base_info

    async def cmd_load(self, args: List[str]) -> str:
        """DeepL n'a pas de modèles à charger"""
        return "ℹ️ DeepL n'utilise pas de modèles. C'est un service de traduction unique."


class AIClient:
    """Client unifié pour gérer tous les providers AI"""

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.json"

        self.config_path = Path(config_path)
        self.load_config()
        self.current_provider = None
        self.providers = {}
        self.init_providers()

    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            self.config = {"ai_providers": {"default_provider": "ollama"}}

    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")

    def init_providers(self):
        """Initialize tous les providers disponibles"""
        ai_config = self.config.get("ai_providers", {})

        # Initialiser Ollama
        if "ollama" in ai_config:
            self.providers["ollama"] = OllamaProvider(ai_config["ollama"])

        # Initialiser OpenAI
        if "openai" in ai_config:
            self.providers["openai"] = OpenAIProvider(ai_config["openai"])

        # Initialiser Mistral
        if "mistral" in ai_config:
            self.providers["mistral"] = MistralProvider(ai_config["mistral"])

        # Initialiser Anthropic
        if "anthropic" in ai_config:
            self.providers["anthropic"] = AnthropicProvider(ai_config["anthropic"])

        # Initialiser DeepL
        if "deepl" in ai_config:
            self.providers["deepl"] = DeepLProvider(ai_config["deepl"])

        # Définir le provider par défaut
        default_provider = ai_config.get("default_provider", "ollama")
        if default_provider in self.providers:
            self.current_provider = self.providers[default_provider]
        elif self.providers:
            self.current_provider = list(self.providers.values())[0]

    def set_provider(self, provider_name: str) -> bool:
        """Change le provider actuel"""
        if provider_name in self.providers:
            self.current_provider = self.providers[provider_name]

            # Mettre à jour la config
            self.config["ai_providers"]["default_provider"] = provider_name
            self.save_config()
            return True
        return False

    def get_available_providers(self) -> List[str]:
        """Retourne la liste des providers disponibles"""
        return list(self.providers.keys())

    def get_current_provider_name(self) -> str:
        """Retourne le nom du provider actuel"""
        for name, provider in self.providers.items():
            if provider == self.current_provider:
                return name
        return "unknown"

    def check_connection(self) -> bool:
        """Vérifie la connexion du provider actuel"""
        if self.current_provider:
            return self.current_provider.check_connection()
        return False

    async def chat(self, message: str, system_prompt: Optional[str] = None, timeout: Optional[int] = None) -> str:
        """Envoie un message de chat au provider actuel"""
        if not self.current_provider:
            raise Exception("Aucun provider AI configuré")

        return await self.current_provider.chat(message, system_prompt, timeout)

    async def execute_internal_command(self, command: str) -> str:
        """Exécute une commande interne sur le provider actuel"""
        if not self.current_provider:
            raise Exception("Aucun provider AI configuré")

        return await self.current_provider.execute_internal_command(command)

    def clear_conversation(self):
        """Efface l'historique de conversation du provider actuel"""
        if self.current_provider:
            self.current_provider.clear_conversation()

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Retourne l'historique de conversation du provider actuel"""
        if self.current_provider:
            return self.current_provider.conversation_history
        return []

    def update_provider_config(self, provider_name: str, config: Dict[str, Any]):
        """Met à jour la configuration d'un provider"""
        if provider_name in self.config["ai_providers"]:
            self.config["ai_providers"][provider_name].update(config)
            self.save_config()

            # Réinitialiser le provider
            if provider_name == "ollama":
                self.providers[provider_name] = OllamaProvider(self.config["ai_providers"][provider_name])
            elif provider_name == "openai":
                self.providers[provider_name] = OpenAIProvider(self.config["ai_providers"][provider_name])
            elif provider_name == "mistral":
                self.providers[provider_name] = MistralProvider(self.config["ai_providers"][provider_name])
            elif provider_name == "anthropic":
                self.providers[provider_name] = AnthropicProvider(self.config["ai_providers"][provider_name])
            elif provider_name == "deepl":
                self.providers[provider_name] = DeepLProvider(self.config["ai_providers"][provider_name])

            # Si c'est le provider actuel, le recharger
            if self.get_current_provider_name() == provider_name:
                self.current_provider = self.providers[provider_name]

    def get_total_character_count(self) -> int:
        """Retourne le total de caractères envoyés tous providers confondus"""
        total = 0
        for provider in self.providers.values():
            total += provider.get_character_count()
        return total

    def get_character_count_by_provider(self) -> Dict[str, int]:
        """Retourne le compteur de caractères pour chaque provider"""
        return {
            name: provider.get_character_count()
            for name, provider in self.providers.items()
        }