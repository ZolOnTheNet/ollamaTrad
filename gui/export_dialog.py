# -*- coding: utf-8 -*-
"""
Dialogue d'export pour OllamaTrad.

Permet d'exporter un fichier .got.json vers un fichier JSON standard
avec différentes options de traduction.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional


class ExportDialog:
    """
    Dialogue pour configurer et exécuter l'export d'un fichier JSON.

    Options:
    - Langue cible
    - Emplacement et nom du fichier
    - Mode d'export (standard ou unique validé)
    """

    def __init__(self, parent, current_file_path: str, target_language: Optional[str] = None,
                 available_languages: list = None):
        """
        Initialise le dialogue d'export.

        Args:
            parent: Fenêtre parente
            current_file_path: Chemin du fichier .got.json actuel
            target_language: Langue pré-sélectionnée (ou None pour "autre...")
            available_languages: Liste des langues disponibles
        """
        self.parent = parent
        self.current_file_path = Path(current_file_path)
        self.target_language = target_language
        self.available_languages = available_languages or []

        # Résultat du dialogue
        self.result = None

        # Créer la fenêtre
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Export JSON")
        self.dialog.geometry("550x380")
        self.dialog.resizable(False, False)

        # Rendre modale
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()

        # Centrer la fenêtre
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (380 // 2)
        self.dialog.geometry(f"550x380+{x}+{y}")

    def _create_widgets(self):
        """Crée les widgets du dialogue."""
        # Titre (compact)
        title_frame = ttk.Frame(self.dialog)
        title_frame.pack(fill="x", padx=15, pady=(10, 5))

        ttk.Label(title_frame, text="📤 Export vers JSON",
                 font=("Arial", 11, "bold")).pack(anchor="w")

        ttk.Separator(self.dialog, orient="horizontal").pack(fill="x", padx=15, pady=5)

        # === Section Langue (compact) ===
        lang_frame = ttk.LabelFrame(self.dialog, text="Langue", padding=5)
        lang_frame.pack(fill="x", padx=15, pady=5)

        lang_container = ttk.Frame(lang_frame)
        lang_container.pack(fill="x")

        ttk.Label(lang_container, text="Langue:", width=10).pack(side="left")

        self.lang_var = tk.StringVar()
        self.lang_combo = ttk.Combobox(lang_container, textvariable=self.lang_var,
                                       state="readonly", width=25)
        self.lang_combo['values'] = self.available_languages

        # Définir la langue par défaut
        if self.target_language and self.target_language in self.available_languages:
            self.lang_var.set(self.target_language)
        elif self.available_languages:
            self.lang_var.set(self.available_languages[0])

        self.lang_combo.pack(side="left", padx=3)

        # Bind pour mettre à jour le nom de fichier quand la langue change
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        # === Section Fichier de destination (compact) ===
        file_frame = ttk.LabelFrame(self.dialog, text="Fichier", padding=5)
        file_frame.pack(fill="x", padx=15, pady=5)

        file_container = ttk.Frame(file_frame)
        file_container.pack(fill="x")

        # Variable pour stocker le chemin complet
        self.output_path_var = tk.StringVar()
        self._update_default_filename()

        # Champ d'affichage (lecture seule)
        file_entry = ttk.Entry(file_container, textvariable=self.output_path_var,
                              state="readonly", font=("Arial", 8))
        file_entry.pack(side="left", fill="x", expand=True, padx=(0, 3))

        # Bouton "Parcourir..." qui ouvre le sélecteur de fichier classique
        ttk.Button(file_container, text="...", width=3,
                  command=self._browse_file).pack(side="left")

        # === Section Mode d'export (compact) ===
        mode_frame = ttk.LabelFrame(self.dialog, text="Mode", padding=5)
        mode_frame.pack(fill="x", padx=15, pady=5)

        self.export_mode_var = tk.StringVar(value="standard")

        # Option "Standard" (compact)
        standard_radio = ttk.Radiobutton(
            mode_frame,
            text="Standard (traduction si définie)",
            variable=self.export_mode_var,
            value="standard"
        )
        standard_radio.pack(anchor="w", pady=2)

        # Tooltip pour Standard
        self._create_tooltip(standard_radio,
            "Export standard :\n"
            "- Utilise la traduction si non vide\n"
            "- Sinon : utilise l'original"
        )

        # Option "Unique Validé" (compact)
        validated_radio = ttk.Radiobutton(
            mode_frame,
            text="Unique Validé (seulement traductions validées)",
            variable=self.export_mode_var,
            value="validated"
        )
        validated_radio.pack(anchor="w", pady=2)

        # Tooltip pour Unique Validé
        self._create_tooltip(validated_radio,
            "Export Unique Validé :\n"
            "- Utilise SEULEMENT les traductions validées\n"
            "- Sinon : utilise l'original"
        )

        # === Boutons (compact) ===
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=15, pady=(10, 10))

        ttk.Button(button_frame, text="Annuler",
                  command=self._on_cancel).pack(side="right", padx=3)

        ttk.Button(button_frame, text="Exporter",
                  command=self._on_export).pack(side="right", padx=3)

    def _create_tooltip(self, widget, text):
        """
        Crée un tooltip pour un widget.

        Args:
            widget: Widget auquel attacher le tooltip
            text: Texte du tooltip
        """
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

            label = tk.Label(tooltip, text=text, background="#ffffe0",
                           relief="solid", borderwidth=1, font=("Arial", 9),
                           justify="left", padx=5, pady=5)
            label.pack()

            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def _update_default_filename(self):
        """Met à jour le chemin de fichier par défaut basé sur la langue."""
        # Récupérer le nom de base du fichier original
        original_name = self.current_file_path.stem

        # Enlever .got si présent
        if original_name.endswith('.got'):
            original_name = original_name[:-4]

        # Ajouter le code langue
        lang = self.lang_var.get()
        if lang:
            new_name = f"{original_name}-{lang}.json"
        else:
            new_name = f"{original_name}-export.json"

        # Construire le chemin complet
        output_path = self.current_file_path.parent / new_name
        self.output_path_var.set(str(output_path))

    def _on_language_change(self, event=None):
        """Appelé quand la langue change."""
        self._update_default_filename()

    def _browse_file(self):
        """Ouvre un dialogue de sélection de fichier classique."""
        # Récupérer le chemin actuel ou le répertoire du fichier source
        current_path = self.output_path_var.get()
        if current_path:
            initialdir = str(Path(current_path).parent)
            initialfile = Path(current_path).name
        else:
            initialdir = str(self.current_file_path.parent)
            initialfile = ""

        # Ouvrir le sélecteur de fichier
        filepath = filedialog.asksaveasfilename(
            parent=self.dialog,
            title="Enregistrer le fichier JSON",
            initialdir=initialdir,
            initialfile=initialfile,
            defaultextension=".json",
            filetypes=[
                ("Fichiers JSON", "*.json"),
                ("Fichiers GOT.JSON", "*.got.json"),
                ("Tous les fichiers", "*.*")
            ]
        )

        # Si l'utilisateur a choisi un fichier, mettre à jour
        if filepath:
            self.output_path_var.set(filepath)

    def _on_cancel(self):
        """Annule le dialogue."""
        self.result = None
        self.dialog.destroy()

    def _on_export(self):
        """Valide et ferme le dialogue."""
        # Validation de la langue
        lang = self.lang_var.get()
        if not lang:
            messagebox.showerror("Erreur", "Veuillez sélectionner une langue",
                               parent=self.dialog)
            return

        # Validation du fichier de sortie
        output_path_str = self.output_path_var.get()
        if not output_path_str:
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier de destination",
                               parent=self.dialog)
            return

        output_path = Path(output_path_str)

        # Vérifier que le répertoire parent existe
        if not output_path.parent.exists():
            messagebox.showerror("Erreur",
                               f"Le répertoire '{output_path.parent}' n'existe pas",
                               parent=self.dialog)
            return

        # Ajouter .json si manquant
        if not output_path.suffix:
            output_path = output_path.with_suffix('.json')
            self.output_path_var.set(str(output_path))

        # Vérifier si le fichier existe déjà
        if output_path.exists():
            response = messagebox.askyesno(
                "Fichier existant",
                f"Le fichier '{output_path.name}' existe déjà.\n\nVoulez-vous le remplacer ?",
                parent=self.dialog
            )
            if not response:
                return

        # Préparer le résultat
        self.result = {
            'language': lang,
            'output_path': str(output_path),
            'mode': self.export_mode_var.get()
        }

        self.dialog.destroy()

    def show(self):
        """
        Affiche le dialogue et attend le résultat.

        Returns:
            dict ou None: Configuration d'export si validé, None si annulé
                {
                    'language': str,
                    'output_path': str,
                    'mode': 'standard' ou 'validated'
                }
        """
        self.dialog.wait_window()
        return self.result
