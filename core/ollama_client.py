import requests
import json
from typing import Dict, List, Optional, Any
import asyncio
import aiohttp

class OllamaClient:
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host.rstrip('/')
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def chat_sync(self, model: str, messages: List[Dict[str, str]], stream: bool = False) -> Dict[str, Any]:
        """Communication synchrone avec Ollama"""
        url = f"{self.host}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur de communication avec Ollama: {e}")

    async def chat_async(self, model: str, messages: List[Dict[str, str]], stream: bool = False) -> Dict[str, Any]:
        """Communication asynchrone avec Ollama"""
        if not self.session:
            raise Exception("Session non initialisée. Utilisez 'async with OllamaClient()' ou appelez __aenter__")

        url = f"{self.host}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }

        try:
            async with self.session.post(url, json=payload, timeout=30) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise Exception(f"Erreur de communication avec Ollama: {e}")

    def translate_text(self, text: str, source_lang: str = "auto", target_lang: str = "fr",
                      model: str = "llama3.1", context: str = "") -> str:
        """Traduit un texte avec contexte optionnel"""
        # Utiliser le gestionnaire d'instructions
        from core.instructions import InstructionsManager
        instructions_manager = InstructionsManager()

        # Détecter si le contenu contient du HTML
        profile = "html" if "<" in text and ">" in text else "default"

        system_prompt = instructions_manager.get_translation_instruction(
            source_lang=source_lang,
            target_lang=target_lang,
            profile=profile,
            context=f"Contexte: {context}" if context else ""
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]

        response = self.chat_sync(model, messages)
        return response.get("message", {}).get("content", "").strip()

    def process_json_field(self, field_content: str, instruction: str,
                          model: str = "llama3.1", context: str = "") -> str:
        """Traite un champ JSON avec une instruction spécifique"""
        # Utiliser le gestionnaire d'instructions
        from core.instructions import InstructionsManager
        instructions_manager = InstructionsManager()

        system_prompt = instructions_manager.get_processing_instruction(
            instruction=instruction,
            context=f"Contexte: {context}" if context else ""
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": field_content}
        ]

        response = self.chat_sync(model, messages)
        return response.get("message", {}).get("content", "").strip()

    def get_available_models(self) -> List[str]:
        """Récupère la liste des modèles disponibles"""
        try:
            url = f"{self.host}/api/tags"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur lors de la récupération des modèles: {e}")

    def check_connection(self) -> bool:
        """Vérifie la connexion avec Ollama"""
        try:
            self.get_available_models()
            return True
        except:
            return False

    def is_ollama_running(self) -> bool:
        """Vérifie si le service Ollama est en cours d'exécution"""
        try:
            url = f"{self.host}/api/tags"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def start_ollama_service(self) -> bool:
        """Tente de démarrer le service Ollama"""
        import subprocess
        import sys
        import time

        try:
            if sys.platform == "win32":
                # Sur Windows, essayer de lancer ollama serve
                subprocess.Popen(["ollama", "serve"],
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            else:
                # Sur Linux/Mac
                subprocess.Popen(["ollama", "serve"],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)

            # Attendre que le service démarre
            for _ in range(10):  # Attendre jusqu'à 10 secondes
                time.sleep(1)
                if self.is_ollama_running():
                    return True

            return False
        except FileNotFoundError:
            print("ERREUR: Ollama n'est pas installe sur ce systeme")
            return False
        except Exception as e:
            print(f"ERREUR lors du demarrage d'Ollama: {e}")
            return False

    def get_preferred_default_model(self) -> str:
        """Détermine le meilleur modèle par défaut avec 'aya' en priorité"""
        try:
            available_models = self.get_available_models()

            if not available_models:
                return "aya"  # Si aucun modèle disponible, retourner aya par défaut

            # 1. Priorité absolue : aya (toute version)
            for model in available_models:
                if "aya" in model.lower():
                    return model

            # 2. Fallback : le premier modèle de la liste
            return available_models[0]

        except Exception as e:
            print(f"Erreur lors de la detection du modele par defaut: {e}")
            return "aya"  # Fallback sur aya en cas d'erreur

    def ensure_model_available(self, model_name: str = None) -> bool:
        """S'assure qu'un modèle spécifique est disponible"""
        if model_name is None:
            model_name = self.get_preferred_default_model()

        try:
            available_models = self.get_available_models()

            # Chercher le modèle (avec ou sans version)
            model_found = any(
                model_name in model or model.startswith(model_name.split(':')[0])
                for model in available_models
            )

            if model_found:
                return True

            # Tenter de télécharger le modèle
            print(f"🔄 Téléchargement du modèle {model_name}...")
            url = f"{self.host}/api/pull"
            payload = {"name": model_name}

            response = requests.post(url, json=payload, timeout=300)  # 5 minutes timeout
            if response.status_code == 200:
                print(f"OK Modele {model_name} telecharge avec succes")
                return True
            else:
                print(f"ERREUR lors du telechargement: {response.status_code}")
                return False

        except Exception as e:
            print(f"ERREUR lors de la verification du modele: {e}")
            return False

    def get_recommended_models(self) -> List[str]:
        """Retourne une liste de modèles recommandés avec aya en priorité"""
        recommended = [
            "aya:latest",
            "aya:8b",
            "llama3.2:latest",
            "llama3.2:3b",
            "llama3.1:latest",
            "llama3.1:8b",
            "mistral:latest",
            "codellama:latest",
            "qwen2.5:latest"
        ]

        try:
            available = self.get_available_models()
            # Retourner d'abord les modèles disponibles, puis les recommandés
            result = []
            for model in available:
                if model not in result:
                    result.append(model)

            for model in recommended:
                if model not in result and model.split(':')[0] not in [m.split(':')[0] for m in result]:
                    result.append(f"{model} (non installé)")

            return result
        except:
            return recommended