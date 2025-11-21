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

    def __init__(self, parent, title="Champs à traiter", on_selection_changed=None, got_manager=None):
        """
        Initialise le sélecteur de champs.

        Args:
            parent: Widget parent
            title: Titre du cadre
            on_selection_changed: Callback appelé quand la sélection change
            got_manager: GotJsonManager pour filtrer les champs
        """
        super().__init__(parent)

        self.field_checkboxes = {}  # {field_name: BooleanVar}
        self.field_to_paths = {}  # {field_name: [list of paths]}
        self.all_leaves = []  # Liste de tous les chemins de feuilles
        self.on_selection_changed = on_selection_changed
        self.got_manager = got_manager
        self.filter_mode = tk.StringVar(value="non_validated")  # Options: "non_validated", "empty"

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

        # Options de filtrage
        ttk.Separator(selection_buttons, orient="vertical").pack(side="left", padx=10, fill="y")

        ttk.Radiobutton(selection_buttons, text="Champs non validés",
                       variable=self.filter_mode, value="non_validated",
                       command=self._on_filter_changed).pack(side="left", padx=5)
        ttk.Radiobutton(selection_buttons, text="Champs vides",
                       variable=self.filter_mode, value="empty",
                       command=self._on_filter_changed).pack(side="left", padx=5)

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

    def set_got_manager(self, got_manager):
        """
        Définit le GotJsonManager pour le filtrage.

        Args:
            got_manager: Instance de GotJsonManager
        """
        self.got_manager = got_manager

    def _on_filter_changed(self):
        """Appelé quand l'option de filtrage change."""
        # Recharger les champs avec le nouveau filtre
        if self.all_leaves:
            self.load_fields(self.all_leaves)

    def _should_include_field(self, leaf_path: str, current_lang: str = None) -> bool:
        """
        Détermine si un champ doit être inclus selon le filtre actuel.

        Args:
            leaf_path: Chemin du champ
            current_lang: Langue actuelle (optionnel)

        Returns:
            True si le champ doit être inclus
        """
        if not self.got_manager:
            return True  # Sans got_manager, inclure tous les champs

        filter_mode = self.filter_mode.get()

        try:
            entry = self.got_manager._get_entry_by_path(leaf_path)

            if not isinstance(entry, dict) or "ori" not in entry:
                return False  # Pas une entrée traduisible

            # Si on a une langue spécifique, vérifier pour cette langue
            # Sinon, vérifier pour toutes les langues cibles
            langs_to_check = [current_lang] if current_lang else self.got_manager.target_languages

            for lang in langs_to_check:
                if filter_mode == "non_validated":
                    # Inclure si non validé (vide ou non validé)
                    if lang not in entry:
                        return True  # Champ vide = non validé
                    lang_data = entry[lang]
                    if isinstance(lang_data, dict):
                        if not lang_data.get("valid", False):
                            return True  # Non validé
                    else:
                        return True  # Format ancien = non validé
                elif filter_mode == "empty":
                    # Inclure seulement si complètement vide
                    if lang not in entry:
                        return True
                    lang_data = entry[lang]
                    if isinstance(lang_data, dict):
                        if not lang_data.get("text", "").strip():
                            return True
                    elif not lang_data.strip():
                        return True

            return False
        except Exception:
            return True  # En cas d'erreur, inclure le champ

    def load_fields(self, leaves: list):
        """
        Charge les champs depuis une liste de chemins de feuilles.

        Args:
            leaves: Liste des chemins des feuilles (ex: ["entries/Demon/name", ...])
        """
        self.all_leaves = leaves

        # Filtrer les feuilles selon le mode de filtrage
        filtered_leaves = [leaf for leaf in leaves if self._should_include_field(leaf)]

        # Grouper les feuilles par nom de champ final
        self.field_to_paths = {}
        for leaf_path in filtered_leaves:
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
