# -*- coding: utf-8 -*-
"""
Onglet de recherche et remplacement par lot.
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

    def __init__(self, parent, on_search_replace: Optional[Callable] = None):
        """
        Initialise l'onglet de recherche/remplacement.

        Args:
            parent: Widget parent
            on_search_replace: Callback(search_text, replace_text, selected_paths, use_regex)
        """
        super().__init__(parent)

        self.on_search_replace = on_search_replace

        self._create_widgets()

    def _create_widgets(self):
        """Crée les widgets de l'onglet."""
        # === Sélecteur de champs ===
        self.field_selector = FieldSelector(self, title="Champs à traiter")
        self.field_selector.pack(fill="both", expand=True, padx=10, pady=10)

        # === Zone de recherche/remplacement ===
        search_frame = ttk.LabelFrame(self, text="Rechercher & Remplacer", padding=10)
        search_frame.pack(fill="x", padx=10, pady=10)

        # Rechercher
        search_label_frame = ttk.Frame(search_frame)
        search_label_frame.pack(fill="x", pady=5)

        ttk.Label(search_label_frame, text="🔍 Rechercher:",
                 font=("Arial", 9, "bold"), width=15).pack(side="left")

        self.search_entry = ttk.Entry(search_label_frame, font=("Arial", 10))
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Remplacer par
        replace_label_frame = ttk.Frame(search_frame)
        replace_label_frame.pack(fill="x", pady=5)

        ttk.Label(replace_label_frame, text="✏️ Remplacer par:",
                 font=("Arial", 9, "bold"), width=15).pack(side="left")

        self.replace_entry = ttk.Entry(replace_label_frame, font=("Arial", 10))
        self.replace_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Options
        options_frame = ttk.Frame(search_frame)
        options_frame.pack(fill="x", pady=5)

        self.case_sensitive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Sensible à la casse",
                       variable=self.case_sensitive_var).pack(side="left", padx=5)

        self.use_regex_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Utiliser regex",
                       variable=self.use_regex_var).pack(side="left", padx=5)

        self.whole_word_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Mot entier uniquement",
                       variable=self.whole_word_var).pack(side="left", padx=5)

        # Bouton d'action
        button_frame = ttk.Frame(search_frame)
        button_frame.pack(fill="x", pady=10)

        self.execute_button = ttk.Button(button_frame,
                                         text="🔄 Appliquer le remplacement",
                                         command=self._on_execute_clicked)
        self.execute_button.pack(expand=True)

        # Info label
        self.info_label = ttk.Label(search_frame, text="",
                                    font=("Arial", 8), foreground="gray")
        self.info_label.pack(pady=5)

    def _on_execute_clicked(self):
        """Appelé lors du clic sur le bouton d'exécution."""
        if self.on_search_replace:
            search_text = self.search_entry.get()
            replace_text = self.replace_entry.get()
            selected_paths = self.field_selector.get_selected_paths()

            options = {
                'case_sensitive': self.case_sensitive_var.get(),
                'use_regex': self.use_regex_var.get(),
                'whole_word': self.whole_word_var.get()
            }

            self.on_search_replace(search_text, replace_text, selected_paths, options)

    def load_fields(self, leaves: list):
        """
        Charge les champs disponibles.

        Args:
            leaves: Liste des chemins des feuilles
        """
        self.field_selector.load_fields(leaves)

    def enable_button(self):
        """Active le bouton d'exécution."""
        self.execute_button.config(state="normal")

    def disable_button(self):
        """Désactive le bouton d'exécution."""
        self.execute_button.config(state="disabled")

    def set_info(self, message: str, color: str = "gray"):
        """
        Affiche un message d'information.

        Args:
            message: Message à afficher
            color: Couleur du texte (gray, green, red, orange)
        """
        self.info_label.config(text=message, foreground=color)
