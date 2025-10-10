"""
Module d'internationalisation pour OllamaFic

Ce module fournit une solution simple d'i18n sans dépendances externes.
Il utilise des dictionnaires Python pour stocker les traductions.
"""

import json
from pathlib import Path
from typing import Dict, Any

class I18n:
    def __init__(self, default_locale: str = "fr"):
        self.current_locale = default_locale
        self.translations: Dict[str, Dict[str, str]] = {}
        self.fallback_locale = "en"
        self.load_translations()

    def load_translations(self):
        """Charge les traductions depuis les fichiers JSON"""
        translations_dir = Path(__file__).parent.parent / "translations"

        # Traductions par défaut intégrées
        self.translations = {
            "fr": {
                "app_title": "OllamaFic - Traitement intelligent de JSON",
                "file_menu": "Fichier",
                "open_file": "Ouvrir JSON",
                "save_file": "Sauvegarder",
                "quit": "Quitter",
                "session_menu": "Session",
                "start_session": "Démarrer session",
                "end_session": "Terminer session",
                "content_selected": "Contenu sélectionné",
                "operations": "Opérations",
                "result": "Résultat",
                "chat_history": "Chat & Historique",
                "metadata": "Métadonnées",
                "tags": "Tags",
                "context": "Contexte",
                "save": "Sauver",
                "apply": "Appliquer",
                "undo": "Annuler",
                "clear": "Effacer",
                "temp_save": "Sauver temp",
                "translate": "Traduire",
                "improve": "Améliorer",
                "summarize": "Résumer",
                "instruction": "Instruction",
                "execute": "Exécuter",
                "batch": "Lot",
                "process_batch": "Traiter lot",
                "stop": "Arrêter",
                "command": "Commande",
                "send": "Envoyer",
                "search": "Rechercher",
                "stats": "Statistiques",
                "ready": "Prêt",
                "no_file_loaded": "Aucun fichier chargé",
                "connecting_ollama": "Vérification d'Ollama...",
                "ollama_connected": "Ollama connecté",
                "ollama_not_connected": "Ollama non connecté",
                "starting_ollama": "Démarrage d'Ollama...",
                "processing": "Traitement en cours...",
                "translation_completed": "Traduction terminée",
                "processing_completed": "Traitement terminé",
                "modifications_applied": "Modifications appliquées",
                "action_undone": "Action annulée",
                "error": "Erreur",
                "warning": "Attention",
                "info": "Information",
                "select_text_field": "Sélectionnez un champ texte",
                "select_element": "Sélectionnez un élément dans l'arbre",
                "no_ollama_connection": "Impossible de se connecter à Ollama",
                "translation_error": "Erreur lors de la traduction",
                "processing_error": "Erreur lors du traitement",
                "batch_started": "Traitement en lot démarré",
                "batch_stopped": "Traitement en lot arrêté",
                "batch_completed": "Traitement en lot terminé",
                "result_not_saved": "Résultat non sauvegardé",
                "temp_saved": "Sauvé temporairement",
                "no_action_to_undo": "Aucune action à annuler",
                "file_loaded": "Fichier chargé",
                "file_saved": "Fichier sauvegardé"
            },
            "en": {
                "app_title": "OllamaFic - Intelligent JSON Processing",
                "file_menu": "File",
                "open_file": "Open JSON",
                "save_file": "Save",
                "quit": "Quit",
                "session_menu": "Session",
                "start_session": "Start session",
                "end_session": "End session",
                "content_selected": "Selected content",
                "operations": "Operations",
                "result": "Result",
                "chat_history": "Chat & History",
                "metadata": "Metadata",
                "tags": "Tags",
                "context": "Context",
                "save": "Save",
                "apply": "Apply",
                "undo": "Undo",
                "clear": "Clear",
                "temp_save": "Temp save",
                "translate": "Translate",
                "improve": "Improve",
                "summarize": "Summarize",
                "instruction": "Instruction",
                "execute": "Execute",
                "batch": "Batch",
                "process_batch": "Process batch",
                "stop": "Stop",
                "command": "Command",
                "send": "Send",
                "search": "Search",
                "stats": "Statistics",
                "ready": "Ready",
                "no_file_loaded": "No file loaded",
                "connecting_ollama": "Checking Ollama...",
                "ollama_connected": "Ollama connected",
                "ollama_not_connected": "Ollama not connected",
                "starting_ollama": "Starting Ollama...",
                "processing": "Processing...",
                "translation_completed": "Translation completed",
                "processing_completed": "Processing completed",
                "modifications_applied": "Modifications applied",
                "action_undone": "Action undone",
                "error": "Error",
                "warning": "Warning",
                "info": "Information",
                "select_text_field": "Select a text field",
                "select_element": "Select an element in the tree",
                "no_ollama_connection": "Cannot connect to Ollama",
                "translation_error": "Translation error",
                "processing_error": "Processing error",
                "batch_started": "Batch processing started",
                "batch_stopped": "Batch processing stopped",
                "batch_completed": "Batch processing completed",
                "result_not_saved": "Result not saved",
                "temp_saved": "Temporarily saved",
                "no_action_to_undo": "No action to undo",
                "file_loaded": "File loaded",
                "file_saved": "File saved"
            }
        }

        # Charger des fichiers de traduction externes s'ils existent
        if translations_dir.exists():
            for locale_file in translations_dir.glob("*.json"):
                locale = locale_file.stem
                try:
                    with open(locale_file, 'r', encoding='utf-8') as f:
                        external_translations = json.load(f)
                        if locale in self.translations:
                            self.translations[locale].update(external_translations)
                        else:
                            self.translations[locale] = external_translations
                except Exception as e:
                    print(f"Erreur lors du chargement de {locale_file}: {e}")

    def set_locale(self, locale: str):
        """Change la langue actuelle"""
        if locale in self.translations:
            self.current_locale = locale
            return True
        return False

    def get_available_locales(self) -> list:
        """Retourne la liste des langues disponibles"""
        return list(self.translations.keys())

    def _(self, key: str, **kwargs) -> str:
        """
        Traduit une clé dans la langue actuelle

        Args:
            key: La clé de traduction
            **kwargs: Variables à interpoler dans la traduction

        Returns:
            Le texte traduit ou la clé si non trouvé
        """
        # Essayer la langue actuelle
        if self.current_locale in self.translations:
            if key in self.translations[self.current_locale]:
                text = self.translations[self.current_locale][key]
                return text.format(**kwargs) if kwargs else text

        # Fallback vers l'anglais
        if self.fallback_locale in self.translations:
            if key in self.translations[self.fallback_locale]:
                text = self.translations[self.fallback_locale][key]
                return text.format(**kwargs) if kwargs else text

        # Retourner la clé si pas de traduction
        return key

    def add_translation(self, locale: str, key: str, value: str):
        """Ajoute une traduction dynamiquement"""
        if locale not in self.translations:
            self.translations[locale] = {}
        self.translations[locale][key] = value

# Instance globale
_i18n = I18n()

def get_i18n() -> I18n:
    """Retourne l'instance i18n globale"""
    return _i18n

def _(key: str, **kwargs) -> str:
    """Raccourci pour traduire une clé"""
    return _i18n._(key, **kwargs)

def set_locale(locale: str) -> bool:
    """Raccourci pour changer la langue"""
    return _i18n.set_locale(locale)

def get_available_locales() -> list:
    """Raccourci pour obtenir les langues disponibles"""
    return _i18n.get_available_locales()