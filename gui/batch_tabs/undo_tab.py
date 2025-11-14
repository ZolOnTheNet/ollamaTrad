# -*- coding: utf-8 -*-
"""
Onglet d'annulation de modifications par lot.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from field_selector import FieldSelector


class UndoTab(ttk.Frame):
    """Onglet pour annuler les dernières modifications de champs sélectionnés."""

    def __init__(self, parent, on_undo: Optional[Callable] = None):
        """
        Initialise l'onglet d'annulation.

        Args:
            parent: Widget parent
            on_undo: Callback(selected_paths) appelé lors du clic sur le bouton
        """
        super().__init__(parent)

        self.on_undo = on_undo

        self._create_widgets()

    def _create_widgets(self):
        """Crée les widgets de l'onglet."""
        # === Description ===
        info_frame = ttk.Frame(self)
        info_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(info_frame,
                 text="⚠️ Annulation des modifications",
                 font=("Arial", 11, "bold")).pack(anchor="w")

        ttk.Label(info_frame,
                 text="Restaure la dernière version sauvegardée des champs sélectionnés.\n"
                      "Cette opération utilise l'historique des opérations.",
                 font=("Arial", 9), foreground="gray",
                 wraplength=500, justify="left").pack(anchor="w", pady=5)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=5)

        # === Sélecteur de champs ===
        self.field_selector = FieldSelector(self, title="Champs à restaurer")
        self.field_selector.pack(fill="both", expand=True, padx=10, pady=10)

        # === Options d'annulation ===
        options_frame = ttk.LabelFrame(self, text="Options", padding=10)
        options_frame.pack(fill="x", padx=10, pady=10)

        self.undo_mode_var = tk.StringVar(value="last")

        ttk.Radiobutton(options_frame,
                       text="Annuler la dernière modification",
                       variable=self.undo_mode_var,
                       value="last").pack(anchor="w", pady=2)

        ttk.Radiobutton(options_frame,
                       text="Restaurer depuis la dernière sauvegarde",
                       variable=self.undo_mode_var,
                       value="last_save").pack(anchor="w", pady=2)

        ttk.Radiobutton(options_frame,
                       text="Restaurer toutes les modifications (retour initial)",
                       variable=self.undo_mode_var,
                       value="all").pack(anchor="w", pady=2)

        # Bouton d'action
        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        self.undo_button = ttk.Button(button_frame,
                                      text="↶ Annuler les modifications",
                                      command=self._on_undo_clicked)
        self.undo_button.pack(expand=True)

        # Info label
        self.info_label = ttk.Label(self, text="",
                                    font=("Arial", 8), foreground="gray")
        self.info_label.pack(pady=5)

    def _on_undo_clicked(self):
        """Appelé lors du clic sur le bouton d'annulation."""
        if self.on_undo:
            selected_paths = self.field_selector.get_selected_paths()
            undo_mode = self.undo_mode_var.get()

            self.on_undo(selected_paths, undo_mode)

    def load_fields(self, leaves: list):
        """
        Charge les champs disponibles.

        Args:
            leaves: Liste des chemins des feuilles
        """
        self.field_selector.load_fields(leaves)

    def enable_button(self):
        """Active le bouton d'annulation."""
        self.undo_button.config(state="normal")

    def disable_button(self):
        """Désactive le bouton d'annulation."""
        self.undo_button.config(state="disabled")

    def set_info(self, message: str, color: str = "gray"):
        """
        Affiche un message d'information.

        Args:
            message: Message à afficher
            color: Couleur du texte (gray, green, red, orange)
        """
        self.info_label.config(text=message, foreground=color)
