"""
Dialog de fusion manuelle de deux fichiers .got.json
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json5
from typing import Optional, Tuple


class MergeDialog:
    """
    Dialog pour fusionner manuellement deux fichiers .got.json.

    Permet de sélectionner:
    - Un fichier .got.json source (ancien, avec traductions)
    - Un fichier .json ou .got.json cible (nouveau, structure à utiliser)
    - Un fichier de destination pour le résultat
    """

    def __init__(self, parent):
        """
        Args:
            parent: Fenêtre parente
        """
        self.source_file: Optional[str] = None
        self.target_file: Optional[str] = None
        self.output_file: Optional[str] = None
        self.result: Optional[Tuple[str, str, str]] = None

        # Créer la fenêtre de dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Fusion de fichiers GOT")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Taille de la fenêtre
        self.dialog.geometry("700x400")
        self._center_window(parent)

        # Rendre la fenêtre modale
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Créer l'interface
        self._create_widgets()

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

    def _create_widgets(self):
        """Crée les widgets du dialog."""
        # Frame principal avec padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Titre
        title_label = ttk.Label(
            main_frame,
            text="🔄 Fusion de fichiers .got.json",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Description
        desc_label = ttk.Label(
            main_frame,
            text="Fusionnez deux fichiers .got.json en récupérant les traductions de l'ancien\n"
                 "et en appliquant la structure du nouveau.",
            justify=tk.CENTER,
            foreground="gray"
        )
        desc_label.pack(pady=(0, 20))

        # Frame pour les sélections de fichiers
        files_frame = ttk.Frame(main_frame)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # --- Fichier source (ancien .got.json) ---
        source_frame = ttk.LabelFrame(files_frame, text="1️⃣  Fichier source (ancien .got.json avec traductions)", padding="10")
        source_frame.pack(fill=tk.X, pady=(0, 10))

        source_path_frame = ttk.Frame(source_frame)
        source_path_frame.pack(fill=tk.X)

        self.source_entry = ttk.Entry(source_path_frame, width=60)
        self.source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(source_path_frame, text="📁 Parcourir...", command=self._browse_source).pack(side=tk.LEFT)

        # --- Fichier cible (nouveau .json ou .got.json) ---
        target_frame = ttk.LabelFrame(files_frame, text="2️⃣  Fichier cible (nouveau .json avec structure à jour)", padding="10")
        target_frame.pack(fill=tk.X, pady=(0, 10))

        target_path_frame = ttk.Frame(target_frame)
        target_path_frame.pack(fill=tk.X)

        self.target_entry = ttk.Entry(target_path_frame, width=60)
        self.target_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(target_path_frame, text="📁 Parcourir...", command=self._browse_target).pack(side=tk.LEFT)

        # --- Fichier de sortie ---
        output_frame = ttk.LabelFrame(files_frame, text="3️⃣  Fichier de sortie (résultat de la fusion)", padding="10")
        output_frame.pack(fill=tk.X)

        output_path_frame = ttk.Frame(output_frame)
        output_path_frame.pack(fill=tk.X)

        self.output_entry = ttk.Entry(output_path_frame, width=60)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(output_path_frame, text="💾 Enregistrer sous...", command=self._browse_output).pack(side=tk.LEFT)

        # Frame pour les boutons d'action
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)

        ttk.Button(
            buttons_frame,
            text="Annuler",
            command=self._on_cancel,
            width=15
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            buttons_frame,
            text="🔄 Fusionner",
            command=self._on_merge,
            width=15,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT)

        # Bind Escape pour annuler
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())

    def _browse_source(self):
        """Parcourir pour sélectionner le fichier source."""
        filename = filedialog.askopenfilename(
            parent=self.dialog,
            title="Sélectionner le fichier source (.got.json)",
            filetypes=[
                ("Fichiers GOT JSON", "*.got.json"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if filename:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, filename)
            self.source_file = filename

            # Proposer un nom de sortie automatique
            if not self.output_entry.get():
                output_name = Path(filename).stem + "_merged.got.json"
                output_path = Path(filename).parent / output_name
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, str(output_path))

    def _browse_target(self):
        """Parcourir pour sélectionner le fichier cible."""
        filename = filedialog.askopenfilename(
            parent=self.dialog,
            title="Sélectionner le fichier cible (.json ou .got.json)",
            filetypes=[
                ("Fichiers JSON", "*.json"),
                ("Fichiers GOT JSON", "*.got.json"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if filename:
            self.target_entry.delete(0, tk.END)
            self.target_entry.insert(0, filename)
            self.target_file = filename

    def _browse_output(self):
        """Parcourir pour sélectionner le fichier de sortie."""
        filename = filedialog.asksaveasfilename(
            parent=self.dialog,
            title="Enregistrer le résultat sous",
            defaultextension=".got.json",
            filetypes=[
                ("Fichiers GOT JSON", "*.got.json"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)
            self.output_file = filename

    def _on_merge(self):
        """Valider et lancer la fusion."""
        # Récupérer les valeurs des champs
        source = self.source_entry.get().strip()
        target = self.target_entry.get().strip()
        output = self.output_entry.get().strip()

        # Validation
        if not source:
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier source.", parent=self.dialog)
            return

        if not target:
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier cible.", parent=self.dialog)
            return

        if not output:
            messagebox.showerror("Erreur", "Veuillez spécifier un fichier de sortie.", parent=self.dialog)
            return

        # Vérifier que les fichiers existent
        if not Path(source).exists():
            messagebox.showerror("Erreur", f"Le fichier source n'existe pas:\n{source}", parent=self.dialog)
            return

        if not Path(target).exists():
            messagebox.showerror("Erreur", f"Le fichier cible n'existe pas:\n{target}", parent=self.dialog)
            return

        # Confirmer si le fichier de sortie existe déjà
        if Path(output).exists():
            if not messagebox.askyesno(
                "Confirmation",
                f"Le fichier existe déjà:\n{output}\n\nVoulez-vous l'écraser ?",
                parent=self.dialog
            ):
                return

        # Tout est OK, retourner les résultats
        self.result = (source, target, output)
        self.dialog.destroy()

    def _on_cancel(self):
        """Annulation."""
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[Tuple[str, str, str]]:
        """
        Affiche le dialog et attend la sélection de l'utilisateur.

        Returns:
            Tuple (source_file, target_file, output_file) ou None si annulé
        """
        self.dialog.wait_window()
        return self.result


def show_merge_dialog(parent) -> Optional[Tuple[str, str, str]]:
    """
    Fonction helper pour afficher le dialog de fusion.

    Args:
        parent: Fenêtre parente

    Returns:
        Tuple (source_file, target_file, output_file) ou None si annulé
    """
    dialog = MergeDialog(parent)
    return dialog.show()
