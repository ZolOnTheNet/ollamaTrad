"""
Dialog de fusion simplifié - Part du fichier actuel
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path
from typing import Optional, Tuple, Callable, Dict
import json5


class MergeDialog:
    """
    Dialog simplifié pour fusionner le fichier .got.json actuel avec un autre fichier.

    Workflow:
    1. Fichier actuel = base de départ
    2. Sélection d'un fichier à fusionner (JSON ou got.json)
    3. Choix du fichier à garder comme structure
    4. Exécution avec progression et rapport
    """

    def __init__(self, parent, current_file_path: str):
        """
        Args:
            parent: Fenêtre parente
            current_file_path: Chemin du fichier .got.json actuellement ouvert
        """
        self.current_file = current_file_path
        self.merge_file: Optional[str] = None
        self.keep_structure: str = "current"  # "current" ou "other"
        self.result: Optional[Tuple[str, str, str]] = None  # (source, target, choice)

        # Créer la fenêtre
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Fusion de fichiers")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.dialog.geometry("800x600")
        self._center_window(parent)

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Variables pour progression
        self.progress_var = tk.DoubleVar(value=0)
        self.status_var = tk.StringVar(value="Prêt")

        self._create_widgets()

        # Analyser le fichier actuel pour afficher les informations de base
        self._add_report_line("📄 Fichier actuellement ouvert")
        self._add_report_line("═" * 60)
        self._analyze_file(current_file_path)

    def _center_window(self, parent):
        """Centre la fenêtre."""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        """Crée l'interface."""
        # Frame principal divisé en 2 parties : contenu scrollable + bandeau boutons

        # --- Zone de contenu scrollable ---
        content_frame = ttk.Frame(self.dialog)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas pour scroll
        canvas = tk.Canvas(content_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Contenu dans la zone scrollable
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Titre
        title_label = ttk.Label(
            main_frame,
            text="🔄 Fusion de fichiers",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(pady=(0, 10))

        # Description
        desc_label = ttk.Label(
            main_frame,
            text="Fusionnez le fichier actuel avec un autre fichier (JSON ou .got.json)",
            justify=tk.CENTER,
            foreground="gray"
        )
        desc_label.pack(pady=(0, 20))

        # --- Fichier actuel ---
        current_frame = ttk.LabelFrame(main_frame, text="📄 Fichier actuel (ouvert)", padding="10")
        current_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            current_frame,
            text=Path(self.current_file).name,
            font=("Consolas", 10, "bold"),
            foreground="blue"
        ).pack(anchor=tk.W)

        # --- Fichier à fusionner ---
        merge_frame = ttk.LabelFrame(main_frame, text="📥 Fichier à fusionner", padding="10")
        merge_frame.pack(fill=tk.X, pady=(0, 10))

        merge_path_frame = ttk.Frame(merge_frame)
        merge_path_frame.pack(fill=tk.X)

        self.merge_entry = ttk.Entry(merge_path_frame, width=60)
        self.merge_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(merge_path_frame, text="📁 Parcourir...", command=self._browse_merge).pack(side=tk.LEFT)

        ttk.Label(
            merge_frame,
            text="💡 Choisissez un .json (structure) ou .got.json (structure + traductions)",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack(anchor=tk.W, pady=(5, 0))

        # --- Choix de la structure ---
        choice_frame = ttk.LabelFrame(main_frame, text="🎯 Quel fichier garder comme structure ?", padding="10")
        choice_frame.pack(fill=tk.X, pady=(0, 15))

        self.structure_var = tk.StringVar(value="current")

        ttk.Radiobutton(
            choice_frame,
            text=f"Garder la structure du fichier actuel ({Path(self.current_file).name})",
            variable=self.structure_var,
            value="current"
        ).pack(anchor=tk.W, pady=2)

        self.other_radio = ttk.Radiobutton(
            choice_frame,
            text="Garder la structure du fichier à fusionner",
            variable=self.structure_var,
            value="other",
            state="disabled"
        )
        self.other_radio.pack(anchor=tk.W, pady=2)

        ttk.Label(
            choice_frame,
            text="Le fichier gardé définit la structure finale. Les traductions sont récupérées de l'autre.",
            font=("Segoe UI", 8),
            foreground="gray"
        ).pack(anchor=tk.W, pady=(5, 0))

        # --- Barre de progression ---
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.status_label = ttk.Label(
            progress_frame,
            textvariable=self.status_var,
            foreground="gray"
        )
        self.status_label.pack(anchor=tk.W)

        # --- Zone de rapport ---
        report_frame = ttk.LabelFrame(main_frame, text="📋 Informations sur la fusion", padding="10")
        report_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.report_text = scrolledtext.ScrolledText(
            report_frame,
            height=10,
            wrap=tk.WORD,
            font=("Consolas", 9),
            state='disabled'
        )
        self.report_text.pack(fill=tk.BOTH, expand=True)

        # --- Bandeau de boutons fixe en bas ---
        # Séparateur
        separator = ttk.Separator(self.dialog, orient='horizontal')
        separator.pack(fill=tk.X)

        buttons_bandeau = ttk.Frame(self.dialog, padding="10")
        buttons_bandeau.pack(fill=tk.X, side=tk.BOTTOM)

        self.cancel_button = ttk.Button(
            buttons_bandeau,
            text="Fermer",
            command=self._on_cancel,
            width=15
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=(5, 0))

        self.merge_button = ttk.Button(
            buttons_bandeau,
            text="🔄 Fusionner",
            command=self._on_merge,
            width=15,
            style="Accent.TButton",
            state="disabled"
        )
        self.merge_button.pack(side=tk.RIGHT)

        # Bind
        self.dialog.bind("<Escape>", lambda e: self._on_cancel())

    def _browse_merge(self):
        """Sélectionner le fichier à fusionner."""
        filename = filedialog.askopenfilename(
            parent=self.dialog,
            title="Sélectionner le fichier à fusionner",
            filetypes=[
                ("Tous fichiers JSON", "*.json *.got.json"),
                ("Fichiers GOT JSON", "*.got.json"),
                ("Fichiers JSON", "*.json"),
                ("Tous les fichiers", "*.*")
            ]
        )
        if filename:
            self.merge_entry.delete(0, tk.END)
            self.merge_entry.insert(0, filename)
            self.merge_file = filename

            # Activer le bouton de fusion et le radio button
            self.merge_button.config(state="normal")
            self.other_radio.config(state="normal")

            # Mettre à jour le texte du radio button
            self.other_radio.config(
                text=f"Garder la structure du fichier à fusionner ({Path(filename).name})"
            )

            # Analyser le fichier immédiatement
            self._analyze_file(filename)

    def _add_report_line(self, text: str):
        """Ajoute une ligne au rapport."""
        self.report_text.config(state='normal')
        self.report_text.insert(tk.END, text + "\n")
        self.report_text.see(tk.END)
        self.report_text.config(state='disabled')
        self.dialog.update()

    def _analyze_file(self, filepath: str):
        """
        Analyse un fichier et affiche ses informations dans le rapport.

        Args:
            filepath: Chemin du fichier à analyser
        """
        try:
            self._add_report_line("📊 Analyse du fichier sélectionné...")
            self._add_report_line(f"  Fichier: {Path(filepath).name}")

            # Charger le fichier
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json5.load(f)

            if not isinstance(data, dict):
                self._add_report_line("  ⚠️ Format non reconnu (pas un objet JSON)")
                return

            # Compter les entrées
            is_got_json = "__ollamafic__" in data
            if is_got_json:
                entry_count = len([k for k in data.keys() if k != "__ollamafic__"])
                self._add_report_line(f"  Type: Fichier .got.json")
                self._add_report_line(f"  Nombre d'entrées: {entry_count}")

                # Analyser les langues disponibles (regarder les premières entrées)
                languages = set()
                entries_checked = 0
                max_check = 10  # Regarder les 10 premières entrées

                for key, value in data.items():
                    if key == "__ollamafic__":
                        continue

                    if isinstance(value, dict):
                        # Chercher les clés de langue
                        for lang_key in value.keys():
                            if lang_key in ["ori", "fr", "en", "es", "de", "it", "ja", "zh", "ru", "pt", "ar"]:
                                languages.add(lang_key)

                    entries_checked += 1
                    if entries_checked >= max_check:
                        break

                if languages:
                    langs_str = ", ".join(sorted(languages))
                    self._add_report_line(f"  Langues détectées: {langs_str}")
                    self._add_report_line(f"  (analyse sur {entries_checked} entrée(s))")
                else:
                    self._add_report_line(f"  Langues: non détectées")

            else:
                # JSON simple
                entry_count = len(data.keys())
                self._add_report_line(f"  Type: Fichier JSON simple")
                self._add_report_line(f"  Nombre de clés racine: {entry_count}")

                # Vérifier si le .got.json correspondant existe
                if filepath.endswith('.json') and not filepath.endswith('.got.json'):
                    got_path = Path(filepath).with_suffix('.got.json')
                    if got_path.exists():
                        self._add_report_line(f"  ℹ️ Le fichier .got.json correspondant existe et sera utilisé")
                    else:
                        self._add_report_line(f"  ℹ️ Pas de .got.json correspondant (sera créé si nécessaire)")

            self._add_report_line("")

        except Exception as e:
            self._add_report_line(f"  ❌ Erreur lors de l'analyse: {str(e)}")
            self._add_report_line("")

    def _on_merge(self):
        """Lance la fusion."""
        if not self.merge_file:
            return

        # Message immédiat pour montrer que le traitement démarre
        self._add_report_line("═" * 60)
        self._add_report_line("🔄 LANCEMENT DE LA FUSION")
        self._add_report_line("═" * 60)
        self._add_report_line("")

        # Désactiver les boutons
        self.merge_button.config(state="disabled")
        self.cancel_button.config(state="disabled")

        # Déterminer la structure
        keep_current = (self.structure_var.get() == "current")

        if keep_current:
            source_file = self.merge_file  # Traductions viennent de l'autre
            target_file = self.current_file  # Structure du courant
        else:
            source_file = self.current_file  # Traductions viennent du courant
            target_file = self.merge_file  # Structure de l'autre

        self.result = (source_file, target_file, self.structure_var.get())

        # Le traitement sera fait par la fonction appelante
        # On retourne juste les infos nécessaires

    def _on_cancel(self):
        """Annulation."""
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[Tuple[str, str, str]]:
        """
        Affiche le dialog.

        Returns:
            Tuple (source_file, target_file, choice) ou None si annulé
            - source_file: Fichier source des traductions
            - target_file: Fichier pour la structure
            - choice: "current" ou "other"
        """
        self.dialog.wait_window()
        return self.result

    def update_progress(self, current: int, total: int):
        """Met à jour la barre de progression et le status."""
        if total == 0:
            return

        percent = int((current / total) * 100)

        # Mettre à jour la barre de progression
        self.progress_var.set(percent)

        # Afficher le nombre d'entrées traitées et le pourcentage dans le status
        self.status_var.set(f"{current}/{total} ({percent}%)")

        # Afficher dans le rapport seulement au début et à la fin
        if current == 1:
            self._add_report_line(f"  Traitement de {total} entrées...")
        elif current == total:
            self._add_report_line(f"  ✓ Traitement terminé: {total}/{total} (100%)")

        # Forcer la mise à jour de l'interface
        self.dialog.update_idletasks()
        self.dialog.update()

    def show_stats(self, stats: Dict):
        """Affiche les statistiques de fusion."""
        self._add_report_line("=" * 60)
        self._add_report_line("✅ FUSION TERMINÉE")
        self._add_report_line("=" * 60)
        self._add_report_line("")
        self._add_report_line(f"📊 Statistiques:")
        self._add_report_line(f"  • Total d'entrées dans le résultat: {stats['total_entries']}")
        self._add_report_line(f"  • Entrées avec traductions récupérées: {stats['recovered']}")
        self._add_report_line(f"  • Nombre de traductions récupérées: {stats['translations_recovered']}")
        self._add_report_line(f"  • Nouvelles entrées (sans traductions): {stats['new_entries']}")
        self._add_report_line(f"  • Entrées dévalidées (texte original modifié): {stats['invalidated']}")
        self._add_report_line(f"  • Entrées perdues (supprimées): {stats['lost_entries']}")
        self._add_report_line("")
        self._add_report_line("✓ Le fichier a été sauvegardé avec succès")

        # Réactiver les boutons
        self.cancel_button.config(state="normal", text="Fermer")
        self.status_var.set("Fusion terminée !")
