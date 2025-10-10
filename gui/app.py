try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    from tkinter import simpledialog
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("⚠️  tkinter n'est pas disponible sur ce système")
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import threading
import time

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from core.json_manager import JsonManager, JsonPath
from core.ollama_client import OllamaClient
from core.metadata import MetadataManager
from core.ai_client import AIClient
from core.operation_history import OperationHistoryManager

class OllamaTradGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OllamaTrad - Interface Graphique")
        self.root.geometry("1200x800")

        # Composants principaux
        self.json_manager: Optional[JsonManager] = None
        self.ollama_client = OllamaClient()
        self.metadata_manager = MetadataManager()
        self.ai_client = AIClient()
        self.history_manager = OperationHistoryManager()
        self.current_path = ""
        self.current_session: Optional[str] = None

        # Variables tkinter
        self.status_var = tk.StringVar(value="Prêt")
        self.file_var = tk.StringVar(value="Aucun fichier chargé")
        # Utiliser la logique de sélection du modèle préféré
        #from core.ollama_client import OllamaClient
        try:
        #   ollama_client = OllamaClient()
            preferred_model = ollama_client.get_preferred_default_model()
        except:
            preferred_model = "aya"  # Fallback en cas d'erreur

        self.model_var = tk.StringVar(value=preferred_model)

        # Variables pour le chat
        self.command_history_list = []
        self.command_history_index = -1

        # Variables pour la nouvelle interface
        self.current_content = ""
        self.pending_result = ""
        self.temp_results = {}  # Stockage temporaire par chemin
        self.undo_stack = []
        self.batch_processing = False
        self.batch_stop_requested = False
        self.batch_current_item = 0

        # Suivi des modifications pour coloration avec tags
        self.path_states = {}  # Dict[path] = set of tags
        # Tags possibles: 'modif', 'svg', 'add', 'plus'

        self.setup_ui()
        self.setup_keybindings()
        self.check_ollama_connection()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Menu principal
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Ouvrir JSON", command=self.open_file)
        file_menu.add_command(label="Sauvegarder", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)

        # Menu Session
        session_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Session", menu=session_menu)
        session_menu.add_command(label="Démarrer session", command=self.start_session)
        session_menu.add_command(label="Terminer session", command=self.end_session)

        # Barre d'outils
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(toolbar, text="📁 Ouvrir", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="💾 Sauver", command=self.save_file).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Boutons historique
        ttk.Button(toolbar, text="⟲ Undo", command=self.undo_operation).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="⟳ Redo", command=self.redo_operation).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="📚 Historique", command=self.show_history).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Sélection du modèle
        ttk.Label(toolbar, text="Modèle:").pack(side=tk.LEFT, padx=2)
        self.model_combo = ttk.Combobox(toolbar, textvariable=self.model_var, width=15)
        self.model_combo.pack(side=tk.LEFT, padx=2)

        # Frame principal avec panneaux
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panel gauche - Navigation JSON
        left_frame = ttk.Frame(main_frame)
        main_frame.add(left_frame, weight=1)

        ttk.Label(left_frame, text="📂 Navigation JSON").pack(anchor=tk.W)

        # Chemin actuel
        self.path_var = tk.StringVar(value="/")
        path_frame = ttk.Frame(left_frame)
        path_frame.pack(fill=tk.X, pady=2)
        ttk.Label(path_frame, text="Chemin:").pack(side=tk.LEFT)
        ttk.Entry(path_frame, textvariable=self.path_var, state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Arborescence JSON
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.json_tree = ttk.Treeview(tree_frame, selectmode="browse")
        self.json_tree.heading("#0", text="Structure JSON")
        self.json_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configurer les couleurs de l'arbre
        self.setup_tree_colors()

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.json_tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.json_tree.configure(yscrollcommand=tree_scroll.set)

        self.json_tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.json_tree.bind("<Double-1>", self.on_tree_double_click)

        # Boutons de navigation
        nav_frame = ttk.Frame(left_frame)
        nav_frame.pack(fill=tk.X, pady=2)
        ttk.Button(nav_frame, text="🔍 Rechercher", command=self.open_search_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="📊 Stats", command=self.show_stats).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="🤖 Providers", command=self.open_provider_config).pack(side=tk.LEFT, padx=2)

        # Panel droit avec sections verticales et chat redimensionnable
        right_main_frame = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        main_frame.add(right_main_frame, weight=2)

        # Section de travail (3/5)
        work_frame = ttk.Frame(right_main_frame)
        right_main_frame.add(work_frame, weight=3)

        # Section chat (2/5)
        chat_main_frame = ttk.Frame(right_main_frame)
        right_main_frame.add(chat_main_frame, weight=2)

        # === SECTION DE TRAVAIL ===

        # PanedWindow vertical pour séparer le travail en deux zones redimensionnables
        work_paned = ttk.PanedWindow(work_frame, orient=tk.VERTICAL)
        work_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # Section supérieure (contenu + opérations) - poids plus faible pour rester compacte
        upper_work_frame = ttk.Frame(work_paned)
        work_paned.add(upper_work_frame, weight=1)

        # 1. Zone de contenu sélectionné (10 lignes)
        content_section = ttk.LabelFrame(upper_work_frame, text="📄 Contenu sélectionné")
        content_section.pack(fill=tk.X, padx=0, pady=2)

        self.content_display = scrolledtext.ScrolledText(content_section, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.content_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 2. Opérations courantes
        operations_section = ttk.LabelFrame(upper_work_frame, text="⚡ Opérations")
        operations_section.pack(fill=tk.X, padx=0, pady=2)

        # Première ligne d'opérations
        ops_row1 = ttk.Frame(operations_section)
        ops_row1.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(ops_row1, text="🌐 FR", command=lambda: self.quick_translate("fr")).pack(side=tk.LEFT, padx=2)
        ttk.Button(ops_row1, text="🌐 EN", command=lambda: self.quick_translate("en")).pack(side=tk.LEFT, padx=2)
        ttk.Button(ops_row1, text="🌐 ES", command=lambda: self.quick_translate("es")).pack(side=tk.LEFT, padx=2)
        ttk.Button(ops_row1, text="✨ Améliorer", command=lambda: self.quick_process("Améliore ce texte")).pack(side=tk.LEFT, padx=2)
        ttk.Button(ops_row1, text="🔍 Résumer", command=lambda: self.quick_process("Résume ce texte")).pack(side=tk.LEFT, padx=2)

        # Deuxième ligne avec instruction personnalisée
        ops_row2 = ttk.Frame(operations_section)
        ops_row2.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(ops_row2, text="Instruction:").pack(side=tk.LEFT)
        self.custom_instruction = tk.StringVar()
        instruction_entry = ttk.Entry(ops_row2, textvariable=self.custom_instruction, width=30)
        instruction_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        instruction_entry.bind("<Return>", self.execute_custom_instruction)
        ttk.Button(ops_row2, text="▶️ Exécuter", command=self.execute_custom_instruction).pack(side=tk.LEFT, padx=2)

        # Troisième ligne pour traitement en lot
        ops_row3 = ttk.Frame(operations_section)
        ops_row3.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(ops_row3, text="Lot:").pack(side=tk.LEFT)
        self.batch_pattern = tk.StringVar()
        batch_entry = ttk.Entry(ops_row3, textvariable=self.batch_pattern, width=20)
        batch_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(ops_row3, text="🔄 Traiter lot", command=self.start_batch_processing).pack(side=tk.LEFT, padx=2)
        self.batch_stop_button = ttk.Button(ops_row3, text="⏸️ Arrêter", command=self.stop_batch_processing, state=tk.DISABLED)
        self.batch_stop_button.pack(side=tk.LEFT, padx=2)

        # Indicateur de progression
        self.progress_var = tk.StringVar(value="")
        self.progress_label = ttk.Label(ops_row3, textvariable=self.progress_var, font=("Arial", 8))
        self.progress_label.pack(side=tk.LEFT, padx=5)

        # 3. Zone de résultat (section inférieure redimensionnable)
        result_section = ttk.LabelFrame(work_paned, text="✨ Résultat")
        work_paned.add(result_section, weight=2)  # Poids plus élevé pour l'expansion

        # Indicateur de sauvegarde
        result_header = ttk.Frame(result_section)
        result_header.pack(fill=tk.X, padx=5, pady=2)

        self.save_indicator = tk.StringVar(value="")
        ttk.Label(result_header, textvariable=self.save_indicator, font=("Arial", 8), foreground="red").pack(side=tk.LEFT)

        self.result_display = scrolledtext.ScrolledText(result_section, wrap=tk.WORD, height=8)
        self.result_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # Boutons d'action sur le résultat
        result_actions = ttk.Frame(result_section)
        result_actions.pack(fill=tk.X, padx=5, pady=2)

        ttk.Button(result_actions, text="✅ Appliquer", command=self.apply_result).pack(side=tk.LEFT, padx=2)
        ttk.Button(result_actions, text="↩️ Annuler", command=self.undo_last_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(result_actions, text="🗑️ Effacer", command=self.clear_result).pack(side=tk.LEFT, padx=2)
        ttk.Button(result_actions, text="💾 Sauver temp", command=self.save_temp_result).pack(side=tk.LEFT, padx=2)

        # === SECTION CHAT ===

        ttk.Label(chat_main_frame, text="💬 Chat & Historique").pack(anchor=tk.W, padx=5)

        # Zone d'historique du chat
        self.chat_history = scrolledtext.ScrolledText(chat_main_frame, wrap=tk.WORD, state=tk.DISABLED)
        self.chat_history.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

        # Configuration des couleurs pour le chat
        self.chat_history.configure(bg="#f8f9fa", fg="#212529")
        self.chat_history.tag_config("user", foreground="#0066cc", font=("Consolas", 10, "bold"))
        self.chat_history.tag_config("system", foreground="#28a745", font=("Consolas", 9))
        self.chat_history.tag_config("error", foreground="#dc3545", font=("Consolas", 9))
        self.chat_history.tag_config("batch", foreground="#6f42c1", font=("Consolas", 9, "italic"))

        # Zone de saisie des commandes
        command_input_frame = ttk.Frame(chat_main_frame)
        command_input_frame.pack(fill=tk.X, padx=5, pady=2)

        # Label avec répertoire courant
        self.command_label_var = tk.StringVar(value="Commande:")
        ttk.Label(command_input_frame, textvariable=self.command_label_var).pack(anchor=tk.W)

        entry_frame = ttk.Frame(command_input_frame)
        entry_frame.pack(fill=tk.X, pady=2)

        self.command_var = tk.StringVar()
        self.command_entry = ttk.Entry(entry_frame, textvariable=self.command_var, font=("Consolas", 10))
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        self.command_entry.bind("<Return>", self.execute_chat_command)
        self.command_entry.bind("<Up>", self.command_history_up)
        self.command_entry.bind("<Down>", self.command_history_down)

        ttk.Button(entry_frame, text="📤", command=self.execute_chat_command).pack(side=tk.RIGHT)

        # Raccourcis rapides
        shortcuts_frame = ttk.Frame(command_input_frame)
        shortcuts_frame.pack(fill=tk.X, pady=2)

        shortcuts = [("ls", "ls /"), ("search", "search "), ("stats", "stats")]
        for label, cmd in shortcuts:
            ttk.Button(shortcuts_frame, text=label, width=6,
                      command=lambda c=cmd: self.insert_command_template(c)).pack(side=tk.LEFT, padx=1)

        # Métadonnées compactes
        meta_compact = ttk.LabelFrame(chat_main_frame, text="🏷️ Métadonnées")
        meta_compact.pack(fill=tk.X, padx=5, pady=2)

        # Tags en une ligne
        tags_frame = ttk.Frame(meta_compact)
        tags_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(tags_frame, text="Tags:").pack(side=tk.LEFT)
        self.tags_var = tk.StringVar()
        self.tags_entry = ttk.Entry(tags_frame, textvariable=self.tags_var, width=15)
        self.tags_entry.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        ttk.Button(tags_frame, text="➕", command=self.add_tag).pack(side=tk.RIGHT)

        # Liste des tags
        self.tags_list = tk.Listbox(meta_compact, height=2)
        self.tags_list.pack(fill=tk.X, padx=5, pady=2)
        self.tags_list.bind("<Double-1>", self.remove_tag)

        # Contexte compact
        ttk.Label(meta_compact, text="Contexte:").pack(anchor=tk.W, padx=5)
        self.context_text = scrolledtext.ScrolledText(meta_compact, wrap=tk.WORD, height=3)
        self.context_text.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(meta_compact, text="💾 Sauver", command=self.save_context).pack(anchor=tk.E, padx=5, pady=2)

        # Barre de statut
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Label(status_frame, textvariable=self.file_var).pack(side=tk.LEFT)
        ttk.Separator(status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)

    def setup_keybindings(self):
        """Configure les raccourcis clavier"""
        self.root.bind('<Control-z>', lambda e: self.undo_last_action())
        self.root.bind('<Control-Z>', lambda e: self.undo_last_action())  # Maj+Ctrl+Z pour Windows
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Escape>', lambda e: self.stop_batch_processing())

    def check_ollama_connection(self):
        """Vérifie la connexion avec Ollama et charge les modèles"""
        def check():
            # Effectuer toutes les vérifications sans modifier l'interface
            try:
                # 1. Vérifier si Ollama est en cours d'exécution
                if not self.ollama_client.is_ollama_running():
                    self.root.after(0, lambda: self.status_var.set("🚀 Démarrage d'Ollama..."))
                    self.root.after(0, lambda: self.add_chat_message("🔄 Ollama n'est pas en cours d'exécution, tentative de démarrage...", "system"))

                    if self.ollama_client.start_ollama_service():
                        self.root.after(0, lambda: self.add_chat_message("✅ Ollama démarré avec succès!", "system"))
                    else:
                        self.root.after(0, lambda: self.status_var.set("❌ Impossible de démarrer Ollama"))
                        self.root.after(0, lambda: self.add_chat_message("❌ Impossible de démarrer Ollama automatiquement", "error"))
                        self.root.after(0, lambda: self.add_chat_message("💡 Veuillez lancer manuellement: ollama serve", "system"))
                        self.root.after(0, lambda: setattr(self.model_combo, 'values', [f"{self.model_var.get()} (Ollama non connecté)"]))
                        return

                # 2. Vérifier/télécharger le modèle préféré
                preferred_model = self.model_var.get()
                self.root.after(0, lambda: self.status_var.set(f"🔄 Vérification du modèle {preferred_model}..."))
                if not self.ollama_client.ensure_model_available(preferred_model):
                    self.root.after(0, lambda: self.add_chat_message(f"⚠️ {preferred_model} n'est pas disponible, utilisation du premier modèle trouvé", "system"))

                # 3. Charger la liste des modèles
                models = self.ollama_client.get_recommended_models()
                available_models = [m for m in models if "(non installé)" not in m]

                self.root.after(0, lambda: setattr(self.model_combo, 'values', models))

                # Définir le modèle par défaut
                if available_models:
                    # Préférer aya s'il est disponible
                    found_preferred = None
                    current_preferred = self.model_var.get()

                    # D'abord chercher aya
                    for model in available_models:
                        if "aya" in model.lower():
                            found_preferred = model
                            break

                    # Sinon, chercher le modèle actuellement configuré
                    if not found_preferred:
                        for model in available_models:
                            if current_preferred in model:
                                found_preferred = model
                                break

                    if found_preferred:
                        self.root.after(0, lambda: self.model_var.set(found_preferred))
                    elif self.model_var.get() not in available_models:
                        self.root.after(0, lambda: self.model_var.set(available_models[0]))

                    self.root.after(0, lambda: self.status_var.set(f"✅ Ollama connecté - {len(available_models)} modèle(s)"))
                    self.root.after(0, lambda: self.add_chat_message(f"✅ Ollama connecté avec {len(available_models)} modèle(s) disponible(s)", "system"))

                    if preferred_model:
                        self.root.after(0, lambda: self.add_chat_message(f"🎯 Modèle par défaut: {preferred_model}", "system"))

                else:
                    self.root.after(0, lambda: self.status_var.set("⚠️ Aucun modèle disponible"))
                    self.root.after(0, lambda: self.add_chat_message("⚠️ Aucun modèle disponible. Téléchargez un modèle avec: ollama pull aya", "system"))

            except Exception as e:
                error_msg = f"❌ Erreur lors de la connexion: {e}"
                self.root.after(0, lambda: self.status_var.set("❌ Erreur de connexion Ollama"))
                self.root.after(0, lambda: self.add_chat_message(error_msg, "error"))
                self.root.after(0, lambda: setattr(self.model_combo, 'values', [f"{self.model_var.get()} (erreur de connexion)"]))

        # Démarrer la vérification initiale dans l'interface
        self.root.after(0, lambda: self.status_var.set("🔄 Vérification d'Ollama..."))
        threading.Thread(target=check, daemon=True).start()

    def open_file(self):
        """Ouvre un fichier JSON"""
        file_path = filedialog.askopenfilename(
            title="Ouvrir un fichier JSON",
            filetypes=[("JSON files", "*.json"), ("JSON5 files", "*.json5"), ("All files", "*.*")]
        )

        if file_path:
            try:
                self.json_manager = JsonManager(file_path)

                # Configurer le hook d'historique
                def operation_hook(operation_type: str, affected_data: dict, user_input: dict = None, result: any = None):
                    self.history_manager.record_operation(
                        operation_type=operation_type,
                        user_input=user_input or {},
                        affected_data=affected_data,
                        result=result,
                        provider_info=self.ai_client.get_current_provider_info()
                    )

                self.json_manager.set_operation_hook(operation_hook)
                self.file_var.set(f"📁 {Path(file_path).name}")
                self.populate_tree()
                self.load_metadata()
                self.update_command_label()  # Mettre à jour l'affichage du répertoire courant
                self.status_var.set("✅ Fichier chargé")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger le fichier:\n{e}")

    def populate_tree(self):
        """Remplit l'arborescence JSON"""
        if not self.json_manager:
            return

        # Vider l'arbre
        for item in self.json_tree.get_children():
            self.json_tree.delete(item)

        def add_node(parent, path, name, value):
            node_id = self.json_tree.insert(parent, tk.END, text=name, values=(path,))

            # Appliquer les couleurs selon l'état de modification
            self.apply_node_colors(node_id, path)

            if isinstance(value, dict):
                for key, subvalue in value.items():
                    sub_path = f"{path}/{key}" if path else key
                    add_node(node_id, sub_path, key, subvalue)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    sub_path = f"{path}/{i}" if path else str(i)
                    add_node(node_id, sub_path, f"[{i}]", item)

        # Ajouter les nœuds racine
        if isinstance(self.json_manager.data, dict):
            for key, value in self.json_manager.data.items():
                add_node("", key, key, value)
        elif isinstance(self.json_manager.data, list):
            for i, item in enumerate(self.json_manager.data):
                add_node("", str(i), f"[{i}]", item)

    def apply_node_colors(self, node_id, path):
        """Applique les couleurs aux nœuds selon leur état de modification"""
        if not self.json_manager:
            return

        # Obtenir l'état de modification
        mod_state = self.json_manager.get_modification_state(path)

        if mod_state == "MOD":
            # Rouge pour les modifications non sauvegardées
            self.json_tree.set(node_id, '#0', self.json_tree.item(node_id, 'text'))
            self.json_tree.item(node_id, tags=('modified',))
        elif mod_state == "SAVED":
            # Vert pour les modifications sauvegardées
            self.json_tree.set(node_id, '#0', self.json_tree.item(node_id, 'text'))
            self.json_tree.item(node_id, tags=('saved',))
        else:
            # Couleur normale
            self.json_tree.item(node_id, tags=('normal',))

    def setup_tree_colors(self):
        """Configure les couleurs pour les différents états dans l'arbre"""
        # Configuration des tags de couleur
        self.json_tree.tag_configure('modified', foreground='red', background='#ffeeee')
        self.json_tree.tag_configure('saved', foreground='green', background='#eeffee')
        self.json_tree.tag_configure('normal', foreground='black', background='white')

    def on_tree_select(self, event):
        """Gère la sélection dans l'arbre"""
        selection = self.json_tree.selection()
        if selection:
            item = selection[0]
            values = self.json_tree.item(item, "values")
            if values:
                path = values[0]
                self.current_path = path
                self.path_var.set(f"/{path}")
                # Synchroniser avec JsonManager
                if self.json_manager:
                    self.json_manager.current_path = path
                    self.update_command_label()
                self.display_content(path)

    def on_tree_double_click(self, event):
        """Gère le double-clic sur l'arbre"""
        pass

    def display_content(self, path):
        """Affiche le contenu d'un chemin dans la nouvelle interface"""
        if not self.json_manager:
            return

        try:
            value = self.json_manager.get_value(path)
            self.content_display.configure(state=tk.NORMAL)
            self.content_display.delete(1.0, tk.END)

            if isinstance(value, (dict, list)):
                content = json.dumps(value, indent=2, ensure_ascii=False)
            else:
                content = str(value)

            self.content_display.insert(1.0, content)
            self.current_content = content

            # Restaurer le résultat temporaire si disponible
            if path in self.temp_results:
                self.result_display.delete(1.0, tk.END)
                self.result_display.insert(1.0, self.temp_results[path])
                self.save_indicator.set("⚠️ Résultat non sauvegardé")
            else:
                self.result_display.delete(1.0, tk.END)
                self.save_indicator.set("")

        except Exception as e:
            self.content_display.delete(1.0, tk.END)
            self.content_display.insert(1.0, f"Erreur: {e}")
            self.current_content = ""
        finally:
            self.content_display.configure(state=tk.DISABLED)

    def translate_to_french(self):
        """Traduit le contenu sélectionné en français"""
        self.translate_content("fr")

    def translate_to_english(self):
        """Traduit le contenu sélectionné en anglais"""
        self.translate_content("en")

    def translate_content(self, target_lang):
        """Traduit le contenu avec Ollama"""
        if not self.json_manager or not self.current_path:
            messagebox.showwarning("Attention", "Sélectionnez d'abord un élément à traduire")
            return

        def translate():
            try:
                self.status_var.set("🔄 Traduction en cours...")
                value = self.json_manager.get_value(self.current_path)

                if not isinstance(value, str):
                    messagebox.showwarning("Attention", "Seuls les champs texte peuvent être traduits")
                    return

                # Récupérer le contexte
                metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
                context = metadata.context

                result = self.ollama_client.translate_text(
                    value, "auto", target_lang, self.model_var.get(), context
                )

                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, result)
                self.status_var.set("✅ Traduction terminée")

            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la traduction:\n{e}")
                self.status_var.set("❌ Erreur de traduction")

        threading.Thread(target=translate, daemon=True).start()

    def process_content(self):
        """Traite le contenu avec une instruction personnalisée"""
        if not self.json_manager or not self.current_path:
            messagebox.showwarning("Attention", "Sélectionnez d'abord un élément à traiter")
            return

        instruction = self.instruction_text.get(1.0, tk.END).strip()
        if not instruction:
            messagebox.showwarning("Attention", "Entrez une instruction")
            return

        def process():
            try:
                self.status_var.set("🔄 Traitement en cours...")
                value = self.json_manager.get_value(self.current_path)

                if not isinstance(value, str):
                    messagebox.showwarning("Attention", "Seuls les champs texte peuvent être traités")
                    return

                metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
                context = metadata.context

                result = self.ollama_client.process_json_field(
                    value, instruction, self.model_var.get(), context
                )

                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, result)
                self.status_var.set("✅ Traitement terminé")

            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors du traitement:\n{e}")
                self.status_var.set("❌ Erreur de traitement")

        threading.Thread(target=process, daemon=True).start()

    def apply_result(self):
        """Applique le résultat au JSON"""
        if not self.json_manager or not self.current_path:
            return

        result = self.result_text.get(1.0, tk.END).strip()
        if not result:
            return

        try:
            self.json_manager.set_value(self.current_path, result)
            self.display_content(self.current_path)
            self.status_var.set("✅ Modifications appliquées")

            # Enregistrer l'opération dans la session
            if self.current_session:
                self.metadata_manager.add_operation(self.current_session, "apply", {
                    "path": self.current_path,
                    "new_value": result[:100]
                })

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'application:\n{e}")

    def clear_result(self):
        """Efface la zone de résultat"""
        self.result_display.delete(1.0, tk.END)
        self.save_indicator.set("")
        if self.current_path in self.temp_results:
            del self.temp_results[self.current_path]

    # === NOUVELLES MÉTHODES POUR LA NOUVELLE INTERFACE ===

    def quick_translate(self, target_lang: str):
        """Traduction rapide"""
        if not self.current_path:
            self.add_chat_message("❌ Sélectionnez un élément dans l'arbre", "error")
            return

        try:
            value = self.json_manager.get_value(self.current_path)
            if not isinstance(value, str):
                self.add_chat_message("❌ Sélectionnez un champ texte à traduire", "error")
                return
        except:
            self.add_chat_message("❌ Impossible d'accéder au contenu", "error")
            return

        command = f"translate /{self.current_path} {target_lang}"
        self.send_to_chat(command)
        self.translate_content_new(target_lang)

    def quick_process(self, instruction: str):
        """Traitement rapide avec instruction prédéfinie"""
        if not self.current_path:
            self.add_chat_message("❌ Sélectionnez un élément dans l'arbre", "error")
            return

        try:
            value = self.json_manager.get_value(self.current_path)
            if not isinstance(value, str):
                self.add_chat_message("❌ Sélectionnez un champ texte à traiter", "error")
                return
        except:
            self.add_chat_message("❌ Impossible d'accéder au contenu", "error")
            return

        command = f'process /{self.current_path} "{instruction}"'
        self.send_to_chat(command)
        self.process_content_with_instruction(instruction)

    def execute_custom_instruction(self, event=None):
        """Exécute une instruction personnalisée"""
        instruction = self.custom_instruction.get().strip()
        if not instruction:
            return

        if not self.current_path:
            self.add_chat_message("❌ Sélectionnez un élément dans l'arbre", "error")
            return

        command = f'process /{self.current_path} "{instruction}"'
        self.send_to_chat(command)
        self.process_content_with_instruction(instruction)

    def process_content_with_instruction(self, instruction: str):
        """Traite le contenu avec une instruction"""
        if not self.json_manager or not self.current_path:
            return

        def process():
            try:
                self.status_var.set("🔄 Traitement en cours...")
                value = self.json_manager.get_value(self.current_path)

                if not isinstance(value, str):
                    self.add_chat_message("❌ Seuls les champs texte peuvent être traités", "error")
                    return

                metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
                context = metadata.context

                result = self.ollama_client.process_json_field(
                    value, instruction, self.model_var.get(), context
                )

                self.result_display.delete(1.0, tk.END)
                self.result_display.insert(1.0, result)
                self.save_indicator.set("⚠️ Résultat non sauvegardé")
                self.status_var.set("✅ Traitement terminé")

                # Marquer comme modifié (rouge) car résultat non sauvegardé
                self.mark_path_modified(self.current_path)

                # Sauvegarder temporairement
                self.temp_results[self.current_path] = result

                # Enregistrer dans les métadonnées
                self.metadata_manager.add_processing_note(
                    self.json_manager.file_path,
                    f"Traité '{self.current_path}': {instruction[:50]}..."
                )

            except Exception as e:
                self.add_chat_message(f"❌ Erreur lors du traitement: {e}", "error")
                self.status_var.set("❌ Erreur de traitement")

        threading.Thread(target=process, daemon=True).start()

    def save_temp_result(self):
        """Sauvegarde le résultat temporaire"""
        if self.current_path:
            result = self.result_display.get(1.0, tk.END).strip()
            if result:
                self.temp_results[self.current_path] = result
                self.save_indicator.set("💾 Sauvé temporairement")
                self.add_chat_message(f"💾 Résultat sauvé temporairement pour {self.current_path}", "system")

    def apply_result(self):
        """Applique le résultat au JSON avec sauvegarde undo"""
        if not self.json_manager or not self.current_path:
            return

        result = self.result_display.get(1.0, tk.END).strip()
        if not result:
            return

        try:
            # Sauvegarder l'état actuel pour undo
            old_value = self.json_manager.get_value(self.current_path)
            self.undo_stack.append({
                'path': self.current_path,
                'old_value': old_value,
                'action': 'modify'
            })

            # Appliquer la modification
            self.json_manager.set_value(self.current_path, result)
            self.mark_path_saved(self.current_path)  # Marquer comme sauvegardé
            self.display_content(self.current_path)
            self.save_indicator.set("")
            self.status_var.set("✅ Modifications appliquées")

            # Supprimer de la sauvegarde temporaire
            if self.current_path in self.temp_results:
                del self.temp_results[self.current_path]

            # Enregistrer l'opération dans la session
            if self.current_session:
                self.metadata_manager.add_operation(self.current_session, "apply", {
                    "path": self.current_path,
                    "new_value": result[:100]
                })

            self.add_chat_message(f"✅ Résultat appliqué à {self.current_path}", "system")

        except Exception as e:
            self.add_chat_message(f"❌ Erreur lors de l'application: {e}", "error")

    def undo_last_action(self):
        """Annule la dernière action (Ctrl+Z)"""
        if not self.undo_stack:
            self.add_chat_message("❌ Aucune action à annuler", "error")
            return

        try:
            last_action = self.undo_stack.pop()

            if last_action['action'] == 'modify':
                self.json_manager.set_value(last_action['path'], last_action['old_value'])

                # Rafraîchir l'affichage si c'est le chemin actuel
                if last_action['path'] == self.current_path:
                    self.display_content(self.current_path)

                self.add_chat_message(f"↩️ Annulation: {last_action['path']}", "system")
                self.status_var.set("↩️ Action annulée")

        except Exception as e:
            self.add_chat_message(f"❌ Erreur lors de l'annulation: {e}", "error")

    def start_batch_processing(self):
        """Démarre le traitement en lot"""
        pattern = self.batch_pattern.get().strip()
        if not pattern:
            self.add_chat_message("❌ Entrez un motif pour le traitement en lot", "error")
            return

        if not self.json_manager:
            self.add_chat_message("❌ Aucun fichier chargé", "error")
            return

        # Analyser le pattern (ex: "translate fr descriptions" ou "process 'améliore' title")
        parts = pattern.split()
        if len(parts) < 2:
            self.add_chat_message("❌ Format: 'operation target [params]' ex: 'translate fr descriptions'", "error")
            return

        operation = parts[0]
        target = parts[-1]  # dernier mot = cible
        params = parts[1:-1] if len(parts) > 2 else []

        # Trouver tous les chemins correspondant au target
        matching_paths = self.find_matching_paths(target)

        if not matching_paths:
            self.add_chat_message(f"❌ Aucun chemin trouvé pour '{target}'", "error")
            return

        self.add_chat_message(f"🔄 Démarrage du traitement en lot: {len(matching_paths)} éléments", "batch")
        self.send_to_chat(f"batch {pattern}")

        # Démarrer le traitement
        self.batch_processing = True
        self.batch_stop_requested = False
        self.batch_current_item = 0
        self.batch_stop_button.configure(state=tk.NORMAL)

        def process_batch():
            for i, path in enumerate(matching_paths):
                if self.batch_stop_requested:
                    break

                self.batch_current_item = i
                self.progress_var.set(f"{i+1}/{len(matching_paths)}")

                try:
                    # Sélectionner l'élément
                    self.current_path = path
                    self.root.after(0, lambda: self.display_content(path))

                    # Appliquer l'opération
                    if operation == "translate" and params:
                        self.translate_content_new(params[0])
                    elif operation == "process" and params:
                        instruction = " ".join(params)
                        self.process_content_with_instruction(instruction)

                    # Petite pause entre les éléments
                    time.sleep(0.5)

                except Exception as e:
                    self.add_chat_message(f"❌ Erreur sur {path}: {e}", "error")

            # Fin du traitement
            self.batch_processing = False
            self.batch_stop_button.configure(state=tk.DISABLED)
            self.progress_var.set("")

            if self.batch_stop_requested:
                self.add_chat_message(f"⏸️ Traitement arrêté à l'élément {self.batch_current_item + 1}", "batch")
            else:
                self.add_chat_message("✅ Traitement en lot terminé", "batch")

        threading.Thread(target=process_batch, daemon=True).start()

    def stop_batch_processing(self):
        """Arrête le traitement en lot"""
        if self.batch_processing:
            self.batch_stop_requested = True
            self.add_chat_message("⏸️ Arrêt du traitement en lot demandé...", "batch")

    def find_matching_paths(self, target: str) -> list:
        """Trouve tous les chemins JSON contenant le target"""
        if not self.json_manager:
            return []

        matching_paths = []

        def search_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}/{key}" if path else key

                    # Vérifier si la clé correspond
                    if target.lower() in key.lower():
                        matching_paths.append(current_path)

                    search_recursive(value, current_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}/{i}" if path else str(i)
                    search_recursive(item, current_path)

        search_recursive(self.json_manager.data)
        return matching_paths

    def send_to_chat(self, command: str):
        """Envoie une commande vers le chat"""
        self.add_chat_message(f"📝 > {command}", "user")

    def parse_command_options(self, command_parts: list) -> tuple:
        """Parse les options d'une commande (celles qui commencent par -)"""
        options = []
        args = []

        for part in command_parts:
            if part.startswith('-'):
                options.append(part[1:])  # Enlever le -
            else:
                args.append(part)

        return args, options

    def parse_translate_command(self, command_parts: list) -> dict:
        """Parse spécifiquement une commande translate avec le nouveau format"""
        result = {
            'language': None,
            'path': None,
            'options': [],
            'valid': False
        }

        # Séparer les options et les arguments
        args, options = self.parse_command_options(command_parts[1:])  # Ignorer 'translate'

        # Rechercher la langue dans les options
        language_options = {
            'fr': 'fr', 'français': 'fr', 'french': 'fr',
            'en': 'en', 'anglais': 'en', 'english': 'en',
            'es': 'es', 'espagnol': 'es', 'spanish': 'es',
            'de': 'de', 'allemand': 'de', 'german': 'de',
            'it': 'it', 'italien': 'it', 'italian': 'it'
        }

        # Trouver la langue dans les options
        for opt in options:
            if opt.lower() in language_options:
                result['language'] = language_options[opt.lower()]
                break

        # Le dernier argument est le chemin (si présent)
        if args:
            result['path'] = args[-1]

        # Les autres options (add, plus)
        special_options = [opt for opt in options if opt.lower() not in language_options]
        result['options'] = special_options

        # Valider la commande
        result['valid'] = result['language'] is not None and result['path'] is not None

        return result

    def collect_text_fields_recursive(self, obj: any, base_path: str = "") -> list:
        """Collecte récursivement tous les champs texte d'un objet JSON"""
        text_fields = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{base_path}/{key}" if base_path else key

                if isinstance(value, str) and value.strip():  # Champ texte non vide
                    text_fields.append(current_path)
                elif isinstance(value, (dict, list)):  # Continuer récursivement
                    text_fields.extend(self.collect_text_fields_recursive(value, current_path))

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f"{base_path}/{i}" if base_path else str(i)

                if isinstance(item, str) and item.strip():  # Élément texte non vide
                    text_fields.append(current_path)
                elif isinstance(item, (dict, list)):  # Continuer récursivement
                    text_fields.extend(self.collect_text_fields_recursive(item, current_path))

        return text_fields

    def translate_recursive(self, path: str, target_lang: str, options: list):
        """Traduit récursivement tous les champs texte d'un objet"""
        if not self.json_manager:
            return

        try:
            # Récupérer l'objet au chemin spécifié
            obj = self.json_manager.get_value(path)

            # Si c'est déjà un string, traduction simple
            if isinstance(obj, str):
                if path == self.current_path:
                    self.translate_with_options(target_lang, options)
                else:
                    self.add_chat_message(f"🔄 Translation de {path}", "system")
                return

            # Collecter tous les champs texte récursivement
            text_fields = self.collect_text_fields_recursive(obj, path)

            if not text_fields:
                self.add_chat_message(f"❌ Aucun champ texte trouvé dans {path}", "error")
                return

            self.add_chat_message(f"🔄 Traduction récursive: {len(text_fields)} champs trouvés", "batch")

            # Démarrer le traitement en lot
            self.batch_processing = True
            self.batch_stop_requested = False
            self.batch_current_item = 0
            self.batch_stop_button.configure(state=tk.NORMAL)

            def process_recursive_translation():
                for i, field_path in enumerate(text_fields):
                    if self.batch_stop_requested:
                        break

                    self.batch_current_item = i
                    self.progress_var.set(f"{i+1}/{len(text_fields)}")

                    try:
                        # Sélectionner et traduire le champ
                        self.current_path = field_path
                        self.root.after(0, lambda: self.display_content(field_path))

                        # Faire la traduction
                        self.translate_with_options(target_lang, options)

                        # Auto-appliquer après une courte pause
                        time.sleep(1)
                        if not self.batch_stop_requested:
                            self.root.after(0, self.apply_result)

                        time.sleep(0.5)  # Pause entre les champs

                    except Exception as e:
                        self.add_chat_message(f"❌ Erreur sur {field_path}: {e}", "error")

                # Fin du traitement
                self.batch_processing = False
                self.batch_stop_button.configure(state=tk.DISABLED)
                self.progress_var.set("")

                if self.batch_stop_requested:
                    self.add_chat_message(f"⏸️ Traduction récursive arrêtée à {self.batch_current_item + 1}/{len(text_fields)}", "batch")
                else:
                    self.add_chat_message(f"✅ Traduction récursive terminée: {len(text_fields)} champs traduits", "batch")

            threading.Thread(target=process_recursive_translation, daemon=True).start()

        except Exception as e:
            self.add_chat_message(f"❌ Erreur lors de la traduction récursive: {e}", "error")

    def apply_node_colors(self, node_id: str, path: str):
        """Applique les couleurs aux nœuds selon leur état (priorité: rouge > orange > vert)"""
        if path in self.path_states:
            tags = self.path_states[path]

            # Priorité rouge : 'modif' (non sauvegardé) est prioritaire
            if 'modif' in tags:
                self.json_tree.item(node_id, tags=("red",))
            # Orange : éléments étendus après sauvegarde
            elif ('add' in tags or 'plus' in tags) and 'svg' in tags:
                self.json_tree.item(node_id, tags=("orange",))
            # Vert : modifié et sauvegardé
            elif 'svg' in tags:
                self.json_tree.item(node_id, tags=("green",))
            else:
                # Pas de couleur spéciale, vérifier si parent modifié
                if self.is_parent_of_modified(path):
                    self.json_tree.item(node_id, tags=("parent_modified",))
                else:
                    self.json_tree.item(node_id, tags=())
        elif self.is_parent_of_modified(path):
            self.json_tree.item(node_id, tags=("parent_modified",))
        else:
            self.json_tree.item(node_id, tags=())

    def is_parent_of_modified(self, path: str) -> bool:
        """Vérifie si un chemin est parent d'un élément modifié"""
        for modified_path in self.path_states.keys():
            if modified_path.startswith(path + "/") or (path == "" and "/" in modified_path):
                return True
        return False

    def add_path_tag(self, path: str, tag: str):
        """Ajoute un tag à un chemin"""
        if path not in self.path_states:
            self.path_states[path] = set()
        self.path_states[path].add(tag)
        self.update_tree_colors()

    def remove_path_tag(self, path: str, tag: str):
        """Supprime un tag d'un chemin"""
        if path in self.path_states:
            self.path_states[path].discard(tag)
            if not self.path_states[path]:  # Si plus de tags, supprimer le chemin
                del self.path_states[path]
            self.update_tree_colors()

    def mark_path_modified(self, path: str):
        """Marque un chemin comme modifié (non sauvegardé)"""
        self.add_path_tag(path, 'modif')
        self.remove_path_tag(path, 'svg')  # Enlever svg si présent

    def mark_path_saved(self, path: str):
        """Marque un chemin comme sauvegardé"""
        self.add_path_tag(path, 'svg')
        self.remove_path_tag(path, 'modif')  # Enlever modif si présent

    def mark_path_extended(self, path: str, extension_type: str):
        """Marque un chemin comme étendu (add ou plus)"""
        if extension_type in ['add', 'plus']:
            self.add_path_tag(path, extension_type)

    def update_tree_colors(self):
        """Met à jour les couleurs de tous les nœuds de l'arbre"""
        def update_node_recursive(node_id):
            # Récupérer le chemin du nœud
            values = self.json_tree.item(node_id, "values")
            if values:
                path = values[0]
                self.apply_node_colors(node_id, path)

            # Traiter les enfants
            for child in self.json_tree.get_children(node_id):
                update_node_recursive(child)

        # Mettre à jour tous les nœuds racine
        for item in self.json_tree.get_children():
            update_node_recursive(item)

    def translate_content_new(self, target_lang: str):
        """Traduit le contenu avec la nouvelle interface"""
        if not self.json_manager or not self.current_path:
            return

        def translate():
            try:
                self.status_var.set("🔄 Traduction en cours...")
                value = self.json_manager.get_value(self.current_path)

                if not isinstance(value, str):
                    self.add_chat_message("❌ Seuls les champs texte peuvent être traduits", "error")
                    return

                # Récupérer le contexte
                metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
                context = metadata.context

                result = self.ollama_client.translate_text(
                    value, "auto", target_lang, self.model_var.get(), context
                )

                self.result_display.delete(1.0, tk.END)
                self.result_display.insert(1.0, result)
                self.save_indicator.set("⚠️ Résultat non sauvegardé")
                self.status_var.set("✅ Traduction terminée")

                # Marquer comme modifié (rouge) car résultat non sauvegardé
                self.mark_path_modified(self.current_path)

                # Sauvegarder temporairement
                self.temp_results[self.current_path] = result

                # Enregistrer dans les métadonnées
                self.metadata_manager.add_processing_note(
                    self.json_manager.file_path,
                    f"Traduit '{self.current_path}' en {target_lang}"
                )

            except Exception as e:
                self.add_chat_message(f"❌ Erreur lors de la traduction: {e}", "error")
                self.status_var.set("❌ Erreur de traduction")

        threading.Thread(target=translate, daemon=True).start()

    def translate_with_options(self, target_lang: str, options: list):
        """Traduit le contenu avec des options spéciales"""
        if not self.json_manager or not self.current_path:
            return

        def translate():
            try:
                self.status_var.set("🔄 Traduction en cours...")
                value = self.json_manager.get_value(self.current_path)

                if not isinstance(value, str):
                    self.add_chat_message("❌ Seuls les champs texte peuvent être traduits", "error")
                    return

                # Récupérer le contexte
                metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
                context = metadata.context

                translated = self.ollama_client.translate_text(
                    value, "auto", target_lang, self.model_var.get(), context
                )

                # Appliquer les options
                if "plus" in options:
                    # Ajouter la traduction après l'original
                    result = f"{value}\n[{target_lang.upper()}] {translated}"
                    self.mark_path_extended(self.current_path, 'plus')
                elif "add" in options:
                    # Ajouter la traduction avant l'original
                    result = f"[{target_lang.upper()}] {translated}\n{value}"
                    self.mark_path_extended(self.current_path, 'add')
                else:
                    # Traduction standard (remplacement)
                    result = translated

                self.result_display.delete(1.0, tk.END)
                self.result_display.insert(1.0, result)
                self.save_indicator.set("⚠️ Résultat non sauvegardé")
                self.status_var.set("✅ Traduction terminée")

                # Marquer comme modifié (rouge) car résultat non sauvegardé
                self.mark_path_modified(self.current_path)

                # Sauvegarder temporairement
                self.temp_results[self.current_path] = result

                # Enregistrer dans les métadonnées
                mode = "avec ajout" if "plus" in options or "add" in options else "standard"
                self.metadata_manager.add_processing_note(
                    self.json_manager.file_path,
                    f"Traduit '{self.current_path}' en {target_lang} ({mode})"
                )

            except Exception as e:
                self.add_chat_message(f"❌ Erreur lors de la traduction: {e}", "error")
                self.status_var.set("❌ Erreur de traduction")

        threading.Thread(target=translate, daemon=True).start()

    def save_file(self):
        """Sauvegarde le fichier JSON"""
        if not self.json_manager:
            messagebox.showwarning("Attention", "Aucun fichier chargé")
            return

        try:
            self.json_manager.save_file()
            self.status_var.set("✅ Fichier sauvegardé")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde:\n{e}")

    def load_metadata(self):
        """Charge les métadonnées du fichier"""
        if not self.json_manager:
            return

        try:
            metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)

            # Charger les tags
            self.tags_list.delete(0, tk.END)
            for tag in metadata.tags:
                self.tags_list.insert(tk.END, tag)

            # Charger le contexte
            self.context_text.delete(1.0, tk.END)
            self.context_text.insert(1.0, metadata.context)

        except Exception as e:
            print(f"Erreur lors du chargement des métadonnées: {e}")

    def add_tag(self):
        """Ajoute un tag"""
        tag = self.tags_var.get().strip()
        if tag and self.json_manager:
            try:
                self.metadata_manager.add_tag(self.json_manager.file_path, tag)
                self.tags_list.insert(tk.END, tag)
                self.tags_var.set("")
                self.status_var.set(f"✅ Tag '{tag}' ajouté")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de l'ajout du tag:\n{e}")

    def remove_tag(self, event):
        """Supprime un tag (double-clic)"""
        selection = self.tags_list.curselection()
        if selection and self.json_manager:
            tag = self.tags_list.get(selection[0])
            try:
                self.metadata_manager.remove_tag(self.json_manager.file_path, tag)
                self.tags_list.delete(selection[0])
                self.status_var.set(f"✅ Tag '{tag}' supprimé")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la suppression du tag:\n{e}")

    def update_command_label(self):
        """Met à jour le label de commande avec le répertoire courant"""
        if self.json_manager:
            current_display = self.json_manager.get_current_path_display()
            self.command_label_var.set(f"Commande {current_display}:")
        else:
            self.command_label_var.set("Commande:")

    def select_tree_node(self, path):
        """Sélectionne le nœud correspondant au chemin dans l'arbre"""
        if not path:
            # Racine
            self.json_tree.selection_set("")
            return

        # Trouver le nœud correspondant au chemin
        def find_node_by_path(item, target_path):
            """Recherche récursive du nœud par chemin"""
            values = self.json_tree.item(item, "values")
            if values and values[0] == target_path:
                return item

            # Rechercher dans les enfants
            for child in self.json_tree.get_children(item):
                result = find_node_by_path(child, target_path)
                if result:
                    return result
            return None

        # Chercher dans tous les nœuds racine
        target_node = None
        for item in self.json_tree.get_children(""):
            target_node = find_node_by_path(item, path)
            if target_node:
                break

        if target_node:
            # Sélectionner et faire défiler vers le nœud
            self.json_tree.selection_set(target_node)
            self.json_tree.focus(target_node)
            self.json_tree.see(target_node)

    def save_context(self):
        """Sauvegarde le contexte"""
        if not self.json_manager:
            return

        context = self.context_text.get(1.0, tk.END).strip()
        try:
            self.metadata_manager.set_context(self.json_manager.file_path, context)
            self.status_var.set("✅ Contexte sauvegardé")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde du contexte:\n{e}")

    def start_session(self):
        """Démarre une nouvelle session"""
        if not self.json_manager:
            messagebox.showwarning("Attention", "Aucun fichier chargé")
            return

        try:
            metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
            self.current_session = self.metadata_manager.start_session(
                self.json_manager.file_path, self.model_var.get(), metadata.context
            )
            self.status_var.set(f"✅ Session démarrée: {self.current_session}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du démarrage de la session:\n{e}")

    def end_session(self):
        """Termine la session actuelle"""
        if self.current_session:
            try:
                self.metadata_manager.end_session(self.current_session)
                self.status_var.set(f"✅ Session terminée")
                self.current_session = None
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la fin de session:\n{e}")
        else:
            messagebox.showinfo("Info", "Aucune session active")

    def open_search_dialog(self):
        """Ouvre une boîte de dialogue de recherche"""
        if not self.json_manager:
            messagebox.showwarning("Attention", "Aucun fichier chargé")
            return

        search_text = simpledialog.askstring("Recherche", "Entrez le terme à rechercher:")
        if search_text:
            try:
                results = self.json_manager.search(search_text)
                if results:
                    result_text = f"Trouvé {len(results)} résultat(s):\n\n"
                    for result in results[:20]:
                        result_text += f"📍 {result['path']}: {result['match'][:50]}...\n"
                    messagebox.showinfo("Résultats", result_text)
                else:
                    messagebox.showinfo("Résultats", "Aucun résultat trouvé")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la recherche:\n{e}")

    def show_stats(self):
        """Affiche les statistiques du fichier"""
        if not self.json_manager:
            messagebox.showwarning("Attention", "Aucun fichier chargé")
            return

        try:
            stats = self.json_manager.get_stats()
            stats_text = f"""📊 Statistiques du fichier:

🗂️  Dictionnaires: {stats['dicts']}
📋 Listes: {stats['lists']}
📄 Valeurs: {stats['values']}
🔢 Total éléments: {stats['total_items']}
✏️  Modifications: {stats['modifications']}

📁 Fichier: {stats['file_path']}"""
            messagebox.showinfo("Statistiques", stats_text)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du calcul des statistiques:\n{e}")

    def add_chat_message(self, message: str, tag: str = "system"):
        """Ajoute un message à l'historique du chat"""
        try:
            if hasattr(self, 'chat_history'):
                self.chat_history.configure(state=tk.NORMAL)
                self.chat_history.insert(tk.END, f"{message}\n", tag)
                self.chat_history.configure(state=tk.DISABLED)
                self.chat_history.see(tk.END)
        except AttributeError:
            # Interface pas encore initialisée, ignorer silencieusement
            pass

    def execute_chat_command(self, event=None):
        """Exécute une commande saisie dans le chat"""
        command = self.command_var.get().strip()
        if not command:
            return

        # Ajouter à l'historique
        self.command_history_list.append(command)
        self.command_history_index = len(self.command_history_list)

        # Afficher la commande dans le chat
        self.add_chat_message(f"📝 > {command}", "user")

        # Vider le champ de saisie
        self.command_var.set("")

        # Traitement spécial pour les commandes /ia et ia
        if command.startswith('/ia ') or command.startswith('ia '):
            # Extraire le message
            if command.startswith('/ia '):
                message = command[4:].strip()
            else:
                message = command[3:].strip()

            if message:
                self.handle_ia_command(message)
                return

        # Traitement des commandes internes (/, /set, /show, etc.)
        if command.startswith('/') and not command.startswith('/ia'):
            self.handle_internal_command(command)
            return

        # Parser la commande pour détecter le nouveau format
        parts = command.split()
        if parts[0] == "translate" and len(parts) >= 2:
            translate_info = self.parse_translate_command(parts)

            if translate_info['valid']:
                path = translate_info['path'].lstrip('/')  # Enlever le / du début
                target_lang = translate_info['language']
                options = translate_info['options']

                # Traduction récursive pour tous les types d'objets
                self.translate_recursive(path, target_lang, options)
                return

        # Traitement standard via CLI
        try:
            from cli.commands import CLIInterface

            # Créer une instance CLI temporaire qui utilise nos objets GUI
            cli = CLIInterface()
            cli.json_manager = self.json_manager
            cli.ollama_client = self.ollama_client
            cli.metadata_manager = self.metadata_manager
            cli.ai_client = self.ai_client
            cli.current_session = self.current_session

            # IMPORTANT: Synchroniser le current_path avec le GUI
            if self.json_manager and hasattr(self, 'current_path'):
                cli.json_manager.current_path = self.current_path
                cli.current_path = self.current_path

            # Capturer la sortie
            import io
            import contextlib

            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                try:
                    cli.parse_and_execute(command)

                    # Récupérer les modifications potentielles
                    if cli.json_manager and cli.json_manager != self.json_manager:
                        self.json_manager = cli.json_manager
                        self.populate_tree()
                        if self.current_path:
                            self.display_content(self.current_path)

                    # Synchroniser le répertoire courant et mettre à jour l'affichage
                    if cli.json_manager and self.json_manager:
                        self.json_manager.current_path = cli.json_manager.current_path
                        # Si c'est une commande cd, synchroniser l'interface GUI
                        if command.strip().startswith('cd ') or command.strip() == 'cd':
                            new_path = self.json_manager.current_path
                            self.current_path = new_path
                            self.path_var.set(f"/{new_path}" if new_path else "/")
                            # Sélectionner le nœud correspondant dans l'arbre
                            self.select_tree_node(new_path)
                            # Afficher le contenu
                            if new_path:
                                self.display_content(new_path)
                            else:
                                self.display_content("")
                        self.update_command_label()

                    self.current_session = cli.current_session

                except Exception as e:
                    self.add_chat_message(f"❌ Erreur: {e}", "error")
                    return

            result = output.getvalue().strip()
            if result:
                self.add_chat_message(result, "system")
            else:
                self.add_chat_message("✅ Commande exécutée", "system")

            # Rafraîchir l'interface si nécessaire
            if command.startswith(("load", "ls", "cat", "translate", "validate")):
                if self.json_manager:
                    self.populate_tree()
                    self.load_metadata()

        except Exception as e:
            self.add_chat_message(f"❌ Erreur lors de l'exécution: {e}", "error")

    def handle_ia_command(self, message: str):
        """Gère les commandes de dialogue direct avec l'IA"""
        def ia_chat():
            try:
                # Vérifier la connexion
                provider_name = self.ai_client.get_current_provider_name()
                if not self.ai_client.check_connection():
                    self.add_chat_message(f"❌ Impossible de se connecter au provider {provider_name}", "error")
                    return

                self.add_chat_message(f"🤖 [{provider_name}] Traitement en cours...", "system")

                # Préparer le contexte si disponible
                system_prompt = None
                if self.json_manager:
                    metadata = self.metadata_manager.get_metadata(self.json_manager.file_path)
                    if metadata.context:
                        system_prompt = f"Contexte du fichier: {metadata.context}"

                # Envoyer le message de manière asynchrone
                import asyncio

                async def send_message():
                    return await self.ai_client.chat(message, system_prompt)

                # Créer une nouvelle boucle d'événements pour ce thread
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(send_message())
                    loop.close()
                except Exception as e:
                    response = f"Erreur lors de la communication: {e}"

                # Afficher la réponse dans l'interface principale
                self.root.after(0, lambda: self.add_chat_message(f"🤖 {response}", "system"))

                # Enregistrer dans l'historique si session active
                if self.current_session:
                    self.root.after(0, lambda: self.metadata_manager.add_operation(
                        self.current_session, "ia_chat", {
                            "provider": provider_name,
                            "message": message[:100],
                            "response": response[:100]
                        }
                    ))

            except Exception as e:
                self.root.after(0, lambda: self.add_chat_message(f"❌ Erreur lors du dialogue avec l'IA: {e}", "error"))

        # Lancer dans un thread séparé pour ne pas bloquer l'interface
        threading.Thread(target=ia_chat, daemon=True).start()

    def handle_internal_command(self, command: str):
        """Gère les commandes internes (/set, /show, /load, etc.)"""
        def execute_internal():
            try:
                # Vérifier la connexion
                provider_name = self.ai_client.get_current_provider_name()
                if not self.ai_client.check_connection():
                    self.root.after(0, lambda: self.add_chat_message(f"❌ Impossible de se connecter au provider {provider_name}", "error"))
                    return

                self.root.after(0, lambda: self.add_chat_message(f"🔧 [{provider_name}] Exécution de: {command}", "system"))

                # Exécuter la commande de manière asynchrone
                import asyncio

                async def run_command():
                    return await self.ai_client.execute_internal_command(command)

                # Créer une nouvelle boucle d'événements pour ce thread
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(run_command())
                    loop.close()
                except Exception as e:
                    response = f"❌ Erreur lors de l'exécution: {e}"

                # Afficher la réponse dans l'interface principale
                self.root.after(0, lambda: self.add_chat_message(response, "system"))

                # Enregistrer dans l'historique si session active
                if self.current_session:
                    self.root.after(0, lambda: self.metadata_manager.add_operation(
                        self.current_session, "internal_command", {
                            "provider": provider_name,
                            "command": command,
                            "response": response[:100]
                        }
                    ))

            except Exception as e:
                self.root.after(0, lambda: self.add_chat_message(f"❌ Erreur lors de l'exécution de la commande interne: {e}", "error"))

        # Lancer dans un thread séparé pour ne pas bloquer l'interface
        threading.Thread(target=execute_internal, daemon=True).start()

    def command_history_up(self, event):
        """Navigation vers le haut dans l'historique des commandes"""
        if self.command_history_list and self.command_history_index > 0:
            self.command_history_index -= 1
            self.command_var.set(self.command_history_list[self.command_history_index])

    def command_history_down(self, event):
        """Navigation vers le bas dans l'historique des commandes"""
        if self.command_history_list:
            if self.command_history_index < len(self.command_history_list) - 1:
                self.command_history_index += 1
                self.command_var.set(self.command_history_list[self.command_history_index])
            else:
                self.command_history_index = len(self.command_history_list)
                self.command_var.set("")

    def insert_command_template(self, template: str):
        """Insert un template de commande dans le champ de saisie"""
        if "{}" in template:
            # Si un élément est sélectionné, utiliser son chemin
            if self.current_path:
                command = template.format(f"/{self.current_path}")
            else:
                command = template.format("")
        else:
            command = template

        self.command_var.set(command)
        self.command_entry.focus()

    def open_provider_config(self):
        """Ouvre la fenêtre de configuration des providers IA"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuration des Providers IA")
        config_window.geometry("600x500")
        config_window.transient(self.root)
        config_window.grab_set()

        # Frame principale avec notebook
        notebook = ttk.Notebook(config_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Provider actuel
        current_frame = ttk.Frame(notebook)
        notebook.add(current_frame, text="Provider Actuel")

        current_provider = self.ai_client.get_current_provider_name()
        connection_status = "✓ Connecté" if self.ai_client.check_connection() else "✗ Déconnecté"

        ttk.Label(current_frame, text=f"Provider actuel: {current_provider}", font=("TkDefaultFont", 12, "bold")).pack(pady=10)
        status_label = ttk.Label(current_frame, text=f"Statut: {connection_status}")
        status_label.pack(pady=5)

        # Liste des providers disponibles
        providers_frame = ttk.LabelFrame(current_frame, text="Changer de provider")
        providers_frame.pack(fill=tk.X, padx=10, pady=10)

        providers = self.ai_client.get_available_providers()
        provider_var = tk.StringVar(value=current_provider)

        for provider in providers:
            ttk.Radiobutton(providers_frame, text=provider.title(), variable=provider_var, value=provider).pack(anchor=tk.W, padx=10, pady=2)

        def change_provider():
            new_provider = provider_var.get()
            if self.ai_client.set_provider(new_provider):
                messagebox.showinfo("Succès", f"Provider changé vers: {new_provider}")
                # Rafraîchir le statut
                new_status = "✓ Connecté" if self.ai_client.check_connection() else "✗ Déconnecté"
                status_label.config(text=f"Statut: {new_status}")
            else:
                messagebox.showerror("Erreur", f"Impossible de changer vers: {new_provider}")

        ttk.Button(providers_frame, text="Changer", command=change_provider).pack(pady=10)

        # Configuration Ollama
        ollama_frame = ttk.Frame(notebook)
        notebook.add(ollama_frame, text="Ollama")

        ollama_config = self.ai_client.config.get("ai_providers", {}).get("ollama", {})

        ttk.Label(ollama_frame, text="Configuration Ollama", font=("TkDefaultFont", 12, "bold")).pack(pady=10)

        # Host
        ttk.Label(ollama_frame, text="Host:").pack(anchor=tk.W, padx=10)
        ollama_host_var = tk.StringVar(value=ollama_config.get("host", "http://localhost:11434"))
        ttk.Entry(ollama_frame, textvariable=ollama_host_var, width=50).pack(padx=10, pady=2)

        # Modèle
        ttk.Label(ollama_frame, text="Modèle par défaut:").pack(anchor=tk.W, padx=10, pady=(10,0))
        ollama_model_var = tk.StringVar(value=ollama_config.get("default_model", "aya"))
        ttk.Entry(ollama_frame, textvariable=ollama_model_var, width=50).pack(padx=10, pady=2)

        def save_ollama_config():
            config = {
                "host": ollama_host_var.get(),
                "default_model": ollama_model_var.get()
            }
            self.ai_client.update_provider_config("ollama", config)
            messagebox.showinfo("Succès", "Configuration Ollama sauvegardée")

        ttk.Button(ollama_frame, text="Sauvegarder", command=save_ollama_config).pack(pady=20)

        # Configuration OpenAI
        openai_frame = ttk.Frame(notebook)
        notebook.add(openai_frame, text="OpenAI")

        openai_config = self.ai_client.config.get("ai_providers", {}).get("openai", {})

        ttk.Label(openai_frame, text="Configuration OpenAI", font=("TkDefaultFont", 12, "bold")).pack(pady=10)

        # API Key
        ttk.Label(openai_frame, text="Clé API:").pack(anchor=tk.W, padx=10)
        openai_key_var = tk.StringVar(value=openai_config.get("api_key", ""))
        key_entry = ttk.Entry(openai_frame, textvariable=openai_key_var, width=50, show="*")
        key_entry.pack(padx=10, pady=2)

        # URL API
        ttk.Label(openai_frame, text="URL API:").pack(anchor=tk.W, padx=10, pady=(10,0))
        openai_url_var = tk.StringVar(value=openai_config.get("api_url", "https://api.openai.com/v1/chat/completions"))
        ttk.Entry(openai_frame, textvariable=openai_url_var, width=50).pack(padx=10, pady=2)

        # Modèle
        ttk.Label(openai_frame, text="Modèle par défaut:").pack(anchor=tk.W, padx=10, pady=(10,0))
        openai_model_var = tk.StringVar(value=openai_config.get("default_model", "gpt-4"))
        ttk.Entry(openai_frame, textvariable=openai_model_var, width=50).pack(padx=10, pady=2)

        def save_openai_config():
            config = {
                "api_key": openai_key_var.get(),
                "api_url": openai_url_var.get(),
                "default_model": openai_model_var.get()
            }
            self.ai_client.update_provider_config("openai", config)
            messagebox.showinfo("Succès", "Configuration OpenAI sauvegardée")

        ttk.Button(openai_frame, text="Sauvegarder", command=save_openai_config).pack(pady=20)

        # Configuration Mistral
        mistral_frame = ttk.Frame(notebook)
        notebook.add(mistral_frame, text="Mistral")

        mistral_config = self.ai_client.config.get("ai_providers", {}).get("mistral", {})

        ttk.Label(mistral_frame, text="Configuration Mistral", font=("TkDefaultFont", 12, "bold")).pack(pady=10)

        # API Key
        ttk.Label(mistral_frame, text="Clé API:").pack(anchor=tk.W, padx=10)
        mistral_key_var = tk.StringVar(value=mistral_config.get("api_key", ""))
        ttk.Entry(mistral_frame, textvariable=mistral_key_var, width=50, show="*").pack(padx=10, pady=2)

        # Modèle
        ttk.Label(mistral_frame, text="Modèle par défaut:").pack(anchor=tk.W, padx=10, pady=(10,0))
        mistral_model_var = tk.StringVar(value=mistral_config.get("default_model", "mistral-large-latest"))
        ttk.Entry(mistral_frame, textvariable=mistral_model_var, width=50).pack(padx=10, pady=2)

        def save_mistral_config():
            config = {
                "api_key": mistral_key_var.get(),
                "default_model": mistral_model_var.get()
            }
            self.ai_client.update_provider_config("mistral", config)
            messagebox.showinfo("Succès", "Configuration Mistral sauvegardée")

        ttk.Button(mistral_frame, text="Sauvegarder", command=save_mistral_config).pack(pady=20)

        # Conversation
        conv_frame = ttk.Frame(notebook)
        notebook.add(conv_frame, text="Conversation")

        ttk.Label(conv_frame, text="Gestion de la conversation", font=("TkDefaultFont", 12, "bold")).pack(pady=10)

        history = self.ai_client.get_conversation_history()
        history_info = f"Messages dans l'historique: {len(history)}"
        ttk.Label(conv_frame, text=history_info).pack(pady=5)

        def clear_conversation():
            self.ai_client.clear_conversation()
            messagebox.showinfo("Succès", "Historique de conversation effacé")
            config_window.destroy()

        ttk.Button(conv_frame, text="Effacer l'historique", command=clear_conversation).pack(pady=20)

        # Afficher l'historique
        if history:
            ttk.Label(conv_frame, text="Historique récent:").pack(anchor=tk.W, padx=10, pady=(10,0))
            history_text = scrolledtext.ScrolledText(conv_frame, height=10, width=60)
            history_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

            for i, msg in enumerate(history[-10:], 1):  # Derniers 10 messages
                role_icon = "👤" if msg["role"] == "user" else "🤖"
                content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
                history_text.insert(tk.END, f"{i}. {role_icon} {content}\n\n")

            history_text.configure(state=tk.DISABLED)

    def undo_operation(self):
        """Annule la dernière opération"""
        if not self.json_manager:
            messagebox.showwarning("Attention", "Aucun fichier chargé")
            return

        try:
            undone_operations = self.history_manager.undo(1)
            if undone_operations:
                operation = undone_operations[0]
                # Appliquer les changements annulés
                for path, (after_value, before_value) in operation.affected_data.items():
                    if before_value is None:
                        # C'était une création, affichage info pour le moment
                        self.status_var.set(f"Annulation: {path} (création)")
                    else:
                        try:
                            # Temporairement désactiver le hook pour éviter la récursion
                            old_hook = self.json_manager.operation_hook
                            self.json_manager.operation_hook = None
                            self.json_manager.set_value(path, before_value)
                            self.json_manager.operation_hook = old_hook
                        except Exception as e:
                            messagebox.showerror("Erreur", f"Erreur lors de l'annulation de {path}: {e}")

                self.populate_tree()  # Rafraîchir l'affichage
                self.status_var.set(f"✅ Opération annulée: {operation.operation_type}")
            else:
                messagebox.showinfo("Information", "Aucune opération à annuler")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'annulation: {e}")

    def redo_operation(self):
        """Rétablit la dernière opération annulée"""
        if not self.json_manager:
            messagebox.showwarning("Attention", "Aucun fichier chargé")
            return

        try:
            redone_operations = self.history_manager.redo(1)
            if redone_operations:
                operation = redone_operations[0]
                # Appliquer les changements rétablis
                for path, (before_value, after_value) in operation.affected_data.items():
                    try:
                        # Temporairement désactiver le hook pour éviter la récursion
                        old_hook = self.json_manager.operation_hook
                        self.json_manager.operation_hook = None
                        self.json_manager.set_value(path, after_value)
                        self.json_manager.operation_hook = old_hook
                    except Exception as e:
                        messagebox.showerror("Erreur", f"Erreur lors du rétablissement de {path}: {e}")

                self.populate_tree()  # Rafraîchir l'affichage
                self.status_var.set(f"✅ Opération rétablie: {operation.operation_type}")
            else:
                messagebox.showinfo("Information", "Aucune opération à rétablir")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du rétablissement: {e}")

    def show_history(self):
        """Affiche l'historique des opérations dans une fenêtre"""
        history_window = tk.Toplevel(self.root)
        history_window.title("Historique des opérations")
        history_window.geometry("800x600")

        # Frame principal
        main_frame = ttk.Frame(history_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Titre
        ttk.Label(main_frame, text="📚 Historique des opérations", font=("Arial", 14, "bold")).pack(pady=(0, 10))

        # Treeview pour l'historique
        columns = ("Position", "Timestamp", "Type", "Provider", "Affectés")
        history_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)

        # Configuration des colonnes
        history_tree.heading("Position", text="Pos")
        history_tree.heading("Timestamp", text="Heure")
        history_tree.heading("Type", text="Type d'opération")
        history_tree.heading("Provider", text="Provider")
        history_tree.heading("Affectés", text="Éléments affectés")

        history_tree.column("Position", width=50)
        history_tree.column("Timestamp", width=150)
        history_tree.column("Type", width=150)
        history_tree.column("Provider", width=100)
        history_tree.column("Affectés", width=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=history_tree.yview)
        history_tree.configure(yscrollcommand=scrollbar.set)

        # Pack treeview et scrollbar
        history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Remplir avec les données
        operations = self.history_manager.get_operations_list()
        current_pos = self.history_manager.get_current_position()

        for i, operation in enumerate(operations):
            marker = "➤" if i == current_pos else ""
            values = (
                f"{marker} {i}",
                operation.timestamp[:16],
                operation.operation_type,
                operation.provider_info.get('provider_name', 'N/A'),
                f"{len(operation.affected_data)} éléments"
            )

            item_id = history_tree.insert("", tk.END, values=values)
            if i == current_pos:
                history_tree.set(item_id, "Position", f"➤ {i}")

        # Frame pour les boutons
        button_frame = ttk.Frame(history_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        def jump_to_operation():
            selection = history_tree.selection()
            if selection:
                item = history_tree.item(selection[0])
                pos_text = item['values'][0]
                try:
                    pos = int(pos_text.replace("➤", "").strip())
                    self.history_manager.jump_to_position(pos)
                    messagebox.showinfo("Succès", f"Position {pos} atteinte")
                    history_window.destroy()
                    self.populate_tree()  # Rafraîchir l'affichage
                except:
                    messagebox.showerror("Erreur", "Position invalide")

        ttk.Button(button_frame, text="Aller à cette position", command=jump_to_operation).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Fermer", command=history_window.destroy).pack(side=tk.RIGHT, padx=5)

    def run(self):
        """Lance l'application"""
        self.root.mainloop()

def main(file_path: str = None):
    """Point d'entrée pour l'interface graphique"""
    if not TKINTER_AVAILABLE:
        print("❌ Erreur: tkinter n'est pas disponible sur ce système.")
        print("💡 Solutions possibles:")
        print("   - Sur Ubuntu/Debian: sudo apt-get install python3-tkinter")
        print("   - Sur Windows: Réinstallez Python avec l'option 'tcl/tk and IDLE'")
        print("   - Ou utilisez le mode CLI: python ollamaTrad.py")
        return

    app = OllamaTradGUI()

    # Charger le fichier si spécifié
    if file_path:
        try:
            # Utiliser la logique de open_file mais directement
            app.json_manager = JsonManager(file_path)
            app.populate_tree()
            app.file_var.set(f"Fichier: {Path(file_path).name}")
            app.status_var.set("✅ Fichier chargé avec succès")
            print(f"✅ Fichier chargé: {file_path}")
        except Exception as e:
            print(f"❌ Erreur lors du chargement du fichier: {e}")

    app.run()

if __name__ == "__main__":
    main()