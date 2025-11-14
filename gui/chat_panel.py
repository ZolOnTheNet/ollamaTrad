# -*- coding: utf-8 -*-
"""
Panneau de chat contextualisé pour OllamaTrad.

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

    def __init__(self, parent, on_user_message: Optional[callable] = None):
        super().__init__(parent)

        self.current_context = None
        self.is_visible = True
        self.paned_window = None  # Référence au PanedWindow parent
        self.on_user_message = on_user_message  # Callback quand l'utilisateur envoie un message

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

        # Séparateur
        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # Zone de saisie pour dialoguer avec l'IA
        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", padx=5, pady=5)

        # Label
        ttk.Label(input_frame, text="💬", font=("Arial", 12)).pack(side="left", padx=(0, 5))

        # Champ de saisie
        self.input_entry = ttk.Entry(input_frame, font=("Arial", 9))
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", self._on_send_message)
        self.input_entry.bind("<Shift-Return>", lambda e: None)  # Permettre Shift+Enter sans envoyer

        # Bouton envoyer
        send_btn = tk.Button(input_frame, text="Envoyer", command=self._on_send_message,
                            bg="#4CAF50", fg="white", relief="flat", padx=10)
        send_btn.pack(side="left")

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

    def add_magic_action(self, lang: str, action: str, sent_text: str,
                        returned_text: str, kept_text: str, validated: bool,
                        full_prompt: str = None):
        """
        Ajoute une action de baguette magique au chat.

        Args:
            lang: Code langue
            action: "translate", "improve", "translate_selection", "improve_selection"
            sent_text: Texte envoyé à l'IA (sélection ou texte complet)
            returned_text: Réponse brute de l'IA
            kept_text: Texte finalement retenu/inséré
            validated: État de validation
            full_prompt: Prompt complet envoyé à l'IA (optionnel, pour mode debug)
        """
        # Déterminer le type d'action
        if "selection" in action:
            action_base = "traduire" if "translate" in action else "améliorer"
            action_text = f"{action_base} (sélection)"
        else:
            action_text = "traduire" if "translate" in action else "améliorer"

        tag = f"🪄 {lang.upper()}: {action_text}"

        # Construire le message détaillé
        message_parts = []

        # Texte envoyé
        sent_preview = sent_text[:100] + "..." if len(sent_text) > 100 else sent_text
        message_parts.append(f"Envoyé: \"{sent_preview}\"")

        # Texte retourné (réponse brute de l'IA)
        returned_preview = returned_text[:100] + "..." if len(returned_text) > 100 else returned_text
        message_parts.append(f"Retourné: \"{returned_preview}\"")

        # Texte retenu (ce qui est inséré)
        kept_preview = kept_text[:100] + "..." if len(kept_text) > 100 else kept_text
        message_parts.append(f"Retenu: \"{kept_preview}\"")

        # Statistiques
        message_parts.append(f"Longueur: envoyé={len(sent_text)}, retourné={len(returned_text)}, retenu={len(kept_text)}")

        # Prompt complet si fourni (mode debug)
        if full_prompt:
            prompt_preview = full_prompt[:200] + "..." if len(full_prompt) > 200 else full_prompt
            message_parts.append(f"[DEBUG] Prompt complet:\n{prompt_preview}")

        # Status
        status = "✓ Validé" if validated else "❌ Non validé"
        message_parts.append(f"[{status}]")

        message = "\n   ".join(message_parts)
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

    def _on_send_message(self, event=None):
        """
        Gère l'envoi d'un message utilisateur.

        Args:
            event: Événement Tkinter (optionnel)
        """
        message = self.input_entry.get().strip()

        if not message:
            return

        # Afficher le message de l'utilisateur dans le chat
        self.add_message("user", message)

        # Effacer le champ de saisie
        self.input_entry.delete(0, "end")

        # Appeler le callback si défini
        if self.on_user_message:
            self.on_user_message(message)

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
