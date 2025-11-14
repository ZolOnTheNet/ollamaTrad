# -*- coding: utf-8 -*-
"""
Widget de sélection de champs pour les opérations par lot.

Affiche une liste de champs uniques avec checkboxes, permettant
de sélectionner quels champs doivent être traités.
"""

import tkinter as tk
from tkinter import ttk


class FieldSelector(ttk.Frame):
    """
    Widget réutilisable pour sélectionner des champs à traiter.

    Affiche:
    - Liste scrollable de checkboxes (un par nom de champ unique)
    - Boutons "Tout sélectionner" / "Tout désélectionner"
    - Compteur de sélection
    """

    def __init__(self, parent, title="Champs à traiter", on_selection_changed=None):
        """
        Initialise le sélecteur de champs.

        Args:
            parent: Widget parent
            title: Titre du cadre
            on_selection_changed: Callback appelé quand la sélection change
        """
        super().__init__(parent)

        self.field_checkboxes = {}  # {field_name: BooleanVar}
        self.field_to_paths = {}  # {field_name: [list of paths]}
        self.all_leaves = []  # Liste de tous les chemins de feuilles
        self.on_selection_changed = on_selection_changed

        self._create_widgets(title)

    def _create_widgets(self, title):
        """Crée les widgets du sélecteur."""
        # === Frame principal ===
        main_frame = ttk.LabelFrame(self, text=title, padding=10)
        main_frame.pack(fill="both", expand=True)

        # Boutons de sélection
        selection_buttons = ttk.Frame(main_frame)
        selection_buttons.pack(fill="x", pady=(0, 5))

        ttk.Button(selection_buttons, text="✓ Tout sélectionner",
                  command=self._select_all).pack(side="left", padx=2)
        ttk.Button(selection_buttons, text="☐ Tout désélectionner",
                  command=self._deselect_all).pack(side="left", padx=2)

        # Zone scrollable pour les checkboxes
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.pack(fill="both", expand=True)

        # Canvas + Scrollbar
        self.canvas = tk.Canvas(canvas_frame, height=200, bg="white")
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                  command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame,
                                 anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Label pour le compteur
        self.count_label = ttk.Label(main_frame,
                                     text="0 / 0 sélectionné(s)",
                                     font=("Arial", 8), foreground="gray")
        self.count_label.pack(anchor="w", pady=(5, 0))

    def load_fields(self, leaves: list):
        """
        Charge les champs depuis une liste de chemins de feuilles.

        Args:
            leaves: Liste des chemins des feuilles (ex: ["entries/Demon/name", ...])
        """
        self.all_leaves = leaves

        # Grouper les feuilles par nom de champ final
        self.field_to_paths = {}
        for leaf_path in leaves:
            field_name = leaf_path.split("/")[-1]

            if field_name not in self.field_to_paths:
                self.field_to_paths[field_name] = []
            self.field_to_paths[field_name].append(leaf_path)

        # Nettoyer les anciennes checkboxes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.field_checkboxes.clear()

        # Créer une checkbox par nom de champ UNIQUE (triée alphabétiquement)
        for field_name in sorted(self.field_to_paths.keys()):
            var = tk.BooleanVar(value=True)  # Par défaut, tout est sélectionné
            self.field_checkboxes[field_name] = var

            # Compter combien de fois ce champ apparaît
            count = len(self.field_to_paths[field_name])

            # Afficher le nom du champ avec le nombre d'occurrences
            if count > 1:
                display_text = f"{field_name} ({count}×)"
            else:
                display_text = field_name

            # Créer la checkbox
            cb = ttk.Checkbutton(self.scrollable_frame,
                                text=display_text,
                                variable=var,
                                command=self._update_count)
            cb.pack(anchor="w", pady=1)

        # Mettre à jour le compteur
        self._update_count()

    def get_selected_paths(self) -> list:
        """
        Retourne la liste des chemins de feuilles sélectionnées.

        Returns:
            Liste des chemins des feuilles cochées
        """
        selected = []
        for field_name, var in self.field_checkboxes.items():
            if var.get():  # Si la checkbox est cochée
                # Ajouter tous les chemins correspondant à ce champ
                selected.extend(self.field_to_paths[field_name])
        return selected

    def get_selected_fields(self) -> list:
        """
        Retourne la liste des noms de champs sélectionnés.

        Returns:
            Liste des noms de champs cochés
        """
        return [field_name for field_name, var in self.field_checkboxes.items() if var.get()]

    def _select_all(self):
        """Coche toutes les checkboxes."""
        for var in self.field_checkboxes.values():
            var.set(True)
        self._update_count()

    def _deselect_all(self):
        """Décoche toutes les checkboxes."""
        for var in self.field_checkboxes.values():
            var.set(False)
        self._update_count()

    def _update_count(self):
        """Met à jour le compteur de sélection."""
        selected_count = sum(1 for var in self.field_checkboxes.values() if var.get())
        total_count = len(self.field_checkboxes)
        self.count_label.config(
            text=f"{selected_count} / {total_count} sélectionné(s)"
        )

        # Notifier le parent du changement de sélection
        if self.on_selection_changed:
            self.on_selection_changed()

    def clear(self):
        """Vide le sélecteur."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.field_checkboxes.clear()
        self.field_to_paths.clear()
        self.all_leaves.clear()
        self._update_count()
