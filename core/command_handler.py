# -*- coding: utf-8 -*-
"""
Gestionnaire de commandes unifié pour CLI et GUI.

Ce module centralise toute la logique des commandes pour permettre
une utilisation identique dans l'interface CLI et l'interface graphique.
"""

import asyncio
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
import json

from core.json_manager import JsonManager
from core.got_json_manager import GotJsonManager
from core.ai_client import AIClient
from core.operation_history import OperationHistoryManager
from utils.file_loader import load_file_intelligently


class CommandHandler:
    """
    Gestionnaire de commandes unifié pour CLI et GUI.

    Permet d'exécuter les mêmes commandes dans les deux interfaces avec
    des callbacks pour synchroniser l'affichage GUI (TreeView, etc.).
    """

    def __init__(self):
        # Gestionnaires de données
        self.json_manager: Optional[JsonManager] = None
        self.got_manager: Optional[GotJsonManager] = None
        self.ai_client = AIClient()
        self.history_manager = OperationHistoryManager()

        # État courant
        self.current_path: str = ""  # Chemin courant dans le JSON (ex: "app/title")
        self.current_file_path: Optional[str] = None

        # Callbacks pour synchroniser l'interface (utilisés par GUI)
        self.callbacks: Dict[str, Callable] = {
            "on_path_changed": None,  # Appelé quand current_path change (pour TreeView)
            "on_output": None,  # Appelé pour afficher du texte (CLI: print, GUI: chat)
            "on_error": None,  # Appelé pour afficher une erreur
            "on_data_changed": None,  # Appelé quand les données JSON changent
            "on_file_loaded": None,  # Appelé quand un fichier est chargé
        }

    def register_callback(self, event: str, callback: Callable):
        """Enregistre un callback pour un événement."""
        if event in self.callbacks:
            self.callbacks[event] = callback

    def _notify(self, event: str, *args, **kwargs):
        """Notifie un événement aux callbacks."""
        if self.callbacks.get(event):
            self.callbacks[event](*args, **kwargs)

    def _output(self, message: str):
        """Affiche un message (CLI: print, GUI: chat)."""
        if self.callbacks["on_output"]:
            self.callbacks["on_output"](message)
        else:
            print(message)

    def _error(self, message: str):
        """Affiche une erreur."""
        if self.callbacks["on_error"]:
            self.callbacks["on_error"](message)
        else:
            print(f"❌ {message}")

    # ========== COMMANDES DE NAVIGATION ==========

    def cmd_cd(self, path: str = None) -> str:
        """
        Change le chemin courant.

        Args:
            path: Chemin destination (ex: "app/title", "/entities", "..")
                 Si None: affiche le chemin actuel

        Returns:
            Message de résultat
        """
        if not path:
            # Afficher le chemin actuel
            current = self.current_path or "/"
            msg = f"📍 Chemin actuel: {current}"
            self._output(msg)
            return msg

        if not self.got_manager:
            msg = "Aucun fichier chargé"
            self._error(msg)
            return msg

        # Nettoyer le chemin
        path = path.strip()
        if path.startswith("/"):
            path = path[1:]

        # Cas spéciaux
        if path == "..":
            # Remonter d'un niveau
            if "/" in self.current_path:
                path = "/".join(self.current_path.split("/")[:-1])
            else:
                path = ""
        elif path == ".":
            # Rester sur place
            return f"📍 Déjà sur: {self.current_path or '/'}"

        # Vérifier si le chemin existe
        try:
            if path:
                entry = self.got_manager._get_entry_by_path(path)
            else:
                entry = self.got_manager.data  # Racine

            # Chemin valide, mettre à jour
            old_path = self.current_path
            self.current_path = path

            # Notifier le changement de chemin (pour GUI: sélectionner dans TreeView)
            self._notify("on_path_changed", path)

            msg = f"✓ Navigué vers: /{path}" if path else "✓ Navigué vers: /"
            self._output(msg)
            return msg

        except (KeyError, ValueError) as e:
            msg = f"Chemin invalide: {path}"
            self._error(msg)
            return msg

    def cmd_ls(self, path: str = "") -> str:
        """
        Liste le contenu d'un chemin.

        Args:
            path: Chemin à lister (vide = chemin courant)

        Returns:
            Contenu formaté
        """
        if not self.got_manager:
            msg = "Aucun fichier chargé"
            self._error(msg)
            return msg

        # Utiliser current_path si path est vide
        target_path = path.strip() if path else self.current_path

        if target_path.startswith("/"):
            target_path = target_path[1:]

        try:
            if target_path:
                entry = self.got_manager._get_entry_by_path(target_path)
            else:
                entry = self.got_manager.data

            # Formater le contenu
            if isinstance(entry, dict):
                # Exclure les métadonnées ollamafic
                items = [k for k in entry.keys() if k != "__ollamafic__"]
                if items:
                    result = f"📂 Contenu de /{target_path or '(racine)'}:\n"
                    for item in items:
                        result += f"  - {item}\n"
                else:
                    result = f"📂 /{target_path or '(racine)'} est vide"
            elif isinstance(entry, list):
                result = f"📋 Liste [{len(entry)} éléments]:\n"
                for i, item in enumerate(entry[:10]):  # Limiter à 10 pour l'affichage
                    result += f"  [{i}] {str(item)[:50]}...\n" if len(str(item)) > 50 else f"  [{i}] {item}\n"
                if len(entry) > 10:
                    result += f"  ... et {len(entry) - 10} autres éléments"
            else:
                result = f"📄 Valeur: {entry}"

            self._output(result)
            return result

        except (KeyError, ValueError) as e:
            msg = f"Chemin invalide: {target_path}"
            self._error(msg)
            return msg

    def cmd_cat(self, path: str) -> str:
        """
        Affiche le contenu d'un élément.

        Args:
            path: Chemin de l'élément

        Returns:
            Contenu formaté en JSON
        """
        if not self.got_manager:
            msg = "Aucun fichier chargé"
            self._error(msg)
            return msg

        target_path = path.strip()
        if target_path.startswith("/"):
            target_path = target_path[1:]

        try:
            entry = self.got_manager._get_entry_by_path(target_path)
            result = json.dumps(entry, indent=2, ensure_ascii=False)
            self._output(result)
            return result
        except (KeyError, ValueError) as e:
            msg = f"Chemin invalide: {target_path}"
            self._error(msg)
            return msg

    # ========== COMMANDES FICHIER ==========

    def cmd_load(self, file_path: str) -> str:
        """
        Charge un fichier JSON ou .got.json.

        Args:
            file_path: Chemin du fichier à charger

        Returns:
            Message de résultat
        """
        try:
            # Charger avec le système intelligent
            self.got_manager, got_path = load_file_intelligently(file_path)

            # Créer JsonManager pour compatibilité
            self.json_manager = JsonManager()
            self.json_manager.data = self.got_manager.data
            self.json_manager.file_path = Path(got_path)
            self.json_manager.original_data = self.got_manager.data.copy()

            # Configurer le hook d'historique
            def operation_hook(operation_type: str, affected_data: dict, user_input: dict = None, result: any = None):
                provider_info = {}
                try:
                    if self.ai_client.current_provider:
                        provider_info = self.ai_client.current_provider.get_current_provider_info()
                except:
                    pass

                self.history_manager.record_operation(
                    operation_type=operation_type,
                    user_input=user_input or {},
                    affected_data=affected_data,
                    result=result,
                    provider_info=provider_info
                )

            self.json_manager.set_operation_hook(operation_hook)
            self.current_file_path = got_path
            self.current_path = ""  # Reset à la racine

            # Notifier le chargement
            self._notify("on_file_loaded", got_path, self.got_manager)
            self._notify("on_path_changed", "")  # Retour à la racine

            msg = f"✓ Fichier chargé: {got_path}"
            self._output(msg)

            # Afficher les stats
            if self.got_manager.is_valid_got_json(self.got_manager.data):
                header = self.got_manager.data["__ollamafic__"]
                self._output(f"📦 Format: .got.json v{header['version']}")
                self._output(f"📄 Fichier source: {header['original_file']}")

            return msg

        except Exception as e:
            msg = f"Erreur lors du chargement: {e}"
            self._error(msg)
            return msg

    def cmd_save(self, file_path: Optional[str] = None) -> str:
        """
        Sauvegarde le fichier courant.

        Args:
            file_path: Chemin de destination (optionnel)

        Returns:
            Message de résultat
        """
        if not self.got_manager:
            msg = "Aucun fichier chargé"
            self._error(msg)
            return msg

        try:
            save_path = file_path or self.current_file_path
            if not save_path:
                msg = "Aucun chemin de fichier spécifié"
                self._error(msg)
                return msg

            self.got_manager.save_got_json(save_path)

            # Notifier le changement
            self._notify("on_data_changed")

            msg = f"✓ Fichier sauvegardé: {save_path}"
            self._output(msg)
            return msg

        except Exception as e:
            msg = f"Erreur lors de la sauvegarde: {e}"
            self._error(msg)
            return msg

    # ========== COMMANDES IA ==========

    async def cmd_ia(self, message: str) -> str:
        """
        Dialogue avec l'IA.

        Args:
            message: Message à envoyer à l'IA

        Returns:
            Réponse de l'IA
        """
        if not message.strip():
            msg = "Message vide"
            self._error(msg)
            return msg

        try:
            # Ajouter le contexte si on est sur un chemin
            context = ""
            if self.current_path and self.got_manager:
                try:
                    entry = self.got_manager._get_entry_by_path(self.current_path)
                    context = f"\nContexte (chemin: {self.current_path}):\n{json.dumps(entry, indent=2, ensure_ascii=False)[:500]}"
                except:
                    pass

            full_message = message
            if context:
                full_message += context

            # Envoyer à l'IA
            response = await self.ai_client.chat(full_message)

            self._output(f"< {response}")
            return response

        except Exception as e:
            msg = f"Erreur IA: {e}"
            self._error(msg)
            return msg

    async def cmd_internal(self, command: str) -> str:
        """
        Exécute une commande interne du provider (/show, /set, etc.).

        Args:
            command: Commande interne (avec le /)

        Returns:
            Résultat de la commande
        """
        try:
            result = await self.ai_client.execute_internal_command(command)
            self._output(result)
            return result
        except Exception as e:
            msg = f"Erreur commande interne: {e}"
            self._error(msg)
            return msg

    # ========== COMMANDES PROVIDER ==========

    def cmd_provider(self, action: str, provider_name: str = "") -> str:
        """
        Gère les providers IA.

        Args:
            action: "list", "set", "info"
            provider_name: Nom du provider (pour "set")

        Returns:
            Message de résultat
        """
        if action == "list":
            providers = self.ai_client.get_available_providers()
            current = self.ai_client.get_current_provider_name()

            result = "📋 Providers disponibles:\n"
            for p in providers:
                marker = "➤ " if p == current else "  "
                result += f"{marker}{p}\n"

            self._output(result)
            return result

        elif action == "set":
            if not provider_name:
                msg = "Nom de provider requis"
                self._error(msg)
                return msg

            if self.ai_client.set_provider(provider_name):
                msg = f"✓ Provider changé vers: {provider_name}"
                self._output(msg)
                return msg
            else:
                msg = f"Provider inconnu: {provider_name}"
                self._error(msg)
                return msg

        elif action == "info":
            provider_name = self.ai_client.get_current_provider_name()
            connected = "✅ Connecté" if self.ai_client.check_connection() else "❌ Déconnecté"

            result = f"🤖 Provider actuel: {provider_name}\n"
            result += f"🔗 Statut: {connected}\n"

            self._output(result)
            return result

        else:
            msg = f"Action inconnue: {action}"
            self._error(msg)
            return msg

    def get_prompt(self) -> str:
        """
        Retourne le prompt CLI actuel (utilisé par CLI seulement).

        Returns:
            Prompt formaté (ex: "app/title> ")
        """
        if self.current_path:
            return f"{self.current_path}> "
        else:
            return "> "
