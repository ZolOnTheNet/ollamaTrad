# -*- coding: utf-8 -*-
"""
Onglet de traduction par lot.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from field_selector import FieldSelector


class TranslationTab(ttk.Frame):
    """Onglet pour la traduction par lot de champs sélectionnés."""

    def __init__(self, parent, visible_languages: list = None,
                 on_translate: Optional[Callable] = None,
                 on_deepl_translate: Optional[Callable] = None,
                 got_manager=None,
                 translation_config: dict = None):
        """
        Initialise l'onglet de traduction.

        Args:
            parent: Widget parent
            visible_languages: Liste des langues visibles (ex: ["fr", "en"])
            on_translate: Callback(langue, selected_paths) appelé lors du clic sur un bouton langue
            on_deepl_translate: Callback(langue, selected_paths) appelé lors du clic sur un bouton DeepL
            got_manager: GotJsonManager pour accéder aux données
            translation_config: Configuration de traduction (pour vérifier si DeepL est activé)
        """
        super().__init__(parent)

        self.visible_languages = visible_languages or []
        self.on_translate = on_translate
        self.on_deepl_translate = on_deepl_translate
        self.got_manager = got_manager
        self.translation_config = translation_config or {}

        self._create_widgets()

    def _create_widgets(self):
        """Crée les widgets de l'onglet."""
        # === Sélecteur de champs ===
        self.field_selector = FieldSelector(
            self,
            title="Champs à traduire (si pas validé)",
            on_selection_changed=self.on_selection_changed
        )
        self.field_selector.pack(fill="both", expand=True, padx=10, pady=10)

        # === Boutons de langue ===
        self.buttons_frame = ttk.LabelFrame(self, text="Langues cibles", padding=10)
        self.buttons_frame.pack(fill="x", padx=10, pady=10)

        self.language_buttons = {}
        self._create_language_buttons()

    def _create_language_buttons(self):
        """Crée les boutons pour chaque langue visible."""
        # Vider les anciens boutons
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        self.language_buttons.clear()

        if not self.visible_languages:
            ttk.Label(self.buttons_frame, text="Aucune langue configurée",
                     foreground="gray").pack()
            return

        # Vérifier si DeepL est activé
        deepl_enabled = self.translation_config.get("ai_config", {}).get("deepl", {}).get("enabled", False)

        # Créer un bouton par langue
        for lang in self.visible_languages:
            # Frame pour regrouper les boutons de cette langue
            lang_frame = ttk.Frame(self.buttons_frame)
            lang_frame.pack(fill="x", pady=3)

            # Bouton de traduction normale
            btn = ttk.Button(lang_frame,
                           text=f"🔄 Traduire en {lang.upper()}",
                           command=lambda l=lang: self._on_language_clicked(l))
            btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
            self.language_buttons[lang] = btn

            # Bouton DeepL si activé
            if deepl_enabled and self.on_deepl_translate:
                # Récupérer le nom complet de la langue
                known_languages = self.translation_config.get("known_languages", {})
                lang_name = known_languages.get(lang, lang.upper())

                deepl_btn = ttk.Button(lang_frame,
                                     text=f"🌐 DeepL: {lang_name} (...)",
                                     command=lambda l=lang: self._on_deepl_clicked(l))
                deepl_btn.pack(side="left", fill="x", expand=True)
                self.language_buttons[f"deepl_{lang}"] = deepl_btn

    def _on_language_clicked(self, lang: str):
        """
        Appelé lors du clic sur un bouton de langue.

        Args:
            lang: Code langue (ex: "fr")
        """
        if self.on_translate:
            selected_paths = self.field_selector.get_selected_paths()
            self.on_translate(lang, selected_paths)

    def _on_deepl_clicked(self, lang: str):
        """
        Appelé lors du clic sur un bouton DeepL.

        Args:
            lang: Code langue (ex: "fr")
        """
        if self.on_deepl_translate:
            selected_paths = self.field_selector.get_selected_paths()
            self.on_deepl_translate(lang, selected_paths)

    def _calculate_character_count(self, paths: list, lang: str = None) -> int:
        """
        Calcule le nombre total de caractères pour les chemins sélectionnés.

        Si une langue est spécifiée, exclut les champs déjà validés pour cette langue.

        Args:
            paths: Liste des chemins des entrées
            lang: Code langue (ex: "fr") pour exclure les champs validés. Si None, compte tous les champs.

        Returns:
            Nombre total de caractères (excluant les champs validés si lang spécifié)
        """
        if not self.got_manager or not paths:
            return 0

        total_chars = 0
        for path in paths:
            try:
                entry = self.got_manager._get_entry_by_path(path)
                if isinstance(entry, dict) and "ori" in entry:
                    # Si une langue est spécifiée, vérifier si le champ est validé ou a déjà une traduction
                    if lang and lang in entry:
                        lang_data = entry[lang]
                        if isinstance(lang_data, dict):
                            is_validated = lang_data.get("valid", False)
                            translation_text = lang_data.get("text", "")

                            # Exclure si validé OU si traduction non vide (comportement du batch)
                            if is_validated or (translation_text and translation_text.strip()):
                                continue  # Ne pas compter ce champ
                        elif isinstance(lang_data, str) and lang_data.strip():
                            # Ancien format avec traduction déjà présente
                            continue  # Ne pas compter ce champ

                    # Compter les caractères du texte original
                    original_text = entry["ori"]
                    if original_text:
                        total_chars += len(original_text)
            except:
                pass

        return total_chars

    def _update_deepl_button_text(self):
        """Met à jour le texte des boutons DeepL avec le nombre de caractères."""
        if not self.got_manager:
            return

        selected_paths = self.field_selector.get_selected_paths()

        # Récupérer les noms complets des langues
        known_languages = self.translation_config.get("known_languages", {})

        for lang in self.visible_languages:
            deepl_btn_key = f"deepl_{lang}"
            if deepl_btn_key in self.language_buttons:
                # Calculer le nombre de caractères POUR CETTE LANGUE SPÉCIFIQUE
                # (exclut les champs validés ou déjà traduits pour cette langue)
                char_count = self._calculate_character_count(selected_paths, lang=lang)

                lang_name = known_languages.get(lang, lang.upper())
                btn = self.language_buttons[deepl_btn_key]
                btn.config(text=f"🌐 DeepL: {lang_name} ({char_count:,} car.)")

    def on_selection_changed(self):
        """Appelé quand la sélection des champs change."""
        self._update_deepl_button_text()

    def set_visible_languages(self, languages: list):
        """
        Définit les langues visibles.

        Args:
            languages: Liste des codes langues (ex: ["fr", "en"])
        """
        self.visible_languages = languages
        self._create_language_buttons()

    def load_fields(self, leaves: list):
        """
        Charge les champs disponibles.

        Args:
            leaves: Liste des chemins des feuilles traduisibles
        """
        self.field_selector.load_fields(leaves)
        # Mettre à jour les boutons DeepL avec le nouveau compte
        self._update_deepl_button_text()

    def set_got_manager(self, got_manager):
        """
        Définit le GotJsonManager.

        Args:
            got_manager: Instance de GotJsonManager
        """
        self.got_manager = got_manager
        self._update_deepl_button_text()

    def set_translation_config(self, config: dict):
        """
        Définit la configuration de traduction.

        Args:
            config: Configuration de traduction
        """
        self.translation_config = config
        self._create_language_buttons()

    def enable_buttons(self):
        """Active les boutons de langue."""
        for btn in self.language_buttons.values():
            btn.config(state="normal")

    def disable_buttons(self):
        """Désactive les boutons de langue."""
        for btn in self.language_buttons.values():
            btn.config(state="disabled")
