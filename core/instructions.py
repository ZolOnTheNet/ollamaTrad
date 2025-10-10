"""
Gestionnaire des consignes et instructions configurables
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class InstructionsManager:
    """Gestionnaire des consignes configurables pour traductions et processing"""

    def __init__(self, config_path: str = "config/settings.json"):
        """Initialise le gestionnaire avec le fichier de configuration"""
        self.config_path = config_path
        self.config = self._load_config()
        self.instructions = self.config.get("instructions", {})

    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier JSON"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Retourne la configuration par défaut"""
        return {
            "instructions": {
                "translation": {
                    "default": "Tu es un assistant de traduction expert.\nTraduis le texte suivant de {source_lang} vers {target_lang}.\nRéponds uniquement avec la traduction, sans explication.",
                    "html": "Tu es un assistant de traduction expert.\nTraduis le texte suivant de {source_lang} vers {target_lang}.\nIMPORTANT: Préserve EXACTEMENT toute la structure HTML, les balises, attributs et formatage.\nTraduis uniquement le contenu textuel entre les balises, pas les balises elles-mêmes.\nRéponds uniquement avec la traduction, sans explication.",
                    "custom": ""
                },
                "processing": {
                    "default": "Tu es un assistant expert pour le traitement de données JSON.\nInstruction: {instruction}\nRéponds uniquement avec le contenu traité, sans formatage JSON ni explication.",
                    "custom": ""
                },
                "active_profiles": {
                    "translation": "default",
                    "processing": "default"
                }
            }
        }

    def save_config(self) -> bool:
        """Sauvegarde la configuration dans le fichier JSON"""
        try:
            # Créer le répertoire si nécessaire
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            return False

    def get_instruction(self, instruction_type: str, profile: Optional[str] = None) -> str:
        """
        Récupère une instruction selon le type et le profil

        Args:
            instruction_type: 'translation' ou 'processing'
            profile: nom du profil (default, html, custom, etc.)

        Returns:
            L'instruction formatée
        """
        if instruction_type not in self.instructions:
            return ""

        # Utiliser le profil actif si non spécifié
        if profile is None:
            profile = self.instructions.get("active_profiles", {}).get(instruction_type, "default")

        return self.instructions[instruction_type].get(profile, "")

    def get_translation_instruction(self, source_lang: str = "auto", target_lang: str = "fr",
                                  profile: Optional[str] = None, context: str = "") -> str:
        """
        Récupère l'instruction de traduction formatée

        Args:
            source_lang: langue source
            target_lang: langue cible
            profile: profil à utiliser (default, html, custom)
            context: contexte additionnel

        Returns:
            L'instruction complète formatée
        """
        instruction = self.get_instruction("translation", profile)

        # Formatage des variables
        formatted = instruction.format(
            source_lang=source_lang,
            target_lang=target_lang
        )

        # Ajouter le contexte si fourni
        if context:
            formatted += f"\n{context}"

        return formatted

    def get_processing_instruction(self, instruction: str, profile: Optional[str] = None,
                                 context: str = "") -> str:
        """
        Récupère l'instruction de processing formatée

        Args:
            instruction: instruction spécifique
            profile: profil à utiliser
            context: contexte additionnel

        Returns:
            L'instruction complète formatée
        """
        base_instruction = self.get_instruction("processing", profile)

        # Formatage des variables
        formatted = base_instruction.format(instruction=instruction)

        # Ajouter le contexte si fourni
        if context:
            formatted += f"\n{context}"

        return formatted

    def set_instruction(self, instruction_type: str, profile: str, content: str) -> bool:
        """
        Définit une instruction pour un type et profil donnés

        Args:
            instruction_type: 'translation' ou 'processing'
            profile: nom du profil
            content: contenu de l'instruction

        Returns:
            True si succès
        """
        if instruction_type not in self.instructions:
            self.instructions[instruction_type] = {}

        self.instructions[instruction_type][profile] = content
        self.config["instructions"] = self.instructions
        return self.save_config()

    def set_active_profile(self, instruction_type: str, profile: str) -> bool:
        """
        Définit le profil actif pour un type d'instruction

        Args:
            instruction_type: 'translation' ou 'processing'
            profile: nom du profil à activer

        Returns:
            True si succès
        """
        if "active_profiles" not in self.instructions:
            self.instructions["active_profiles"] = {}

        self.instructions["active_profiles"][instruction_type] = profile
        self.config["instructions"] = self.instructions
        return self.save_config()

    def get_available_profiles(self, instruction_type: str) -> List[str]:
        """
        Retourne la liste des profils disponibles pour un type d'instruction

        Args:
            instruction_type: 'translation' ou 'processing'

        Returns:
            Liste des noms de profils
        """
        return list(self.instructions.get(instruction_type, {}).keys())

    def get_active_profile(self, instruction_type: str) -> str:
        """
        Retourne le profil actif pour un type d'instruction

        Args:
            instruction_type: 'translation' ou 'processing'

        Returns:
            Nom du profil actif
        """
        return self.instructions.get("active_profiles", {}).get(instruction_type, "default")

    def delete_profile(self, instruction_type: str, profile: str) -> bool:
        """
        Supprime un profil d'instruction

        Args:
            instruction_type: 'translation' ou 'processing'
            profile: nom du profil à supprimer

        Returns:
            True si succès
        """
        if instruction_type in self.instructions and profile in self.instructions[instruction_type]:
            # Ne pas supprimer les profils par défaut
            if profile in ["default", "html"]:
                return False

            del self.instructions[instruction_type][profile]

            # Si c'était le profil actif, revenir au défaut
            if self.get_active_profile(instruction_type) == profile:
                self.set_active_profile(instruction_type, "default")

            self.config["instructions"] = self.instructions
            return self.save_config()

        return False

    def get_instructions_summary(self) -> Dict[str, Any]:
        """
        Retourne un résumé des instructions configurées

        Returns:
            Dictionnaire avec le résumé des instructions
        """
        summary = {}

        for instr_type in ["translation", "processing"]:
            profiles = self.get_available_profiles(instr_type)
            active = self.get_active_profile(instr_type)

            summary[instr_type] = {
                "active_profile": active,
                "available_profiles": profiles,
                "profiles_count": len(profiles)
            }

        return summary