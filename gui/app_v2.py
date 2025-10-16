# -*- coding: utf-8 -*-
"""
OllamaFic GUI v2.0 - Interface graphique modernisée avec formulaire de traduction.

Cette version intègre:
- Formulaire de traduction avec baguette magique
- Chat panel contextualisé
- Arbre JSON avec code couleur par état de validation
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

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent))

from core.got_json_manager import GotJsonManager
from core.ai_client import AIClient
from utils.file_loader import load_file_intelligently
from gui.translation_form_v2 import TranslationFormV2
from gui.chat_panel import ChatPanel
from gui.options_dialog import OptionsDialog


class OllamaFicGUIv2:
    """Interface graphique modernisée pour OllamaFic avec support .got.json v2.0"""

    def __init__(self, initial_file: Optional[str] = None):
        self.root = tk.Tk()
        self.root.title("OllamaFic v2.0 - Traduction Intelligente")
        self.root.geometry("1400x900")

        # Composants principaux
        self.got_manager: Optional[GotJsonManager] = None
        self.ai_client = AIClient()
        self.current_file_path: Optional[str] = None

        # Configuration des traductions
        self.translation_config = self._load_translation_config()

        # Mapping des items de l'arbre vers les chemins
        self.tree_item_to_path: Dict[str, str] = {}
        self.path_to_tree_item: Dict[str, str] = {}

        # État de l'entrée courante (approche objet propre)
        self.current_entry_state = {
            "path": None,        # Chemin de l'entrée actuelle
            "entry": None        # Données de l'entrée actuelle
        }

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
        self.chat_panel = ChatPanel(self.main_paned)
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

        # Formulaire
        self.translation_form = TranslationFormV2(
            form_frame,
            self.got_manager,
            on_magic_click=self._on_magic_click,
            on_validate=self._on_validate,
            on_rollback=self._on_rollback,
            on_manual_edit=self._on_manual_edit
        )
        self.translation_form.pack(fill="both", expand=True)

    def _create_statusbar(self):
        """Crée la barre de statut."""
        statusbar = ttk.Frame(self.root)
        statusbar.pack(side="bottom", fill="x")

        self.status_label = ttk.Label(statusbar, text="Prêt", relief="sunken", anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)

        self.file_label = ttk.Label(statusbar, text="Aucun fichier", relief="sunken", anchor="e")
        self.file_label.pack(side="right")

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

    def open_options_dialog(self):
        """Ouvre la fenêtre d'options"""
        def on_save(config):
            self.translation_config = config
            # Recharger l'affichage si un fichier est ouvert
            if self.got_manager:
                self._refresh_after_config_change()

        OptionsDialog(self.root, on_save=on_save)

    def _refresh_after_config_change(self):
        """Rafraîchit l'affichage après changement de configuration"""
        # Mettre à jour les langues cibles du manager
        self.got_manager.target_languages = self.translation_config.get("target_languages", ["fr", "en", "es"])

        # Recharger l'entrée courante si elle existe
        if self.current_entry_state["path"]:
            current_path = self.current_entry_state["path"]
            self.translation_form.load_entry(current_path)

        # Mettre à jour les couleurs de l'arbre
        self._refresh_tree_colors()

        self.status_label.config(text="✓ Configuration mise à jour")

    def open_file_dialog(self):
        """Ouvre un dialogue pour sélectionner un fichier."""
        filename = filedialog.askopenfilename(
            title="Ouvrir un fichier JSON ou .got.json",
            filetypes=[
                ("Tous fichiers JSON", "*.json;*.got.json"),
                ("Fichiers .got.json", "*.got.json"),
                ("Fichiers JSON", "*.json"),
                ("Tous les fichiers", "*.*")
            ]
        )

        if filename:
            self.load_file(filename)

    def load_file(self, filepath: str):
        """
        Charge un fichier JSON ou .got.json.

        Args:
            filepath: Chemin vers le fichier à charger
        """
        try:
            self.status_label.config(text="Chargement en cours...")
            self.root.update()

            # Utiliser le chargement intelligent
            self.got_manager, got_path = load_file_intelligently(filepath)
            self.current_file_path = got_path

            # Mettre à jour le formulaire
            self.translation_form.set_got_manager(self.got_manager)

            # Charger l'arbre
            self._populate_tree()

            # Mettre à jour la barre de statut
            filename = Path(got_path).name
            self.file_label.config(text=filename)
            self.status_label.config(text=f"✓ Fichier chargé: {filename}")

            # Afficher les stats dans le chat
            stats = self.got_manager.get_translation_stats()
            self.chat_panel.add_message("system",
                f"Fichier chargé: {stats['total_entries']} entrées traduisibles")

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

    def _add_tree_node(self, parent_item, current_path, data):
        """
        Ajoute récursivement des nœuds à l'arbre.

        Args:
            parent_item: Item parent dans l'arbre
            current_path: Chemin actuel (ex: "app/title")
            data: Données à ajouter
        """
        if isinstance(data, dict):
            for key, value in data.items():
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

            # Mettre à jour le formulaire
            self.translation_form.load_entry(path)

            # Mettre à jour le contexte du chat
            self.chat_panel.set_context(path)

    def _on_magic_click(self, lang: str, action: str):
        """
        Gère le clic sur la baguette magique.

        Args:
            lang: Code langue
            action: "translate" ou "improve"
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

        original = captured_entry["ori"]
        current_text = captured_entry[captured_lang]["text"]

        # Calculer un timeout dynamique basé sur la taille du texte
        # Formule: timeout_base + (nb_caractères / vitesse_estimation) * marge
        # Ollama local avec HTML: ~5 tokens/sec, avec ~4 chars/token = ~20 chars/sec (théorique)
        # En pratique, avec HTML complexe: beaucoup plus lent
        # Utiliser une vitesse très conservatrice de 5 chars/sec et marge x4
        text_length = len(original) + len(current_text)
        estimated_time = text_length / 5  # secondes (vitesse très conservatrice)
        captured_timeout = max(120, int(estimated_time * 4))  # minimum 120s, marge x4

        # Construire le prompt à partir de la configuration
        prompts = self.translation_config.get("prompts", {})

        if captured_action == "translate":
            # Détecter si le texte contient du HTML
            has_html = '<' in original and '>' in original

            if has_html:
                # Utiliser le prompt HTML de la config, ou fallback sur le défaut
                prompt_template = prompts.get("translate_html",
                    'Traduis le texte suivant en {lang}.\nIMPORTANT: Préserve TOUTES les balises HTML.\n\n{text}')
                prompt = prompt_template.format(text=original, lang=captured_lang)
            else:
                # Utiliser le prompt simple de la config, ou fallback
                prompt_template = prompts.get("translate",
                    'Traduis "{text}" en {lang}. Réponds uniquement avec la traduction, sans explication.')
                prompt = prompt_template.format(text=original, lang=captured_lang)
        else:  # improve
            context = self._get_context_for_path(captured_path)
            has_html = '<' in current_text and '>' in current_text

            if has_html:
                # Utiliser le prompt amélioration HTML de la config
                prompt_template = prompts.get("improve_html",
                    'Améliore cette traduction {lang}.\nIMPORTANT: Préserve TOUTES les balises HTML.\n\nOriginal: {original}\nActuel: {current}\nContexte: {context}')
                prompt = prompt_template.format(lang=captured_lang, original=original,
                                               current=current_text, context=context)
            else:
                # Utiliser le prompt amélioration simple de la config
                prompt_template = prompts.get("improve",
                    'Améliore cette traduction {lang}:\nOriginal: "{original}"\nActuel: "{current}"\nContexte: {context}')
                prompt = prompt_template.format(lang=captured_lang, original=original,
                                               current=current_text, context=context)

        # Logger le début de la traduction dans le chat avec le texte original
        if captured_action == "translate":
            self.chat_panel.add_message("system", f"{captured_lang.upper()}: Traduire → \"{original}\" (timeout: {captured_timeout}s)")
        else:
            self.chat_panel.add_message("system", f"{captured_lang.upper()}: Améliorer → \"{current_text}\" (timeout: {captured_timeout}s)")

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
                result = loop.run_until_complete(self.ai_client.chat(prompt, timeout=captured_timeout))
                result = result.strip().strip('"').strip("'")

                # Fermer la boucle
                loop.close()

                # Mettre à jour l'UI dans le thread principal
                # Utiliser les variables capturées (pas les variables de _on_magic_click qui peuvent changer!)
                self.root.after(0, lambda p=captured_path, l=captured_lang, r=result, a=captured_action:
                              self._on_translation_success(p, l, r, a))

            except Exception as ex:
                # Capturer l'erreur dans une variable locale
                error_msg = str(ex)
                # Afficher l'erreur dans le thread principal
                self.root.after(0, lambda msg=error_msg: self._on_translation_error(msg))

        # Lancer le thread
        thread = threading.Thread(target=run_translation, daemon=True)
        thread.start()

    def _on_translation_success(self, path: str, lang: str, result: str, action: str):
        """
        Callback appelé après succès de la traduction (dans le thread principal).
        """
        try:
            # Mettre à jour avec historique dans got_manager
            self.got_manager.update_translation(path, lang, result)

            # Récupérer l'entrée mise à jour
            updated_entry = self.got_manager._get_entry_by_path(path)

            # Mettre à jour les couleurs de l'arbre
            self._update_tree_colors(path)

            # Log dans le chat
            validated = updated_entry[lang]["valid"]
            self.chat_panel.add_magic_action(lang, action, result, validated)

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

        # Mettre à jour current_entry_state
        self.current_entry_state["entry"] = self.got_manager._get_entry_by_path(path)

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

        Returns:
            "green" - Tous les enfants traduisibles sont validés
            "orange" - Certains enfants sont validés, d'autres non
            "red" - Aucun enfant n'est validé (ou tous non traduits)
            "none" - Pas d'enfants traduisibles
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

        # Compter les états
        green_count = states.count("green")
        orange_count = states.count("orange")
        red_count = states.count("red")
        none_count = states.count("none")

        total = len(states)

        # Logique de décision
        if none_count == total:
            # Tous les enfants sont "none" (aucune traduction) → parent aussi "none"
            return "none"
        elif green_count == total:
            # Tous verts (toutes traductions validées)
            return "green"
        elif green_count > 0 or orange_count > 0:
            # Au moins un validé partiellement ou totalement
            return "orange"
        else:
            # Aucun validé (tous rouges : traductions non validées)
            return "red"

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

    def save_file(self):
        """Sauvegarde le fichier .got.json."""
        if not self.got_manager or not self.current_file_path:
            messagebox.showwarning("Attention", "Aucun fichier chargé")
            return

        try:
            self.got_manager.save_to_file()
            self.status_label.config(text=f"✓ Fichier sauvegardé: {Path(self.current_file_path).name}")
            self.chat_panel.add_message("system", "Fichier sauvegardé")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder:\n{e}")
            self.status_label.config(text="❌ Erreur de sauvegarde")

    def _show_about(self):
        """Affiche la boîte de dialogue À propos."""
        messagebox.showinfo("À propos",
            "OllamaFic v2.0\n\n"
            "Traduction intelligente de fichiers JSON\n"
            "avec support multi-langues et IA.\n\n"
            "Format: .got.json v2.0\n"
            "© 2025")

    def run(self):
        """Lance l'application."""
        self.root.mainloop()


def main(initial_file: Optional[str] = None):
    """Point d'entrée principal pour l'interface graphique."""
    if not TKINTER_AVAILABLE:
        print("❌ tkinter n'est pas disponible sur ce système")
        print("   Installation requise pour utiliser l'interface graphique")
        return

    app = OllamaFicGUIv2(initial_file)
    app.run()


if __name__ == "__main__":
    import sys
    file_to_load = sys.argv[1] if len(sys.argv) > 1 else None
    main(file_to_load)
