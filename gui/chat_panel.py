# -*- coding: utf-8 -*-
"""
Panneau de chat contextualisé pour OllamaFic.

Ce module fournit un panneau de chat réductible qui affiche l'historique
des actions de traduction pour l'entrée actuellement sélectionnée.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional


class ChatPanel(ttk.Frame):
    """
    Panel de chat réductible avec historique contextualisé.

    Fonctionnalités:
    - Affichage de l'historique des actions
    - Contexte basé sur le chemin sélectionné
    - Réductible avec bouton toggle
    - Bouton clear pour effacer l'historique
    - Coloration par type de message
    """

    def __init__(self, parent):
        super().__init__(parent)

        self.current_context = None
        self.is_visible = True
        self.paned_window = None  # Référence au PanedWindow parent

        self._create_widgets()

    def set_paned_window(self, paned_window):
        """Définit la référence au PanedWindow pour gérer le redimensionnement."""
        self.paned_window = paned_window

    def _create_widgets(self):
        """Crée les widgets du panel."""
        # Header avec contexte et bouton toggle
        self.header = ttk.Frame(self)
        self.header.pack(fill="x", padx=5, pady=2)

        # Bouton toggle
        self.toggle_btn = tk.Button(self.header, text="▼", width=2,
                                    relief="flat", command=self.toggle_visibility,
                                    font=("Arial", 10, "bold"))
        self.toggle_btn.pack(side="left")

        # Label contexte
        self.context_label = ttk.Label(self.header, text="Chat & Historique",
                                       font=("Arial", 9, "bold"))
        self.context_label.pack(side="left", padx=5)

        # Bouton clear
        clear_btn = tk.Button(self.header, text="🗙", width=2,
                             relief="flat", command=self.clear_history,
                             font=("Arial", 10))
        clear_btn.pack(side="right")

        # Séparateur
        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # Zone de texte avec scrollbar
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self.content_frame)
        scrollbar.pack(side="right", fill="y")

        self.text_widget = tk.Text(self.content_frame, height=10, wrap="word",
                                   state="disabled", yscrollcommand=scrollbar.set,
                                   font=("Arial", 9), bg="#f9f9f9")
        self.text_widget.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar.config(command=self.text_widget.yview)

        # Tags pour la coloration
        self.text_widget.tag_config("user", foreground="blue", font=("Arial", 9, "bold"))
        self.text_widget.tag_config("assistant", foreground="green", font=("Arial", 9))
        self.text_widget.tag_config("system", foreground="orange", font=("Arial", 9, "italic"))
        self.text_widget.tag_config("error", foreground="red", font=("Arial", 9, "bold"))
        self.text_widget.tag_config("timestamp", foreground="gray", font=("Arial", 7))
        self.text_widget.tag_config("magic", foreground="purple", font=("Arial", 9, "bold"))

    def set_context(self, path: str):
        """
        Change le contexte du chat.

        Args:
            path: Nouveau chemin (ex: "app/title")
        """
        self.current_context = path
        self.context_label.config(text=f"Chat & Historique ({path})")

    def add_message(self, role: str, message: str, tag: Optional[str] = None):
        """
        Ajoute un message au chat.

        Args:
            role: "user", "assistant", "system", "error"
            message: Texte du message
            tag: Tag supplémentaire (ex: "🪄 fr: traduire")
        """
        self.text_widget.config(state="normal")

        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_widget.insert("end", f"[{timestamp}] ", "timestamp")

        # Prefix avec tag si fourni
        if tag:
            self.text_widget.insert("end", f"{tag}\n", "magic")
        else:
            prefix = "> " if role == "user" else "< "
            self.text_widget.insert("end", prefix, role)

        # Message
        self.text_widget.insert("end", f"{message}\n", role)

        # Ligne vide pour séparation
        self.text_widget.insert("end", "\n")

        self.text_widget.config(state="disabled")
        self.text_widget.see("end")

    def add_magic_action(self, lang: str, action: str, result: str, validated: bool):
        """
        Ajoute une action de baguette magique au chat.

        Args:
            lang: Code langue
            action: "translate" ou "improve"
            result: Texte résultant
            validated: État de validation
        """
        action_text = "traduire" if action == "translate" else "améliorer"
        tag = f"🪄 {lang.upper()}: {action_text}"

        status = "✓ Validé" if validated else "❌ Non validé"
        message = f'"{result}"\n   [{status}]'

        self.add_message("assistant", message, tag)

    def add_validation_change(self, lang: str, validated: bool):
        """
        Ajoute un changement de validation au chat.

        Args:
            lang: Code langue
            validated: Nouvel état de validation
        """
        status = "validée" if validated else "invalidée"
        message = f"Traduction {lang.upper()} {status}"
        self.add_message("user", message)

    def add_rollback(self, lang: str, restored_text: str):
        """
        Ajoute un rollback au chat.

        Args:
            lang: Code langue
            restored_text: Texte restauré
        """
        message = f"↶ {lang.upper()}: Retour à \"{restored_text}\""
        self.add_message("system", message)

    def add_manual_edit(self, lang: str, new_text: str):
        """
        Ajoute une édition manuelle au chat.

        Args:
            lang: Code langue
            new_text: Nouveau texte
        """
        message = f"✏ {lang.upper()}: Édition manuelle → \"{new_text}\""
        self.add_message("user", message)

    def add_error(self, error_message: str):
        """
        Ajoute un message d'erreur au chat.

        Args:
            error_message: Message d'erreur
        """
        self.add_message("error", f"❌ Erreur: {error_message}")

    def clear_history(self):
        """Efface l'historique du chat."""
        self.text_widget.config(state="normal")
        self.text_widget.delete("1.0", "end")
        self.text_widget.config(state="disabled")

        # Ajouter un message de confirmation
        self.add_message("system", "Historique effacé")

    def toggle_visibility(self):
        """Affiche/cache le contenu du chat et redimensionne le pane."""
        if self.is_visible:
            # Cacher le contenu
            self.content_frame.pack_forget()
            self.toggle_btn.config(text="▶")
            self.is_visible = False

            # Redimensionner le pane pour qu'il soit minimal (juste le header)
            if self.paned_window:
                self.update_idletasks()  # Forcer la mise à jour des dimensions
                # Hauteur du header seulement (~30 pixels)
                self.paned_window.sashpos(0, self.paned_window.winfo_height() - 30)
        else:
            # Afficher le contenu
            self.content_frame.pack(fill="both", expand=True)
            self.toggle_btn.config(text="▼")
            self.is_visible = True

            # Redimensionner le pane pour afficher le chat (~200 pixels)
            if self.paned_window:
                self.update_idletasks()
                self.paned_window.sashpos(0, self.paned_window.winfo_height() - 200)
