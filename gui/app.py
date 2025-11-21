# -*- coding: utf-8 -*-
"""
OllamaTrad - Interface graphique de traduction intelligente avec IA.

Fonctionnalités:
- Formulaire de traduction avec baguette magique
- Support multi-providers IA (Ollama, OpenAI, Mistral, Anthropic, DeepL)
- Chat contextualisé avec l'IA
- Arbre JSON avec code couleur par état de validation
- Traduction par lot avec sélection de champs
- Support complet du format .got.json v2.0
"""

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("⚠️  tkinter n'est pas disponible sur ce système")

import sys
from pathlib import Path
from typing import Optional, Dict
import asyncio
import threading
import json
import re

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent))

from core.got_json_manager import GotJsonManager
from core.ai_client import AIClient
from utils.file_loader import load_file_intelligently, load_file_with_evolution_check
from gui.translation_form import TranslationForm
from gui.batch_translation_form import BatchTranslationForm
from gui.chat_panel import ChatPanel
from gui.options_dialog import OptionsDialog


class OllamaTradGUI:
    """Interface graphique pour OllamaTrad - Traduction intelligente avec IA"""

    def __init__(self, initial_file: Optional[str] = None):
        self.root = tk.Tk()
        self.root.title("OllamaTrad - Traduction Intelligente")
        self.root.geometry("1400x900")

        # Composants principaux
        self.got_manager: Optional[GotJsonManager] = None
        self.ai_client = AIClient()
        self.current_file_path: Optional[str] = None

        # Configuration des traductions
        self.translation_config = self._load_translation_config()

        # Tracker de modifications non sauvegardées
        self.has_unsaved_changes = False
        self.last_saved_state = None  # Hash des données pour détecter les changements

        # Mode debug pour afficher les prompts complets dans le chat
        self.debug_mode = True  # Mettre à True pour voir les prompts complets

        # Mapping des items de l'arbre vers les chemins
        self.tree_item_to_path: Dict[str, str] = {}
        self.path_to_tree_item: Dict[str, str] = {}

        # État de l'entrée courante (approche objet propre)
        self.current_entry_state = {
            "path": None,        # Chemin de l'entrée actuelle
            "entry": None        # Données de l'entrée actuelle
        }

        # Mode de tri de l'arbre
        self.tree_sort_mode = "original"  # "original", "ascending", "descending"

        # Créer l'interface
        self._create_menu()
        self._create_main_layout()
        self._create_statusbar()

        # Charger le fichier initial si fourni
        if initial_file:
            self.load_file(initial_file)

    def _create_menu(self):
        """Crée le menu principal."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Ouvrir JSON/GOT...", command=self.open_file_dialog, accelerator="Ctrl+O")
        file_menu.add_command(label="Sauvegarder", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="🔄 Fusion de fichiers GOT...", command=self.open_merge_dialog)
        file_menu.add_separator()

        # Menu Export (sera créé dynamiquement)
        self.export_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="📤 Exporter vers JSON...", menu=self.export_menu)
        self._update_export_menu()  # Initialiser le menu export

        file_menu.add_separator()
        file_menu.add_command(label="⚙️ Options...", command=self.open_options_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit, accelerator="Ctrl+Q")

        # Menu Affichage
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Affichage", menu=view_menu)
        view_menu.add_command(label="Tout déplier", command=self._expand_all)
        view_menu.add_command(label="Tout plier", command=self._collapse_all)

        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self._show_about)

        # Bindings clavier
        self.root.bind("<Control-o>", lambda e: self.open_file_dialog())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-q>", lambda e: self.root.quit())

    def _create_main_layout(self):
        """Crée le layout principal avec PanedWindow."""
        # PanedWindow vertical principal
        self.main_paned = ttk.PanedWindow(self.root, orient="vertical")
        self.main_paned.pack(fill="both", expand=True)

        # PanedWindow horizontal pour arbre + formulaire
        top_paned = ttk.PanedWindow(self.main_paned, orient="horizontal")
        self.main_paned.add(top_paned, weight=3)

        # === GAUCHE: Arbre JSON ===
        self._create_tree_panel(top_paned)

        # === DROITE: Formulaire de traduction ===
        self._create_form_panel(top_paned)

        # === BAS: Chat Panel ===
        self.chat_panel = ChatPanel(self.main_paned, on_user_message=self._on_user_chat_message)
        self.chat_panel.set_paned_window(self.main_paned)  # Passer la référence
        self.main_paned.add(self.chat_panel, weight=1)

    def _create_tree_panel(self, parent):
        """Crée le panneau de l'arbre JSON."""
        tree_frame = ttk.Frame(parent)
        parent.add(tree_frame, weight=1)

        # Header
        tree_header = ttk.Frame(tree_frame)
        tree_header.pack(fill="x", padx=5, pady=5)

        ttk.Label(tree_header, text="📂 Structure JSON",
                 font=("Arial", 10, "bold")).pack(side="left")

        ttk.Button(tree_header, text="Tout déplier",
                  command=self._expand_all, width=12).pack(side="right", padx=2)
        ttk.Button(tree_header, text="Tout plier",
                  command=self._collapse_all, width=12).pack(side="right", padx=2)

        # Affichage du chemin actuel (pour debug)
        current_path_frame = ttk.Frame(tree_frame)
        current_path_frame.pack(fill="x", padx=5, pady=(0, 5))

        ttk.Label(current_path_frame, text="Chemin actuel:",
                 font=("Arial", 8, "bold")).pack(side="left")
        self.current_path_label = ttk.Label(current_path_frame, text="(aucun)",
                                           font=("Arial", 8), foreground="blue")
        self.current_path_label.pack(side="left", padx=5)

        # === Zone de recherche ===
        search_frame = ttk.Frame(tree_frame)
        search_frame.pack(fill="x", padx=5, pady=(0, 5))

        # Boutons de tri (à gauche)
        sort_frame = ttk.Frame(search_frame)
        sort_frame.pack(side="left", padx=(0, 10))

        ttk.Button(sort_frame, text="↑", width=2,
                  command=self._sort_tree_ascending,
                  style="Small.TButton").pack(side="left", padx=1)

        ttk.Button(sort_frame, text="↓", width=2,
                  command=self._sort_tree_descending,
                  style="Small.TButton").pack(side="left", padx=1)

        ttk.Button(sort_frame, text="−", width=2,
                  command=self._sort_tree_original,
                  style="Small.TButton").pack(side="left", padx=1)

        ttk.Label(search_frame, text="Rechercher entrée:",
                 font=("Arial", 8, "bold")).pack(side="left", padx=(0, 5))

        # Zone de texte pour la recherche
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.pack(side="left", padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", self._on_search_text_changed)

        # Bouton précédent
        self.search_prev_btn = ttk.Button(search_frame, text="<", width=3,
                                         command=self._search_previous, state="disabled")
        self.search_prev_btn.pack(side="left", padx=2)

        # Bouton suivant
        self.search_next_btn = ttk.Button(search_frame, text=">", width=3,
                                         command=self._search_next, state="disabled")
        self.search_next_btn.pack(side="left", padx=2)

        # Label pour afficher l'occurrence actuelle
        self.search_occurrence_label = ttk.Label(search_frame, text="",
                                                font=("Arial", 8), foreground="gray")
        self.search_occurrence_label.pack(side="left", padx=5)

        # Variables pour la recherche
        self.search_results = []  # Liste des items trouvés
        self.search_current_index = -1  # Index de l'occurrence actuelle

        # Treeview avec scrollbar
        tree_scroll_frame = ttk.Frame(tree_frame)
        tree_scroll_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        tree_scrolly = ttk.Scrollbar(tree_scroll_frame, orient="vertical")
        tree_scrolly.pack(side="right", fill="y")

        tree_scrollx = ttk.Scrollbar(tree_scroll_frame, orient="horizontal")
        tree_scrollx.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(tree_scroll_frame,
                                yscrollcommand=tree_scrolly.set,
                                xscrollcommand=tree_scrollx.set)
        self.tree.pack(side="left", fill="both", expand=True)

        tree_scrolly.config(command=self.tree.yview)
        tree_scrollx.config(command=self.tree.xview)

        # Configurer la colonne pour qu'elle prenne toute la largeur
        self.tree.column("#0", width=400, minwidth=200, stretch=True)

        # Configurer les tags de couleur
        self.tree.tag_configure("green", foreground="#008800")
        self.tree.tag_configure("orange", foreground="#FF8800")
        self.tree.tag_configure("red", foreground="#CC0000")
        self.tree.tag_configure("none", foreground="#000000")

        # Bind sélection
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _create_form_panel(self, parent):
        """Crée le panneau du formulaire de traduction."""
        form_frame = ttk.Frame(parent)
        parent.add(form_frame, weight=2)

        # Titre avec boutons undo/redo
        title_frame = ttk.Frame(form_frame)
        title_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(title_frame, text="✏ Formulaire de Traduction",
                 font=("Arial", 10, "bold")).pack(side="left")

        # Boutons undo/redo (rollback utilise déjà l'historique de traduction)
        ttk.Label(title_frame, text="Historique:",
                 font=("Arial", 9)).pack(side="right", padx=(10, 5))
        ttk.Button(title_frame, text="↶ Annuler",
                  command=self._undo_all_languages, width=12).pack(side="right", padx=2)
        ttk.Label(title_frame, text="(Le bouton ↶ annule chaque langue individuellement)",
                 font=("Arial", 8), foreground="gray").pack(side="right", padx=5)

        # Conteneur pour les formulaires (on switch entre feuille et branche)
        self.form_container = ttk.Frame(form_frame)
        self.form_container.pack(fill="both", expand=True)

        # Formulaire de traduction (feuilles)
        self.translation_form = TranslationForm(
            self.form_container,
            self.got_manager,
            on_magic_click=self._on_magic_click,
            on_deepl_click=self._on_deepl_click,
            on_validate=self._on_validate,
            on_rollback=self._on_rollback,
            on_manual_edit=self._on_manual_edit
        )

        # Formulaire de traduction par lot (branches)
        self.batch_form = BatchTranslationForm(
            self.form_container,
            visible_languages=self.translation_config.get("visible_languages", []),
            on_batch_translate=self._on_batch_translate,
            on_batch_deepl_translate=self._on_batch_deepl_translate,
            on_clear_unvalidated=self._on_batch_clear_unvalidated,
            on_search_replace=self._on_batch_search_replace,
            got_manager=self.got_manager,
            translation_config=self.translation_config
        )

        # Par défaut, rien n'est affiché
        # Les formulaires seront affichés selon la sélection

    def _create_statusbar(self):
        """Crée la barre de statut."""
        statusbar = ttk.Frame(self.root)
        statusbar.pack(side="bottom", fill="x")

        self.status_label = ttk.Label(statusbar, text="Prêt", relief="sunken", anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)

        # Label pour le compteur DeepL (spécifique)
        self.deepl_count_label = ttk.Label(statusbar, text="", relief="sunken", anchor="e")
        self.deepl_count_label.pack(side="right", padx=(5, 0))

        # Label pour le compteur de caractères (autres APIs payantes)
        self.char_count_label = ttk.Label(statusbar, text="📊 0 car.", relief="sunken", anchor="e")
        self.char_count_label.pack(side="right", padx=(5, 0))

        self.file_label = ttk.Label(statusbar, text="Aucun fichier", relief="sunken", anchor="e")
        self.file_label.pack(side="right")

        # Mettre à jour le compteur toutes les 2 secondes
        self._update_character_count()

    def _load_translation_config(self) -> Dict:
        """Charge la configuration des traductions"""
        config_path = Path(__file__).parent.parent / "config" / "translation_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # Configuration par défaut
        return {
            "target_languages": ["fr", "en", "es"],
            "visible_languages": ["fr", "en", "es"],
            "prompts": {}
        }

    def _mark_as_modified(self):
        """Marque le fichier comme ayant des modifications non sauvegardées"""
        self.has_unsaved_changes = True
        # Mettre à jour le titre de la fenêtre pour indiquer les modifications
        if self.current_file_path:
            filename = Path(self.current_file_path).name
            self.root.title(f"OllamaTrad - {filename} *")

    def _mark_as_saved(self):
        """Marque le fichier comme sauvegardé"""
        self.has_unsaved_changes = False
        # Mettre à jour le titre de la fenêtre
        if self.current_file_path:
            filename = Path(self.current_file_path).name
            self.root.title(f"OllamaTrad - {filename}")

    def open_options_dialog(self):
        """Ouvre la fenêtre d'options"""
        def on_save(config):
            self.translation_config = config

            # Recharger le AI client avec la nouvelle configuration
            if "ai_config" in config:
                ai_config = config["ai_config"]

                # Mettre à jour chaque provider configuré
                for provider_name in ["ollama", "openai", "mistral", "anthropic", "deepl"]:
                    if provider_name in ai_config:
                        self.ai_client.update_provider_config(provider_name, ai_config[provider_name])

                # Changer le provider actif si nécessaire
                if "provider" in ai_config:
                    self.ai_client.set_provider(ai_config["provider"])

            # Recharger l'affichage si un fichier est ouvert
            if self.got_manager:
                self._refresh_after_config_change()

        OptionsDialog(self.root, on_save=on_save, ai_client=self.ai_client)

    def _refresh_after_config_change(self):
        """Rafraîchit l'affichage après changement de configuration"""
        # Mettre à jour les langues visibles dans le formulaire
        self.translation_form.visible_languages = self.translation_config.get("visible_languages", [])

        # Mettre à jour les langues cibles du manager (si un fichier est chargé)
        if self.got_manager:
            self.got_manager.target_languages = self.translation_config.get("target_languages", ["fr", "en", "es"])

            # Recharger l'entrée courante si elle existe
            if self.current_entry_state["path"]:
                current_path = self.current_entry_state["path"]
                self.translation_form.load_entry(current_path)

            # Mettre à jour les couleurs de l'arbre
            self._update_all_parent_colors()

        # Mettre à jour la configuration du batch_form
        self.batch_form.set_visible_languages(self.translation_config.get("visible_languages", []))
        self.batch_form.set_translation_config(self.translation_config)
        if self.got_manager:
            self.batch_form.set_got_manager(self.got_manager)

        # Mettre à jour le compteur DeepL avec la nouvelle limite
        self._update_character_count()

        self.status_label.config(text="✓ Configuration mise à jour")

    def open_file_dialog(self):
        """Ouvre un dialogue pour sélectionner un fichier."""
        filename = filedialog.askopenfilename(
            title="Ouvrir un fichier JSON ou .got.json",
            filetypes=[
                ("Tous fichiers JSON", "*.json *.got.json"),
                ("Fichiers .got.json", "*.got.json"),
                ("Fichiers JSON", "*.json"),
                ("Tous les fichiers", "*.*")
            ]
        )

        if filename:
            self.load_file(filename)

    def open_merge_dialog(self):
        """Ouvre le dialog de fusion simplifié."""
        # Vérifier qu'un fichier est ouvert
        if not self.current_file_path:
            messagebox.showwarning(
                "Aucun fichier ouvert",
                "Veuillez d'abord ouvrir un fichier .got.json avant de fusionner."
            )
            return

        from gui.dialogs.merge_dialog import MergeDialog
        from utils.file_loader import create_backup_with_timestamp
        import json5

        # Créer et afficher le dialog
        dialog = MergeDialog(self.root, self.current_file_path)

        # Fonction de traitement après sélection
        def do_merge():
            print("DEBUG: do_merge() démarré")
            result = dialog.result
            if not result:
                print("DEBUG: Pas de résultat dans do_merge()")
                dialog.dialog.destroy()
                return

            source_file, target_file, choice = result
            print(f"DEBUG: source={source_file}, target={target_file}, choice={choice}")

            try:
                dialog._add_report_line("🔄 Démarrage de la fusion...")
                dialog._add_report_line(f"  Fichier source (traductions): {Path(source_file).name}")
                dialog._add_report_line(f"  Fichier cible (structure): {Path(target_file).name}")
                dialog._add_report_line("")

                # Charger les fichiers
                dialog._add_report_line("📂 Chargement des fichiers...")

                # Charger le fichier source (avec détection automatique .got.json)
                actual_source_file = source_file
                source_path = Path(source_file)

                # Si c'est un .json, chercher le .got.json correspondant
                if source_path.suffix == '.json' and not source_path.name.endswith('.got.json'):
                    got_path = source_path.with_suffix('.got.json')
                    if got_path.exists():
                        actual_source_file = str(got_path)
                        dialog._add_report_line(f"  ℹ️ Utilisation de {got_path.name} (trouvé à partir de {source_path.name})")

                dialog._add_report_line(f"  Lecture du fichier source: {Path(actual_source_file).name}")
                with open(actual_source_file, 'r', encoding='utf-8') as f:
                    source_data = json5.load(f)

                # Compter les entrées du fichier source
                source_count = 0
                if isinstance(source_data, dict):
                    if "__ollamafic__" in source_data:
                        # Fichier .got.json - compter les entrées
                        source_count = len([k for k in source_data.keys() if k != "__ollamafic__"])
                    else:
                        # JSON normal - compter les clés racine
                        source_count = len(source_data.keys())
                dialog._add_report_line(f"  → {source_count} entrée(s) trouvée(s)")

                # Charger le fichier cible (avec détection automatique .got.json)
                actual_target_file = target_file
                target_path = Path(target_file)

                # Si c'est un .json, chercher le .got.json correspondant
                if target_path.suffix == '.json' and not target_path.name.endswith('.got.json'):
                    got_path = target_path.with_suffix('.got.json')
                    if got_path.exists():
                        actual_target_file = str(got_path)
                        dialog._add_report_line(f"  ℹ️ Utilisation de {got_path.name} (trouvé à partir de {target_path.name})")

                dialog._add_report_line(f"  Lecture du fichier cible: {Path(actual_target_file).name}")
                with open(actual_target_file, 'r', encoding='utf-8') as f:
                    target_data = json5.load(f)

                # Compter les entrées du fichier cible
                target_count = 0
                if isinstance(target_data, dict):
                    if "__ollamafic__" in target_data:
                        # Fichier .got.json - compter les entrées
                        target_count = len([k for k in target_data.keys() if k != "__ollamafic__"])
                    else:
                        # JSON normal - compter les clés racine
                        target_count = len(target_data.keys())
                dialog._add_report_line(f"  → {target_count} entrée(s) trouvée(s)")
                dialog._add_report_line("")

                # Créer un backup du fichier actuel
                dialog._add_report_line("💾 Création du backup...")
                backup_path = create_backup_with_timestamp(self.current_file_path)
                dialog._add_report_line(f"  Backup: {Path(backup_path).name}")
                dialog._add_report_line("")

                # Déterminer le nom du fichier original
                if isinstance(target_data, dict) and "__ollamafic__" in target_data:
                    original_filename = target_data["__ollamafic__"].get("original_file", Path(target_file).name)
                    is_target_got_json = True
                else:
                    original_filename = Path(target_file).name
                    is_target_got_json = False

                # Récupérer les langues
                target_languages = self.translation_config.get("target_languages", ["fr", "en", "es"])

                # Créer le gestionnaire
                from core.got_json_manager import GotJsonManager
                temp_manager = GotJsonManager(target_languages=target_languages)

                # Si le target est déjà un .got.json, extraire le JSON de base
                if is_target_got_json:
                    dialog._add_report_line("  ℹ️ Le fichier cible est déjà un .got.json")
                    dialog._add_report_line("  → Extraction du JSON de base pour la fusion...")

                    # Convertir le .got.json en .json simple (sans traductions)
                    base_json = temp_manager.extract_base_json(target_data)
                    target_data_for_merge = base_json
                else:
                    target_data_for_merge = target_data

                # Callback de progression
                def progress_callback(current, total):
                    dialog.update_progress(current, total)

                dialog._add_report_line("🔄 Fusion en cours...")

                # Faire la fusion
                merged_data, stats = temp_manager.evolve_got_json(
                    source_data,
                    target_data_for_merge,
                    original_filename,
                    progress_callback
                )

                # Sauvegarder dans le fichier actuel
                dialog._add_report_line("")
                dialog._add_report_line("💾 Sauvegarde du résultat...")
                temp_manager.save_to_file(self.current_file_path)

                # Afficher les stats
                dialog.show_stats(stats)

                # Recharger le fichier dans l'interface
                self.got_manager = temp_manager

                # Mettre à jour les formulaires avec le nouveau manager
                self.translation_form.set_got_manager(self.got_manager)
                self.batch_form.set_got_manager(self.got_manager)

                # Revenir en mode formulaire normal (si on était en mode batch)
                if self.batch_form.winfo_ismapped():
                    self.batch_form.pack_forget()

                self.translation_form.pack(fill=tk.BOTH, expand=True)

                # Recharger l'arbre et marquer comme sauvegardé
                self._populate_tree()
                self._mark_as_saved()

                # Message dans le chat
                self.chat_panel.add_message(
                    "system",
                    f"Fusion réussie: {stats['recovered']} entrées récupérées, {stats['new_entries']} nouvelles"
                )

                self.status_label.config(text="✓ Fusion terminée")

            except Exception as e:
                dialog._add_report_line("")
                dialog._add_report_line("❌ ERREUR:")
                dialog._add_report_line(str(e))
                dialog.cancel_button.config(state="normal")
                import traceback
                traceback.print_exc()

        # Connecter le bouton de fusion
        original_merge = dialog._on_merge

        def new_on_merge():
            try:
                print("DEBUG: new_on_merge appelé")
                original_merge()
                print(f"DEBUG: dialog.result = {dialog.result}")
                if dialog.result:
                    print("DEBUG: Appel de do_merge()")
                    do_merge()
                else:
                    print("DEBUG: Pas de résultat, annulation")
            except Exception as e:
                print(f"ERROR dans new_on_merge: {e}")
                import traceback
                traceback.print_exc()
                dialog._add_report_line("")
                dialog._add_report_line(f"❌ ERREUR: {str(e)}")
                dialog.cancel_button.config(state="normal")

        # IMPORTANT: Reconfigurer le bouton pour utiliser notre wrapper
        # (car le bouton a déjà une référence à l'ancienne méthode)
        dialog.merge_button.config(command=new_on_merge)

        # Afficher le dialog
        dialog.show()

    def load_file(self, filepath: str):
        """
        Charge un fichier JSON ou .got.json.

        Args:
            filepath: Chemin vers le fichier à charger
        """
        try:
            self.status_label.config(text="Chargement en cours...")
            self.root.update()

            # Récupérer les langues cibles avant le chargement
            target_languages = self.translation_config.get("target_languages", ["fr", "en", "es"])

            # Utiliser le chargement intelligent avec détection d'évolution
            self.got_manager, got_path = load_file_with_evolution_check(
                filepath,
                parent_window=self.root,
                target_languages=target_languages
            )
            self.current_file_path = got_path
            self.translation_form.visible_languages = self.translation_config.get("visible_languages", [])

            # Mettre à jour le formulaire
            self.translation_form.set_got_manager(self.got_manager)

            # Mettre à jour le batch_form
            self.batch_form.set_got_manager(self.got_manager)
            self.batch_form.set_translation_config(self.translation_config)

            # Charger l'arbre
            self._populate_tree()

            # Mettre à jour la barre de statut
            filename = Path(got_path).name
            self.file_label.config(text=filename)

            # Marquer comme non modifié (fichier vient d'être chargé)
            self._mark_as_saved()

            # Afficher les stats dans le chat
            stats = self.got_manager.get_translation_stats()
            self.chat_panel.add_message("system",
                f"Fichier chargé: {stats['total_entries']} entrées traduisibles")

            # Mettre à jour le menu Export
            self._update_export_menu()

            # Message de succès
            self.status_label.config(text=f"✓ Fichier chargé: {filename}")

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le fichier:\n{e}")
            self.status_label.config(text="❌ Erreur de chargement")
            import traceback
            traceback.print_exc()

    def _populate_tree(self):
        """Remplit l'arbre avec les données du .got.json."""
        # Nettoyer l'arbre
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.tree_item_to_path.clear()
        self.path_to_tree_item.clear()

        if not self.got_manager or not self.got_manager.data:
            return

        # Construire l'arbre récursivement
        self._add_tree_node("", "", self.got_manager.data)

        # Après construction, propager les couleurs à tous les parents
        self._update_all_parent_colors()

    def _sort_tree_ascending(self):
        """Trie l'arbre par ordre alphabétique croissant (A→Z)."""
        self.tree_sort_mode = "ascending"
        self._populate_tree()

    def _sort_tree_descending(self):
        """Trie l'arbre par ordre alphabétique décroissant (Z→A)."""
        self.tree_sort_mode = "descending"
        self._populate_tree()

    def _sort_tree_original(self):
        """Restaure l'ordre original de l'arbre (tel que dans le JSON)."""
        self.tree_sort_mode = "original"
        self._populate_tree()

    def _add_tree_node(self, parent_item, current_path, data):
        """
        Ajoute récursivement des nœuds à l'arbre.

        Args:
            parent_item: Item parent dans l'arbre
            current_path: Chemin actuel (ex: "app/title")
            data: Données à ajouter
        """
        if isinstance(data, dict):
            # Trier les clés selon le mode de tri
            keys = list(data.items())
            if self.tree_sort_mode == "ascending":
                keys.sort(key=lambda x: str(x[0]).lower())
            elif self.tree_sort_mode == "descending":
                keys.sort(key=lambda x: str(x[0]).lower(), reverse=True)
            # else: "original" - garder l'ordre du dictionnaire

            for key, value in keys:
                # Ignorer le header __ollamafic__
                if key == "__ollamafic__":
                    continue

                # Construire le chemin
                new_path = f"{current_path}/{key}" if current_path else key

                # Déterminer si c'est une entrée traduisible
                is_translatable = isinstance(value, dict) and "ori" in value

                # Créer le nœud
                if is_translatable:
                    # Entrée traduisible - obtenir l'état de validation
                    state = self.got_manager.get_validation_state(new_path)
                    icon = self._get_icon_for_state(state)
                    display_text = f"{icon} {key}"
                    item = self.tree.insert(parent_item, "end", text=display_text, tags=(state,))
                else:
                    # Container ou valeur non traduisible
                    icon = "📁" if isinstance(value, dict) else "📄"
                    item = self.tree.insert(parent_item, "end", text=f"{icon} {key}")

                # Sauvegarder le mapping
                self.tree_item_to_path[item] = new_path
                self.path_to_tree_item[new_path] = item

                # Récursion pour les enfants
                if isinstance(value, dict) and not is_translatable:
                    self._add_tree_node(item, new_path, value)

        elif isinstance(data, list):
            for i, value in enumerate(data):
                new_path = f"{current_path}[{i}]"

                # Vérifier si c'est traduisible
                is_translatable = isinstance(value, dict) and "ori" in value

                if is_translatable:
                    state = self.got_manager.get_validation_state(new_path)
                    icon = self._get_icon_for_state(state)
                    display_text = f"{icon} [{i}]"
                    item = self.tree.insert(parent_item, "end", text=display_text, tags=(state,))
                else:
                    item = self.tree.insert(parent_item, "end", text=f"[{i}]")

                self.tree_item_to_path[item] = new_path
                self.path_to_tree_item[new_path] = item

                if isinstance(value, (dict, list)) and not is_translatable:
                    self._add_tree_node(item, new_path, value)

    def _get_icon_for_state(self, state: str) -> str:
        """Retourne l'icône pour un état de validation."""
        icons = {
            "green": "✅",
            "orange": "🟠",
            "red": "❌",
            "none": "⚪"
        }
        return icons.get(state, "⚪")

    def _on_tree_select(self, event):
        """Gère la sélection dans l'arbre."""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        path = self.tree_item_to_path.get(item)

        if path:
            # Mettre à jour l'état courant AVANT tout
            try:
                entry = self.got_manager._get_entry_by_path(path)
                self.current_entry_state["path"] = path
                self.current_entry_state["entry"] = entry
            except:
                self.current_entry_state["path"] = None
                self.current_entry_state["entry"] = None

            # Mettre à jour l'affichage du chemin actuel
            self.current_path_label.config(text=path)

            # Vérifier si c'est une feuille traduisible ou une branche
            is_leaf = self.got_manager.is_translatable_leaf(path)

            if is_leaf:
                # C'est une feuille -> Afficher le formulaire de traduction
                self.batch_form.pack_forget()
                self.translation_form.pack(fill="both", expand=True)
                self.translation_form.load_entry(path)
            else:
                # C'est une branche -> Afficher le formulaire de traduction par lot
                self.translation_form.pack_forget()
                leaves = self.got_manager.get_translatable_leaves_in_subtree(path)
                self.batch_form.pack(fill="both", expand=True)
                self.batch_form.load_branch(path, leaves)

            # Mettre à jour le contexte du chat
            self.chat_panel.set_context(path)

    def _translate_text(self, text: str, target_lang: str, source_lang: str = "auto") -> Optional[str]:
        """
        Traduit un texte avec gestion du timeout.

        Args:
            text: Texte à traduire
            target_lang: Code langue cible (ex: "fr")
            source_lang: Code langue source (ex: "en" ou "auto")

        Returns:
            Texte traduit ou None en cas d'erreur/timeout
        """
        if not text or not text.strip():
            return None

        # Calculer un timeout dynamique basé sur la taille du texte
        text_length = len(text)
        estimated_time = text_length / 5  # secondes (vitesse très conservatrice: 5 chars/sec)
        timeout = max(120, int(estimated_time * 4))  # minimum 120s, marge x4

        # Construire le prompt
        prompts = self.translation_config.get("prompts", {})
        has_html = '<' in text and '>' in text

        # Construire la phrase de langue source
        source_lang_phrase = ""
        if source_lang and source_lang != "auto":
            lang_names = {
                "en": "anglais", "fr": "français", "es": "espagnol", "de": "allemand",
                "it": "italien", "pt": "portugais", "ru": "russe", "ja": "japonais",
                "zh": "chinois", "ko": "coréen", "ar": "arabe"
            }
            source_lang_name = lang_names.get(source_lang, source_lang)
            source_lang_phrase = f" depuis le {source_lang_name}"

        # Obtenir le nom complet de la langue
        known_languages = self.translation_config.get("known_languages", {})
        lang_name = known_languages.get(target_lang, target_lang.upper())

        if has_html:
            prompt_template = prompts.get("translate_html",
                'Traduis le texte suivant{source_lang} en {lang}.\nIMPORTANT: Préserve TOUTES les balises HTML.\n\n{text}')
            prompt = prompt_template.format(text=text, lang=lang_name, source_lang=source_lang_phrase)
        else:
            prompt_template = prompts.get("translate",
                'Traduis "{text}"{source_lang} en {lang}. Réponds uniquement avec la traduction, sans explication.')
            prompt = prompt_template.format(text=text, lang=lang_name, source_lang=source_lang_phrase)

        try:
            # Effacer l'historique pour éviter les réponses précédentes
            self.ai_client.clear_conversation()

            # Créer une nouvelle boucle d'événements pour ce thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Exécuter l'appel asynchrone avec timeout dynamique
            raw_result = loop.run_until_complete(self.ai_client.chat(prompt, timeout=timeout))

            # Fermer la boucle
            loop.close()

            # Nettoyer le résultat
            if isinstance(raw_result, dict):
                result = raw_result.get("message", {}).get("content", "")
            else:
                result = str(raw_result)

            result = result.strip().strip('"').strip("'")
            return result if result else None

        except asyncio.TimeoutError:
            print(f"⏱️ Timeout lors de la traduction ({timeout}s dépassé)")
            return None
        except Exception as e:
            print(f"❌ Erreur lors de la traduction: {e}")
            return None

    def _on_magic_click(self, lang: str, action: str, selection_data: dict = None, source_lang: str = "auto"):
        """
        Gère le clic sur la baguette magique.

        Args:
            lang: Code langue cible
            action: "translate", "improve", "translate_selection" ou "improve_selection"
            selection_data: Dict avec {"start": index, "end": index, "text": str} ou None
            source_lang: Langue d'origine ("auto" pour détection automatique)
        """
        # Utiliser current_entry_state systématiquement
        if not self.current_entry_state["path"] or not self.current_entry_state["entry"]:
            return

        # IMPORTANT: Capturer les variables IMMÉDIATEMENT pour éviter les race conditions
        # Si on clique rapidement sur plusieurs traductions, current_entry_state peut changer
        captured_path = self.current_entry_state["path"]
        captured_entry = self.current_entry_state["entry"]
        captured_lang = lang
        captured_action = action
        captured_selection = selection_data  # Peut être None
        captured_source_lang = source_lang

        original = captured_entry["ori"]
        current_text = captured_entry[captured_lang]["text"]

        # Construire le prompt à partir de la configuration
        prompts = self.translation_config.get("prompts", {})

        # Gérer les actions de sélection
        is_selection = captured_action in ("translate_selection", "improve_selection")
        text_to_translate = captured_selection["text"] if is_selection and captured_selection else None

        # Calculer un timeout dynamique basé sur la taille du texte RÉELLEMENT ENVOYÉ
        # Formule: timeout_base + (nb_caractères / vitesse_estimation) * marge
        # Ollama local avec HTML: ~5 tokens/sec, avec ~4 chars/token = ~20 chars/sec (théorique)
        # En pratique, avec HTML complexe: beaucoup plus lent
        # Utiliser une vitesse très conservatrice de 5 chars/sec et marge x4
        if is_selection and text_to_translate:
            # Pour une sélection, calculer sur la taille de la sélection
            text_length = len(text_to_translate)
        elif captured_action in ("translate", "translate_selection"):
            # Pour une traduction, calculer sur la taille de l'original ou de la sélection
            text_length = len(text_to_translate) if text_to_translate else len(original)
        else:
            # Pour une amélioration, calculer sur l'original + texte actuel
            text_length = len(original) + len(current_text)

        estimated_time = text_length / 5  # secondes (vitesse très conservatrice)
        captured_timeout = max(120, int(estimated_time * 4))  # minimum 120s, marge x4

        # Construire la phrase de langue source
        source_lang_phrase = ""
        if captured_source_lang and captured_source_lang != "auto":
            # Mapping des codes de langue vers noms complets
            lang_names = {
                "en": "anglais", "fr": "français", "es": "espagnol", "de": "allemand",
                "it": "italien", "pt": "portugais", "ru": "russe", "ja": "japonais",
                "zh": "chinois", "ko": "coréen", "ar": "arabe"
            }
            source_lang_name = lang_names.get(captured_source_lang, captured_source_lang)
            source_lang_phrase = f" depuis le {source_lang_name}"

        if captured_action in ("translate", "translate_selection"):
            # Détecter si le texte contient du HTML
            source_text = text_to_translate if is_selection else original
            has_html = '<' in source_text and '>' in source_text

            if is_selection:
                # Pour une sélection, être TRÈS strict sur le format de réponse
                if has_html:
                    prompt_template = prompts.get("translate_selection_html",
                        'Traduis UNIQUEMENT ce fragment{source_lang} en {lang}.\nIMPORTANT: Préserve TOUTES les balises HTML.\nRéponds UNIQUEMENT avec la traduction du fragment, RIEN d\'autre.\n\n{text}')
                    prompt = prompt_template.format(text=source_text, lang=captured_lang, source_lang=source_lang_phrase)
                else:
                    prompt_template = prompts.get("translate_selection",
                        'Traduis UNIQUEMENT ce fragment{source_lang} en {lang}.\nRéponds UNIQUEMENT avec la traduction du fragment, sans guillemets, sans explication, RIEN d\'autre.\n\n{text}')
                    prompt = prompt_template.format(text=source_text, lang=captured_lang, source_lang=source_lang_phrase)
            else:
                # Traduction complète
                if has_html:
                    # Utiliser le prompt HTML de la config, ou fallback sur le défaut
                    prompt_template = prompts.get("translate_html",
                        'Traduis le texte suivant{source_lang} en {lang}.\nIMPORTANT: Préserve TOUTES les balises HTML.\n\n{text}')
                    prompt = prompt_template.format(text=source_text, lang=captured_lang, source_lang=source_lang_phrase)
                else:
                    # Utiliser le prompt simple de la config, ou fallback
                    prompt_template = prompts.get("translate",
                        'Traduis "{text}"{source_lang} en {lang}. Réponds uniquement avec la traduction, sans explication.')
                    prompt = prompt_template.format(text=source_text, lang=captured_lang, source_lang=source_lang_phrase)
        else:  # improve ou improve_selection
            context = self._get_context_for_path(captured_path)

            if is_selection:
                # Pour une sélection, on améliore uniquement la partie sélectionnée
                source_text = text_to_translate
                # On ne connaît pas l'original de la sélection, donc on ne l'inclut pas
                has_html = '<' in source_text and '>' in source_text

                if has_html:
                    prompt_template = prompts.get("improve_selection_html",
                        'Améliore UNIQUEMENT ce fragment de traduction{source_lang} vers {lang}.\nIMPORTANT: Préserve TOUTES les balises HTML.\nRéponds UNIQUEMENT avec le fragment amélioré, RIEN d\'autre.\n\nTexte: {current}\nContexte: {context}')
                    prompt = prompt_template.format(lang=captured_lang, current=source_text, context=context, source_lang=source_lang_phrase)
                else:
                    prompt_template = prompts.get("improve_selection",
                        'Améliore UNIQUEMENT ce fragment de traduction{source_lang} vers {lang}.\nRéponds UNIQUEMENT avec le fragment amélioré, sans guillemets, sans explication, RIEN d\'autre.\n\nTexte: "{current}"\nContexte: {context}')
                    prompt = prompt_template.format(lang=captured_lang, current=source_text, context=context, source_lang=source_lang_phrase)
            else:
                # Amélioration complète (comportement normal)
                has_html = '<' in current_text and '>' in current_text

                if has_html:
                    # Utiliser le prompt amélioration HTML de la config
                    prompt_template = prompts.get("improve_html",
                        'Améliore cette traduction{source_lang} vers {lang}.\nIMPORTANT: Préserve TOUTES les balises HTML.\n\nOriginal: {original}\nActuel: {current}\nContexte: {context}')
                    prompt = prompt_template.format(lang=captured_lang, original=original,
                                                   current=current_text, context=context, source_lang=source_lang_phrase)
                else:
                    # Utiliser le prompt amélioration simple de la config
                    prompt_template = prompts.get("improve",
                        'Améliore cette traduction{source_lang} vers {lang}:\nOriginal: "{original}"\nActuel: "{current}"\nContexte: {context}')
                    prompt = prompt_template.format(lang=captured_lang, original=original,
                                                   current=current_text, context=context, source_lang=source_lang_phrase)

        # Logger le début de la traduction dans le chat avec le texte original
        if captured_action in ("translate", "translate_selection"):
            source_text = text_to_translate if is_selection else original
            action_text = "Traduire sélection" if is_selection else "Traduire"
            self.chat_panel.add_message("system", f"{captured_lang.upper()}: {action_text} → \"{source_text[:100]}{'...' if len(source_text) > 100 else ''}\" (timeout: {captured_timeout}s)")
        else:
            source_text = text_to_translate if is_selection else current_text
            action_text = "Améliorer sélection" if is_selection else "Améliorer"
            self.chat_panel.add_message("system", f"{captured_lang.upper()}: {action_text} → \"{source_text[:100]}{'...' if len(source_text) > 100 else ''}\" (timeout: {captured_timeout}s)")

        # Lancer l'appel IA dans un thread séparé
        self.status_label.config(text=f"🪄 Traduction {captured_lang} en cours... (max {captured_timeout}s)")
        self.root.update()

        def run_translation():
            """Fonction exécutée dans un thread séparé"""
            try:
                # IMPORTANT: Effacer l'historique de conversation avant chaque traduction
                # pour éviter que Ollama réutilise les réponses précédentes
                self.ai_client.clear_conversation()

                # Créer une nouvelle boucle d'événements pour ce thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Exécuter l'appel asynchrone avec timeout dynamique
                raw_result = loop.run_until_complete(self.ai_client.chat(prompt, timeout=captured_timeout))
                # Sauvegarder la réponse brute (retourné par l'IA)
                returned_by_ai = raw_result.strip()

                result = returned_by_ai.strip('"').strip("'")

                # Pour les sélections, vérifier que le résultat n'est pas trop long
                if is_selection and text_to_translate:
                    original_length = len(text_to_translate)
                    result_length = len(result)

                    # Ratio de tolérance : une traduction peut être jusqu'à 2x plus longue
                    # (certaines langues comme le français sont plus verbeuses)
                    max_acceptable_length = original_length * 2.5

                    if result_length > max_acceptable_length:
                        # Le résultat semble contenir du texte supplémentaire
                        # Essayer de nettoyer en cherchant des motifs communs

                        # Motif : "Traduction : xxxx" ou "Voici la traduction : xxxx"
                        patterns = [
                            r'^.*?[Tt]raduction\s*:?\s*(.+)$',
                            r'^.*?[Vv]oici\s*:?\s*(.+)$',
                            r'^.*?[Rr]ésultat\s*:?\s*(.+)$',
                        ]

                        cleaned = result
                        for pattern in patterns:
                            match = re.search(pattern, result, re.DOTALL)
                            if match:
                                cleaned = match.group(1).strip().strip('"').strip("'")
                                break

                        # Si après nettoyage c'est encore trop long, tronquer avec avertissement
                        if len(cleaned) > max_acceptable_length:
                            # Logger un avertissement dans le chat
                            warning_msg = f"⚠️ Résultat trop long ({len(result)} car. pour {original_length} car. originaux). Utilisation du résultat tel quel - vérifiez manuellement."
                            self.root.after(0, lambda msg=warning_msg: self.chat_panel.add_message("system", msg))
                            result = cleaned  # Utiliser le résultat nettoyé même s'il est long
                        else:
                            result = cleaned

                # Fermer la boucle
                loop.close()

                # Déterminer le texte envoyé à l'IA
                sent_to_ai = text_to_translate if is_selection and text_to_translate else (original if captured_action in ("translate", "translate_selection") else current_text)

                # Mettre à jour l'UI dans le thread principal
                # Utiliser les variables capturées (pas les variables de _on_magic_click qui peuvent changer!)
                # Passer : path, lang, result (texte retenu), action, selection_data, sent_to_ai, returned_by_ai, prompt (pour debug)
                self.root.after(0, lambda p=captured_path, l=captured_lang, kept=result, a=captured_action, s=captured_selection, sent=sent_to_ai, ret=returned_by_ai, pr=prompt:
                              self._on_translation_success(p, l, kept, a, s, sent, ret, pr))

            except Exception as ex:
                # Capturer l'erreur dans une variable locale
                error_msg = str(ex)
                # Afficher l'erreur dans le thread principal
                self.root.after(0, lambda msg=error_msg: self._on_translation_error(msg))

        # Lancer le thread
        thread = threading.Thread(target=run_translation, daemon=True)
        thread.start()

    def _on_deepl_click(self, lang: str, action: str, selection_data: dict = None, source_lang: str = "auto"):
        """
        Gère le clic sur le bouton DeepL.

        Args:
            lang: Code langue cible
            action: "translate", "improve", "translate_selection" ou "improve_selection"
            selection_data: Dict avec {"start": index, "end": index, "text": str} ou None
            source_lang: Langue d'origine ("auto" pour détection automatique)
        """
        # Vérifier si DeepL est activé dans la configuration
        deepl_config = self.translation_config.get("ai_config", {}).get("deepl", {})
        deepl_enabled = deepl_config.get("enabled", False)

        if not deepl_enabled:
            messagebox.showwarning("DeepL désactivé",
                                 "DeepL n'est pas activé. Veuillez l'activer dans Options > Configuration IA.")
            return

        api_key = deepl_config.get("api_key", "")
        if not api_key:
            messagebox.showwarning("Clé API manquante",
                                 "Clé API DeepL non configurée. Veuillez la configurer dans Options > Configuration IA.")
            return

        # Utiliser current_entry_state systématiquement
        if not self.current_entry_state["path"] or not self.current_entry_state["entry"]:
            return

        # IMPORTANT: Capturer les variables IMMÉDIATEMENT
        captured_path = self.current_entry_state["path"]
        captured_entry = self.current_entry_state["entry"]
        captured_lang = lang
        captured_action = action
        captured_selection = selection_data
        captured_source_lang = source_lang

        original = captured_entry["ori"]
        current_text = captured_entry[captured_lang]["text"]

        # Gérer les actions de sélection
        is_selection = captured_action in ("translate_selection", "improve_selection")
        text_to_translate = captured_selection["text"] if is_selection and captured_selection else None

        # Pour DeepL, on ne fait que de la traduction (pas d'amélioration comme avec les LLM)
        # Si l'action est "improve", on re-traduit simplement le texte actuel
        if is_selection and text_to_translate:
            source_text = text_to_translate
        elif captured_action in ("translate", "translate_selection"):
            source_text = text_to_translate if is_selection else original
        else:  # improve ou improve_selection
            source_text = text_to_translate if is_selection else current_text

        # Timeout pour DeepL (plus court car c'est une API rapide)
        timeout = 30

        # Logger le début de la traduction
        self.chat_panel.add_message("system",
            f"DeepL {captured_lang.upper()}: Traduction → \"{source_text[:100]}{'...' if len(source_text) > 100 else ''}\"")

        # Lancer l'appel DeepL dans un thread séparé
        self.status_label.config(text=f"🌐 Traduction DeepL {captured_lang} en cours...")
        self.root.update()

        def run_deepl_translation():
            """Fonction exécutée dans un thread séparé"""
            try:
                # Utiliser l'instance globale de DeepL pour le comptage
                # Si disponible, sinon créer une instance locale
                if "deepl" in self.ai_client.providers:
                    deepl_provider = self.ai_client.providers["deepl"]
                else:
                    # Fallback : créer une instance locale (ne comptera pas dans le total)
                    from core.ai_client import DeepLProvider
                    deepl_provider = DeepLProvider({
                        "api_key": api_key,
                        "is_pro": deepl_config.get("is_pro", False),
                        "timeout": timeout
                    })

                # Mapper le code langue pour DeepL
                # DeepL utilise des codes en majuscules avec tiret (ex: EN-US, FR, ES)
                deepl_lang_map = {
                    "en": "EN-US",
                    "fr": "FR",
                    "es": "ES",
                    "de": "DE",
                    "it": "IT",
                    "pt": "PT-BR",
                    "ru": "RU",
                    "ja": "JA",
                    "zh": "ZH",
                    "ko": "KO",
                    "ar": "AR"
                }
                target_lang_deepl = deepl_lang_map.get(captured_lang, captured_lang.upper())

                # Mapper la langue source si spécifiée
                source_lang_deepl = None
                if captured_source_lang and captured_source_lang != "auto":
                    source_lang_deepl = deepl_lang_map.get(captured_source_lang, captured_source_lang.upper())

                # Créer une boucle d'événements pour ce thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Appeler DeepL avec timeout
                result = loop.run_until_complete(
                    deepl_provider.translate(source_text, target_lang_deepl, source_lang_deepl, timeout)
                )

                # Fermer la boucle
                loop.close()

                # Nettoyer le résultat
                result = result.strip() if result else ""

                if not result:
                    raise Exception("Traduction vide reçue de DeepL")

                # Mettre à jour l'UI dans le thread principal
                self.root.after(0, lambda p=captured_path, l=captured_lang, kept=result, a=captured_action,
                              s=captured_selection, sent=source_text, ret=result:
                              self._on_translation_success(p, l, kept, a, s, sent, ret, f"DeepL: {source_text} -> {target_lang_deepl}"))

            except Exception as ex:
                error_msg = str(ex)
                self.root.after(0, lambda msg=error_msg: self._on_translation_error(msg))

        # Lancer le thread
        thread = threading.Thread(target=run_deepl_translation, daemon=True)
        thread.start()

    def _on_translation_success(self, path: str, lang: str, kept_text: str, action: str,
                               selection_data: dict = None, sent_text: str = None,
                               returned_text: str = None, full_prompt: str = None):
        """
        Callback appelé après succès de la traduction (dans le thread principal).

        Args:
            path: Chemin de l'entrée
            lang: Code langue
            kept_text: Texte retenu/inséré dans le champ
            action: Action effectuée
            selection_data: Données de sélection (None si traduction complète)
            sent_text: Texte envoyé à l'IA
            returned_text: Réponse brute de l'IA
            full_prompt: Prompt complet (pour debug)
        """
        try:
            is_selection = action in ("translate_selection", "improve_selection")

            if is_selection and selection_data:
                # Traduction partielle : remplacer uniquement la sélection
                # Récupérer l'entrée actuelle
                current_entry = self.got_manager._get_entry_by_path(path)
                current_text_before = current_entry[lang]["text"]

                # Construire le nouveau texte en remplaçant la sélection
                # Utiliser les index de sélection pour remplacer
                text_widget = self.translation_form.text_widgets.get(lang)
                if text_widget:
                    # Obtenir les positions actuelles
                    start_idx = selection_data["start"]
                    end_idx = selection_data["end"]

                    # Construire le nouveau texte
                    text_before = text_widget.get("1.0", start_idx)
                    text_after = text_widget.get(end_idx, "end-1c")
                    new_full_text = text_before + kept_text + text_after

                    # Mettre à jour dans got_manager (gère automatiquement l'historique)
                    self.got_manager.update_translation(path, lang, new_full_text)
                    updated_entry = self.got_manager._get_entry_by_path(path)
                    self._mark_as_modified()
                else:
                    # Fallback : mettre à jour le texte complet
                    self.got_manager.update_translation(path, lang, kept_text)
                    updated_entry = self.got_manager._get_entry_by_path(path)
                    self._mark_as_modified()
            else:
                # Traduction complète : comportement normal
                self.got_manager.update_translation(path, lang, kept_text)
                updated_entry = self.got_manager._get_entry_by_path(path)
                self._mark_as_modified()

            # Mettre à jour les couleurs de l'arbre
            self._update_tree_colors(path)

            # Log dans le chat avec informations Envoyé/Retourné/Retenu
            validated = updated_entry[lang]["valid"]

            # Passer le prompt complet si en mode debug
            debug_prompt = full_prompt if self.debug_mode else None

            self.chat_panel.add_magic_action(
                lang=lang,
                action=action,
                sent_text=sent_text or "",
                returned_text=returned_text or "",
                kept_text=kept_text,
                validated=validated,
                full_prompt=debug_prompt
            )

            # Vérifier avec current_entry_state pour savoir si on doit rafraîchir
            if self.current_entry_state["path"] == path:
                # C'est toujours la même entrée - mettre à jour current_entry_state
                self.current_entry_state["entry"] = updated_entry

                # Mettre à jour le formulaire directement
                self.translation_form.current_entry = updated_entry
                self.translation_form.update_language_data(lang)

                self.status_label.config(text="✓ Traduction terminée")
            else:
                # L'utilisateur a changé de sélection pendant la traduction
                self.status_label.config(text=f"✓ Traduction terminée pour {path}")

        except Exception as e:
            self._on_translation_error(str(e))

    def _on_translation_error(self, error_message: str):
        """
        Callback appelé en cas d'erreur de traduction (dans le thread principal).
        """
        messagebox.showerror("Erreur IA", f"Erreur lors de l'appel IA: {error_message}")
        self.chat_panel.add_error(error_message)
        self.status_label.config(text="❌ Erreur de traduction")

    def _on_validate(self, lang: str, valid: bool):
        """Gère le changement de validation."""
        if not self.current_entry_state["path"]:
            return

        path = self.current_entry_state["path"]
        self.got_manager.validate_translation(path, lang, valid)
        self._mark_as_modified()

        # Mettre à jour current_entry_state
        self.current_entry_state["entry"] = self.got_manager._get_entry_by_path(path)

        # Mettre à jour l'entrée dans le formulaire
        self.translation_form.current_entry = self.current_entry_state["entry"]

        # Mettre à jour les couleurs
        self._update_tree_colors(path)

        # Log dans le chat
        self.chat_panel.add_validation_change(lang, valid)

    def _on_rollback(self, lang: str):
        """Gère le retour arrière."""
        if not self.current_entry_state["path"]:
            return

        path = self.current_entry_state["path"]
        restored = self.got_manager.rollback_translation(path, lang)

        if restored:
            # Mettre à jour current_entry_state
            self.current_entry_state["entry"] = self.got_manager._get_entry_by_path(path)

            # Rafraîchir l'entrée et le formulaire
            self.translation_form.current_entry = self.current_entry_state["entry"]
            self.translation_form.update_language_data(lang)

            # Mettre à jour les couleurs
            self._update_tree_colors(path)

            # Log dans le chat
            self.chat_panel.add_rollback(lang, restored)

    def _undo_all_languages(self):
        """Annule la dernière traduction pour toutes les langues du champ actuel."""
        if not self.current_entry_state["path"]:
            messagebox.showinfo("Aucune sélection", "Veuillez sélectionner un champ à annuler.")
            return

        path = self.current_entry_state["path"]
        entry = self.current_entry_state["entry"]

        if not isinstance(entry, dict) or "ori" not in entry:
            messagebox.showwarning("Non traduisible", "Ce champ n'est pas traduisible.")
            return

        # Compter combien de langues ont un historique
        languages_with_history = []
        for lang in self.got_manager.target_languages:
            if lang in entry and len(entry[lang]["history"]) > 0:
                languages_with_history.append(lang)

        if not languages_with_history:
            messagebox.showinfo("Pas d'historique", "Aucune langue n'a d'historique à annuler.")
            return

        # Confirmer l'action
        langs_str = ", ".join(languages_with_history)
        if not messagebox.askyesno("Confirmer l'annulation",
                                   f"Annuler la dernière traduction pour: {langs_str}?"):
            return

        # Annuler pour chaque langue
        for lang in languages_with_history:
            restored = self.got_manager.rollback_translation(path, lang)
            if restored:
                self.chat_panel.add_rollback(lang, restored)

        # Rafraîchir le formulaire
        self.translation_form.load_entry(path)
        self._update_tree_colors(path)

        messagebox.showinfo("Annulation réussie",
                           f"Annulé pour {len(languages_with_history)} langue(s).")

    def _on_manual_edit(self, lang: str, new_text: str):
        """Gère l'édition manuelle."""
        if not self.current_entry_state["path"]:
            return

        path = self.current_entry_state["path"]

        # Mettre à jour avec historique
        self.got_manager.update_translation(path, lang, new_text)
        self._mark_as_modified()

        # Mettre à jour current_entry_state
        self.current_entry_state["entry"] = self.got_manager._get_entry_by_path(path)

    def _on_batch_deepl_translate(self, lang: str, selected_paths: list):
        """
        Gère la traduction DeepL par lot d'un sous-arbre.

        Args:
            lang: Code langue cible
            selected_paths: Liste des chemins sélectionnés
        """
        if not selected_paths:
            messagebox.showinfo("Aucune feuille sélectionnée",
                              "Veuillez sélectionner au moins une feuille à traduire.")
            return

        # Vérifier si DeepL est configuré
        deepl_config = self.translation_config.get("ai_config", {}).get("deepl", {})
        deepl_enabled = deepl_config.get("enabled", False)

        if not deepl_enabled:
            messagebox.showwarning("DeepL désactivé",
                                 "DeepL n'est pas activé. Veuillez l'activer dans Options > Configuration IA.")
            return

        api_key = deepl_config.get("api_key", "")
        if not api_key:
            messagebox.showwarning("Clé API manquante",
                                 "Clé API DeepL non configurée. Veuillez la configurer dans Options > Configuration IA.")
            return

        # Démarrer le traitement
        self.batch_form.start_processing(len(selected_paths))

        # Sauvegarder le chemin de la branche pour la resélectionner après
        branch_path = self.current_entry_state.get("path", "")

        # Lancer le traitement dans un thread pour ne pas bloquer l'interface
        import threading

        def batch_process_deepl():
            """Traite toutes les feuilles une par une avec DeepL."""
            for i, leaf_path in enumerate(selected_paths):
                # Vérifier si l'utilisateur a demandé l'arrêt
                if self.batch_form.is_stopped():
                    self.root.after(0, lambda: self.batch_form.finish_processing(success=False))
                    # Mettre à jour l'arbre même après interruption
                    self.root.after(0, self._populate_tree)
                    # Resélectionner la branche après le rafraîchissement
                    if branch_path:
                        self.root.after(100, lambda: self._select_path_in_tree(branch_path))
                    return

                # Mettre à jour la progression (dans le thread principal)
                self.root.after(0, lambda curr=i, tot=len(selected_paths), p=leaf_path:
                                self.batch_form.update_progress(curr, tot, p))

                try:
                    # Récupérer l'entrée
                    entry = self.got_manager._get_entry_by_path(leaf_path)

                    # Vérifier si c'est bien une entrée traduisible
                    if not isinstance(entry, dict) or "ori" not in entry:
                        continue

                    # Vérifier si la traduction existe et est non vide, OU si elle est validée
                    skip_translation = False
                    if lang in entry:
                        lang_data = entry[lang]
                        if isinstance(lang_data, dict):
                            translation_text = lang_data.get("text", "")
                            is_validated = lang_data.get("valid", False)

                            # Sauter si : (1) texte validé (ne JAMAIS retraduire), OU (2) texte non vide
                            # IMPORTANT : Les traductions validées ne doivent JAMAIS être retraduits
                            if is_validated:
                                # Traduction validée : ne jamais retraduire
                                skip_translation = True
                            elif translation_text and translation_text.strip():
                                # Traduction non validée mais présente : passer pour l'instant
                                # (ne traduire que les champs vides)
                                skip_translation = True
                        elif isinstance(lang_data, str):
                            # Ancien format : traduction directe en string
                            if lang_data.strip():
                                skip_translation = True

                    if skip_translation:
                        continue

                    # Pas de traduction -> Traduire avec DeepL
                    original = entry.get("ori", "")
                    if not original or not original.strip():
                        continue  # Pas d'original, rien à traduire

                    # Traduire avec DeepL en utilisant l'instance globale pour le comptage
                    # Utiliser self.ai_client.providers["deepl"] si disponible, sinon créer une instance locale
                    if "deepl" in self.ai_client.providers:
                        deepl_provider = self.ai_client.providers["deepl"]
                    else:
                        # Fallback : créer une instance locale (ne comptera pas dans le total)
                        from core.ai_client import DeepLProvider
                        deepl_provider = DeepLProvider({
                            "api_key": api_key,
                            "is_pro": deepl_config.get("is_pro", False),
                            "timeout": 30
                        })

                    # Mapper le code langue pour DeepL
                    deepl_lang_map = {
                        "en": "EN-US",
                        "fr": "FR",
                        "es": "ES",
                        "de": "DE",
                        "it": "IT",
                        "pt": "PT-BR",
                        "ru": "RU",
                        "ja": "JA",
                        "zh": "ZH",
                        "ko": "KO",
                        "ar": "AR"
                    }
                    target_lang_deepl = deepl_lang_map.get(lang, lang.upper())

                    # Créer une boucle d'événements pour ce thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    # Appeler DeepL avec timeout
                    translated_text = loop.run_until_complete(
                        deepl_provider.translate(original, target_lang_deepl, "auto", 30)
                    )

                    # Fermer la boucle
                    loop.close()

                    # Mettre à jour la traduction si on a un résultat
                    if translated_text:
                        self.got_manager.update_translation(leaf_path, lang, translated_text)
                        # Marquer comme modifié (dans le thread principal)
                        self.root.after(0, self._mark_as_modified)
                    else:
                        # Erreur - on laisse vide
                        print(f"⚠️ Pas de traduction pour {leaf_path}")

                except Exception as e:
                    import traceback
                    print(f"Erreur lors de la traduction de {leaf_path}:")
                    print(f"  Type: {type(e).__name__}")
                    print(f"  Message: {e}")
                    print(f"  Traceback: {traceback.format_exc()}")
                    # Continuer avec la feuille suivante

            # Traitement terminé
            self.root.after(0, lambda: self.batch_form.finish_processing(success=True))
            self.root.after(0, self._populate_tree)
            # Resélectionner la branche après le rafraîchissement
            if branch_path:
                self.root.after(100, lambda: self._select_path_in_tree(branch_path))

        # Lancer le thread
        thread = threading.Thread(target=batch_process_deepl, daemon=True)
        thread.start()

    def _on_batch_clear_unvalidated(self, lang: str, selected_paths: list):
        """
        Efface les traductions non validées pour une langue (les met dans l'historique).

        Args:
            lang: Code langue (ex: "fr")
            selected_paths: Liste des chemins sélectionnés
        """
        if not self.got_manager:
            return

        # Confirmation
        from tkinter import messagebox
        confirmed = messagebox.askyesno(
            "Confirmation",
            f"Voulez-vous effacer toutes les traductions NON VALIDÉES en {lang.upper()} pour les {len(selected_paths)} champ(s) sélectionné(s) ?\n\n"
            f"Les traductions seront sauvegardées dans l'historique avant d'être effacées.\n"
            f"Les traductions VALIDÉES (✓) ne seront PAS affectées."
        )

        if not confirmed:
            return

        # Démarrer le traitement
        self.batch_form.start_processing(len(selected_paths))

        # Sauvegarder le chemin de la branche pour la resélectionner après
        branch_path = self.current_entry_state.get("path", "")

        # Compteurs
        cleared_count = 0
        skipped_count = 0

        # Traiter chaque feuille
        for i, leaf_path in enumerate(selected_paths):
            # Mettre à jour la progression
            self.root.after(0, lambda curr=i, tot=len(selected_paths), p=leaf_path:
                            self.batch_form.update_progress(curr, tot, p))

            try:
                # Récupérer l'entrée
                entry = self.got_manager._get_entry_by_path(leaf_path)

                # Vérifier si c'est bien une entrée traduisible
                if not isinstance(entry, dict) or "ori" not in entry:
                    continue

                # Vérifier si la langue existe dans l'entrée
                if lang not in entry:
                    continue

                lang_data = entry[lang]
                if isinstance(lang_data, dict):
                    is_validated = lang_data.get("valid", False)
                    translation_text = lang_data.get("text", "")

                    # Si validé, on ne touche pas
                    if is_validated:
                        skipped_count += 1
                        continue

                    # Si non vide, on l'efface (avec historique)
                    if translation_text and translation_text.strip():
                        # Ajouter à l'historique
                        history = lang_data.get("history", [])
                        if translation_text not in history:
                            history.append(translation_text)

                        # Mettre à jour : vider le texte mais garder l'historique
                        self.got_manager.update_translation(leaf_path, lang, "")
                        cleared_count += 1

                        # Marquer comme modifié
                        self.root.after(0, self._mark_as_modified)

            except Exception as e:
                print(f"Erreur lors de l'effacement de {leaf_path}: {e}")
                continue

        # Terminer le traitement
        self.root.after(0, lambda: self.batch_form.finish_processing(success=True))

        # Rafraîchir l'arbre
        self.root.after(0, self._populate_tree)

        # Resélectionner la branche
        if branch_path:
            self.root.after(100, lambda: self._select_tree_item(branch_path))

        # Message de résumé
        summary_msg = f"✓ Effacement terminé :\n\n"
        summary_msg += f"  • {cleared_count} traduction(s) effacée(s)\n"
        summary_msg += f"  • {skipped_count} traduction(s) validée(s) conservée(s)"

        self.root.after(0, lambda: messagebox.showinfo("Effacement terminé", summary_msg))

    def _on_batch_search_replace(self, lang: str, mode: str, search_text: str,
                                 replace_text: str, selected_paths: list):
        """
        Gère la recherche et le remplacement par lot.

        Args:
            lang: Code langue (ex: "fr")
            mode: "translation" (remplacer dans le champ langue) ou "from_ori" (pré-remplir depuis l'original)
            search_text: Texte à rechercher
            replace_text: Texte de remplacement (ignoré en mode "from_ori")
            selected_paths: Liste des chemins sélectionnés
        """
        if not self.got_manager:
            return

        if not search_text:
            return

        # Démarrer le traitement
        self.batch_form.start_processing(len(selected_paths))

        # Sauvegarder le chemin de la branche pour la resélectionner après
        branch_path = self.current_entry_state.get("path", "")

        # Compteurs
        replaced_count = 0
        prefilled_count = 0

        # Fonction pour préserver la casse du premier caractère
        def preserve_case(original_text: str, replacement: str) -> str:
            """
            Préserve la casse du premier caractère de l'original dans le remplacement.
            Ex: "Beastmaster" avec remplacement "maître des animaux" -> "Maître des animaux"
            """
            if not original_text or not replacement:
                return replacement

            if original_text[0].isupper():
                return replacement[0].upper() + replacement[1:] if len(replacement) > 1 else replacement.upper()
            else:
                return replacement[0].lower() + replacement[1:] if len(replacement) > 1 else replacement.lower()

        # Traiter chaque feuille
        for i, leaf_path in enumerate(selected_paths):
            # Vérifier si l'utilisateur a demandé l'arrêt
            if self.batch_form.is_stopped():
                self.root.after(0, lambda: self.batch_form.finish_processing(success=False))
                return

            # Mettre à jour la progression
            self.root.after(0, lambda curr=i, tot=len(selected_paths), p=leaf_path:
                            self.batch_form.update_progress(curr, tot, p))

            try:
                # Récupérer l'entrée
                entry = self.got_manager._get_entry_by_path(leaf_path)

                # Vérifier si c'est bien une entrée traduisible
                if not isinstance(entry, dict) or "ori" not in entry:
                    continue

                if mode == "translation":
                    # Mode 1: Remplacer dans le champ de traduction
                    if lang not in entry:
                        continue

                    lang_data = entry[lang]
                    current_text = ""

                    if isinstance(lang_data, dict):
                        current_text = lang_data.get("text", "")
                    elif isinstance(lang_data, str):
                        current_text = lang_data

                    # Vérifier si le texte de recherche est présent
                    if search_text in current_text:
                        # Compter les occurrences pour le remplacement avec casse
                        occurrences = current_text.count(search_text)

                        # Remplacer avec préservation de la casse du premier caractère
                        new_text = current_text
                        for _ in range(occurrences):
                            # Trouver la position de l'occurrence
                            idx = new_text.find(search_text)
                            if idx != -1:
                                # Extraire le texte original à remplacer
                                original_fragment = new_text[idx:idx+len(search_text)]

                                # Appliquer le remplacement avec préservation de la casse
                                case_preserved_replacement = preserve_case(original_fragment, replace_text)

                                # Remplacer cette occurrence
                                new_text = new_text[:idx] + case_preserved_replacement + new_text[idx+len(search_text):]

                        # Mettre à jour la traduction
                        self.got_manager.update_translation(leaf_path, lang, new_text)
                        replaced_count += 1

                        # Marquer comme modifié
                        self.root.after(0, self._mark_as_modified)

                elif mode == "from_ori":
                    # Mode 2: Pré-remplir depuis l'original si correspondance exacte
                    ori_text = entry.get("ori", "")

                    # Vérifier si l'original correspond exactement au texte de recherche
                    if ori_text == search_text:
                        # Vérifier si le champ de traduction est vide
                        is_empty = False

                        if lang not in entry:
                            is_empty = True
                        else:
                            lang_data = entry[lang]
                            if isinstance(lang_data, dict):
                                translation_text = lang_data.get("text", "")
                                is_empty = not translation_text or not translation_text.strip()
                            elif isinstance(lang_data, str):
                                is_empty = not lang_data or not lang_data.strip()
                            else:
                                is_empty = True

                        # Si vide, pré-remplir avec le texte de remplacement
                        if is_empty:
                            self.got_manager.update_translation(leaf_path, lang, replace_text)
                            prefilled_count += 1

                            # Marquer comme modifié
                            self.root.after(0, self._mark_as_modified)

            except Exception as e:
                print(f"Erreur lors du traitement de {leaf_path}: {e}")
                continue

        # Terminer le traitement
        self.root.after(0, lambda: self.batch_form.finish_processing(success=True))

        # Rafraîchir l'arbre
        self.root.after(0, self._populate_tree)

        # Resélectionner la branche
        if branch_path:
            self.root.after(100, lambda: self._select_tree_item(branch_path))

        # Message de résumé
        if mode == "translation":
            summary_msg = f"✓ Remplacement terminé :\n\n"
            summary_msg += f"  • {replaced_count} champ(s) modifié(s)\n"
            summary_msg += f"  • Recherche : \"{search_text}\"\n"
            summary_msg += f"  • Remplacement : \"{replace_text}\""
        else:  # from_ori
            summary_msg = f"✓ Pré-remplissage terminé :\n\n"
            summary_msg += f"  • {prefilled_count} champ(s) pré-rempli(s)\n"
            summary_msg += f"  • Original : \"{search_text}\"\n"
            summary_msg += f"  • Traduction : \"{replace_text}\""

        from tkinter import messagebox
        self.root.after(0, lambda: messagebox.showinfo("Recherche & Remplacement", summary_msg))

    def _on_batch_translate(self, lang: str, selected_paths: list):
        """
        Gère la traduction par lot d'un sous-arbre.

        Args:
            lang: Code langue cible
            selected_paths: Liste des chemins sélectionnés
        """
        if not selected_paths:
            messagebox.showinfo("Aucune feuille sélectionnée",
                              "Veuillez sélectionner au moins une feuille à traduire.")
            return

        # Démarrer le traitement
        self.batch_form.start_processing(len(selected_paths))

        # Sauvegarder le chemin de la branche pour la resélectionner après
        branch_path = self.current_entry_state.get("path", "")

        # Lancer le traitement dans un thread pour ne pas bloquer l'interface
        import threading

        def batch_process():
            """Traite toutes les feuilles une par une."""
            for i, leaf_path in enumerate(selected_paths):
                # Vérifier si l'utilisateur a demandé l'arrêt
                if self.batch_form.is_stopped():
                    self.root.after(0, lambda: self.batch_form.finish_processing(success=False))
                    # Mettre à jour l'arbre même après interruption
                    self.root.after(0, self._populate_tree)
                    # Resélectionner la branche après le rafraîchissement
                    if branch_path:
                        self.root.after(100, lambda: self._select_path_in_tree(branch_path))
                    return

                # Mettre à jour la progression (dans le thread principal)
                self.root.after(0, lambda curr=i, tot=len(selected_paths), p=leaf_path:
                                self.batch_form.update_progress(curr, tot, p))

                try:
                    # Récupérer l'entrée
                    entry = self.got_manager._get_entry_by_path(leaf_path)

                    # Vérifier si c'est bien une entrée traduisible
                    if not isinstance(entry, dict) or "ori" not in entry:
                        continue

                    # Vérifier si la traduction existe et est non vide, OU si elle est validée
                    skip_translation = False
                    if lang in entry:
                        lang_data = entry[lang]
                        if isinstance(lang_data, dict):
                            translation_text = lang_data.get("text", "")
                            is_validated = lang_data.get("valid", False)

                            # Sauter si : (1) texte validé (ne JAMAIS retraduire), OU (2) texte non vide
                            # IMPORTANT : Les traductions validées ne doivent JAMAIS être retraduits
                            if is_validated:
                                # Traduction validée : ne jamais retraduire
                                skip_translation = True
                            elif translation_text and translation_text.strip():
                                # Traduction non validée mais présente : passer pour l'instant
                                # (ne traduire que les champs vides)
                                skip_translation = True
                        elif isinstance(lang_data, str):
                            # Ancien format : traduction directe en string
                            if lang_data.strip():
                                skip_translation = True

                    if skip_translation:
                        continue

                    # Pas de traduction -> Traduire
                    original = entry.get("ori", "")
                    if not original or not original.strip():
                        continue  # Pas d'original, rien à traduire

                    # Utiliser la méthode factorisée qui gère timeout et tout
                    translated_text = self._translate_text(original, lang, source_lang="auto")

                    # Mettre à jour la traduction si on a un résultat
                    if translated_text:
                        self.got_manager.update_translation(leaf_path, lang, translated_text)
                        # Marquer comme modifié (dans le thread principal)
                        self.root.after(0, self._mark_as_modified)
                    else:
                        # Timeout ou erreur - on laisse vide comme demandé
                        print(f"⚠️ Pas de traduction pour {leaf_path} (timeout ou erreur)")

                except Exception as e:
                    import traceback
                    print(f"Erreur lors de la traduction de {leaf_path}:")
                    print(f"  Type: {type(e).__name__}")
                    print(f"  Message: {e}")
                    print(f"  Traceback: {traceback.format_exc()}")
                    # Continuer avec la feuille suivante

            # Traitement terminé
            self.root.after(0, lambda: self.batch_form.finish_processing(success=True))
            self.root.after(0, self._populate_tree)
            # Resélectionner la branche après le rafraîchissement
            if branch_path:
                self.root.after(100, lambda: self._select_path_in_tree(branch_path))

        # Lancer le thread
        thread = threading.Thread(target=batch_process, daemon=True)
        thread.start()

    def _on_user_chat_message(self, message: str):
        """
        Gère les messages utilisateur dans le chat.

        Supporte les commandes console avec "/" :
        - /cd <path> : Change le chemin actuel et sélectionne dans l'arbre
        - /ia <message> : Dialogue avec l'IA (commande par défaut)
        - /set, /show, /load, etc. : Commandes internes du provider

        Si pas de "/" au début, traite comme "/ia <message>"

        Args:
            message: Message de l'utilisateur
        """
        # Détecter les commandes (commencent par "/")
        if message.startswith("/"):
            # Parser la commande
            parts = message.split(None, 1)  # Séparer au premier espace
            command = parts[0][1:].lower()  # Enlever le "/" et mettre en minuscules
            args = parts[1] if len(parts) > 1 else ""

            # Router vers le bon handler
            if command == "cd":
                self._handle_cd_command(args)
            elif command == "ia":
                # Dialogue avec l'IA
                self._handle_ia_command(args)
            else:
                # Commande interne du provider (/set, /show, /load, /clear, etc.)
                self._handle_internal_command(message)
        else:
            # Pas de "/" : traiter comme "/ia <message>"
            self._handle_ia_command(message)

    def _select_path_in_tree(self, path: str) -> bool:
        """
        Sélectionne un chemin dans l'arbre.

        Args:
            path: Chemin à sélectionner (ex: "app/title")

        Returns:
            True si la sélection a réussi, False sinon
        """
        if not path or not self.got_manager:
            return False

        # Nettoyer le chemin (enlever le "/" initial si présent)
        path = path.strip()
        if path.startswith("/"):
            path = path[1:]

        # Vérifier si le chemin existe
        try:
            entry = self.got_manager._get_entry_by_path(path)

            # Le chemin existe, trouver l'item correspondant dans l'arbre
            tree_item = self.path_to_tree_item.get(path)

            if tree_item:
                # Sélectionner l'item dans l'arbre
                self.tree.selection_set(tree_item)
                self.tree.see(tree_item)  # Scroll pour rendre visible

                # La sélection déclenchera automatiquement _on_tree_select
                # qui mettra à jour le formulaire et le contexte
                return True
            else:
                return False

        except (KeyError, ValueError):
            return False

    def _handle_cd_command(self, path: str):
        """
        Gère la commande /cd pour naviguer dans l'arbre.

        Args:
            path: Chemin de destination (ex: "app/title" ou "/app/title")
        """
        if not path:
            # Afficher le chemin actuel
            current = self.current_entry_state["path"] or "(aucun)"
            self.chat_panel.add_message("system", f"📍 Chemin actuel: {current}")
            return

        if not self.got_manager:
            self.chat_panel.add_error("Aucun fichier chargé")
            return

        # Utiliser la méthode _select_path_in_tree
        success = self._select_path_in_tree(path)

        if success:
            self.chat_panel.add_message("system", f"✓ Navigué vers: {path}")
        else:
            self.chat_panel.add_error(f"Chemin invalide ou item non trouvé: {path}")

    def _handle_ia_command(self, message: str):
        """
        Gère le dialogue avec l'IA (/ia ou message direct).

        Args:
            message: Message pour l'IA
        """
        if not message.strip():
            self.chat_panel.add_error("Message vide pour l'IA")
            return

        # Afficher un message de traitement
        self.chat_panel.add_message("system", "💭 Réflexion en cours...")
        self.status_label.config(text="💬 Dialogue avec l'IA...")
        self.root.update()

        def run_chat():
            """Fonction exécutée dans un thread séparé pour le dialogue"""
            try:
                # Créer une nouvelle boucle d'événements pour ce thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Appeler l'IA avec le message de l'utilisateur
                # Timeout plus court pour le dialogue (60 secondes)
                result = loop.run_until_complete(self.ai_client.chat(message, timeout=60))
                result = result.strip()

                # Fermer la boucle
                loop.close()

                # Afficher la réponse dans le chat (dans le thread principal)
                self.root.after(0, lambda r=result: self._on_chat_response_success(r))

            except Exception as ex:
                error_msg = str(ex)
                self.root.after(0, lambda msg=error_msg: self._on_chat_response_error(msg))

        # Lancer le thread
        thread = threading.Thread(target=run_chat, daemon=True)
        thread.start()

    def _handle_internal_command(self, command: str):
        """
        Gère les commandes internes du provider (/set, /show, /load, etc.).

        Args:
            command: Commande complète avec "/"
        """
        # Afficher un message de traitement
        self.chat_panel.add_message("system", f"🔧 Exécution: {command}")
        self.status_label.config(text=f"🔧 Commande: {command}")
        self.root.update()

        def run_command():
            """Fonction exécutée dans un thread séparé"""
            try:
                # Créer une nouvelle boucle d'événements pour ce thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Exécuter la commande interne
                result = loop.run_until_complete(self.ai_client.execute_internal_command(command))

                # Fermer la boucle
                loop.close()

                # Afficher la réponse dans le chat
                self.root.after(0, lambda r=result: self._on_command_response_success(r))

            except Exception as ex:
                error_msg = str(ex)
                self.root.after(0, lambda msg=error_msg: self._on_chat_response_error(msg))

        # Lancer le thread
        thread = threading.Thread(target=run_command, daemon=True)
        thread.start()

    def _on_command_response_success(self, response: str):
        """
        Affiche la réponse d'une commande interne.

        Args:
            response: Réponse de la commande
        """
        self.chat_panel.add_message("system", response)
        self.status_label.config(text="✓ Commande exécutée")

    def _on_chat_response_success(self, response: str):
        """
        Affiche la réponse de l'IA dans le chat.

        Args:
            response: Réponse de l'IA
        """
        self.chat_panel.add_message("assistant", response)
        self.status_label.config(text="✓ Réponse reçue")

    def _on_chat_response_error(self, error_message: str):
        """
        Affiche une erreur de dialogue dans le chat.

        Args:
            error_message: Message d'erreur
        """
        self.chat_panel.add_error(f"Erreur de dialogue: {error_message}")
        self.status_label.config(text="❌ Erreur de dialogue")

        # Rafraîchir l'entrée dans le formulaire
        self.translation_form.current_entry = self.current_entry_state["entry"]

        # Mettre à jour les couleurs
        self._update_tree_colors(path)

        # Log dans le chat
        self.chat_panel.add_manual_edit(lang, new_text)

    def _update_tree_colors(self, path: str):
        """Met à jour les couleurs de l'arbre pour un chemin et ses parents."""
        item = self.path_to_tree_item.get(path)
        if not item:
            return

        # Obtenir l'état de validation
        state = self.got_manager.get_validation_state(path)

        # Mettre à jour l'icône et la couleur
        current_text = self.tree.item(item, "text")
        # Extraire le nom sans l'icône
        parts = current_text.split(" ", 1)
        name = parts[1] if len(parts) > 1 else parts[0]

        icon = self._get_icon_for_state(state)
        self.tree.item(item, text=f"{icon} {name}", tags=(state,))

        # Propager la couleur aux parents
        self._propagate_colors_to_parents(path)

    def _update_all_parent_colors(self):
        """
        Met à jour les couleurs de tous les nœuds parents lors du chargement initial.
        """
        # Obtenir tous les chemins uniques des parents
        all_paths = list(self.path_to_tree_item.keys())
        parent_paths = set()

        for path in all_paths:
            parts = path.split("/")
            # Ajouter tous les chemins parents
            for i in range(1, len(parts)):
                parent_path = "/".join(parts[:i])
                parent_paths.add(parent_path)

        # Trier par profondeur (du plus profond au plus haut) pour mettre à jour correctement
        sorted_parents = sorted(parent_paths, key=lambda p: p.count("/"), reverse=True)

        # Mettre à jour chaque parent
        for parent_path in sorted_parents:
            parent_item = self.path_to_tree_item.get(parent_path)
            if not parent_item:
                continue

            parent_state = self._calculate_parent_state(parent_path)
            if parent_state == "none":
                continue

            # Mettre à jour la couleur
            current_text = self.tree.item(parent_item, "text")
            if current_text.startswith(("📁", "📄", "✅", "🟠", "❌", "⚪")):
                parts = current_text.split(" ", 1)
                name = parts[1] if len(parts) > 1 else parts[0]
            else:
                name = current_text

            icon = "📁"
            self.tree.item(parent_item, text=f"{icon} {name}", tags=(parent_state,))

    def _propagate_colors_to_parents(self, path: str):
        """
        Propage les couleurs aux nœuds parents en fonction de l'état de leurs enfants.

        Logique:
        - Si tous les enfants sont verts → parent vert
        - Si au moins un enfant est vert ou orange → parent orange
        - Si tous les enfants sont rouges ou none → parent rouge
        - Si aucun enfant traduisible → pas de couleur
        """
        path_parts = path.split("/")

        # Parcourir tous les niveaux parents (du plus profond vers la racine)
        for i in range(len(path_parts) - 1, 0, -1):
            parent_path = "/".join(path_parts[:i])
            parent_item = self.path_to_tree_item.get(parent_path)

            if not parent_item:
                continue

            # Calculer l'état agrégé des enfants
            parent_state = self._calculate_parent_state(parent_path)

            # Si aucun enfant traduisible, ne pas changer la couleur du parent
            if parent_state == "none":
                continue

            # Mettre à jour la couleur du parent
            current_text = self.tree.item(parent_item, "text")
            # Extraire le nom sans icône éventuelle
            if current_text.startswith(("📁", "📄", "✅", "🟠", "❌", "⚪")):
                parts = current_text.split(" ", 1)
                name = parts[1] if len(parts) > 1 else parts[0]
            else:
                name = current_text

            # Garder l'icône de dossier mais changer la couleur
            icon = "📁"
            self.tree.item(parent_item, text=f"{icon} {name}", tags=(parent_state,))

    def _calculate_parent_state(self, parent_path: str) -> str:
        """
        Calcule l'état d'un parent basé sur l'état de tous ses enfants traduisibles.

        Logique (noir = "none" = neutre):
        - Toutes noires (none) → parent noir (none)
        - Toutes vertes OU noires (au moins une verte, pas de rouge) → parent vert
        - Toutes rouges OU noires (au moins une rouge, pas de verte) → parent rouge
        - Mélange de rouges ET vertes (avec ou sans noires) → parent orange

        Returns:
            "green" - Toutes les entrées non-noires sont vertes
            "orange" - Mélange de rouges et vertes
            "red" - Toutes les entrées non-noires sont rouges
            "none" - Toutes les entrées sont noires (ou pas d'enfants traduisibles)
        """
        # Récupérer tous les chemins traduisibles
        all_translatable_paths = self.got_manager.get_all_translatable_paths()

        # Filtrer pour ne garder que les enfants directs et descendants de ce parent
        children_paths = [
            p for p in all_translatable_paths
            if p.startswith(parent_path + "/") or p.startswith(parent_path + "[")
        ]

        if not children_paths:
            return "none"

        # Obtenir l'état de chaque enfant
        states = [self.got_manager.get_validation_state(p) for p in children_paths]

        # Compter les états (noir = "none" est neutre)
        green_count = states.count("green")
        orange_count = states.count("orange")  # Orange compte comme à la fois rouge et vert
        red_count = states.count("red")
        none_count = states.count("none")

        total = len(states)

        # Logique de décision
        # 1. Toutes noires → parent noir
        if none_count == total:
            return "none"

        # Compter les "vraies" entrées colorées (ignorer les noires)
        has_green = green_count > 0 or orange_count > 0
        has_red = red_count > 0 or orange_count > 0

        # 2. Il y a des rouges ET des vertes → parent orange
        if has_green and has_red:
            return "orange"

        # 3. Toutes vertes ou noires (au moins une verte) → parent vert
        if has_green and not has_red:
            return "green"

        # 4. Toutes rouges ou noires (au moins une rouge) → parent rouge
        if has_red and not has_green:
            return "red"

        # Par défaut (ne devrait pas arriver)
        return "none"

    def _get_context_for_path(self, path: str) -> str:
        """Récupère le contexte d'un chemin pour l'IA."""
        parts = path.split("/")
        return " > ".join(parts)

    def _expand_all(self):
        """Déplie tous les nœuds de l'arbre."""
        def expand_recursive(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand_recursive(child)

        for item in self.tree.get_children():
            expand_recursive(item)

    def _collapse_all(self):
        """Plie tous les nœuds de l'arbre."""
        def collapse_recursive(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                collapse_recursive(child)

        for item in self.tree.get_children():
            collapse_recursive(item)

    # === Méthodes de recherche dans l'arbre ===

    def _on_search_text_changed(self, event=None):
        """Appelée quand le texte de recherche change."""
        search_text = self.search_entry.get().strip()

        # Si moins de 3 caractères ou vide, réinitialiser
        if len(search_text) < 3:
            self._reset_search()
            return

        # Effectuer la recherche
        self._perform_search(search_text)

    def _perform_search(self, search_text: str):
        """
        Recherche toutes les occurrences dans l'arbre.

        Args:
            search_text: Texte à rechercher (insensible à la casse)
        """
        self.search_results = []
        search_lower = search_text.lower()

        # Parcourir tous les items de l'arbre
        def search_recursive(item):
            # Récupérer le texte de l'item
            item_text = self.tree.item(item, "text")

            # Rechercher dans le texte (insensible à la casse)
            if search_lower in item_text.lower():
                self.search_results.append(item)

            # Continuer récursivement
            for child in self.tree.get_children(item):
                search_recursive(child)

        # Rechercher dans tous les éléments racine
        for item in self.tree.get_children():
            search_recursive(item)

        # Mettre à jour l'UI
        if self.search_results:
            self.search_current_index = 0
            self._select_search_result(self.search_current_index)
            self._update_search_ui()
        else:
            self._reset_search()

    def _search_next(self):
        """Passe à l'occurrence suivante."""
        if not self.search_results:
            return

        self.search_current_index = (self.search_current_index + 1) % len(self.search_results)
        self._select_search_result(self.search_current_index)
        self._update_search_ui()

    def _search_previous(self):
        """Passe à l'occurrence précédente."""
        if not self.search_results:
            return

        self.search_current_index = (self.search_current_index - 1) % len(self.search_results)
        self._select_search_result(self.search_current_index)
        self._update_search_ui()

    def _select_search_result(self, index: int):
        """
        Sélectionne un résultat de recherche dans l'arbre.

        Args:
            index: Index du résultat à sélectionner
        """
        if 0 <= index < len(self.search_results):
            item = self.search_results[index]

            # Déplier tous les parents pour rendre l'item visible
            parent = self.tree.parent(item)
            while parent:
                self.tree.item(parent, open=True)
                parent = self.tree.parent(parent)

            # Sélectionner l'item et le rendre visible
            self.tree.selection_set(item)
            self.tree.see(item)

    def _update_search_ui(self):
        """Met à jour l'interface de recherche (boutons et label)."""
        if self.search_results:
            # Activer les boutons
            self.search_prev_btn.config(state="normal")
            self.search_next_btn.config(state="normal")

            # Afficher l'occurrence actuelle
            current = self.search_current_index + 1
            total = len(self.search_results)
            self.search_occurrence_label.config(text=f"{current} / {total}")
        else:
            # Désactiver les boutons
            self.search_prev_btn.config(state="disabled")
            self.search_next_btn.config(state="disabled")
            self.search_occurrence_label.config(text="")

    def _reset_search(self):
        """Réinitialise la recherche."""
        self.search_results = []
        self.search_current_index = -1
        self.search_prev_btn.config(state="disabled")
        self.search_next_btn.config(state="disabled")
        self.search_occurrence_label.config(text="")

    def save_file(self):
        """Sauvegarde le fichier .got.json."""
        if not self.got_manager or not self.current_file_path:
            messagebox.showwarning("Attention", "Aucun fichier chargé")
            return

        try:
            self.got_manager.save_to_file()
            self._mark_as_saved()
            self.status_label.config(text=f"✓ Fichier sauvegardé: {Path(self.current_file_path).name}")
            self.chat_panel.add_message("system", "Fichier sauvegardé")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder:\n{e}")
            self.status_label.config(text="❌ Erreur de sauvegarde")

    def _show_about(self):
        """Affiche la boîte de dialogue À propos."""
        messagebox.showinfo("À propos",
            "OllamaTrad\n\n"
            "Traduction intelligente de fichiers JSON\n"
            "avec support multi-langues et IA.\n\n"
            "Format: .got.json v2.0\n"
            "© 2025")

    def _update_export_menu(self):
        """Met à jour le menu Export avec les langues disponibles."""
        # Vider le menu
        self.export_menu.delete(0, "end")

        if not self.got_manager:
            # Aucun fichier chargé
            self.export_menu.add_command(label="(Aucun fichier chargé)", state="disabled")
            return

        # Ajouter une entrée pour chaque langue cible
        for lang in self.got_manager.target_languages:
            self.export_menu.add_command(
                label=f"{lang.upper()}",
                command=lambda l=lang: self._export_with_language(l)
            )

        # Séparateur
        self.export_menu.add_separator()

        # Entrée "Autre..."
        self.export_menu.add_command(
            label="Autre...",
            command=lambda: self._export_with_language(None)
        )

    def _export_with_language(self, language: Optional[str]):
        """
        Ouvre le dialogue d'export avec une langue pré-sélectionnée.

        Args:
            language: Code langue ou None pour "Autre..."
        """
        if not self.got_manager or not self.current_file_path:
            messagebox.showerror("Erreur", "Aucun fichier chargé")
            return

        # Importer le dialogue d'export
        from gui.export_dialog import ExportDialog

        # Créer et afficher le dialogue
        dialog = ExportDialog(
            parent=self.root,
            current_file_path=self.current_file_path,
            target_language=language,
            available_languages=self.got_manager.target_languages
        )

        result = dialog.show()

        if result:
            # Exécuter l'export
            self._perform_export(
                output_path=result['output_path'],
                target_language=result['language'],
                mode=result['mode']
            )

    def _perform_export(self, output_path: str, target_language: str, mode: str):
        """
        Effectue l'export vers JSON.

        Args:
            output_path: Chemin du fichier de sortie
            target_language: Langue cible
            mode: "standard" ou "validated"
        """
        try:
            # Obtenir les statistiques avant export
            stats = self.got_manager.get_export_stats(target_language, mode)

            # Confirmation avec statistiques
            mode_label = "Standard" if mode == "standard" else "Unique Validé"
            message = (
                f"Export en mode {mode_label}\n\n"
                f"Langue: {target_language.upper()}\n"
                f"Fichier: {Path(output_path).name}\n\n"
                f"Statistiques:\n"
                f"  • Total d'entrées: {stats['total_entries']}\n"
                f"  • Traductions utilisées: {stats['translated_entries']}\n"
                f"  • Originaux conservés: {stats['original_entries']}\n"
                f"  • Taux de traduction: {stats['percentage']:.1f}%\n\n"
                f"Continuer l'export ?"
            )

            response = messagebox.askyesno("Confirmer l'export", message)
            if not response:
                return

            # Effectuer l'export
            self.status_label.config(text="📤 Export en cours...")
            self.root.update()

            self.got_manager.export_to_json(output_path, target_language, mode)

            # Succès
            self.status_label.config(text=f"✓ Export réussi: {Path(output_path).name}")

            messagebox.showinfo(
                "Export réussi",
                f"Le fichier a été exporté avec succès !\n\n"
                f"Fichier: {output_path}\n"
                f"Langue: {target_language.upper()}\n"
                f"Mode: {mode_label}\n"
                f"Entrées traduites: {stats['translated_entries']}/{stats['total_entries']}"
            )

        except ValueError as e:
            messagebox.showerror("Erreur", f"Erreur de configuration:\n{str(e)}")
            self.status_label.config(text="❌ Erreur d'export")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export:\n{str(e)}")
            self.status_label.config(text="❌ Erreur d'export")

    def _update_character_count(self):
        """Met à jour l'affichage du compteur de caractères dans la barre de statut."""
        try:
            # Obtenir le compteur par provider
            counts = self.ai_client.get_character_count_by_provider()

            # Gérer DeepL séparément
            deepl_count = counts.get("deepl", 0)
            if deepl_count > 0:
                # Récupérer la limite configurée
                deepl_config = self.translation_config.get("ai_config", {}).get("deepl", {})
                limit = deepl_config.get("character_limit", 0)

                if limit > 0:
                    percentage = (deepl_count / limit) * 100
                    # Changer la couleur selon le pourcentage
                    if percentage >= 90:
                        self.deepl_count_label.config(text=f"DLP: {deepl_count:,} car. ({percentage:.0f}%)", foreground="red")
                    elif percentage >= 70:
                        self.deepl_count_label.config(text=f"DLP: {deepl_count:,} car. ({percentage:.0f}%)", foreground="orange")
                    else:
                        self.deepl_count_label.config(text=f"DLP: {deepl_count:,} car.", foreground="green")
                else:
                    self.deepl_count_label.config(text=f"DLP: {deepl_count:,} car.", foreground="blue")
            else:
                self.deepl_count_label.config(text="")

            # Filtrer pour les autres providers payants (sans DeepL)
            other_paid_providers = ["openai", "mistral", "anthropic"]
            active_counts = {name: count for name, count in counts.items()
                           if name in other_paid_providers and count > 0}

            if active_counts:
                # Formater l'affichage
                total = sum(active_counts.values())
                display_text = f"📊 {total:,} car."
                self.char_count_label.config(text=display_text)
            else:
                self.char_count_label.config(text="📊 0 car.")

        except Exception as e:
            print(f"Erreur mise à jour compteur: {e}")

        # Répéter toutes les 2 secondes
        self.root.after(2000, self._update_character_count)

    def _show_character_usage_summary(self):
        """Affiche un résumé de l'utilisation des caractères à la fermeture."""
        try:
            counts = self.ai_client.get_character_count_by_provider()
            paid_providers = ["openai", "mistral", "anthropic", "deepl"]
            active_counts = {name: count for name, count in counts.items()
                           if name in paid_providers and count > 0}

            if active_counts:
                message = "📊 Résumé de l'utilisation durant cette session:\n\n"

                for name, count in sorted(active_counts.items()):
                    message += f"  • {name.upper()}: {count:,} caractères\n"

                total = sum(active_counts.values())
                message += f"\n  Total: {total:,} caractères\n"

                # Ajouter des estimations de coût approximatives
                message += "\n💰 Estimation de coût approximative:\n"

                if "openai" in active_counts:
                    # GPT-4: ~$0.03 / 1K tokens (~4 chars/token = ~4K chars)
                    cost = (active_counts["openai"] / 4000) * 0.03
                    message += f"  • OpenAI: ~${cost:.4f}\n"

                if "anthropic" in active_counts:
                    # Claude: ~$0.015 / 1K tokens
                    cost = (active_counts["anthropic"] / 4000) * 0.015
                    message += f"  • Anthropic: ~${cost:.4f}\n"

                if "mistral" in active_counts:
                    # Mistral: ~$0.002 / 1K tokens
                    cost = (active_counts["mistral"] / 4000) * 0.002
                    message += f"  • Mistral: ~${cost:.4f}\n"

                if "deepl" in active_counts:
                    # DeepL: récupérer la limite configurée
                    chars = active_counts["deepl"]
                    deepl_config = self.translation_config.get("ai_config", {}).get("deepl", {})
                    limit = deepl_config.get("character_limit", 500000)
                    is_pro = deepl_config.get("is_pro", False)

                    if limit > 0:
                        percentage = (chars / limit) * 100
                        message += f"  • DeepL: {chars:,} / {limit:,} chars ({percentage:.1f}%)\n"
                        if chars > limit:
                            message += f"    ⚠️ Limite dépassée!\n"
                    else:
                        message += f"  • DeepL: {chars:,} chars (pas de limite configurée)\n"

                    if not is_pro:
                        message += f"    ℹ️ Compte gratuit: 500,000 chars/mois\n"

                message += "\nℹ️ Ces estimations sont approximatives."

                messagebox.showinfo("Utilisation des APIs", message)
        except Exception as e:
            print(f"Erreur affichage résumé: {e}")

    def run(self):
        """Lance l'application."""
        # Intercepter la fermeture pour afficher le résumé et vérifier les modifications
        def on_closing():
            # Vérifier si des modifications non sauvegardées existent
            if self.has_unsaved_changes and self.got_manager:
                # Vérifier l'option de sauvegarde automatique
                auto_save = self.translation_config.get("auto_save_on_exit", False)

                if auto_save:
                    # Sauvegarde automatique
                    try:
                        self.got_manager.save_to_file()
                        self.chat_panel.add_message("system", "✓ Fichier sauvegardé automatiquement")
                    except Exception as e:
                        # En cas d'erreur, demander à l'utilisateur
                        messagebox.showerror("Erreur de sauvegarde automatique",
                            f"Impossible de sauvegarder automatiquement:\n{e}\n\nLe fichier n'a pas été sauvegardé.")
                else:
                    # Demander confirmation à l'utilisateur
                    response = messagebox.askyesnocancel(
                        "Modifications non sauvegardées",
                        "Le fichier contient des modifications non sauvegardées.\n\n"
                        "Voulez-vous sauvegarder avant de quitter ?\n\n"
                        "Oui: Sauvegarder et quitter\n"
                        "Non: Quitter sans sauvegarder\n"
                        "Annuler: Revenir à l'application"
                    )

                    if response is None:  # Annuler
                        return
                    elif response:  # Oui - Sauvegarder
                        try:
                            self.got_manager.save_to_file()
                            self.chat_panel.add_message("system", "✓ Fichier sauvegardé")
                        except Exception as e:
                            messagebox.showerror("Erreur", f"Impossible de sauvegarder:\n{e}")
                            return  # Ne pas quitter si la sauvegarde a échoué
                    # Si Non, continuer sans sauvegarder

            # Afficher le résumé d'utilisation des APIs
            self._show_character_usage_summary()
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()


def main(initial_file: Optional[str] = None):
    """Point d'entrée principal pour l'interface graphique."""
    if not TKINTER_AVAILABLE:
        print("❌ tkinter n'est pas disponible sur ce système")
        print("   Installation requise pour utiliser l'interface graphique")
        return

    app = OllamaTradGUI(initial_file)
    app.run()


if __name__ == "__main__":
    import sys
    file_to_load = sys.argv[1] if len(sys.argv) > 1 else None
    main(file_to_load)
