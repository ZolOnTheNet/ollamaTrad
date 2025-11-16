"""
Dialog de choix pour l'évolution des fichiers .got.json
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional, Literal


class EvolutionChoiceDialog:
    """
    Dialog pour choisir comment gérer un fichier .got.json qui ne correspond plus au JSON source.

    Options:
    - Nouveau: Créer un nouveau .got.json (ignorer l'ancien)
    - Évolution: Fusionner ancien + nouveau (défaut recommandé)
    - Ancien: Utiliser seulement le .got.json actuel
    """

    def __init__(self, parent, json_filename: str, got_filename: str, backup_filename: str):
        """
        Args:
            parent: Fenêtre parente
            json_filename: Nom du fichier .json source
            got_filename: Nom du fichier .got.json existant
            backup_filename: Nom du backup qui sera créé
        """
        self.choice: Optional[Literal["nouveau", "evolution", "ancien"]] = None

        # Créer la fenêtre de dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Fichier source modifié")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Centrer la fenêtre (hauteur doublée pour voir tous les boutons)
        self.dialog.geometry("600x700")
        self._center_window(parent)

        # Rendre la fenêtre modale
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Créer l'interface
        self._create_widgets(json_filename, got_filename, backup_filename)

    def _center_window(self, parent):
        """Centre la fenêtre sur le parent."""
        self.dialog.update_idletasks()

        # Obtenir les dimensions
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()

        # Obtenir la position du parent
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Calculer la position centrée
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2

        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self, json_filename: str, got_filename: str, backup_filename: str):
        """Crée les widgets du dialog."""
        # Frame principal avec padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Icône et titre
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))

        icon_label = ttk.Label(title_frame, text="⚠️", font=("Segoe UI", 32))
        icon_label.pack(side=tk.LEFT, padx=(0, 15))

        title_label = ttk.Label(
            title_frame,
            text="Fichier source modifié détecté",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(side=tk.LEFT)

        # Message explicatif
        message = (
            f"Le programme a détecté que le fichier source (.json) ne correspond plus\n"
            f"au fichier de travail (.got.json).\n\n"
            f"Que voulez-vous faire ?"
        )
        message_label = ttk.Label(
            main_frame,
            text=message,
            justify=tk.LEFT,
            wraplength=550
        )
        message_label.pack(fill=tk.X, pady=(0, 15))

        # Informations sur les fichiers
        info_frame = ttk.LabelFrame(main_frame, text="Fichiers concernés", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(info_frame, text=f"Source (JSON):  {json_filename}", font=("Consolas", 9)).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Travail (.got):  {got_filename}", font=("Consolas", 9)).pack(anchor=tk.W, pady=(5, 0))
        ttk.Label(info_frame, text=f"Backup créé:  {backup_filename}", font=("Consolas", 9)).pack(anchor=tk.W, pady=(5, 0))

        # Frame pour les boutons de choix
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        # Bouton 1: Nouveau
        btn_nouveau = ttk.Button(
            buttons_frame,
            text="🆕 Nouveau fichier",
            command=self._on_nouveau,
            width=25
        )
        btn_nouveau.pack(pady=5, fill=tk.X)

        ttk.Label(
            buttons_frame,
            text="Créer un nouveau .got.json (l'ancien est sauvegardé)",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack(pady=(0, 10))

        # Bouton 2: Évolution (recommandé)
        btn_evolution = ttk.Button(
            buttons_frame,
            text="🔄 Évolution (fusion) - RECOMMANDÉ",
            command=self._on_evolution,
            width=25,
            style="Accent.TButton"  # Style spécial pour le mettre en évidence
        )
        btn_evolution.pack(pady=5, fill=tk.X)

        ttk.Label(
            buttons_frame,
            text="Fusionner ancien + nouveau (conserve les traductions)",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack(pady=(0, 10))

        # Bouton 3: Ancien
        btn_ancien = ttk.Button(
            buttons_frame,
            text="📂 Fichier .got.json actuel",
            command=self._on_ancien,
            width=25
        )
        btn_ancien.pack(pady=5, fill=tk.X)

        ttk.Label(
            buttons_frame,
            text="Utiliser uniquement le .got.json existant (ignorer le nouveau JSON)",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack(pady=(0, 10))

        # Mettre le focus sur le bouton "Évolution"
        btn_evolution.focus_set()

        # Bind Escape pour annuler
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())

    def _on_nouveau(self):
        """Choix: Créer un nouveau fichier."""
        self.choice = "nouveau"
        self.dialog.destroy()

    def _on_evolution(self):
        """Choix: Faire une évolution (fusion)."""
        self.choice = "evolution"
        self.dialog.destroy()

    def _on_ancien(self):
        """Choix: Utiliser l'ancien fichier."""
        self.choice = "ancien"
        self.dialog.destroy()

    def _on_cancel(self):
        """Annulation - fermeture de la fenêtre sans choix."""
        self.choice = None
        self.dialog.destroy()

    def show(self) -> Optional[Literal["nouveau", "evolution", "ancien"]]:
        """
        Affiche le dialog et attend le choix de l'utilisateur.

        Returns:
            "nouveau", "evolution", "ancien", ou None si annulé
        """
        self.dialog.wait_window()
        return self.choice


def show_evolution_choice_dialog(parent, json_filename: str, got_filename: str, backup_filename: str) -> Optional[str]:
    """
    Fonction helper pour afficher le dialog de choix d'évolution.

    Args:
        parent: Fenêtre parente
        json_filename: Nom du fichier .json source
        got_filename: Nom du fichier .got.json existant
        backup_filename: Nom du backup qui sera créé

    Returns:
        "nouveau", "evolution", "ancien", ou None si annulé
    """
    dialog = EvolutionChoiceDialog(parent, json_filename, got_filename, backup_filename)
    return dialog.show()
