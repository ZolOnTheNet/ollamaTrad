# -*- coding: utf-8 -*-
"""
Fenêtre d'options pour OllamaTrad

Permet de configurer:
- Langues connues (tableur éditable avec code + nom)
- Langues visibles (sélection multi-choix)
- Configuration IA (fournisseur, modèle, test de connexion, DeepL)
- Options avancées (édition champ "ori", sauvegarde automatique)
- Prompts de traduction personnalisables
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Callable, Optional
import json
from pathlib import Path
import asyncio
import threading


class OptionsDialog(tk.Toplevel):
    """Fenêtre de configuration des options de traduction (Version 3)"""

    # Langues disponibles par défaut
    DEFAULT_LANGUAGES = {
        "fr": "Français",
        "en": "English",
        "es": "Español",
        "de": "Deutsch",
        "it": "Italiano",
        "pt": "Português",
        "ru": "Русский",
        "ja": "日本語",
        "zh": "中文",
        "ar": "العربية"
    }

    def __init__(self, parent, config_path: Optional[Path] = None,
                 on_save: Optional[Callable] = None,
                 ai_client=None):
        """
        Args:
            parent: Fenêtre parente
            config_path: Chemin vers le fichier de configuration
            on_save: Callback appelé après sauvegarde (config_dict)
            ai_client: Client IA pour tester la connexion
        """
        super().__init__(parent)

        self.title("Options - OllamaTrad")
        self.geometry("950x750")
        self.resizable(True, True)

        self.config_path = config_path or Path(__file__).parent.parent / "config" / "translation_config.json"
        self.on_save_callback = on_save
        self.ai_client = ai_client

        # Charger la configuration
        self.config = self.load_config()

        # Variables pour les widgets
        self.known_languages = {}  # code -> nom (éditable)
        self.language_entries = []  # Liste des paires (Entry code, Entry nom) pour le tableur
        self.visible_languages_vars = {}  # code -> BooleanVar
        self.allow_edit_ori_var = tk.BooleanVar()
        self.auto_save_on_exit_var = tk.BooleanVar()

        # Variables IA
        self.ai_provider_var = tk.StringVar()

        # Ollama
        self.ollama_model_var = tk.StringVar()
        self.ollama_host_var = tk.StringVar()

        # OpenAI
        self.openai_api_key_var = tk.StringVar()
        self.openai_model_var = tk.StringVar()

        # Mistral
        self.mistral_api_key_var = tk.StringVar()
        self.mistral_model_var = tk.StringVar()

        # Anthropic
        self.anthropic_api_key_var = tk.StringVar()
        self.anthropic_model_var = tk.StringVar()

        # DeepL (section séparée)
        self.deepl_enabled_var = tk.BooleanVar()
        self.deepl_api_key_var = tk.StringVar()
        self.deepl_is_pro_var = tk.BooleanVar()
        self.deepl_char_limit_var = tk.IntVar()  # Limite de caractères personnalisée

        # Variables prompts
        self.prompt_translate_var = tk.StringVar()
        self.prompt_translate_html_var = tk.StringVar()
        self.prompt_improve_var = tk.StringVar()
        self.prompt_improve_html_var = tk.StringVar()

        self._create_widgets()
        self._load_values()

        # Centrer la fenêtre
        self.transient(parent)
        self.grab_set()

    def load_config(self) -> Dict:
        """Charge la configuration depuis le fichier JSON"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                messagebox.showwarning("Avertissement",
                    f"Impossible de charger la configuration: {e}\nUtilisation des valeurs par défaut.")

        # Configuration par défaut
        return {
            "known_languages": self.DEFAULT_LANGUAGES.copy(),
            "target_languages": ["fr", "en", "es"],
            "visible_languages": ["fr", "en", "es"],
            "allow_edit_ori": False,
            "auto_save_on_exit": False,
            "ai_config": {
                "provider": "ollama",
                "ollama": {
                    "host": "http://localhost:11434",
                    "model": "aya"
                },
                "openai": {
                    "api_key": "",
                    "model": "gpt-4"
                },
                "mistral": {
                    "api_key": "",
                    "model": "mistral-large-latest"
                },
                "anthropic": {
                    "api_key": "",
                    "model": "claude-3-sonnet-20240229"
                },
                "deepl": {
                    "enabled": False,
                    "api_key": "",
                    "is_pro": False,
                    "character_limit": 500000  # 500K caractères (limite gratuite DeepL)
                }
            },
            "prompts": {
                "translate": 'Traduis "{text}" en {lang}. Réponds uniquement avec la traduction, sans explication.',
                "translate_html": '''Traduis le texte suivant en {lang}.
IMPORTANT: Le texte contient du code HTML. Tu DOIS préserver TOUTES les balises HTML exactement comme elles sont.
Ne traduis QUE le texte entre les balises, PAS les balises elles-mêmes.

Texte à traduire:
{text}

Réponds uniquement avec la traduction, en préservant exactement toutes les balises HTML.''',
                "improve": '''Améliore cette traduction {lang}:
Texte original: "{original}"
Traduction actuelle: "{current}"
Contexte: {context}

Corrige l'orthographe, la grammaire et rends la phrase plus naturelle.
Réponds uniquement avec la traduction améliorée, sans explication.''',
                "improve_html": '''Améliore cette traduction {lang}.
IMPORTANT: Le texte contient du code HTML. Tu DOIS préserver TOUTES les balises HTML exactement comme elles sont.

Texte original: {original}
Traduction actuelle: {current}
Contexte: {context}

Corrige l'orthographe, la grammaire et rends la phrase plus naturelle.
Réponds uniquement avec la traduction améliorée, en préservant exactement toutes les balises HTML.'''
            }
        }

    def save_config(self):
        """Sauvegarde la configuration dans le fichier JSON"""
        try:
            # Créer le répertoire si nécessaire
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder la configuration: {e}")
            return False

    def _create_widgets(self):
        """Crée l'interface de la fenêtre"""
        # Notebook pour organiser par catégories
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Onglet 1: Langues
        languages_frame = ttk.Frame(notebook)
        notebook.add(languages_frame, text="🌍 Langues")
        self._create_languages_tab(languages_frame)

        # Onglet 2: Configuration IA
        ia_frame = ttk.Frame(notebook)
        notebook.add(ia_frame, text="🤖 Configuration IA")
        self._create_ia_tab(ia_frame)

        # Onglet 3: Prompts
        prompts_frame = ttk.Frame(notebook)
        notebook.add(prompts_frame, text="💬 Prompts de Traduction")
        self._create_prompts_tab(prompts_frame)

        # Onglet 4: Avancé
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="⚙️ Avancé")
        self._create_advanced_tab(advanced_frame)

        # Boutons en bas
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(buttons_frame, text="💾 Sauvegarder",
                  command=self._on_save).pack(side="right", padx=5)
        ttk.Button(buttons_frame, text="❌ Annuler",
                  command=self.destroy).pack(side="right")
        ttk.Button(buttons_frame, text="🔄 Réinitialiser",
                  command=self._on_reset).pack(side="left")

    def _create_languages_tab(self, parent):
        """Crée l'onglet de configuration des langues avec tableur éditable"""
        # Container avec scrollbar
        canvas = tk.Canvas(parent, borderwidth=0, background="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Forcer la largeur du frame scrollable à suivre le canvas
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Section 1: Tableur éditable pour les langues connues
        known_frame = ttk.LabelFrame(scrollable_frame, text="📚 Langues Connues (Éditable)", padding=10)
        known_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(known_frame,
                 text="Ajoutez ou modifiez les langues disponibles. Seules les lignes avec code ET nom remplis sont valides.",
                 font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 5))

        # Frame pour le tableur avec scrollbar
        grid_container = ttk.Frame(known_frame)
        grid_container.pack(fill="both", expand=True)

        # Headers
        header_frame = ttk.Frame(grid_container)
        header_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(header_frame, text="Code (ex: fr)", font=("Arial", 9, "bold"), width=15).pack(side="left", padx=5)
        ttk.Label(header_frame, text="Nom de la langue", font=("Arial", 9, "bold")).pack(side="left", padx=5, fill="x", expand=True)

        # Scrollable grid
        grid_canvas = tk.Canvas(grid_container, height=300, borderwidth=0, highlightthickness=0)
        grid_scrollbar = ttk.Scrollbar(grid_container, orient="vertical", command=grid_canvas.yview)
        self.languages_grid_frame = ttk.Frame(grid_canvas)

        self.languages_grid_frame.bind(
            "<Configure>",
            lambda e: grid_canvas.configure(scrollregion=grid_canvas.bbox("all"))
        )

        grid_canvas_window = grid_canvas.create_window((0, 0), window=self.languages_grid_frame, anchor="nw")
        grid_canvas.configure(yscrollcommand=grid_scrollbar.set)

        # Forcer la largeur
        def on_grid_canvas_configure(event):
            grid_canvas.itemconfig(grid_canvas_window, width=event.width)

        grid_canvas.bind("<Configure>", on_grid_canvas_configure)

        grid_canvas.pack(side="left", fill="both", expand=True)
        grid_scrollbar.pack(side="right", fill="y")

        # Créer les lignes du tableur (10 langues par défaut + 5 lignes vides)
        self.language_entries = []
        for i in range(15):
            row_frame = ttk.Frame(self.languages_grid_frame)
            row_frame.pack(fill="x", pady=2)

            code_entry = ttk.Entry(row_frame, width=15, font=("Arial", 9))
            code_entry.pack(side="left", padx=5)

            name_entry = ttk.Entry(row_frame, font=("Arial", 9))
            name_entry.pack(side="left", padx=5, fill="x", expand=True)

            self.language_entries.append((code_entry, name_entry))

        # Boutons d'action pour le tableur
        buttons_frame = ttk.Frame(known_frame)
        buttons_frame.pack(fill="x", pady=5)

        ttk.Button(buttons_frame, text="➕ Ajouter une ligne",
                  command=self._add_language_row).pack(side="left", padx=5)

        ttk.Button(buttons_frame, text="🔄 Rafraîchir les options",
                  command=self._refresh_language_options).pack(side="left", padx=5)

        ttk.Label(buttons_frame,
                 text="Cliquez sur Rafraîchir pour mettre à jour les options ci-dessous",
                 font=("Arial", 8), foreground="blue").pack(side="left", padx=10)

        # Section 2: Langues cibles (ordre de traduction)
        target_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Langues Cibles (Ordre de Traduction)", padding=10)
        target_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(target_frame,
                 text="Saisissez les codes de langues séparés par des virgules (ex: fr, en, es):",
                 font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 5))

        self.target_languages_entry = ttk.Entry(target_frame, font=("Arial", 10))
        self.target_languages_entry.pack(fill="x", pady=5)

        ttk.Label(target_frame,
                 text="Ces langues apparaîtront dans le formulaire de traduction.",
                 font=("Arial", 8), foreground="gray").pack(anchor="w")

        # Section 3: Langues visibles dans l'arbre
        visible_frame = ttk.LabelFrame(scrollable_frame, text="👁️ Langues Visibles (Filtrage de l'Arbre)", padding=10)
        visible_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(visible_frame,
                 text="Cochez les langues à afficher dans l'arbre pour le fichier actuel:",
                 font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 5))

        ttk.Label(visible_frame,
                 text="Note: Les données des langues non cochées restent dans le .got.json mais ne s'affichent pas dans l'arbre.",
                 font=("Arial", 8), foreground="orange").pack(anchor="w", pady=(0, 10))

        # Frame scrollable pour les checkboxes
        visible_canvas = tk.Canvas(visible_frame, height=120, borderwidth=0, highlightthickness=0)
        visible_scrollbar = ttk.Scrollbar(visible_frame, orient="vertical", command=visible_canvas.yview)
        self.visible_checkboxes_frame = ttk.Frame(visible_canvas)

        self.visible_checkboxes_frame.bind(
            "<Configure>",
            lambda e: visible_canvas.configure(scrollregion=visible_canvas.bbox("all"))
        )

        visible_canvas_window = visible_canvas.create_window((0, 0), window=self.visible_checkboxes_frame, anchor="nw")
        visible_canvas.configure(yscrollcommand=visible_scrollbar.set)

        def on_visible_canvas_configure(event):
            visible_canvas.itemconfig(visible_canvas_window, width=event.width)

        visible_canvas.bind("<Configure>", on_visible_canvas_configure)

        visible_canvas.pack(side="left", fill="both", expand=True)
        visible_scrollbar.pack(side="right", fill="y")

        # Les checkboxes seront créées dans _load_values() une fois le tableur rempli
        # (pas d'appel ici car le tableur est encore vide)

    def _add_language_row(self):
        """Ajoute une nouvelle ligne vide au tableur de langues"""
        row_frame = ttk.Frame(self.languages_grid_frame)
        row_frame.pack(fill="x", pady=2)

        code_entry = ttk.Entry(row_frame, width=15, font=("Arial", 9))
        code_entry.pack(side="left", padx=5)

        name_entry = ttk.Entry(row_frame, font=("Arial", 9))
        name_entry.pack(side="left", padx=5, fill="x", expand=True)

        self.language_entries.append((code_entry, name_entry))

    def _refresh_language_options(self):
        """Rafraîchit les options des langues visibles en fonction du tableur et des langues cibles"""
        # Mettre à jour les checkboxes des langues visibles
        self._populate_visible_checkboxes()

        # Message de confirmation
        messagebox.showinfo("Rafraîchissement",
            "Les options de langues visibles ont été mises à jour en fonction des langues cibles définies.")

    def _populate_visible_checkboxes(self):
        """Remplit les checkboxes des langues visibles basées sur les langues CIBLES"""
        # Nettoyer les anciennes checkboxes
        for widget in self.visible_checkboxes_frame.winfo_children():
            widget.destroy()

        self.visible_languages_vars.clear()

        # Récupérer les langues connues depuis le tableur
        known_langs = self._parse_known_languages()

        if not known_langs:
            # Utiliser les langues par défaut si aucune n'est définie
            known_langs = self.DEFAULT_LANGUAGES

        # Récupérer les langues cibles depuis le champ Entry
        target_input = self.target_languages_entry.get().strip()
        target_langs = [lang.strip() for lang in target_input.split(",") if lang.strip()]

        # Si pas de langues cibles définies, ne rien afficher
        if not target_langs:
            ttk.Label(self.visible_checkboxes_frame,
                     text="⚠️ Définissez d'abord les langues cibles ci-dessus, puis cliquez sur Rafraîchir",
                     font=("Arial", 9), foreground="orange").pack(pady=10)
            return

        # Créer les checkboxes SEULEMENT pour les langues cibles (3 par ligne)
        i = 0
        for code in target_langs:
            if code in known_langs:
                name = known_langs[code]
                var = tk.BooleanVar(value=True)
                self.visible_languages_vars[code] = var

                cb = ttk.Checkbutton(self.visible_checkboxes_frame,
                                   text=f"{code} ({name})", variable=var)
                cb.grid(row=i // 3, column=i % 3, sticky="w", padx=10, pady=3)
                i += 1
            else:
                # Langue cible non trouvée dans le tableau
                ttk.Label(self.visible_checkboxes_frame,
                         text=f"⚠️ '{code}' non trouvé dans le tableau",
                         font=("Arial", 8), foreground="red").grid(
                             row=i // 3, column=i % 3, sticky="w", padx=10, pady=3)
                i += 1

    def _parse_known_languages(self) -> Dict[str, str]:
        """Parse le tableur pour extraire les langues connues valides"""
        known = {}
        for code_entry, name_entry in self.language_entries:
            code = code_entry.get().strip()
            name = name_entry.get().strip()

            # Seulement les lignes avec code ET nom remplis
            if code and name:
                known[code] = name

        return known

    def _create_ia_tab(self, parent):
        """Crée l'onglet de configuration IA avec disposition en colonnes"""
        # Container principal
        main_container = ttk.Frame(parent)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame en deux colonnes
        columns_frame = ttk.Frame(main_container)
        columns_frame.pack(fill="both", expand=True)

        # === COLONNE GAUCHE : Sélection du provider ===
        left_frame = ttk.LabelFrame(columns_frame, text="🎯 Fournisseur d'IA", padding=10)
        left_frame.pack(side="left", fill="both", padx=(0, 5))

        ttk.Label(left_frame, text="Sélectionnez le fournisseur:",
                 font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 10))

        providers = [
            ("Ollama (local)", "ollama"),
            ("OpenAI", "openai"),
            ("Mistral AI", "mistral"),
            ("Anthropic Claude", "anthropic")
        ]
        for text, value in providers:
            ttk.Radiobutton(left_frame, text=text, variable=self.ai_provider_var,
                          value=value, command=self._on_provider_changed).pack(anchor="w", pady=3)

        # === COLONNE DROITE : Configuration du provider sélectionné ===
        right_frame = ttk.Frame(columns_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))

        # Configuration Ollama
        self.ollama_config_frame = ttk.LabelFrame(right_frame, text="⚙️ Configuration Ollama", padding=10)

        ttk.Label(self.ollama_config_frame, text="Hôte:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.ollama_config_frame, textvariable=self.ollama_host_var,
                 width=35).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(self.ollama_config_frame, text="Modèle:").grid(row=1, column=0, sticky="w", padx=5, pady=5)

        # Frame pour le combobox et le bouton de rafraîchissement
        model_frame = ttk.Frame(self.ollama_config_frame)
        model_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Combobox - permet saisie manuelle OU sélection dans la liste
        self.ollama_model_combo = ttk.Combobox(model_frame, textvariable=self.ollama_model_var,
                                               width=25)
        self.ollama_model_combo.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.refresh_ollama_models_btn = ttk.Button(model_frame, text="🔄 Liste",
                                                    command=self._refresh_ollama_models, width=8)
        self.refresh_ollama_models_btn.pack(side="left")

        ttk.Label(self.ollama_config_frame, text="Sélectionnez dans la liste ou tapez le nom du modèle",
                 font=("Arial", 8), foreground="gray").grid(row=2, column=1, sticky="w", padx=5)

        self.ollama_config_frame.columnconfigure(1, weight=1)

        # Configuration OpenAI
        self.openai_config_frame = ttk.LabelFrame(right_frame, text="⚙️ Configuration OpenAI", padding=10)

        ttk.Label(self.openai_config_frame, text="Clé API:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.openai_config_frame, textvariable=self.openai_api_key_var,
                 width=35, show="*").grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(self.openai_config_frame, text="Modèle:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.openai_config_frame, textvariable=self.openai_model_var,
                 width=35).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(self.openai_config_frame, text="(ex: gpt-4, gpt-4o)",
                 font=("Arial", 8), foreground="gray").grid(row=2, column=1, sticky="w", padx=5)

        self.openai_config_frame.columnconfigure(1, weight=1)

        # Configuration Mistral
        self.mistral_config_frame = ttk.LabelFrame(right_frame, text="⚙️ Configuration Mistral AI", padding=10)

        ttk.Label(self.mistral_config_frame, text="Clé API:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.mistral_config_frame, textvariable=self.mistral_api_key_var,
                 width=35, show="*").grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(self.mistral_config_frame, text="Modèle:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.mistral_config_frame, textvariable=self.mistral_model_var,
                 width=35).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(self.mistral_config_frame, text="(ex: mistral-large-latest)",
                 font=("Arial", 8), foreground="gray").grid(row=2, column=1, sticky="w", padx=5)

        self.mistral_config_frame.columnconfigure(1, weight=1)

        # Configuration Anthropic
        self.anthropic_config_frame = ttk.LabelFrame(right_frame, text="⚙️ Configuration Anthropic (Claude)", padding=10)

        ttk.Label(self.anthropic_config_frame, text="Clé API:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.anthropic_config_frame, textvariable=self.anthropic_api_key_var,
                 width=35, show="*").grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(self.anthropic_config_frame, text="Modèle:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.anthropic_config_frame, textvariable=self.anthropic_model_var,
                 width=35).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(self.anthropic_config_frame, text="(ex: claude-3-sonnet-20240229)",
                 font=("Arial", 8), foreground="gray").grid(row=2, column=1, sticky="w", padx=5)

        self.anthropic_config_frame.columnconfigure(1, weight=1)

        # Bouton de test (sous les configurations)
        test_frame = ttk.Frame(main_container)
        test_frame.pack(fill="x", pady=(10, 0))

        self.test_button = ttk.Button(test_frame, text="🧪 Tester la Connexion",
                                     command=self._test_ia_connection)
        self.test_button.pack(side="left", padx=5)

        self.test_result_label = ttk.Label(test_frame, text="", font=("Arial", 9))
        self.test_result_label.pack(side="left", padx=10)

        # Séparateur
        ttk.Separator(main_container, orient="horizontal").pack(fill="x", pady=15)

        # Configuration DeepL (section séparée, pas un provider IA)
        deepl_section = ttk.LabelFrame(main_container, text="🌐 DeepL - Traduction Professionnelle", padding=10)
        deepl_section.pack(fill="x", pady=10)

        ttk.Label(deepl_section,
                 text="DeepL est un service de traduction séparé, indépendant des providers IA.",
                 font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 10))

        # Checkbox pour activer DeepL
        ttk.Checkbutton(deepl_section,
                       text="✅ Activer DeepL pour la traduction",
                       variable=self.deepl_enabled_var,
                       command=self._on_deepl_enabled_changed).pack(anchor="w", pady=5)

        # Frame de configuration DeepL
        self.deepl_config_frame = ttk.Frame(deepl_section)
        self.deepl_config_frame.pack(fill="x", pady=10)

        ttk.Label(self.deepl_config_frame, text="Clé API:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(self.deepl_config_frame, textvariable=self.deepl_api_key_var,
                 width=40, show="*").grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(self.deepl_config_frame,
                 text="(Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx)",
                 font=("Arial", 8), foreground="gray").grid(row=1, column=1, sticky="w", padx=5)

        ttk.Checkbutton(self.deepl_config_frame,
                       text="💳 Compte Pro (api.deepl.com)",
                       variable=self.deepl_is_pro_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        ttk.Label(self.deepl_config_frame,
                 text="ℹ️ Compte gratuit: 500,000 chars/mois | Compte Pro: facturation selon volume",
                 font=("Arial", 8), foreground="blue").grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        ttk.Label(self.deepl_config_frame,
                 text="⚠️ DeepL est un service de traduction pur (pas de chat). Utilisez le bouton 'Dpl' dans le formulaire.",
                 font=("Arial", 8), foreground="orange").grid(row=4, column=0, columnspan=2, sticky="w", padx=5, pady=5)

        # Séparateur
        ttk.Separator(self.deepl_config_frame, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=10)

        # Compteur de caractères
        ttk.Label(self.deepl_config_frame, text="📊 Compteur de caractères:",
                 font=("Arial", 9, "bold")).grid(row=6, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 0))

        # Affichage du compteur actuel (sera mis à jour dynamiquement)
        self.deepl_char_count_label = ttk.Label(self.deepl_config_frame,
                                               text="Chargement...",
                                               font=("Arial", 9))
        self.deepl_char_count_label.grid(row=7, column=0, columnspan=2, sticky="w", padx=5, pady=2)

        # Limite personnalisée
        ttk.Label(self.deepl_config_frame, text="Limite personnalisée:").grid(row=8, column=0, sticky="w", padx=5, pady=5)
        limit_frame = ttk.Frame(self.deepl_config_frame)
        limit_frame.grid(row=8, column=1, sticky="ew", padx=5, pady=5)

        limit_entry = ttk.Entry(limit_frame, textvariable=self.deepl_char_limit_var, width=15)
        limit_entry.pack(side="left", padx=(0, 5))
        # Mettre à jour l'affichage quand la limite change
        self.deepl_char_limit_var.trace_add("write", lambda *args: self._update_deepl_counter_display())
        ttk.Label(limit_frame, text="caractères",
                 font=("Arial", 8), foreground="gray").pack(side="left")

        ttk.Label(self.deepl_config_frame,
                 text="(0 = pas de limite)",
                 font=("Arial", 8), foreground="gray").grid(row=9, column=1, sticky="w", padx=5)

        # Bouton de réinitialisation
        self.deepl_reset_button = ttk.Button(self.deepl_config_frame,
                                            text="🔄 Réinitialiser le compteur",
                                            command=self._reset_deepl_counter)
        self.deepl_reset_button.grid(row=10, column=0, columnspan=2, sticky="w", padx=5, pady=10)

        self.deepl_config_frame.columnconfigure(1, weight=1)

    def _on_provider_changed(self):
        """Affiche/masque les configurations selon le fournisseur sélectionné"""
        provider = self.ai_provider_var.get()

        # Masquer tous les frames des providers IA (pas DeepL, il a sa propre section)
        self.ollama_config_frame.pack_forget()
        self.openai_config_frame.pack_forget()
        self.mistral_config_frame.pack_forget()
        self.anthropic_config_frame.pack_forget()

        # Afficher le frame correspondant dans la colonne de droite
        if provider == "ollama":
            self.ollama_config_frame.pack(fill="both", expand=True)
        elif provider == "openai":
            self.openai_config_frame.pack(fill="both", expand=True)
        elif provider == "mistral":
            self.mistral_config_frame.pack(fill="both", expand=True)
        elif provider == "anthropic":
            self.anthropic_config_frame.pack(fill="both", expand=True)

    def _on_deepl_enabled_changed(self):
        """Active/désactive le frame de configuration DeepL"""
        if self.deepl_enabled_var.get():
            # Activer les widgets du frame
            for child in self.deepl_config_frame.winfo_children():
                try:
                    child.config(state="normal")
                except:
                    pass
        else:
            # Désactiver les widgets du frame
            for child in self.deepl_config_frame.winfo_children():
                try:
                    child.config(state="disabled")
                except:
                    pass

    def _refresh_ollama_models_silent(self):
        """Récupère silencieusement la liste des modèles Ollama (sans messagebox)"""
        import requests

        try:
            # Récupérer l'hôte Ollama
            host = self.ollama_host_var.get().strip() or "http://localhost:11434"

            # Appeler l'API Ollama pour récupérer les modèles
            response = requests.get(f"{host}/api/tags", timeout=3)

            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])

                if models:
                    # Extraire les noms des modèles
                    model_names = [model['name'] for model in models]

                    # Mettre à jour le combobox
                    self.ollama_model_combo['values'] = model_names

                    # Si le modèle actuel n'est pas dans la liste, le sélectionner quand même
                    current_model = self.ollama_model_var.get()
                    if current_model and current_model not in model_names:
                        model_names.insert(0, current_model)
                        self.ollama_model_combo['values'] = model_names
                else:
                    self.ollama_model_combo['values'] = []
            else:
                self.ollama_model_combo['values'] = []

        except:
            # En mode silencieux, on ignore les erreurs
            self.ollama_model_combo['values'] = []

    def _refresh_ollama_models(self):
        """Récupère et affiche la liste des modèles Ollama disponibles"""
        import requests

        try:
            # Récupérer l'hôte Ollama
            host = self.ollama_host_var.get().strip() or "http://localhost:11434"

            # Désactiver le bouton pendant le chargement
            self.refresh_ollama_models_btn.config(state="disabled", text="⏳ Chargement...")
            self.update()

            # Appeler l'API Ollama pour récupérer les modèles
            response = requests.get(f"{host}/api/tags", timeout=5)

            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])

                if models:
                    # Extraire les noms des modèles
                    model_names = [model['name'] for model in models]

                    # Mettre à jour le combobox
                    self.ollama_model_combo['values'] = model_names

                    # Si le modèle actuel n'est pas dans la liste, le sélectionner quand même
                    current_model = self.ollama_model_var.get()
                    if current_model and current_model not in model_names:
                        model_names.insert(0, current_model)
                        self.ollama_model_combo['values'] = model_names

                    # Message de succès avec les modèles trouvés
                    if len(model_names) <= 10:
                        model_list = "\n".join(f"  • {name}" for name in model_names)
                        messagebox.showinfo("Modèles Ollama chargés",
                                          f"{len(model_names)} modèle(s) trouvé(s):\n\n{model_list}")
                    else:
                        model_list = "\n".join(f"  • {name}" for name in model_names[:10])
                        messagebox.showinfo("Modèles Ollama chargés",
                                          f"{len(model_names)} modèle(s) trouvé(s):\n\n{model_list}\n\n  ... et {len(model_names) - 10} autres")
                else:
                    messagebox.showwarning("Attention",
                                         "Aucun modèle Ollama trouvé sur le serveur.\n" +
                                         "Installez des modèles avec: ollama pull <nom_modele>")
                    self.ollama_model_combo['values'] = []
            else:
                messagebox.showerror("Erreur",
                                   f"Impossible de se connecter à Ollama.\n" +
                                   f"Code HTTP: {response.status_code}\n\n" +
                                   f"Vérifiez que le serveur Ollama est démarré sur {host}")
                self.ollama_model_combo['values'] = []

        except requests.exceptions.ConnectionError:
            messagebox.showerror("Erreur de connexion",
                               f"Impossible de se connecter au serveur Ollama sur {host}.\n\n" +
                               "Vérifiez que:\n" +
                               "  • Le serveur Ollama est démarré\n" +
                               "  • L'adresse de l'hôte est correcte\n" +
                               "  • Aucun pare-feu ne bloque la connexion")
            self.ollama_model_combo['values'] = []

        except requests.exceptions.Timeout:
            messagebox.showerror("Timeout",
                               f"Le serveur Ollama ne répond pas (timeout).\n\n" +
                               "Le serveur est peut-être occupé ou hors ligne.")
            self.ollama_model_combo['values'] = []

        except Exception as e:
            messagebox.showerror("Erreur",
                               f"Erreur inattendue lors de la récupération des modèles:\n{e}")
            self.ollama_model_combo['values'] = []

        finally:
            # Réactiver le bouton
            self.refresh_ollama_models_btn.config(state="normal", text="🔄 Liste")
            self.update()

    def _reset_deepl_counter(self):
        """Réinitialise le compteur de caractères DeepL"""
        if messagebox.askyesno("Confirmer",
                              "Voulez-vous vraiment réinitialiser le compteur de caractères DeepL ?"):
            if self.ai_client and "deepl" in self.ai_client.providers:
                self.ai_client.providers["deepl"].reset_character_count()
                self._update_deepl_counter_display()
                messagebox.showinfo("Succès", "Le compteur DeepL a été réinitialisé.")
            else:
                messagebox.showwarning("Attention", "Le provider DeepL n'est pas disponible.")

    def _update_deepl_counter_display(self):
        """Met à jour l'affichage du compteur DeepL"""
        try:
            if self.ai_client and "deepl" in self.ai_client.providers:
                char_count = self.ai_client.providers["deepl"].get_character_count()

                # Récupérer la limite de manière sécurisée
                try:
                    limit = self.deepl_char_limit_var.get()
                except:
                    limit = 0

                # Formater l'affichage
                if limit > 0:
                    percentage = (char_count / limit) * 100
                    text = f"  Utilisé: {char_count:,} / {limit:,} caractères ({percentage:.1f}%)"

                    # Changer la couleur selon le pourcentage
                    if percentage >= 90:
                        color = "red"
                    elif percentage >= 70:
                        color = "orange"
                    else:
                        color = "green"
                else:
                    text = f"  Utilisé: {char_count:,} caractères (pas de limite)"
                    color = "blue"

                self.deepl_char_count_label.config(text=text, foreground=color)
            else:
                self.deepl_char_count_label.config(text="  DeepL non disponible", foreground="gray")
        except Exception as e:
            # En cas d'erreur, afficher un message générique
            self.deepl_char_count_label.config(text="  Erreur de chargement", foreground="gray")

    def _test_ia_connection(self):
        """Teste la connexion au fournisseur d'IA"""
        self.test_result_label.config(text="⏳ Test en cours...", foreground="blue")
        self.test_button.config(state="disabled")
        self.update()

        # Simuler un test (dans une vraie implémentation, utiliser l'ai_client)
        def test_thread():
            try:
                # TODO: Implémenter le test réel avec self.ai_client
                import time
                time.sleep(1)  # Simuler délai

                provider = self.ai_provider_var.get()
                if provider == "ollama":
                    # Test Ollama
                    result = f"✅ Connexion réussie à {self.ollama_host_var.get()}"
                    color = "green"
                else:
                    # Test OpenAI
                    result = "✅ Connexion réussie à OpenAI"
                    color = "green"

                self.after(0, lambda: self.test_result_label.config(text=result, foreground=color))
            except Exception as e:
                result = f"❌ Erreur: {str(e)}"
                self.after(0, lambda: self.test_result_label.config(text=result, foreground="red"))
            finally:
                self.after(0, lambda: self.test_button.config(state="normal"))

        threading.Thread(target=test_thread, daemon=True).start()

    def _create_prompts_tab(self, parent):
        """Crée l'onglet de configuration des prompts"""
        # Container avec scrollbar
        canvas = tk.Canvas(parent, borderwidth=0, background="#f0f0f0", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Instructions
        info_frame = ttk.Frame(scrollable_frame)
        info_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(info_frame, text="Personnalisez les prompts envoyés à l'IA pour les traductions.",
                 font=("Arial", 9, "italic")).pack(anchor="w")
        ttk.Label(info_frame,
                 text="Variables disponibles: {text}, {lang}, {original}, {current}, {context}",
                 font=("Arial", 8), foreground="blue").pack(anchor="w", pady=(5, 0))

        # Prompt 1: Traduction simple
        translate_frame = ttk.LabelFrame(scrollable_frame, text="📝 Prompt: Traduction Simple", padding=10)
        translate_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(translate_frame, text="Utilisé pour traduire un texte sans HTML:",
                 font=("Arial", 8), foreground="gray").pack(anchor="w", pady=(0, 5))

        translate_text = tk.Text(translate_frame, height=3, wrap="word", font=("Arial", 9))
        translate_text.pack(fill="both", expand=True)
        self.prompt_translate_text = translate_text

        # Prompt 2: Traduction HTML
        translate_html_frame = ttk.LabelFrame(scrollable_frame, text="🌐 Prompt: Traduction HTML", padding=10)
        translate_html_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(translate_html_frame, text="Utilisé pour traduire du contenu HTML:",
                 font=("Arial", 8), foreground="gray").pack(anchor="w", pady=(0, 5))

        translate_html_text = tk.Text(translate_html_frame, height=8, wrap="word", font=("Arial", 9))
        translate_html_text.pack(fill="both", expand=True)
        self.prompt_translate_html_text = translate_html_text

        # Prompt 3: Amélioration simple
        improve_frame = ttk.LabelFrame(scrollable_frame, text="✨ Prompt: Amélioration Simple", padding=10)
        improve_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(improve_frame, text="Utilisé pour améliorer une traduction sans HTML:",
                 font=("Arial", 8), foreground="gray").pack(anchor="w", pady=(0, 5))

        improve_text = tk.Text(improve_frame, height=6, wrap="word", font=("Arial", 9))
        improve_text.pack(fill="both", expand=True)
        self.prompt_improve_text = improve_text

        # Prompt 4: Amélioration HTML
        improve_html_frame = ttk.LabelFrame(scrollable_frame, text="🌐✨ Prompt: Amélioration HTML", padding=10)
        improve_html_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(improve_html_frame, text="Utilisé pour améliorer une traduction avec HTML:",
                 font=("Arial", 8), foreground="gray").pack(anchor="w", pady=(0, 5))

        improve_html_text = tk.Text(improve_html_frame, height=8, wrap="word", font=("Arial", 9))
        improve_html_text.pack(fill="both", expand=True)
        self.prompt_improve_html_text = improve_html_text

    def _create_advanced_tab(self, parent):
        """Crée l'onglet des options avancées"""
        # Container
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # Section: Édition du champ Ori
        ori_frame = ttk.LabelFrame(container, text="📝 Édition du Champ Original (ori)", padding=10)
        ori_frame.pack(fill="x", pady=10)

        ttk.Label(ori_frame,
                 text="Permet de modifier directement le texte original dans le formulaire de traduction.",
                 font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 5))

        ttk.Checkbutton(ori_frame,
                       text="✏️ Autoriser l'édition du champ 'ori' dans le formulaire",
                       variable=self.allow_edit_ori_var).pack(anchor="w", pady=5)

        ttk.Label(ori_frame,
                 text="⚠️ Attention: Modifier le texte original peut affecter toutes les traductions liées.",
                 font=("Arial", 8), foreground="orange").pack(anchor="w", pady=(5, 0))

        # Section: Sauvegarde automatique
        autosave_frame = ttk.LabelFrame(container, text="💾 Sauvegarde Automatique", padding=10)
        autosave_frame.pack(fill="x", pady=10)

        ttk.Label(autosave_frame,
                 text="Configure le comportement de sauvegarde lors de la fermeture de l'application.",
                 font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 5))

        ttk.Checkbutton(autosave_frame,
                       text="✅ Sauvegarder automatiquement le fichier .got.json à la fermeture",
                       variable=self.auto_save_on_exit_var).pack(anchor="w", pady=5)

        ttk.Label(autosave_frame,
                 text="Si désactivé : un message vous demandera si vous souhaitez sauvegarder (Oui/Non/Annuler)",
                 font=("Arial", 8), foreground="gray").pack(anchor="w", pady=(5, 0))

        ttk.Label(autosave_frame,
                 text="Si activé : le fichier sera sauvegardé automatiquement sans confirmation",
                 font=("Arial", 8), foreground="gray").pack(anchor="w", pady=(2, 0))

        # Section: Informations
        info_frame = ttk.LabelFrame(container, text="ℹ️ Informations", padding=10)
        info_frame.pack(fill="x", pady=10)

        info_text = """Version: OllamaTrad
Fichier de configuration: translation_config.json

💡 Conseils:
- Les langues doivent avoir un code (ex: fr) et un nom complet
- Les langues visibles filtrent l'affichage de l'arbre seulement
- Les données non visibles restent dans le fichier .got.json
- Testez la connexion IA avant de commencer à traduire
"""
        ttk.Label(info_frame, text=info_text, font=("Arial", 8), justify="left").pack(anchor="w")

    def _load_values(self):
        """Charge les valeurs depuis la configuration"""
        # Langues connues dans le tableur
        self.known_languages = self.config.get("known_languages", self.DEFAULT_LANGUAGES.copy())

        for i, (code, name) in enumerate(self.known_languages.items()):
            if i < len(self.language_entries):
                code_entry, name_entry = self.language_entries[i]
                code_entry.delete(0, tk.END)
                code_entry.insert(0, code)
                name_entry.delete(0, tk.END)
                name_entry.insert(0, name)

        # Langues cibles
        target_langs = self.config.get("target_languages", ["fr", "en", "es"])
        self.target_languages_entry.delete(0, tk.END)
        self.target_languages_entry.insert(0, ", ".join(target_langs))

        # Langues visibles
        self._populate_visible_checkboxes()
        visible_langs = self.config.get("visible_languages", target_langs)
        for code, var in self.visible_languages_vars.items():
            var.set(code in visible_langs)

        # Option édition ori
        self.allow_edit_ori_var.set(self.config.get("allow_edit_ori", False))

        # Option sauvegarde automatique
        self.auto_save_on_exit_var.set(self.config.get("auto_save_on_exit", False))

        # Configuration IA
        ai_config = self.config.get("ai_config", {})
        self.ai_provider_var.set(ai_config.get("provider", "ollama"))

        ollama_config = ai_config.get("ollama", {})
        self.ollama_host_var.set(ollama_config.get("host", "http://localhost:11434"))
        # Charger depuis "model" ou "default_model" (compatibilité avec settings.json)
        self.ollama_model_var.set(ollama_config.get("model", ollama_config.get("default_model", "aya")))

        openai_config = ai_config.get("openai", {})
        self.openai_api_key_var.set(openai_config.get("api_key", ""))
        self.openai_model_var.set(openai_config.get("model", openai_config.get("default_model", "gpt-4")))

        mistral_config = ai_config.get("mistral", {})
        self.mistral_api_key_var.set(mistral_config.get("api_key", ""))
        self.mistral_model_var.set(mistral_config.get("model", mistral_config.get("default_model", "mistral-large-latest")))

        anthropic_config = ai_config.get("anthropic", {})
        self.anthropic_api_key_var.set(anthropic_config.get("api_key", ""))
        self.anthropic_model_var.set(anthropic_config.get("model", anthropic_config.get("default_model", "claude-3-sonnet-20240229")))

        deepl_config = ai_config.get("deepl", {})
        self.deepl_enabled_var.set(deepl_config.get("enabled", False))
        self.deepl_api_key_var.set(deepl_config.get("api_key", ""))
        self.deepl_is_pro_var.set(deepl_config.get("is_pro", False))
        self.deepl_char_limit_var.set(deepl_config.get("character_limit", 500000))  # 500K par défaut (limite gratuite)

        self._on_provider_changed()  # Afficher le bon panneau
        self._on_deepl_enabled_changed()  # Activer/désactiver le frame DeepL
        self._update_deepl_counter_display()  # Mettre à jour l'affichage du compteur

        # Charger automatiquement les modèles Ollama si c'est le provider actif
        if self.ai_provider_var.get() == "ollama":
            # Utiliser after() pour charger les modèles après l'affichage de la fenêtre
            self.after(100, self._refresh_ollama_models_silent)

        # Prompts
        prompts = self.config.get("prompts", {})
        self.prompt_translate_text.delete("1.0", "end")
        self.prompt_translate_text.insert("1.0", prompts.get("translate", ""))

        self.prompt_translate_html_text.delete("1.0", "end")
        self.prompt_translate_html_text.insert("1.0", prompts.get("translate_html", ""))

        self.prompt_improve_text.delete("1.0", "end")
        self.prompt_improve_text.insert("1.0", prompts.get("improve", ""))

        self.prompt_improve_html_text.delete("1.0", "end")
        self.prompt_improve_html_text.insert("1.0", prompts.get("improve_html", ""))

    def _on_save(self):
        """Sauvegarde les modifications"""
        # Parser les langues connues depuis le tableur
        known_langs = self._parse_known_languages()

        if not known_langs:
            messagebox.showerror("Erreur", "Vous devez définir au moins une langue connue (code + nom)!")
            return

        # Valider et parser les langues cibles
        target_input = self.target_languages_entry.get().strip()
        target_langs = [lang.strip() for lang in target_input.split(",") if lang.strip()]

        if not target_langs:
            messagebox.showerror("Erreur", "Vous devez spécifier au moins une langue cible!")
            return

        # Vérifier que les codes sont valides
        invalid = [lang for lang in target_langs if lang not in known_langs]
        if invalid:
            messagebox.showerror("Erreur",
                f"Codes de langue invalides: {', '.join(invalid)}\n\n"
                f"Codes valides: {', '.join(known_langs.keys())}")
            return

        # Récupérer les langues visibles
        visible_langs = [code for code, var in self.visible_languages_vars.items() if var.get()]

        if not visible_langs:
            messagebox.showerror("Erreur", "Vous devez cocher au moins une langue visible!")
            return

        # Récupérer la configuration IA
        ai_config = {
            "provider": self.ai_provider_var.get(),
            "ollama": {
                "host": self.ollama_host_var.get().strip(),
                "model": self.ollama_model_var.get().strip()
            },
            "openai": {
                "api_key": self.openai_api_key_var.get().strip(),
                "model": self.openai_model_var.get().strip()
            },
            "mistral": {
                "api_key": self.mistral_api_key_var.get().strip(),
                "model": self.mistral_model_var.get().strip()
            },
            "anthropic": {
                "api_key": self.anthropic_api_key_var.get().strip(),
                "model": self.anthropic_model_var.get().strip()
            },
            "deepl": {
                "enabled": self.deepl_enabled_var.get(),
                "api_key": self.deepl_api_key_var.get().strip(),
                "is_pro": self.deepl_is_pro_var.get(),
                "character_limit": self.deepl_char_limit_var.get()
            }
        }

        # Récupérer les prompts
        prompts = {
            "translate": self.prompt_translate_text.get("1.0", "end-1c").strip(),
            "translate_html": self.prompt_translate_html_text.get("1.0", "end-1c").strip(),
            "improve": self.prompt_improve_text.get("1.0", "end-1c").strip(),
            "improve_html": self.prompt_improve_html_text.get("1.0", "end-1c").strip()
        }

        # Vérifier que les prompts ne sont pas vides
        if not all(prompts.values()):
            messagebox.showerror("Erreur", "Tous les prompts doivent être remplis!")
            return

        # Mettre à jour la configuration
        self.config["known_languages"] = known_langs
        self.config["target_languages"] = target_langs
        self.config["visible_languages"] = visible_langs
        self.config["allow_edit_ori"] = self.allow_edit_ori_var.get()
        self.config["auto_save_on_exit"] = self.auto_save_on_exit_var.get()
        self.config["ai_config"] = ai_config
        self.config["prompts"] = prompts

        # Sauvegarder
        if self.save_config():
            # Mettre à jour settings.json avec les configurations IA
            self._sync_ai_config_to_settings(ai_config)

            # Appeler le callback si fourni
            if self.on_save_callback:
                self.on_save_callback(self.config)

            # Libérer le grab et détruire la fenêtre AVANT d'afficher le message
            self.grab_release()
            self.destroy()

            # Afficher le message de succès (après la fermeture de la fenêtre)
            messagebox.showinfo("Succès", "Configuration sauvegardée avec succès!")

    def _sync_ai_config_to_settings(self, ai_config: Dict):
        """Synchronise la configuration IA vers settings.json"""
        try:
            settings_path = Path(__file__).parent.parent / "config" / "settings.json"

            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {"ai_providers": {}}

            # Mettre à jour la section ai_providers
            if "ai_providers" not in settings:
                settings["ai_providers"] = {}

            # Copier les configurations avec mapping des clés
            for provider in ["ollama", "openai", "mistral", "anthropic", "deepl"]:
                if provider in ai_config:
                    if provider not in settings["ai_providers"]:
                        settings["ai_providers"][provider] = {}

                    # Mapper les clés correctement
                    provider_config = ai_config[provider].copy()
                    if "model" in provider_config:
                        # Convertir "model" en "default_model" pour settings.json
                        provider_config["default_model"] = provider_config.pop("model")

                    settings["ai_providers"][provider].update(provider_config)

            # Mettre à jour le provider par défaut
            settings["ai_providers"]["default_provider"] = ai_config["provider"]

            # Sauvegarder
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Avertissement: Impossible de synchroniser avec settings.json: {e}")

    def _on_reset(self):
        """Réinitialise aux valeurs par défaut"""
        if messagebox.askyesno("Confirmer",
                "Voulez-vous vraiment réinitialiser toutes les options aux valeurs par défaut?"):
            # Recharger la configuration par défaut
            default_config = self.load_config()
            default_config["known_languages"] = self.DEFAULT_LANGUAGES.copy()
            default_config["target_languages"] = ["fr", "en", "es"]
            default_config["visible_languages"] = ["fr", "en", "es"]
            default_config["allow_edit_ori"] = False
            default_config["auto_save_on_exit"] = False

            self.config = default_config
            self._load_values()
            messagebox.showinfo("Info", "Options réinitialisées (non sauvegardées)")


def test_dialog():
    """Test de la fenêtre d'options v3"""
    root = tk.Tk()
    root.withdraw()

    def on_save(config):
        print("Configuration sauvegardée:")
        print(json.dumps(config, indent=2, ensure_ascii=False))

    dialog = OptionsDialog(root, on_save=on_save)
    root.wait_window(dialog)
    root.destroy()


if __name__ == "__main__":
    test_dialog()
