# -*- coding: utf-8 -*-
"""
Formulaire de traduction avec baguette magique pour OllamaFic.

Ce module fournit une interface graphique pour éditer les traductions
avec support de la baguette magique, validation, et rollback.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Callable, Optional
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent))

from core.got_json_manager import GotJsonManager


class TranslationForm(ttk.Frame):
    """
    Formulaire de traduction avec baguette magique pour chaque langue.

    Fonctionnalités:
    - Affichage du texte original (lecture seule)
    - Zone de texte éditable par langue
    - Bouton baguette magique (🪄) pour traduire/améliorer
    - Checkbox de validation
    - Bouton rollback (↶) pour retour arrière
    - Tooltip avec historique
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

        # Variables Tkinter pour chaque langue
        self.text_vars = {}
        self.valid_vars = {}
        self.editing_disabled = False  # Flag pour éviter les boucles

        # Widgets
        self.path_label = None
        self.original_text = None
        self.language_rows = {}

        self._create_widgets()

    def _create_widgets(self):
        """Crée la structure du formulaire."""
        # Container principal avec scrollbar
        canvas = tk.Canvas(self, borderwidth=0, background="#f0f0f0")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Header avec chemin
        header = ttk.Frame(self.scrollable_frame)
        header.pack(fill="x", padx=10, pady=(10, 5))

        ttk.Label(header, text="📍 Chemin:", font=("Arial", 9, "bold")).pack(side="left")
        self.path_label = ttk.Label(header, text="", font=("Arial", 9), foreground="blue")
        self.path_label.pack(side="left", padx=5)

        # Séparateur
        ttk.Separator(self.scrollable_frame, orient="horizontal").pack(fill="x", padx=10, pady=5)

        # Zone original (ori)
        ori_frame = ttk.Frame(self.scrollable_frame)
        ori_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(ori_frame, text="Original (ori):",
                 font=("Arial", 9, "bold")).pack(anchor="w")

        self.original_text = tk.Text(ori_frame, height=3, width=50,
                                     state="disabled", wrap="word",
                                     background="#f9f9f9", relief="flat",
                                     font=("Arial", 10))
        self.original_text.pack(fill="x", pady=(2, 0))

        # Séparateur
        ttk.Separator(self.scrollable_frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

        # Label pour les traductions
        ttk.Label(self.scrollable_frame, text="Traductions:",
                 font=("Arial", 9, "bold")).pack(anchor="w", padx=10, pady=(0, 5))

        # Container pour les langues
        self.languages_container = ttk.Frame(self.scrollable_frame)
        self.languages_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

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

            # Afficher l'original
            self.original_text.config(state="normal")
            self.original_text.delete("1.0", "end")
            self.original_text.insert("1.0", entry["ori"])
            self.original_text.config(state="disabled")

            # Nettoyer les anciennes langues
            for widget in self.languages_container.winfo_children():
                widget.destroy()

            self.text_vars.clear()
            self.valid_vars.clear()
            self.language_rows.clear()

            # Créer une ligne pour chaque langue
            languages = self.got_manager.target_languages
            for lang in languages:
                if lang in entry:
                    self._create_language_row(lang, entry[lang])

        except KeyError as e:
            messagebox.showerror("Erreur", f"Chemin invalide: {path}\n{e}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {e}")
            import traceback
            traceback.print_exc()

    def _create_language_row(self, lang: str, lang_data: Dict):
        """
        Crée une ligne complète pour une langue.

        Args:
            lang: Code langue (ex: "fr")
            lang_data: {"text": "...", "history": [...], "valid": bool}
        """
        row_frame = ttk.Frame(self.languages_container)
        row_frame.pack(fill="x", pady=5)

        # Container pour aligner les éléments
        controls = ttk.Frame(row_frame)
        controls.pack(fill="x")

        # 🪄 Bouton magique
        magic_btn = tk.Button(controls, text="🪄", font=("Arial", 14),
                             width=2, relief="raised", cursor="hand2",
                             bg="#FFE4B5", activebackground="#FFD700",
                             command=lambda: self._on_magic_clicked(lang))
        magic_btn.pack(side="left", padx=(0, 5))

        # Tooltip pour la baguette
        self._create_tooltip(magic_btn, "Cliquer pour traduire ou améliorer")

        # Label langue
        lang_label = ttk.Label(controls, text=f"{lang.upper()}:",
                              font=("Arial", 9, "bold"), width=4)
        lang_label.pack(side="left", padx=(0, 5))

        # Zone de texte
        text_var = tk.StringVar(value=lang_data["text"])
        text_entry = ttk.Entry(controls, textvariable=text_var, width=40,
                              font=("Arial", 10))
        text_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Bind pour édition manuelle
        def on_text_change(*args):
            if not self.editing_disabled:
                self._on_text_edited(lang, text_var.get())

        text_var.trace_add("write", on_text_change)

        # ✓ Checkbox validation
        valid_var = tk.BooleanVar(value=lang_data["valid"])
        valid_check = ttk.Checkbutton(controls, variable=valid_var,
                                      command=lambda: self._on_validate_toggled(lang, valid_var.get()))
        valid_check.pack(side="left", padx=(0, 5))

        # Tooltip validation
        self._create_tooltip(valid_check, "Marquer comme validé")

        # ↶ Bouton rollback
        has_history = len(lang_data["history"]) > 0
        rollback_btn = tk.Button(controls, text="↶", font=("Arial", 12),
                                width=2, relief="raised",
                                state="normal" if has_history else "disabled",
                                command=lambda: self._on_rollback_clicked(lang))
        rollback_btn.pack(side="left")

        # Tooltip pour l'historique
        if has_history:
            tooltip_text = f"Historique ({len(lang_data['history'])}):\n"
            tooltip_text += "\n".join([f"  • {h[:50]}..." if len(h) > 50 else f"  • {h}"
                                      for h in lang_data["history"][:3]])
            if len(lang_data["history"]) > 3:
                tooltip_text += f"\n  ... et {len(lang_data['history']) - 3} autres"
            self._create_tooltip(rollback_btn, tooltip_text)
        else:
            self._create_tooltip(rollback_btn, "Pas d'historique")

        # Sauvegarder les références
        self.text_vars[lang] = text_var
        self.valid_vars[lang] = valid_var
        self.language_rows[lang] = {
            "frame": row_frame,
            "magic_btn": magic_btn,
            "text_entry": text_entry,
            "valid_check": valid_check,
            "rollback_btn": rollback_btn
        }

    def _on_magic_clicked(self, lang: str):
        """Gère le clic sur la baguette magique."""
        if not self.current_entry or lang not in self.text_vars:
            return

        text = self.text_vars[lang].get().strip()
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
        """Gère l'édition manuelle du texte."""
        # Éviter les boucles infinies et vérifier que le texte a vraiment changé
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

        # Désactiver temporairement les callbacks pour éviter les boucles
        self.editing_disabled = True

        # Mettre à jour le texte
        if lang in self.text_vars:
            self.text_vars[lang].set(lang_data["text"])

        # Mettre à jour la validation
        if lang in self.valid_vars:
            self.valid_vars[lang].set(lang_data["valid"])

        # Mettre à jour l'état du bouton rollback
        has_history = len(lang_data["history"]) > 0
        if lang in self.language_rows:
            rollback_btn = self.language_rows[lang]["rollback_btn"]
            rollback_btn.config(state="normal" if has_history else "disabled")

            # Mettre à jour le tooltip
            if has_history:
                tooltip_text = f"Historique ({len(lang_data['history'])}):\n"
                tooltip_text += "\n".join([f"  • {h[:50]}..." if len(h) > 50 else f"  • {h}"
                                          for h in lang_data["history"][:3]])
                if len(lang_data["history"]) > 3:
                    tooltip_text += f"\n  ... et {len(lang_data['history']) - 3} autres"
                # Note: pour mettre à jour le tooltip, il faudrait recréer les bindings

        # Réactiver les callbacks
        self.editing_disabled = False

    def _show_not_translatable(self):
        """Affiche un message pour les entrées non traduisibles."""
        # Nettoyer
        self.path_label.config(text="")
        self.original_text.config(state="normal")
        self.original_text.delete("1.0", "end")
        self.original_text.config(state="disabled")

        for widget in self.languages_container.winfo_children():
            widget.destroy()

        # Message
        msg = ttk.Label(self.languages_container,
                       text="⚠ Cette entrée n'est pas traduisible\n(nombres, booléens, ou valeur non-string)",
                       font=("Arial", 10), foreground="orange")
        msg.pack(pady=20)

    def _show_no_file_loaded(self):
        """Affiche un message quand aucun fichier n'est chargé."""
        # Nettoyer
        self.path_label.config(text="")
        self.original_text.config(state="normal")
        self.original_text.delete("1.0", "end")
        self.original_text.config(state="disabled")

        for widget in self.languages_container.winfo_children():
            widget.destroy()

        # Message
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
