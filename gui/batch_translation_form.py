# -*- coding: utf-8 -*-
"""
Formulaire de traitement par lot (batch) pour les sous-arbres.

Permet différents types de traitements par lot avec système d'onglets:
- Traduction
- Rechercher & Remplacer
- Annuler modifications

Avec barre de progression et possibilité d'interruption.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import sys
import os

# Ajouter le répertoire gui au path pour les imports
sys.path.insert(0, os.path.dirname(__file__))

from batch_tabs.translation_tab import TranslationTab
from batch_tabs.search_replace_tab import SearchReplaceTab
from batch_tabs.undo_tab import UndoTab


class BatchTranslationForm(ttk.Frame):
    """
    Formulaire pour les traitements par lot sur un sous-arbre.

    Affiche:
    - Système d'onglets avec différents types de traitements
    - Barre de progression avec chemin actuel
    - Bouton d'interruption
    """

    def __init__(self, parent, visible_languages: list = None,
                 on_batch_translate: Optional[Callable] = None,
                 on_batch_deepl_translate: Optional[Callable] = None,
                 on_clear_unvalidated: Optional[Callable] = None,
                 on_search_replace: Optional[Callable] = None,
                 on_undo: Optional[Callable] = None,
                 got_manager=None,
                 translation_config: dict = None):
        """
        Initialise le formulaire de traitement par lot.

        Args:
            parent: Widget parent
            visible_languages: Liste des langues visibles (ex: ["fr", "en"])
            on_batch_translate: Callback(langue, selected_paths) pour la traduction
            on_batch_deepl_translate: Callback(langue, selected_paths) pour la traduction DeepL
            on_clear_unvalidated: Callback(langue, selected_paths) pour effacer les non validés
            on_search_replace: Callback(search, replace, selected_paths, options) pour rechercher/remplacer
            on_undo: Callback(selected_paths, mode) pour annuler les modifications
            got_manager: GotJsonManager pour accéder aux données
            translation_config: Configuration de traduction
        """
        super().__init__(parent)

        self.visible_languages = visible_languages or []
        self.on_batch_translate = on_batch_translate
        self.on_batch_deepl_translate = on_batch_deepl_translate
        self.on_clear_unvalidated = on_clear_unvalidated
        self.on_search_replace = on_search_replace
        self.on_undo = on_undo
        self.got_manager = got_manager
        self.translation_config = translation_config or {}

        self.current_path = None
        self.is_processing = False
        self.all_leaves = []  # Liste de tous les chemins de feuilles

        self._create_widgets()

    def _create_widgets(self):
        """Crée les widgets du formulaire."""
        # === Header (toujours visible) ===
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(header_frame, text="📦 Traitements par lot",
                 font=("Arial", 12, "bold")).pack(anchor="w")

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=5)

        # === Chemin sélectionné (toujours visible) ===
        path_frame = ttk.Frame(self)
        path_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(path_frame, text="📍 Branche:",
                 font=("Arial", 9, "bold")).pack(side="left")

        self.path_label = ttk.Label(path_frame, text="(aucune sélection)",
                                    font=("Arial", 9), foreground="gray")
        self.path_label.pack(side="left", padx=5)

        # === CONFIGURATION FRAME (masqué pendant traitement) ===
        self.config_frame = ttk.Frame(self)
        self.config_frame.pack(fill="both", expand=True)

        # === Notebook (système d'onglets) ===
        self.notebook = ttk.Notebook(self.config_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglet 1: Traduction
        self.translation_tab = TranslationTab(
            self.notebook,
            visible_languages=self.visible_languages,
            on_translate=self._on_translate_clicked,
            on_deepl_translate=self._on_deepl_translate_clicked,
            on_clear_unvalidated=self._on_clear_unvalidated_clicked,
            got_manager=self.got_manager,
            translation_config=self.translation_config
        )
        self.notebook.add(self.translation_tab, text="🔄 Traduction")

        # Onglet 2: Rechercher & Remplacer
        self.search_replace_tab = SearchReplaceTab(
            self.notebook,
            on_search_replace=self._on_search_replace_clicked
        )
        self.notebook.add(self.search_replace_tab, text="🔍 Rechercher & Remplacer")

        # Onglet 3: Annuler modifications
        self.undo_tab = UndoTab(
            self.notebook,
            on_undo=self._on_undo_clicked
        )
        self.notebook.add(self.undo_tab, text="↶ Annuler modifications")

        # === PROGRESS FRAME (masqué par défaut, remplace config_frame pendant traitement) ===
        self.progress_frame = ttk.Frame(self)
        # Ne pas pack() par défaut, sera affiché pendant le traitement

        # Barre de progression
        progress_bar_frame = ttk.Frame(self.progress_frame)
        progress_bar_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(progress_bar_frame, text="Progression:",
                 font=("Arial", 9, "bold")).pack(anchor="w")

        self.progress_bar = ttk.Progressbar(progress_bar_frame, mode='determinate')
        self.progress_bar.pack(fill="x", pady=5)

        # Label de progression
        self.progress_label = ttk.Label(progress_bar_frame, text="0 / 0",
                                       font=("Arial", 8))
        self.progress_label.pack(anchor="w")

        # Chemin en cours
        current_path_frame = ttk.Frame(self.progress_frame)
        current_path_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(current_path_frame, text="En cours:",
                 font=("Arial", 9, "bold")).pack(anchor="w")

        self.current_path_label = ttk.Label(current_path_frame, text="",
                                           font=("Arial", 8), foreground="blue",
                                           wraplength=400)
        self.current_path_label.pack(anchor="w", padx=5)

        # Bouton Stop
        self.stop_button = ttk.Button(self.progress_frame, text="⏹ Arrêter",
                                     command=self._on_stop_clicked)
        self.stop_button.pack(pady=10)

    def _on_translate_clicked(self, lang: str, selected_paths: list):
        """Callback pour la traduction."""
        if self.on_batch_translate and not self.is_processing:
            self.on_batch_translate(lang, selected_paths)

    def _on_deepl_translate_clicked(self, lang: str, selected_paths: list):
        """Callback pour la traduction DeepL."""
        if self.on_batch_deepl_translate and not self.is_processing:
            self.on_batch_deepl_translate(lang, selected_paths)

    def _on_clear_unvalidated_clicked(self, lang: str, selected_paths: list):
        """Callback pour effacer les non validés."""
        if self.on_clear_unvalidated and not self.is_processing:
            self.on_clear_unvalidated(lang, selected_paths)

    def _on_search_replace_clicked(self, search_text: str, replace_text: str,
                                   selected_paths: list, options: dict):
        """Callback pour rechercher/remplacer."""
        if self.on_search_replace and not self.is_processing:
            self.on_search_replace(search_text, replace_text, selected_paths, options)

    def _on_undo_clicked(self, selected_paths: list, mode: str):
        """Callback pour annuler les modifications."""
        if self.on_undo and not self.is_processing:
            self.on_undo(selected_paths, mode)

    def set_visible_languages(self, languages: list):
        """
        Définit les langues visibles.

        Args:
            languages: Liste des codes langues (ex: ["fr", "en"])
        """
        self.visible_languages = languages
        self.translation_tab.set_visible_languages(languages)

    def set_got_manager(self, got_manager):
        """
        Définit le GotJsonManager.

        Args:
            got_manager: Instance de GotJsonManager
        """
        self.got_manager = got_manager
        self.translation_tab.set_got_manager(got_manager)

    def set_translation_config(self, config: dict):
        """
        Définit la configuration de traduction.

        Args:
            config: Configuration de traduction
        """
        self.translation_config = config
        self.translation_tab.set_translation_config(config)

    def load_branch(self, path: str, leaves: list):
        """
        Charge une branche pour traitement par lot.

        Args:
            path: Chemin de la branche (ex: "app/settings")
            leaves: Liste des chemins des feuilles traduisibles (ex: ["entries/Demon/name", ...])
        """
        self.current_path = path
        self.path_label.config(text=path, foreground="blue")

        # Sauvegarder la liste des feuilles
        self.all_leaves = leaves

        # Charger les champs dans tous les onglets
        self.translation_tab.load_fields(leaves)
        self.search_replace_tab.load_fields(leaves)
        self.undo_tab.load_fields(leaves)

        # Réinitialiser l'état
        self.is_processing = False
        self._hide_progress()
        self._enable_tabs()

    def start_processing(self, total_items: int):
        """
        Démarre le traitement (affiche la barre de progression).

        Args:
            total_items: Nombre total d'éléments à traiter
        """
        self.is_processing = True
        self._disable_tabs()
        self._show_progress()

        self.progress_bar['maximum'] = total_items
        self.progress_bar['value'] = 0
        self.progress_label.config(text=f"0 / {total_items}")
        self.current_path_label.config(text="Initialisation...")

    def update_progress(self, current: int, total: int, current_path: str):
        """
        Met à jour la barre de progression.

        Args:
            current: Nombre d'éléments traités
            total: Nombre total d'éléments
            current_path: Chemin en cours de traitement
        """
        self.progress_bar['value'] = current
        self.progress_label.config(text=f"{current} / {total}")
        self.current_path_label.config(text=current_path)

        # Forcer la mise à jour de l'interface
        self.update_idletasks()

    def finish_processing(self, success: bool = True):
        """
        Termine le traitement.

        Args:
            success: True si terminé avec succès, False si interrompu
        """
        self.is_processing = False
        self._enable_tabs()

        if success:
            self.current_path_label.config(text="✓ Traitement terminé avec succès",
                                          foreground="green")
        else:
            self.current_path_label.config(text="⏹ Traitement interrompu",
                                          foreground="orange")

        # Cacher la barre de progression après 3 secondes
        self.after(3000, self._hide_progress)

    def _on_stop_clicked(self):
        """Appelé lors du clic sur le bouton Stop."""
        self.is_processing = False
        # Le traitement doit vérifier is_processing périodiquement

    def _show_progress(self):
        """Affiche la zone de progression et cache la configuration."""
        self.config_frame.pack_forget()  # Cacher la configuration
        self.progress_frame.pack(fill="both", expand=True, padx=10, pady=10)  # Afficher la progression

    def _hide_progress(self):
        """Cache la zone de progression et réaffiche la configuration."""
        self.progress_frame.pack_forget()  # Cacher la progression
        self.config_frame.pack(fill="both", expand=True)  # Réafficher la configuration

    def _enable_tabs(self):
        """Active tous les boutons des onglets."""
        self.translation_tab.enable_buttons()
        self.search_replace_tab.enable_button()
        self.undo_tab.enable_button()

    def _disable_tabs(self):
        """Désactive tous les boutons des onglets."""
        self.translation_tab.disable_buttons()
        self.search_replace_tab.disable_button()
        self.undo_tab.disable_button()

    def is_stopped(self) -> bool:
        """
        Vérifie si l'utilisateur a demandé l'arrêt.

        Returns:
            True si l'arrêt a été demandé
        """
        return not self.is_processing

    def get_selected_leaves(self) -> list:
        """
        Retourne la liste des feuilles sélectionnées dans l'onglet actif.

        Returns:
            Liste des chemins des feuilles cochées
        """
        # Déterminer quel onglet est actif
        current_tab = self.notebook.index(self.notebook.select())

        if current_tab == 0:  # Onglet traduction
            return self.translation_tab.field_selector.get_selected_paths()
        elif current_tab == 1:  # Onglet search/replace
            return self.search_replace_tab.field_selector.get_selected_paths()
        elif current_tab == 2:  # Onglet undo
            return self.undo_tab.field_selector.get_selected_paths()

        return []
