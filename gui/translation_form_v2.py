# -*- coding: utf-8 -*-
"""
Formulaire de traduction v2 avec champs multi-lignes pour OllamaFic.

Améliorations v2:
- Text widgets multilignes au lieu d'Entry
- Hauteur auto-ajustable basée sur le contenu
- Tracking des changements sur FocusOut au lieu de chaque frappe
- Ascenseurs verticaux si nécessaire
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, Callable, Optional
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent))

from core.got_json_manager import GotJsonManager


class TranslationFormV2(ttk.Frame):
    """
    Formulaire de traduction avec champs multilignes et baguette magique.
    """

    def __init__(self, parent, got_manager: Optional[GotJsonManager] = None,
                 on_magic_click: Optional[Callable] = None,
                 on_validate: Optional[Callable] = None,
                 on_rollback: Optional[Callable] = None,
                 on_manual_edit: Optional[Callable] = None):
        """
        Args:
            parent: Widget parent
            got_manager: Instance de GotJsonManager
            on_magic_click: Callback(lang, action, selection_data, source_lang) pour la baguette magique
            on_validate: Callback(lang, valid) pour la validation
            on_rollback: Callback(lang) pour le retour arrière
            on_manual_edit: Callback(lang, new_text) pour édition manuelle
        """
        super().__init__(parent)

        self.got_manager = got_manager
        self.visible_languages = []  # Liste des langues à afficher (filtre)
        self.on_magic_click = on_magic_click or (lambda lang, action, sel, src: None)
        self.on_validate = on_validate or (lambda lang, valid: None)
        self.on_rollback = on_rollback or (lambda lang: None)
        self.on_manual_edit = on_manual_edit or (lambda lang, text: None)

        self.current_path = None
        self.current_entry = None

        # Dictionnaires pour stocker les widgets et états
        self.text_widgets = {}  # lang -> Text widget
        self.valid_vars = {}    # lang -> BooleanVar
        self.language_rows = {} # lang -> dict de widgets
        self.last_saved_texts = {}  # lang -> dernière valeur sauvegardée
        self.history_indices = {}  # lang -> index courant dans l'historique (0 = texte actuel, 1 = premier historique, etc.)
        self.current_texts_before_undo = {}  # lang -> texte actuel avant le premier undo (pour pouvoir redo jusqu'à lui)

        # Widgets
        self.path_label = None
        self.original_text = None
        self.source_lang_combo = None
        self.source_lang_var = None

        self._create_widgets()

    def _create_widgets(self):
        """Crée la structure du formulaire."""
        # Header fixe en haut (header + langue d'origine)
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Header avec chemin
        header = ttk.Frame(header_frame)
        header.pack(fill="x", pady=(0, 5))

        ttk.Label(header, text="📍 Chemin:", font=("Arial", 9, "bold")).pack(side="left")
        self.path_label = ttk.Label(header, text="", font=("Arial", 9), foreground="blue")
        self.path_label.pack(side="left", padx=5)

        # Séparateur
        ttk.Separator(header_frame, orient="horizontal").pack(fill="x", pady=5)

        # Zone langue d'origine
        source_lang_frame = ttk.Frame(header_frame)
        source_lang_frame.pack(fill="x", pady=5)

        ttk.Label(source_lang_frame, text="Langue d'origine:",
                 font=("Arial", 9, "bold")).pack(side="left", padx=(0, 5))

        # Liste des langues disponibles
        # On utilisera les langues cibles du got_manager + "auto"
        available_languages = ["auto", "en", "fr", "es", "de", "it", "pt", "ru", "ja", "zh", "ko", "ar"]

        self.source_lang_var = tk.StringVar(value="auto")
        self.source_lang_combo = ttk.Combobox(source_lang_frame,
                                              textvariable=self.source_lang_var,
                                              values=available_languages,
                                              state="readonly",
                                              width=10)
        self.source_lang_combo.pack(side="left")
        self.source_lang_combo.set("auto")

        # Tooltip
        self._create_tooltip(self.source_lang_combo,
                           "Sélectionnez la langue du texte original\n'auto' = détection automatique")

        # Séparateur
        ttk.Separator(header_frame, orient="horizontal").pack(fill="x", pady=5)

        # PanedWindow vertical pour séparer original et traductions de manière redimensionnable
        # Utiliser tk.PanedWindow au lieu de ttk pour pouvoir styliser le sash
        self.paned_window = tk.PanedWindow(self, orient="vertical",
                                          sashwidth=8,  # Largeur du séparateur
                                          sashrelief="raised",  # Relief du séparateur
                                          bg="#d0d0d0",  # Couleur de fond du séparateur
                                          bd=0)  # Pas de bordure
        self.paned_window.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # === HAUT: Zone original (ori) ===
        ori_container = ttk.Frame(self.paned_window)
        self.paned_window.add(ori_container, minsize=50, stretch="never")

        ttk.Label(ori_container, text="Original (ori):",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=(5, 2))

        # Frame pour le texte + scrollbar
        ori_text_frame = ttk.Frame(ori_container)
        ori_text_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Scrollbar verticale
        ori_scrollbar = ttk.Scrollbar(ori_text_frame, orient="vertical")
        ori_scrollbar.pack(side="right", fill="y")

        self.original_text = tk.Text(ori_text_frame, height=5,
                                     state="disabled", wrap="word",
                                     background="#f9f9f9", relief="flat",
                                     font=("Arial", 10),
                                     yscrollcommand=ori_scrollbar.set)
        self.original_text.pack(side="left", fill="both", expand=True)
        ori_scrollbar.config(command=self.original_text.yview)

        # === BAS: Section traductions ===
        translations_container = ttk.Frame(self.paned_window)
        self.paned_window.add(translations_container, minsize=100, stretch="always")

        # Label pour les traductions
        ttk.Label(translations_container, text="Traductions:",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=(5, 2))

        # Section scrollable (traductions)
        translations_frame = ttk.Frame(translations_container)
        translations_frame.pack(fill="both", expand=True)

        # Canvas + scrollbar pour les traductions
        canvas = tk.Canvas(translations_frame, borderwidth=0, background="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(translations_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # CRUCIAL: Forcer la largeur de scrollable_frame à suivre la largeur du canvas
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Container pour les langues (dans le frame scrollable)
        # Pas de padding pour aller jusqu'aux bords
        self.languages_container = ttk.Frame(self.scrollable_frame)
        self.languages_container.pack(fill="both", expand=True)

    def set_got_manager(self, got_manager: GotJsonManager):
        """Définit le gestionnaire .got.json."""
        self.got_manager = got_manager

    def load_entry(self, path: str):
        """
        Charge une entrée traduisible dans le formulaire.

        Args:
            path: Chemin vers l'entrée (ex: "app/title")
        """
        if not self.got_manager:
            self._show_no_file_loaded()
            return

        try:
            entry = self.got_manager._get_entry_by_path(path)

            # Vérifier que c'est une entrée traduisible
            if not isinstance(entry, dict) or "ori" not in entry:
                self._show_not_translatable()
                return

            self.current_path = path
            self.current_entry = entry

            # Mettre à jour le chemin
            self.path_label.config(text=path)

            # Afficher l'original avec hauteur auto
            ori_text = entry["ori"]
            lines = max(3, min(10, ori_text.count('\n') + 1))
            self.original_text.config(state="normal", height=lines)
            self.original_text.delete("1.0", "end")
            self.original_text.insert("1.0", ori_text)
            self.original_text.config(state="disabled")

            # Nettoyer les anciennes langues
            for widget in self.languages_container.winfo_children():
                widget.destroy()

            self.text_widgets.clear()
            self.valid_vars.clear()
            self.language_rows.clear()
            self.last_saved_texts.clear()
            self.history_indices.clear()  # Réinitialiser les indices d'historique
            self.current_texts_before_undo.clear()  # Réinitialiser les textes sauvegardés

            # Créer une ligne pour chaque langue cible
            languages = self.got_manager.target_languages

            # Filtrer par les langues visibles si configurées
            if self.visible_languages:
                languages = [lang for lang in languages if lang in self.visible_languages]

            for lang in languages:
                # Si la langue n'existe pas dans l'entrée, la créer avec une structure vide
                if lang not in entry:
                    entry[lang] = {
                        "text": "",
                        "history": [],
                        "valid": False
                    }

                self._create_language_row(lang, entry[lang], ori_text)

        except KeyError as e:
            messagebox.showerror("Erreur", f"Chemin invalide: {path}\n{e}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {e}")
            import traceback
            traceback.print_exc()

    def _create_language_row(self, lang: str, lang_data: Dict, ori_text: str):
        """
        Crée une ligne complète pour une langue avec Text widget multiligne.

        Args:
            lang: Code langue (ex: "fr")
            lang_data: {"text": "...", "history": [...], "valid": bool}
            ori_text: Texte original pour calculer la hauteur
        """
        row_frame = ttk.Frame(self.languages_container)
        # Padding vertical minimal, pas de padding horizontal pour aller d'un bord à l'autre
        row_frame.pack(fill="both", expand=True, pady=3, padx=0)

        # Header avec boutons - petit padding interne pour ne pas coller au bord
        header_frame = ttk.Frame(row_frame)
        header_frame.pack(fill="x", pady=(0, 2), padx=5)

        # 🪄 Bouton magique
        magic_btn = tk.Button(header_frame, text="🪄", font=("Arial", 14),
                             width=2, relief="raised", cursor="hand2",
                             bg="#FFE4B5", activebackground="#FFD700",
                             command=lambda: self._on_magic_clicked(lang))
        magic_btn.pack(side="left", padx=(0, 5))
        self._create_tooltip(magic_btn, "Cliquer pour traduire ou améliorer")

        # Label langue
        lang_label = ttk.Label(header_frame, text=f"{lang.upper()}:",
                              font=("Arial", 9, "bold"))
        lang_label.pack(side="left", padx=(0, 5))

        # ✓ Checkbox validation
        valid_var = tk.BooleanVar(value=lang_data["valid"])
        valid_check = ttk.Checkbutton(header_frame, variable=valid_var,
                                      command=lambda: self._on_validate_toggled(lang, valid_var.get()))
        valid_check.pack(side="left", padx=(0, 5))
        self._create_tooltip(valid_check, "Marquer comme validé")

        # Initialiser l'index d'historique à 0 (texte actuel)
        self.history_indices[lang] = 0
        has_history = len(lang_data["history"]) > 0

        # ↶ Bouton undo (reculer dans l'historique)
        undo_btn = tk.Button(header_frame, text="↶", font=("Arial", 12),
                            width=2, relief="raised",
                            state="normal" if has_history else "disabled",
                            command=lambda: self._on_history_undo(lang))
        undo_btn.pack(side="left", padx=(0, 2))

        if has_history:
            tooltip_text = f"Reculer dans l'historique ({len(lang_data['history'])}):\n"
            tooltip_text += "\n".join([f"  • {h[:50]}..." if len(h) > 50 else f"  • {h}"
                                      for h in lang_data["history"][:3]])
            if len(lang_data["history"]) > 3:
                tooltip_text += f"\n  ... et {len(lang_data['history']) - 3} autres"
            self._create_tooltip(undo_btn, tooltip_text)
        else:
            self._create_tooltip(undo_btn, "Pas d'historique")

        # ↷ Bouton redo (avancer dans l'historique)
        redo_btn = tk.Button(header_frame, text="↷", font=("Arial", 12),
                            width=2, relief="raised",
                            state="disabled",  # Désactivé au départ (on est au texte actuel)
                            command=lambda: self._on_history_redo(lang))
        redo_btn.pack(side="left")
        self._create_tooltip(redo_btn, "Avancer dans l'historique")

        # Zone de texte multiligne avec scrollbar individuel
        # Pas de padding pour aller d'un bord à l'autre
        text_frame = ttk.Frame(row_frame)
        text_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Calculer hauteur basée sur le contenu de l'original
        # On veut que chaque champ soit assez grand pour afficher le texte original
        # avec une hauteur minimum de 5 lignes et maximum de 15 lignes
        current_text = lang_data["text"]
        ori_lines = ori_text.count('\n') + 1

        # Estimer les lignes avec wrapping (approximation: 80 caractères par ligne)
        chars_per_line = 80
        ori_wrapped_lines = max(ori_lines, len(ori_text) // chars_per_line + 1)
        text_wrapped_lines = max(current_text.count('\n') + 1,
                                len(current_text) // chars_per_line + 1) if current_text else 3

        # Hauteur = maximum entre original et texte actuel, avec bornes
        calculated_height = max(ori_wrapped_lines, text_wrapped_lines)
        height = max(5, min(15, calculated_height))

        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
        text_scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(text_frame, height=height,
                             wrap="word", font=("Arial", 10),
                             yscrollcommand=text_scrollbar.set,
                             borderwidth=1, relief="solid")
        text_widget.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        text_scrollbar.config(command=text_widget.yview)

        # Insérer le texte actuel
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", current_text)

        # Sauvegarder le texte initial
        self.last_saved_texts[lang] = current_text

        # Bind FocusOut pour détecter les changements
        def on_focus_out(event):
            new_text = text_widget.get("1.0", "end-1c")
            if new_text != self.last_saved_texts.get(lang, ""):
                self.last_saved_texts[lang] = new_text
                self._on_text_edited(lang, new_text)

        text_widget.bind("<FocusOut>", on_focus_out)

        # Sauvegarder les références
        self.text_widgets[lang] = text_widget
        self.valid_vars[lang] = valid_var
        self.language_rows[lang] = {
            "frame": row_frame,
            "magic_btn": magic_btn,
            "text_widget": text_widget,
            "valid_check": valid_check,
            "undo_btn": undo_btn,
            "redo_btn": redo_btn
        }

    def _on_magic_clicked(self, lang: str):
        """Gère le clic sur la baguette magique."""
        if not self.current_entry or lang not in self.text_widgets:
            return

        text_widget = self.text_widgets[lang]

        # Vérifier s'il y a une sélection
        selection_data = None
        try:
            selection_start = text_widget.index("sel.first")
            selection_end = text_widget.index("sel.last")
            selected_text = text_widget.get(selection_start, selection_end)

            if selected_text:
                # Il y a une sélection
                selection_data = {
                    "start": selection_start,
                    "end": selection_end,
                    "text": selected_text
                }
        except tk.TclError:
            # Pas de sélection
            pass

        # Déterminer l'action
        if selection_data:
            # Si une sélection existe, toujours traduire/améliorer la sélection
            full_text = text_widget.get("1.0", "end-1c").strip()
            action = "translate_selection" if full_text == "" or selection_data["text"] == full_text else "improve_selection"
        else:
            # Comportement normal
            text = text_widget.get("1.0", "end-1c").strip()
            action = "translate" if text == "" else "improve"

        # Récupérer la langue d'origine sélectionnée
        source_lang = self.source_lang_var.get() if self.source_lang_var else "auto"

        # Appeler le callback parent avec les données de sélection et la langue d'origine
        self.on_magic_click(lang, action, selection_data, source_lang)

    def _on_validate_toggled(self, lang: str, valid: bool):
        """Gère le changement d'état de validation."""
        self.on_validate(lang, valid)

    def _on_history_undo(self, lang: str):
        """Recule dans l'historique (undo)."""
        if not self.current_entry or lang not in self.current_entry:
            return

        lang_data = self.current_entry[lang]
        current_index = self.history_indices.get(lang, 0)

        # Vérifier qu'on peut reculer
        if current_index >= len(lang_data["history"]):
            return

        # Sauvegarder le texte actuel avant le premier undo
        if current_index == 0:
            self.current_texts_before_undo[lang] = lang_data["text"]

        # Passer à l'historique précédent
        new_index = current_index + 1
        self.history_indices[lang] = new_index

        # Récupérer le texte de l'historique
        # history[0] = le plus récent historique, history[-1] = le plus ancien
        history_text = lang_data["history"][new_index - 1]

        # Mettre à jour le texte
        lang_data["text"] = history_text
        self.update_language_data(lang)
        self._update_history_buttons_state(lang)

    def _on_history_redo(self, lang: str):
        """Avance dans l'historique (redo)."""
        if not self.current_entry or lang not in self.current_entry:
            return

        lang_data = self.current_entry[lang]
        current_index = self.history_indices.get(lang, 0)

        # Vérifier qu'on peut avancer
        if current_index <= 0:
            return

        # Revenir vers le texte actuel ou un historique plus récent
        new_index = current_index - 1
        self.history_indices[lang] = new_index

        if new_index == 0:
            # Retour au texte actuel (celui qui était avant les undo)
            if lang in self.current_texts_before_undo:
                lang_data["text"] = self.current_texts_before_undo[lang]
            # Sinon, lang_data["text"] contient déjà le texte actuel
        else:
            # Récupérer le texte de l'historique
            history_text = lang_data["history"][new_index - 1]
            lang_data["text"] = history_text

        self.update_language_data(lang)
        self._update_history_buttons_state(lang)

    def _on_text_edited(self, lang: str, new_text: str):
        """Gère l'édition manuelle du texte (appelé sur FocusOut)."""
        if (self.current_entry and
            lang in self.current_entry and
            self.current_entry[lang]["text"] != new_text):
            self.on_manual_edit(lang, new_text)

    def _update_history_buttons_state(self, lang: str):
        """
        Met à jour l'état des boutons undo/redo selon la position dans l'historique.

        Args:
            lang: Code langue
        """
        if not self.current_entry or lang not in self.current_entry:
            return

        if lang not in self.language_rows:
            return

        lang_data = self.current_entry[lang]
        current_index = self.history_indices.get(lang, 0)
        history_length = len(lang_data["history"])

        # Bouton undo (↶): activé si on peut reculer dans l'historique
        can_undo = current_index < history_length
        self.language_rows[lang]["undo_btn"].config(
            state="normal" if can_undo else "disabled"
        )

        # Bouton redo (↷): activé si on peut avancer (si on n'est pas à l'index 0)
        can_redo = current_index > 0
        self.language_rows[lang]["redo_btn"].config(
            state="normal" if can_redo else "disabled"
        )

    def update_language_data(self, lang: str):
        """
        Met à jour l'affichage d'une langue après modification.

        Args:
            lang: Code langue
        """
        if not self.current_entry or lang not in self.current_entry:
            return

        lang_data = self.current_entry[lang]

        # IMPORTANT: Mettre à jour last_saved_texts AVANT de modifier le widget
        # pour éviter que FocusOut déclenche _on_text_edited
        self.last_saved_texts[lang] = lang_data["text"]

        # Mettre à jour le texte
        if lang in self.text_widgets:
            text_widget = self.text_widgets[lang]
            current_pos = text_widget.index(tk.INSERT)
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", lang_data["text"])
            # Essayer de restaurer la position du curseur
            try:
                text_widget.mark_set(tk.INSERT, current_pos)
            except:
                pass

        # Mettre à jour la validation
        if lang in self.valid_vars:
            self.valid_vars[lang].set(lang_data["valid"])

        # Mettre à jour l'état des boutons undo/redo
        self._update_history_buttons_state(lang)

    def _show_not_translatable(self):
        """Affiche un message pour les entrées non traduisibles."""
        self.path_label.config(text="")
        self.original_text.config(state="normal")
        self.original_text.delete("1.0", "end")
        self.original_text.config(state="disabled")

        for widget in self.languages_container.winfo_children():
            widget.destroy()

        msg = ttk.Label(self.languages_container,
                       text="⚠ Cette entrée n'est pas traduisible\n(nombres, booléens, ou valeur non-string)",
                       font=("Arial", 10), foreground="orange")
        msg.pack(pady=20)

    def _show_no_file_loaded(self):
        """Affiche un message quand aucun fichier n'est chargé."""
        self.path_label.config(text="")
        self.original_text.config(state="normal")
        self.original_text.delete("1.0", "end")
        self.original_text.config(state="disabled")

        for widget in self.languages_container.winfo_children():
            widget.destroy()

        msg = ttk.Label(self.languages_container,
                       text="📂 Aucun fichier chargé\nUtilisez Fichier > Ouvrir pour charger un fichier JSON",
                       font=("Arial", 10), foreground="gray")
        msg.pack(pady=20)

    def _create_tooltip(self, widget, text):
        """Crée une infobulle pour un widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")

            label = tk.Label(tooltip, text=text, background="lightyellow",
                           relief="solid", borderwidth=1, font=("Arial", 8),
                           padx=5, pady=3)
            label.pack()

            widget.tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
