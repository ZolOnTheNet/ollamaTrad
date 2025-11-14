# -*- coding: utf-8 -*-
"""
Onglet de recherche et remplacement par lot - Version améliorée.

Permet de :
1. Remplacer dans le champ de traduction (avec respect de la casse)
2. Pré-remplir depuis l'original si correspondance exacte
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from field_selector import FieldSelector


class SearchReplaceTab(ttk.Frame):
    """Onglet pour rechercher et remplacer dans les champs sélectionnés."""

    def __init__(self, parent,
                 visible_languages: list = None,
                 on_search_replace: Optional[Callable] = None,
                 got_manager=None,
                 translation_config: dict = None):
        """
        Initialise l'onglet de recherche/remplacement.

        Args:
            parent: Widget parent
            visible_languages: Liste des langues visibles
            on_search_replace: Callback(lang, mode, search, replace, selected_paths)
            got_manager: GotJsonManager pour calculer les aperçus
            translation_config: Configuration pour les noms de langues
        """
        super().__init__(parent)

        self.visible_languages = visible_languages or []
        self.on_search_replace = on_search_replace
        self.got_manager = got_manager
        self.translation_config = translation_config or {}

        self._create_widgets()

    def _create_widgets(self):
        """Crée les widgets de l'onglet."""
        # === Sélecteur de champs (hauteur limitée) ===
        selector_frame = ttk.Frame(self, height=200)
        selector_frame.pack(fill="both", expand=False, padx=10, pady=(10, 0))
        selector_frame.pack_propagate(False)

        self.field_selector = FieldSelector(
            selector_frame,
            title="Champs à traiter"
        )
        self.field_selector.pack(fill="both", expand=True)

        # === Formulaire de recherche/remplacement ===
        form_frame = ttk.LabelFrame(self, text="📝 Recherche et Remplacement", padding=10)
        form_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Champ 1 : Texte à rechercher + label de comptage
        search_frame = ttk.Frame(form_frame)
        search_frame.pack(fill="x", pady=5)

        ttk.Label(search_frame, text="🔍 Rechercher :", width=15, anchor="e").pack(side="left", padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, font=("Arial", 10))
        self.search_entry.pack(side="left", fill="x", expand=True)

        # Label de comptage (nombre de champs trouvés)
        self.count_label = ttk.Label(search_frame, text="", font=("Arial", 9), foreground="blue")
        self.count_label.pack(side="left", padx=(10, 0))

        # Lier la modification du champ de recherche au recalcul
        self.search_entry.bind("<KeyRelease>", lambda e: self._update_count_label())

        # Champ 2 : Texte de remplacement
        replace_frame = ttk.Frame(form_frame)
        replace_frame.pack(fill="x", pady=5)

        ttk.Label(replace_frame, text="✏️ Remplacer par :", width=15, anchor="e").pack(side="left", padx=(0, 5))
        self.replace_entry = ttk.Entry(replace_frame, font=("Arial", 10))
        self.replace_entry.pack(side="left", fill="x", expand=True)

        # === Groupe de choix du mode (global) ===
        mode_frame = ttk.Frame(form_frame)
        mode_frame.pack(fill="x", pady=(10, 5))

        ttk.Label(mode_frame, text="Mode :", width=15, anchor="e").pack(side="left", padx=(0, 5))

        self.mode_var = tk.StringVar(value="translation")

        ttk.Radiobutton(mode_frame,
                       text="Dans la traduction",
                       variable=self.mode_var,
                       value="translation",
                       command=self._update_count_label).pack(side="left", padx=5)

        ttk.Radiobutton(mode_frame,
                       text="Depuis Ori",
                       variable=self.mode_var,
                       value="from_ori",
                       command=self._update_count_label).pack(side="left", padx=5)

        # === Boutons par langue (avec scrollbar) ===
        buttons_container = ttk.Frame(form_frame)
        buttons_container.pack(fill="both", expand=True, pady=(10, 0))

        # Canvas avec scrollbar
        canvas = tk.Canvas(buttons_container, highlightthickness=0, height=150)
        scrollbar = ttk.Scrollbar(buttons_container, orient="vertical", command=canvas.yview)

        self.buttons_frame = ttk.Frame(canvas)
        self.buttons_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.buttons_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.language_buttons = {}
        self._create_language_buttons()

    def _create_language_buttons(self):
        """Crée des boutons simples pour chaque langue."""
        # Vider les anciens boutons
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()
        self.language_buttons.clear()

        if not self.visible_languages:
            ttk.Label(self.buttons_frame, text="Aucune langue configurée",
                     foreground="gray").pack()
            return

        known_languages = self.translation_config.get("known_languages", {})

        # Créer un bouton simple par langue
        for lang in self.visible_languages:
            lang_name = known_languages.get(lang, lang.upper())

            # Bouton simple
            btn = ttk.Button(self.buttons_frame,
                           text=f"🔄 Appliquer sur {lang_name}",
                           command=lambda l=lang: self._on_execute_clicked(l))
            btn.pack(fill="x", pady=3, padx=5)
            self.language_buttons[f"btn_{lang}"] = btn

    def _on_execute_clicked(self, lang: str):
        """
        Appelé lors du clic sur un bouton d'exécution.

        Args:
            lang: Code langue
        """
        if not self.on_search_replace:
            return

        search_text = self.search_entry.get().strip()
        replace_text = self.replace_entry.get().strip()

        if not search_text:
            from tkinter import messagebox
            messagebox.showwarning("Champ vide", "Veuillez saisir un texte à rechercher.")
            return

        # Utiliser le mode global
        mode = self.mode_var.get()

        selected_paths = self.field_selector.get_selected_paths()

        # Appeler le callback
        self.on_search_replace(lang, mode, search_text, replace_text, selected_paths)

    def _update_count_label(self):
        """Met à jour le label indiquant le nombre de champs trouvés."""
        search_text = self.search_entry.get().strip()

        if not search_text:
            self.count_label.config(text="")
            return

        mode = self.mode_var.get()
        total_count = self._calculate_total_found_count(mode, search_text)

        if total_count > 0:
            self.count_label.config(text=f"({total_count} champ{'s' if total_count > 1 else ''} trouvé{'s' if total_count > 1 else ''})")
        else:
            self.count_label.config(text="(0 champ trouvé)")

    def _calculate_total_found_count(self, mode: str, search: str) -> int:
        """
        Calcule le nombre TOTAL de champs trouvés (tous les champs sélectionnés).

        Args:
            mode: "translation" ou "from_ori"
            search: Texte à rechercher

        Returns:
            Nombre total de champs où le texte est trouvé
        """
        if not self.got_manager or not search:
            return 0

        count = 0
        selected_paths = self.field_selector.get_selected_paths()

        for path in selected_paths:
            try:
                entry = self.got_manager._get_entry_by_path(path)
                if not isinstance(entry, dict) or "ori" not in entry:
                    continue

                if mode == "translation":
                    # Recherche dans les champs de traduction de TOUTES les langues
                    for lang in self.visible_languages:
                        if lang in entry:
                            lang_data = entry[lang]
                            text = ""
                            if isinstance(lang_data, dict):
                                text = lang_data.get("text", "")
                            elif isinstance(lang_data, str):
                                text = lang_data

                            if search in text:
                                count += 1
                                break  # Compter le champ une seule fois même s'il est trouvé dans plusieurs langues

                elif mode == "from_ori":
                    # Remplacement depuis l'original
                    ori = entry.get("ori", "")
                    if ori == search:
                        count += 1

            except:
                continue

        return count

    def update_button_counts(self):
        """Met à jour le label de comptage (plus utilisé sur les boutons)."""
        self._update_count_label()

    def load_fields(self, leaves: list):
        """
        Charge les champs disponibles.

        Args:
            leaves: Liste des chemins des feuilles
        """
        self.field_selector.load_fields(leaves)

    def set_visible_languages(self, languages: list):
        """Définit les langues visibles."""
        self.visible_languages = languages
        self._create_language_buttons()

    def enable_button(self):
        """Active les boutons d'exécution."""
        for lang in self.visible_languages:
            btn = self.language_buttons.get(f"btn_{lang}")
            if btn:
                btn.config(state="normal")

    def disable_button(self):
        """Désactive les boutons d'exécution."""
        for lang in self.visible_languages:
            btn = self.language_buttons.get(f"btn_{lang}")
            if btn:
                btn.config(state="disabled")
