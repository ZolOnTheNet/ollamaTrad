import argparse
import sys
from pathlib import Path
from typing import List, Optional
import json

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from core.json_manager import JsonManager, JsonPath
from core.ollama_client import OllamaClient
from core.metadata import MetadataManager
from core.ai_client import AIClient
from core.operation_history import OperationHistoryManager
from core.got_json_manager import GotJsonManager
from utils.file_loader import load_file_intelligently

class CLIInterface:
    def __init__(self):
        self.json_manager: Optional[JsonManager] = None
        self.got_manager: Optional[GotJsonManager] = None  # Nouveau gestionnaire .got.json
        self.ollama_client = OllamaClient()
        self.metadata_manager = MetadataManager()
        self.ai_client = AIClient()
        self.history_manager = OperationHistoryManager()
        self.current_session: Optional[str] = None
        self.current_path: str = ""  # Chemin courant dans le JSON

    def get_preferred_model(self) -> str:
        """Retourne le modèle préféré avec aya en priorité"""
        try:
            return self.ollama_client.get_preferred_default_model()
        except:
            return "aya"

    def _sync_current_path(self) -> None:
        """Synchronise le current_path entre CLI et JsonManager"""
        if self.json_manager:
            # Synchroniser du JsonManager vers CLI
            self.current_path = self.json_manager.get_current_path()

    def cmd_load(self, file_path: str) -> None:
        """Charge un fichier JSON ou .got.json avec gestion intelligente"""
        try:
            # Utiliser le nouveau système de chargement intelligent
            self.got_manager, got_path = load_file_intelligently(file_path)

            # Créer un JsonManager à partir des données du GotJsonManager
            # pour maintenir la compatibilité avec le reste du code
            self.json_manager = JsonManager()
            self.json_manager.data = self.got_manager.data
            self.json_manager.file_path = Path(got_path)
            self.json_manager.original_data = self.got_manager.data.copy()

            # Configurer le hook d'historique
            def operation_hook(operation_type: str, affected_data: dict, user_input: dict = None, result: any = None):
                self.history_manager.record_operation(
                    operation_type=operation_type,
                    user_input=user_input or {},
                    affected_data=affected_data,
                    result=result,
                    provider_info=self.ai_client.get_current_provider_info()
                )

            self.json_manager.set_operation_hook(operation_hook)
            print(f"✓ Fichier chargé: {got_path}")

            # Afficher les informations sur le .got.json
            if self.got_manager.is_valid_got_json(self.got_manager.data):
                header = self.got_manager.data["__ollamafic__"]
                print(f"📦 Format: .got.json v{header['version']}")
                print(f"📄 Fichier source: {header['original_file']}")
                print(f"🕒 Dernière modification: {header['last_modified']}")

                # Afficher les statistiques de traduction
                stats_trans = self.got_manager.get_translation_stats()
                print(f"\n📊 Statistiques de traduction:")
                print(f"  - Entrées traduisibles: {stats_trans['total_entries']}")

                for lang in self.got_manager.target_languages:
                    lang_stats = stats_trans['by_language'][lang]
                    print(f"  - {lang.upper()}: {lang_stats['translated']}/{stats_trans['total_entries']} " +
                          f"({lang_stats['percentage']:.1f}%) traduites, " +
                          f"{lang_stats['validated']} validées")

                # Afficher les états de validation
                val_stats = stats_trans['validation_states']
                print(f"\n🎨 États de validation:")
                print(f"  - ✅ Toutes validées (vert): {val_stats['green']}")
                print(f"  - 🟠 Partiellement (orange): {val_stats['orange']}")
                print(f"  - ❌ Non validées (rouge): {val_stats['red']}")
                print(f"  - ⚪ Pas de traduction: {val_stats['none']}")

            # Afficher les statistiques JSON
            stats = self.json_manager.get_stats()
            print(f"\n📊 Statistiques JSON:")
            print(f"  - Dictionnaires: {stats['dicts']}")
            print(f"  - Listes: {stats['lists']}")
            print(f"  - Valeurs: {stats['values']}")
            print(f"  - Total éléments: {stats['total_items']}")

            # Charger les métadonnées (legacy)
            metadata = self.metadata_manager.get_metadata(file_path)
            if metadata.tags:
                print(f"\n🏷️  Tags: {', '.join(metadata.tags)}")
            if metadata.context:
                print(f"📝 Contexte: {metadata.context[:100]}...")

        except FileNotFoundError as e:
            print(f"❌ Fichier non trouvé: {e}")
        except ValueError as e:
            print(f"❌ Opération annulée: {e}")
        except Exception as e:
            print(f"❌ Erreur lors du chargement: {e}")
            import traceback
            traceback.print_exc()

    def cmd_ls(self, path: str = "") -> None:
        """Liste le contenu d'un chemin JSON"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé. Utilisez 'load <fichier>' d'abord.")
            return

        try:
            # Si aucun chemin spécifié, utiliser le répertoire courant
            if not path:
                path = self.json_manager.get_current_path()
            else:
                # Résoudre le chemin par rapport au répertoire courant
                path = self.json_manager._resolve_path(path)

            contents = self.json_manager.list_contents(path)
            display_path = f"/{path}" if path else "/"

            if not contents:
                print(f"📂 Chemin vide: {display_path}")
                return

            print(f"📂 Contenu de {display_path}:")
            for item in contents:
                type_icon = {'dict': '📁', 'list': '📋', 'value': '📄'}
                icon = type_icon.get(item['type'], '❓')
                print(f"  {icon} {item['name']:<20} ({item['type']:<5}) [{item['size']}] {item['preview']}")

        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_cat(self, path: str) -> None:
        """Affiche le contenu d'un chemin JSON"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        try:
            # Résoudre le chemin par rapport au répertoire courant
            resolved_path = self.json_manager._resolve_path(path)
            value = self.json_manager.get_value(resolved_path)
            display_path = f"/{resolved_path}" if resolved_path else "/"
            print(f"📄 Contenu de {display_path}:")
            print(json.dumps(value, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_search(self, pattern: str, keys: bool = True, values: bool = True) -> None:
        """Recherche dans le JSON"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        try:
            results = self.json_manager.search(pattern, keys, values)
            if not results:
                print(f"🔍 Aucun résultat pour: {pattern}")
                return

            print(f"🔍 Résultats pour '{pattern}' ({len(results)} trouvé(s)):")
            for result in results[:20]:  # Limiter l'affichage
                type_icon = '🔑' if result['type'] == 'key' else '📝'
                print(f"  {type_icon} {result['path']}: {result['match'][:50]}...")

            if len(results) > 20:
                print(f"  ... et {len(results) - 20} autres résultats")

        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_cd(self, path: str = None) -> None:
        """Change ou affiche le chemin courant"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        if path is None:
            # Afficher le chemin courant
            current_display = self.json_manager.get_current_path_display()
            print(f"Chemin courant: {current_display}")
            return

        try:
            # Utiliser les nouvelles méthodes du JsonManager
            self.json_manager.set_current_path(path)
            # Synchroniser le chemin CLI avec JsonManager
            self.current_path = self.json_manager.get_current_path()
            print(f"✓ Changement vers: {self.json_manager.get_current_path_display()}")

        except ValueError as e:
            print(f"❌ {e}")
        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_translate(self, options: List[str], path: str, model: str = None) -> None:
        """Traduit un champ JSON avec nouvelle syntaxe: translate -fr "chemin" """
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        # Synchroniser le current_path
        self._sync_current_path()

        # Parser les options pour extraire la langue
        target_lang = "fr"  # Défaut
        for option in options:
            if option.startswith('-'):
                lang_code = option[1:]  # Enlever le -
                if lang_code in ["fr", "en", "es", "de", "it", "pt", "ru", "ja", "zh"]:
                    target_lang = lang_code
                    break

        # Résoudre le chemin (relatif ou absolu) et gérer les jokers
        if path == '.':
            # Cas spécial pour le répertoire courant
            resolved_paths = [self.json_manager.current_path]
        elif self.json_manager._has_wildcards(path):
            # Expansion des jokers (*, ?, #)
            resolved_paths = self.json_manager._expand_wildcards(path)
        else:
            resolved_paths = [self.json_manager._resolve_path(path)]

        if not resolved_paths:
            print(f"❌ Aucun chemin trouvé pour: {path}")
            return

        # Utiliser le modèle préféré si aucun n'est spécifié
        if model is None:
            model = self.get_preferred_model()

        try:
            # Vérifier la connexion Ollama
            if not self.ollama_client.check_connection():
                print("❌ Impossible de se connecter à Ollama")
                return

            # Traiter chaque chemin trouvé
            total_paths = len(resolved_paths)
            processed = 0

            try:
                for i, resolved_path in enumerate(resolved_paths, 1):
                    try:
                        # Affichage du progrès pour les traductions batch
                        if total_paths > 1:
                            print(f"\n📊 Progression: {i}/{total_paths} - {resolved_path}")

                        # Récupérer la valeur
                        value = self.json_manager.get_value(resolved_path)

                        if not isinstance(value, str):
                            print(f"⚠️ Ignoré {resolved_path}: seuls les champs texte peuvent être traduits")
                            continue

                        # Récupérer le contexte des métadonnées
                        metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
                        context = metadata.context

                        print(f"🔄 Traduction de /{resolved_path} en cours... (modèle: {model})")
                        translated = self.ollama_client.translate_text(value, "auto", target_lang, model, context)

                        print(f"📝 Original: {value}")
                        print(f"🌐 Traduit: {translated}")

                        # Mode interactif pour chaque traduction
                        if total_paths > 1:
                            # Mode batch - demander pour chaque traduction
                            print(f"\n💾 Options pour {resolved_path}:")
                            print("  o - Accepter cette traduction")
                            print("  n - Ignorer cette traduction")
                            print("  s - Arrêter les traductions")
                            print("  a - Accepter toutes les traductions restantes")

                            while True:
                                response = input("Votre choix (o/n/s/a): ").lower().strip()
                                if response in ['o', 'n', 's', 'a']:
                                    break
                                print("Réponse invalide. Utilisez o, n, s ou a.")

                            if response == 's':
                                print("🛑 Arrêt des traductions demandé")
                                break
                            elif response == 'a':
                                # Accepter toutes les traductions restantes
                                self.json_manager.set_pending_modification(resolved_path, translated)
                                print("✓ Traduction marquée comme modifiée (MOD)")

                                # Traiter tous les chemins restants automatiquement
                                for remaining_path in resolved_paths[i:]:
                                    try:
                                        remaining_value = self.json_manager.get_value(remaining_path)
                                        if isinstance(remaining_value, str):
                                            remaining_translated = self.ollama_client.translate_text(
                                                remaining_value, "auto", target_lang, model, context
                                            )
                                            self.json_manager.set_pending_modification(remaining_path, remaining_translated)
                                            print(f"✓ {remaining_path} - traduit et marqué MOD")
                                    except Exception as e:
                                        print(f"❌ Erreur sur {remaining_path}: {e}")
                                break
                            elif response == 'o':
                                # Marquer comme modification en attente
                                self.json_manager.set_pending_modification(resolved_path, translated)
                                print("✓ Traduction marquée comme modifiée (MOD)")
                            else:  # response == 'n'
                                print("⚠️ Traduction ignorée")
                                continue
                        else:
                            # Mode unique - demander confirmation normale
                            response = input("💾 Sauvegarder la traduction? (o/N): ").lower()
                            if response == 'o':
                                self.json_manager.set_pending_modification(resolved_path, translated)
                                print("✓ Traduction marquée comme modifiée (MOD)")

                        # Enregistrer l'opération
                        if self.current_session:
                            self.metadata_manager.add_operation(self.current_session, "translate", {
                                "path": resolved_path,
                                "source": value[:100],
                                "target": translated[:100],
                                "target_lang": target_lang,
                                "model": model
                            })

                        # Ajouter une note dans les métadonnées
                        self.metadata_manager.add_processing_note(
                            self.json_manager.file_path,
                            f"Traduit '{resolved_path}' en {target_lang}"
                        )

                        processed += 1

                    except Exception as e:
                        print(f"❌ Erreur lors de la traduction de /{resolved_path}: {e}")
                        continue

            except KeyboardInterrupt:
                print(f"\n🛑 Interruption par l'utilisateur (Ctrl+C)")
                print(f"📊 {processed}/{total_paths} traductions traitées")
                return

            # Résumé final pour les traductions batch
            if total_paths > 1:
                pending_count = len(self.json_manager.get_pending_modifications())
                print(f"\n📊 Résumé:")
                print(f"  - Traductions traitées: {processed}/{total_paths}")
                print(f"  - Modifications en attente: {pending_count}")
                if pending_count > 0:
                    print("💡 Utilisez 'validate' pour confirmer toutes les modifications ou naviguez dans le GUI")

        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_validate(self, action: str = "list") -> None:
        """Gère les modifications en attente (list/commit/reject)"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        pending = self.json_manager.get_pending_modifications()

        if action == "list":
            if not pending:
                print("📝 Aucune modification en attente")
                return

            print(f"📋 Modifications en attente ({len(pending)}):")
            for i, (path, value) in enumerate(pending.items(), 1):
                original = self.json_manager.get_value(path)
                print(f"  {i}. {path}")
                print(f"     Original: {str(original)[:60]}...")
                print(f"     Modifié:  {str(value)[:60]}...")
                print()

        elif action == "commit":
            if not pending:
                print("📝 Aucune modification à valider")
                return

            confirmed = 0
            for path in list(pending.keys()):
                if self.json_manager.commit_pending_modification(path):
                    confirmed += 1
                    print(f"✅ {path} - modification appliquée")

            print(f"📊 {confirmed} modification(s) validée(s)")

        elif action == "reject":
            if not pending:
                print("📝 Aucune modification à rejeter")
                return

            rejected = 0
            for path in list(pending.keys()):
                if self.json_manager.reject_pending_modification(path):
                    rejected += 1
                    print(f"❌ {path} - modification rejetée")

            print(f"📊 {rejected} modification(s) rejetée(s)")

        else:
            print("❌ Action invalide. Utilisez: list, commit, reject")

    def cmd_process(self, path: str, instruction: str, model: str = None) -> None:
        """Traite un champ avec une instruction personnalisée"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        # Utiliser le modèle préféré si aucun n'est spécifié
        if model is None:
            model = self.get_preferred_model()

        try:
            if not self.ollama_client.check_connection():
                print("❌ Impossible de se connecter à Ollama")
                return

            value = self.json_manager.get_value(path)
            if not isinstance(value, str):
                print("❌ Seuls les champs texte peuvent être traités")
                return

            metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
            context = metadata.context

            print(f"🔄 Traitement en cours... (modèle: {model})")
            processed = self.ollama_client.process_json_field(value, instruction, model, context)

            print(f"📝 Original: {value}")
            print(f"⚡ Traité: {processed}")

            response = input("💾 Sauvegarder le résultat? (o/N): ").lower()
            if response == 'o':
                self.json_manager.set_value(path, processed)
                print("✓ Résultat sauvegardé")

                if self.current_session:
                    self.metadata_manager.add_operation(self.current_session, "process", {
                        "path": path,
                        "instruction": instruction,
                        "source": value[:100],
                        "result": processed[:100],
                        "model": model
                    })

        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_save(self, file_path: Optional[str] = None) -> None:
        """Sauvegarde le fichier JSON"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        try:
            self.json_manager.save_file(file_path)
            print("✓ Fichier sauvegardé")
        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_tag(self, action: str, tag: str) -> None:
        """Gère les tags (add/remove)"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        try:
            if action == "add":
                self.metadata_manager.add_tag(self.json_manager.file_path, tag)
                print(f"✓ Tag '{tag}' ajouté")
            elif action == "remove":
                self.metadata_manager.remove_tag(self.json_manager.file_path, tag)
                print(f"✓ Tag '{tag}' supprimé")
            else:
                print("❌ Action invalide. Utilisez 'add' ou 'remove'")
        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_context(self, context: str = "") -> None:
        """Définit ou affiche le contexte"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        try:
            if context:
                self.metadata_manager.set_context(self.json_manager.file_path, context)
                print("✓ Contexte défini")
            else:
                metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
                print(f"📝 Contexte actuel: {metadata.context or 'Aucun'}")
        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_session(self, action: str, model: str = None) -> None:
        """Gère les sessions (start/end)"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        # Utiliser le modèle préféré si aucun n'est spécifié
        if model is None:
            model = self.get_preferred_model()

        try:
            if action == "start":
                metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
                self.current_session = self.metadata_manager.start_session(
                    self.json_manager.file_path, model, metadata.context
                )
                print(f"✓ Session démarrée: {self.current_session}")
            elif action == "end":
                if self.current_session:
                    self.metadata_manager.end_session(self.current_session)
                    print(f"✓ Session terminée: {self.current_session}")
                    self.current_session = None
                else:
                    print("❌ Aucune session active")
            else:
                print("❌ Action invalide. Utilisez 'start' ou 'end'")
        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_models(self) -> None:
        """Liste les modèles Ollama disponibles"""
        try:
            models = self.ollama_client.get_available_models()
            print("🤖 Modèles disponibles:")
            for model in models:
                print(f"  - {model}")
        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_ia(self, message: str) -> None:
        """Dialogue direct avec l'IA"""
        if not message.strip():
            print("❌ Veuillez fournir un message pour l'IA")
            return

        try:
            import asyncio

            # Vérifier la connexion
            if not self.ai_client.check_connection():
                print(f"❌ Impossible de se connecter au provider {self.ai_client.get_current_provider_name()}")
                return

            print(f"🤖 [{self.ai_client.get_current_provider_name()}] Traitement en cours...")

            # Préparer le contexte si disponible
            system_prompt = None
            if self.json_manager:
                metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
                if metadata.context:
                    system_prompt = f"Contexte du fichier: {metadata.context}"

            # Envoyer le message
            async def send_message():
                return await self.ai_client.chat(message, system_prompt)

            response = asyncio.run(send_message())

            print(f"🤖 Réponse:")
            print(response)

            # Enregistrer dans l'historique si session active
            if self.current_session:
                self.metadata_manager.add_operation(self.current_session, "ia_chat", {
                    "provider": self.ai_client.get_current_provider_name(),
                    "message": message[:100],
                    "response": response[:100]
                })

        except Exception as e:
            print(f"❌ Erreur lors du dialogue avec l'IA: {e}")

    def cmd_provider(self, action: str, provider_name: str = "") -> None:
        """Gère les providers IA (list/set)"""
        try:
            if action == "list":
                current = self.ai_client.get_current_provider_name()
                providers = self.ai_client.get_available_providers()
                print("🤖 Providers disponibles:")
                for provider in providers:
                    status = " (actuel)" if provider == current else ""
                    connection = "✓" if provider == current and self.ai_client.check_connection() else "✗"
                    print(f"  {connection} {provider}{status}")

            elif action == "set" and provider_name:
                if self.ai_client.set_provider(provider_name):
                    print(f"✓ Provider changé vers: {provider_name}")
                    if self.ai_client.check_connection():
                        print("✓ Connexion établie")
                    else:
                        print("⚠️ Connexion non établie - vérifiez la configuration")
                else:
                    print(f"❌ Provider '{provider_name}' non trouvé")

            elif action == "clear":
                self.ai_client.clear_conversation()
                print("✓ Historique de conversation effacé")

            elif action == "history":
                history = self.ai_client.get_conversation_history()
                if history:
                    print("📝 Historique de conversation:")
                    for i, msg in enumerate(history[-10:], 1):  # Derniers 10 messages
                        role_icon = "👤" if msg["role"] == "user" else "🤖"
                        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                        print(f"  {i}. {role_icon} {content}")
                else:
                    print("📝 Aucun historique de conversation")

            else:
                print("❌ Action invalide. Utilisez: list, set <provider>, clear, history")

        except Exception as e:
            print(f"❌ Erreur: {e}")

    def cmd_internal(self, command: str) -> None:
        """Exécute une commande interne (/set, /show, /load, etc.)"""
        try:
            import asyncio

            # Vérifier la connexion
            if not self.ai_client.check_connection():
                print(f"❌ Impossible de se connecter au provider {self.ai_client.get_current_provider_name()}")
                return

            print(f"🔧 [{self.ai_client.get_current_provider_name()}] Exécution de: {command}")

            # Exécuter la commande de manière asynchrone
            async def execute_command():
                return await self.ai_client.execute_internal_command(command)

            # Créer une nouvelle boucle d'événements pour ce thread
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(execute_command())
                loop.close()
            except Exception as e:
                response = f"❌ Erreur lors de l'exécution: {e}"

            print(response)

            # Enregistrer dans l'historique si session active
            if self.current_session:
                self.metadata_manager.add_operation(self.current_session, "internal_command", {
                    "provider": self.ai_client.get_current_provider_name(),
                    "command": command,
                    "response": response[:100]
                })

        except Exception as e:
            print(f"❌ Erreur lors de l'exécution de la commande interne: {e}")

    def cmd_undo(self, steps: str = "1") -> None:
        """Annule les dernières opérations"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        try:
            num_steps = int(steps)
            undone_operations = self.history_manager.undo(num_steps)

            if undone_operations:
                # Appliquer les changements annulés au JsonManager
                for operation in undone_operations:
                    for path, (after_value, before_value) in operation.affected_data.items():
                        if before_value is None:
                            # C'était une création, on supprime
                            # Pour le moment, on affiche juste l'info
                            print(f"🔄 Annulation: {path} (création)")
                        else:
                            # On restaure l'ancienne valeur
                            try:
                                self.json_manager.set_value(path, before_value)
                                print(f"🔄 Annulation: {path}")
                            except Exception as e:
                                print(f"❌ Erreur lors de l'annulation de {path}: {e}")

                print(f"✅ {len(undone_operations)} opération(s) annulée(s)")
            else:
                print("📝 Aucune opération à annuler")

        except ValueError:
            print("❌ Nombre d'étapes invalide")
        except Exception as e:
            print(f"❌ Erreur lors de l'annulation: {e}")

    def cmd_redo(self, steps: str = "1") -> None:
        """Refait les opérations annulées"""
        if not self.json_manager:
            print("❌ Aucun fichier chargé.")
            return

        try:
            num_steps = int(steps)
            redone_operations = self.history_manager.redo(num_steps)

            if redone_operations:
                # Appliquer les changements refaits au JsonManager
                for operation in redone_operations:
                    for path, (before_value, after_value) in operation.affected_data.items():
                        try:
                            self.json_manager.set_value(path, after_value)
                            print(f"🔄 Rétablissement: {path}")
                        except Exception as e:
                            print(f"❌ Erreur lors du rétablissement de {path}: {e}")

                print(f"✅ {len(redone_operations)} opération(s) rétablie(s)")
            else:
                print("📝 Aucune opération à rétablir")

        except ValueError:
            print("❌ Nombre d'étapes invalide")
        except Exception as e:
            print(f"❌ Erreur lors du rétablissement: {e}")

    def cmd_history(self, count: str = "10") -> None:
        """Affiche l'historique des opérations"""
        try:
            num_count = int(count)
            operations = self.history_manager.get_operations_list()

            if not operations:
                print("📝 Aucune opération dans l'historique")
                return

            current_pos = self.history_manager.get_current_position()

            print(f"📚 Historique des opérations (position: {current_pos + 1}/{len(operations)}):")
            print("="*50)

            # Afficher les dernières opérations
            for i, operation in enumerate(operations[-num_count:]):
                index = len(operations) - num_count + i
                marker = "➤" if index == current_pos else " "

                print(f"{marker} [{index:3d}] {operation.timestamp[:16]} | {operation.operation_type}")
                print(f"      Provider: {operation.provider_info.get('provider_name', 'N/A')}")
                print(f"      Affectés: {len(operation.affected_data)} élément(s)")

                # Afficher les chemins affectés (limités)
                for j, path in enumerate(list(operation.affected_data.keys())[:3]):
                    print(f"        - {path}")
                if len(operation.affected_data) > 3:
                    print(f"        ... et {len(operation.affected_data) - 3} autres")
                print()

        except ValueError:
            print("❌ Nombre invalide")
        except Exception as e:
            print(f"❌ Erreur lors de l'affichage de l'historique: {e}")

    def cmd_help(self) -> None:
        """Affiche l'aide"""
        print("""
🚀 OllamaTrad - Interface de ligne de commande

📁 GESTION DE FICHIERS:
  load <fichier>              Charge un fichier JSON
  ls [chemin]                 Liste le contenu d'un chemin
  cat <chemin>                Affiche le contenu d'un chemin
  save [fichier]              Sauvegarde le fichier
  search <pattern>            Recherche dans le JSON
  cd [chemin]                 Change/affiche le chemin courant

🤖 TRAITEMENT IA:
  translate -fr <chemin>      Traduit un champ (nouvelle syntaxe)
  process <chemin> "<instruction>" [modele]  Traite avec instruction
  models                      Liste les modèles Ollama
  ia "<message>"              Dialogue direct avec l'IA
  provider list               Liste les providers IA
  provider set <nom>          Change le provider IA
  provider clear              Efface l'historique de conversation
  provider history            Affiche l'historique de conversation

📝 GESTION DES CONSIGNES:
  instructions list           Liste toutes les consignes
  instructions show <type> <profile>  Affiche une consigne
  instructions set <type> <profile> "<consigne>"  Définit une consigne
  instructions active <type> <profile>  Active un profil
  instructions delete <type> <profile>  Supprime un profil

🔧 COMMANDES INTERNES:
  /show                       Affiche les informations du provider/modèle
  /set [var] [val]            Définit/affiche les variables de session
  /load [model]               Change le modèle actuel
  /save <nom>                 Sauvegarde la session
  /clear                      Efface l'historique de conversation
  /help                       Aide sur les commandes internes
  /bye                        Termine la session

🏷️ MÉTADONNÉES:
  tag add <tag>               Ajoute un tag
  tag remove <tag>            Supprime un tag
  context [texte]             Définit/affiche le contexte

🔄 MODIFICATIONS:
  validate [list/commit/reject] Gère les modifications en attente
                              - list: Affiche les modifications (défaut)
                              - commit: Valide toutes les modifications
                              - reject: Rejette toutes les modifications

📚 HISTORIQUE:
  undo [étapes]               Annule les dernières opérations
  redo [étapes]               Rétablit les opérations annulées
  history [nombre]            Affiche l'historique des opérations

📊 SESSIONS:
  session start [modele]      Démarre une session
  session end                 Termine la session

❓ AIDE:
  help                        Affiche cette aide
  exit                        Quitte le programme

💡 EXEMPLES:
  load data.json
  ls
  cd entries/monster1
  translate -fr name
  translate -en description
  process /description "Rendre plus concis"
  ia "Comment améliorer cette traduction ?"
  provider list
  provider set openai
  /show
  /set temperature 0.7
  /load aya
  save

🃏 JOKERS DANS LES CHEMINS:
  * = n'importe quelle séquence de caractères
  ? = n'importe quel caractère unique
  # = n'importe quel chiffre unique

  Exemples:
  translate -en "*"           # Traduit tous les objets du niveau
  translate -en "*/name"      # Traduit tous les champs 'name'
  translate -en "dragon*/name" # Noms des objets commençant par 'dragon'
  translate -en "dragon?"     # Objets 'dragon' + 1 caractère
  translate -en "monster#"    # Objets 'monster' + 1 chiffre
  translate -en "*#/name"     # Noms des objets se terminant par un chiffre
        """)

    def cmd_instructions(self, action: str, instr_type: str = "", profile: str = "", content: str = "") -> None:
        """Gère les consignes configurables"""
        from core.instructions import InstructionsManager

        try:
            instructions_manager = InstructionsManager()

            if action == "list":
                # Afficher un résumé de toutes les consignes
                summary = instructions_manager.get_instructions_summary()
                print("📝 Résumé des consignes configurables:")
                print()

                for instr_type, info in summary.items():
                    print(f"🔧 {instr_type.upper()}:")
                    print(f"   Profil actif: {info['active_profile']}")
                    print(f"   Profils disponibles: {', '.join(info['available_profiles'])}")
                    print()

                print("💡 Commandes disponibles:")
                print("   instructions show <type> <profile>    - Affiche une consigne")
                print("   instructions set <type> <profile> \"<consigne>\"  - Définit une consigne")
                print("   instructions active <type> <profile>  - Active un profil")
                print("   instructions delete <type> <profile>  - Supprime un profil")
                print()
                print("📌 Types: translation, processing")
                print("📌 Profils pour translation: default, html, custom")
                print("📌 Profils pour processing: default, custom")

            elif action == "show":
                if not instr_type or not profile:
                    print("❌ Usage: instructions show <type> <profile>")
                    return

                instruction = instructions_manager.get_instruction(instr_type, profile)
                if instruction:
                    is_active = instructions_manager.get_active_profile(instr_type) == profile
                    status = " (ACTIF)" if is_active else ""
                    print(f"📝 Consigne {instr_type}.{profile}{status}:")
                    print("─" * 50)
                    print(instruction)
                    print("─" * 50)
                else:
                    print(f"❌ Consigne '{instr_type}.{profile}' non trouvée")

            elif action == "set":
                if not instr_type or not profile or not content:
                    print("❌ Usage: instructions set <type> <profile> \"<consigne>\"")
                    return

                # Enlever les guillemets si présents
                if content.startswith('"') and content.endswith('"'):
                    content = content[1:-1]

                if instructions_manager.set_instruction(instr_type, profile, content):
                    print(f"✅ Consigne '{instr_type}.{profile}' mise à jour")
                else:
                    print(f"❌ Erreur lors de la mise à jour de '{instr_type}.{profile}'")

            elif action == "active":
                if not instr_type or not profile:
                    print("❌ Usage: instructions active <type> <profile>")
                    return

                available_profiles = instructions_manager.get_available_profiles(instr_type)
                if profile not in available_profiles:
                    print(f"❌ Profil '{profile}' non trouvé pour {instr_type}")
                    print(f"   Profils disponibles: {', '.join(available_profiles)}")
                    return

                if instructions_manager.set_active_profile(instr_type, profile):
                    print(f"✅ Profil '{profile}' activé pour {instr_type}")
                else:
                    print(f"❌ Erreur lors de l'activation du profil '{profile}'")

            elif action == "delete":
                if not instr_type or not profile:
                    print("❌ Usage: instructions delete <type> <profile>")
                    return

                if profile in ["default", "html"]:
                    print(f"❌ Impossible de supprimer le profil par défaut '{profile}'")
                    return

                if instructions_manager.delete_profile(instr_type, profile):
                    print(f"✅ Profil '{instr_type}.{profile}' supprimé")
                else:
                    print(f"❌ Profil '{instr_type}.{profile}' non trouvé ou erreur")
            else:
                print("❌ Action invalide. Utilisez: list, show, set, active, delete")

        except Exception as e:
            print(f"❌ Erreur lors de la gestion des consignes: {e}")

    def run_interactive(self) -> None:
        """Lance le mode interactif"""
        print("🚀 OllamaFic CLI - Mode interactif")
        print("Tapez 'help' pour voir les commandes disponibles")

        while True:
            try:
                # Construire le prompt avec le répertoire courant
                if self.json_manager:
                    current_display = self.json_manager.get_current_path_display()
                    prompt = f"📝 {current_display} > "
                else:
                    prompt = "📝 > "

                cmd_input = input(prompt).strip()
                if not cmd_input:
                    continue

                if cmd_input.lower() in ['exit', 'quit', 'q']:
                    break

                self.parse_and_execute(cmd_input)

            except KeyboardInterrupt:
                print("\n👋 Au revoir!")
                break
            except Exception as e:
                print(f"❌ Erreur: {e}")

    def _parse_command_line(self, command_line: str) -> List[str]:
        """Parse une ligne de commande en respectant les guillemets"""
        import shlex
        try:
            return shlex.split(command_line)
        except ValueError:
            # Fallback si les guillemets ne sont pas bien fermés
            return command_line.split()

    def parse_and_execute(self, command_line: str) -> None:
        """Parse et exécute une commande"""
        parts = self._parse_command_line(command_line)
        if not parts:
            return

        # Vérifier d'abord les commandes internes (qui commencent par /)
        if parts[0].startswith("/"):
            # Commandes internes Ollama/IA (/, /set, /show, etc.)
            self.cmd_internal(command_line)
            return

        cmd = parts[0].lower()

        if cmd == "help":
            self.cmd_help()
        elif cmd == "load" and len(parts) >= 2:
            self.cmd_load(parts[1])
        elif cmd == "ls":
            path = parts[1] if len(parts) > 1 else ""
            self.cmd_ls(path)
        elif cmd == "cat" and len(parts) >= 2:
            self.cmd_cat(parts[1])
        elif cmd == "search" and len(parts) >= 2:
            self.cmd_search(parts[1])
        elif cmd == "translate" and len(parts) >= 2:
            # Nouvelle syntaxe: translate -fr "chemin"
            options = []
            path_args = []

            # Séparer les options (-fr) des arguments
            for part in parts[1:]:
                if part.startswith('-'):
                    options.append(part)
                else:
                    path_args.append(part)

            if path_args:
                path = path_args[0]
                self.cmd_translate(options, path)
            else:
                print("❌ Usage: translate -fr \"chemin\"")
        elif cmd == "cd":
            if len(parts) > 1:
                self.cmd_cd(parts[1])
            else:
                self.cmd_cd()  # Afficher le chemin courant
        elif cmd == "process" and len(parts) >= 3:
            path = parts[1]
            instruction = " ".join(parts[2:])
            model = self.get_preferred_model()
            # Chercher si un modèle est spécifié après l'instruction
            if instruction.count('"') >= 2:
                end_quote = instruction.rfind('"')
                if end_quote < len(instruction) - 1:
                    remaining = instruction[end_quote + 1:].strip()
                    if remaining:
                        model = remaining
                        instruction = instruction[:end_quote + 1]
            instruction = instruction.strip('"')
            self.cmd_process(path, instruction, model)
        elif cmd == "save":
            file_path = parts[1] if len(parts) > 1 else None
            self.cmd_save(file_path)
        elif cmd == "tag" and len(parts) >= 3:
            action = parts[1]
            tag = parts[2]
            self.cmd_tag(action, tag)
        elif cmd == "context":
            context = " ".join(parts[1:]) if len(parts) > 1 else ""
            self.cmd_context(context)
        elif cmd == "session" and len(parts) >= 2:
            action = parts[1]
            model = parts[2] if len(parts) > 2 else self.get_preferred_model()
            self.cmd_session(action, model)
        elif cmd == "models":
            self.cmd_models()
        elif cmd == "validate":
            action = parts[1] if len(parts) > 1 else "list"
            self.cmd_validate(action)
        elif cmd == "ia" and len(parts) >= 2:
            message = " ".join(parts[1:])
            # Enlever les guillemets si présents
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]
            self.cmd_ia(message)
        elif cmd == "provider" and len(parts) >= 2:
            action = parts[1]
            provider_name = parts[2] if len(parts) > 2 else ""
            self.cmd_provider(action, provider_name)
        elif cmd == "instructions" or cmd == "instr":
            if len(parts) == 1:
                self.cmd_instructions("list")
            elif parts[1] == "list":
                self.cmd_instructions("list")
            elif parts[1] == "show" and len(parts) >= 4:
                instr_type = parts[2]
                profile = parts[3]
                self.cmd_instructions("show", instr_type, profile)
            elif parts[1] == "set" and len(parts) >= 5:
                instr_type = parts[2]
                profile = parts[3]
                content = " ".join(parts[4:])
                self.cmd_instructions("set", instr_type, profile, content)
            elif parts[1] == "active" and len(parts) >= 4:
                instr_type = parts[2]
                profile = parts[3]
                self.cmd_instructions("active", instr_type, profile)
            elif parts[1] == "delete" and len(parts) >= 4:
                instr_type = parts[2]
                profile = parts[3]
                self.cmd_instructions("delete", instr_type, profile)
            else:
                print("❌ Usage: instructions [list|show|set|active|delete] [type] [profile] [content]")
        else:
            print(f"❌ Commande inconnue: {cmd}. Tapez 'help' pour voir les commandes.")

def main():
    """Point d'entrée principal pour le CLI"""
    parser = argparse.ArgumentParser(description="OllamaFic CLI")
    parser.add_argument("--file", "-f", help="Fichier JSON à charger au démarrage")
    parser.add_argument("--command", "-c", help="Commande à exécuter directement")

    args = parser.parse_args()

    cli = CLIInterface()

    # Charger un fichier au démarrage si spécifié
    if args.file:
        cli.cmd_load(args.file)

    # Exécuter une commande directement ou lancer le mode interactif
    if args.command:
        cli.parse_and_execute(args.command)
    else:
        cli.run_interactive()

if __name__ == "__main__":
    main()