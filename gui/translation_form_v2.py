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
            on_magic_click: Callback(lang, action) pour la baguette magique
            on_validate: Callback(lang, valid) pour la validation
            on_rollback: Callback(lang) pour le retour arrière
            on_manual_edit: Callback(lang, new_text) pour édition manuelle
        """
        super().__init__(parent)

        self.got_manager = got_manager
        self.on_magic_click = on_magic_click or (lambda lang, action: None)
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

        # Widgets
        self.path_label = None
        self.original_text = None

        self._create_widgets()

    def _create_widgets(self):
        """Crée la structure du formulaire."""
        # Section supérieure fixe (header + original)
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=10)

        # Header avec chemin
        header = ttk.Frame(top_frame)
        header.pack(fill="x", pady=(0, 5))

        ttk.Label(header, text="📍 Chemin:", font=("Arial", 9, "bold")).pack(side="left")
        self.path_label = ttk.Label(header, text="", font=("Arial", 9), foreground="blue")
        self.path_label.pack(side="left", padx=5)

        # Séparateur
        ttk.Separator(top_frame, orient="horizontal").pack(fill="x", pady=5)

        # Zone original (ori) - multilignes
        ori_frame = ttk.Frame(top_frame)
        ori_frame.pack(fill="x", pady=5)

        ttk.Label(ori_frame, text="Original (ori):",
                 font=("Arial", 9, "bold")).pack(anchor="w")

        self.original_text = tk.Text(ori_frame, height=3,
                                     state="disabled", wrap="word",
                                     background="#f9f9f9", relief="flat",
                                     font=("Arial", 10))
        self.original_text.pack(fill="both", expand=True, pady=(2, 0))

        # Séparateur
        ttk.Separator(top_frame, orient="horizontal").pack(fill="x", pady=5)

        # Label pour les traductions
        ttk.Label(top_frame, text="Traductions:",
                 font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 5))

        # Section inférieure scrollable (traductions)
        # Pas de padx pour aller d'un bord à l'autre
        translations_frame = ttk.Frame(self)
        translations_frame.pack(fill="both", expand=True, pady=(0, 5))

        # Canvas + scrollbar pour les traductions
        canvas = tk.Canvas(translations_frame, borderwidth=0, background="#f0f00f", highlightthickness=0)
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

            # Créer une ligne pour chaque langue
            languages = self.got_manager.target_languages
            for lang in languages:
                if lang in entry:
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

        # ↶ Bouton rollback
        has_history = len(lang_data["history"]) > 0
        rollback_btn = tk.Button(header_frame, text="↶", font=("Arial", 12),
                                width=2, relief="raised",
                                state="normal" if has_history else "disabled",
                                command=lambda: self._on_rollback_clicked(lang))
        rollback_btn.pack(side="left")

        if has_history:
            tooltip_text = f"Historique ({len(lang_data['history'])}):\n"
            tooltip_text += "\n".join([f"  • {h[:50]}..." if len(h) > 50 else f"  • {h}"
                                      for h in lang_data["history"][:3]])
            if len(lang_data["history"]) > 3:
                tooltip_text += f"\n  ... et {len(lang_data['history']) - 3} autres"
            self._create_tooltip(rollback_btn, tooltip_text)
        else:
            self._create_tooltip(rollback_btn, "Pas d'historique")

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
            "rollback_btn": rollback_btn
        }

    def _on_magic_clicked(self, lang: str):
        """Gère le clic sur la baguette magique."""
        if not self.current_entry or lang not in self.text_widgets:
            return

        text = self.text_widgets[lang].get("1.0", "end-1c").strip()
        action = "translate" if text == "" else "improve"

        # Appeler le callback parent
        self.on_magic_click(lang, action)

    def _on_validate_toggled(self, lang: str, valid: bool):
        """Gère le changement d'état de validation."""
        self.on_validate(lang, valid)

    def _on_rollback_clicked(self, lang: str):
        """Gère le retour arrière."""
        self.on_rollback(lang)

    def _on_text_edited(self, lang: str, new_text: str):
        """Gère l'édition manuelle du texte (appelé sur FocusOut)."""
        if (self.current_entry and
            lang in self.current_entry and
            self.current_entry[lang]["text"] != new_text):
            self.on_manual_edit(lang, new_text)

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

        # Mettre à jour l'état du bouton rollback
        has_history = len(lang_data["history"]) > 0
        if lang in self.language_rows:
            self.language_rows[lang]["rollback_btn"].config(
                state="normal" if has_history else "disabled"
            )

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
