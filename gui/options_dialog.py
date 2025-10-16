# -*- coding: utf-8 -*-
"""
Fenêtre d'options pour OllamaFic v2.0

Permet de configurer:
- Langues connues (code + nom complet)
- Langues cibles (ordre de traduction)
- Langues visibles (filtrage de l'affichage)
- Prompts de traduction personnalisables
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Callable, Optional
import json
from pathlib import Path


class OptionsDialog(tk.Toplevel):
    """Fenêtre de configuration des options de traduction"""

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
                 on_save: Optional[Callable] = None):
        """
        Args:
            parent: Fenêtre parente
            config_path: Chemin vers le fichier de configuration
            on_save: Callback appelé après sauvegarde (config_dict)
        """
        super().__init__(parent)

        self.title("Options - OllamaFic v2.0")
        self.geometry("900x700")
        self.resizable(True, True)

        self.config_path = config_path or Path(__file__).parent.parent / "config" / "translation_config.json"
        self.on_save_callback = on_save

        # Charger la configuration
        self.config = self.load_config()

        # Variables pour les widgets
        self.known_languages = {}  # code -> nom
        self.target_languages_var = tk.StringVar()
        self.visible_languages_vars = {}  # code -> BooleanVar
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

        # Onglet 2: Prompts
        prompts_frame = ttk.Frame(notebook)
        notebook.add(prompts_frame, text="💬 Prompts de Traduction")
        self._create_prompts_tab(prompts_frame)

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
        """Crée l'onglet de configuration des langues"""
        # Container avec scrollbar
        canvas = tk.Canvas(parent, borderwidth=0, background="#f0f0f0")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Section 1: Langues connues
        known_frame = ttk.LabelFrame(scrollable_frame, text="📚 Langues Connues", padding=10)
        known_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(known_frame, text="Liste des langues disponibles pour la traduction:",
                 font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 5))

        # Grille des langues connues
        known_grid = ttk.Frame(known_frame)
        known_grid.pack(fill="both", expand=True)

        ttk.Label(known_grid, text="Code", font=("Arial", 9, "bold")).grid(
            row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Label(known_grid, text="Nom", font=("Arial", 9, "bold")).grid(
            row=0, column=1, padx=5, pady=2, sticky="w")

        self.known_languages_widgets = []
        for i, (code, name) in enumerate(self.DEFAULT_LANGUAGES.items(), start=1):
            code_label = ttk.Label(known_grid, text=code, foreground="blue")
            code_label.grid(row=i, column=0, padx=5, pady=2, sticky="w")

            name_label = ttk.Label(known_grid, text=name)
            name_label.grid(row=i, column=1, padx=5, pady=2, sticky="w")

            self.known_languages_widgets.append((code, name))

        # Section 2: Langues cibles
        target_frame = ttk.LabelFrame(scrollable_frame, text="🎯 Langues Cibles (Ordre de Traduction)", padding=10)
        target_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(target_frame,
                 text="Saisissez les codes de langues séparés par des virgules (ex: fr, en, es):",
                 font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 5))

        target_entry = ttk.Entry(target_frame, textvariable=self.target_languages_var,
                                font=("Arial", 10))
        target_entry.pack(fill="x", pady=5)

        ttk.Label(target_frame,
                 text="Ces langues apparaîtront dans le formulaire de traduction.",
                 font=("Arial", 8), foreground="gray").pack(anchor="w")

        # Section 3: Langues visibles
        visible_frame = ttk.LabelFrame(scrollable_frame, text="👁️ Langues Visibles (Filtrage)", padding=10)
        visible_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(visible_frame,
                 text="Cochez les langues à afficher pour le fichier actuel:",
                 font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 5))

        ttk.Label(visible_frame,
                 text="Note: Les données des langues non cochées restent dans le .got.json mais ne s'affichent pas.",
                 font=("Arial", 8), foreground="orange").pack(anchor="w", pady=(0, 10))

        # Grille de checkboxes pour langues visibles
        visible_grid = ttk.Frame(visible_frame)
        visible_grid.pack(fill="both")

        for i, (code, name) in enumerate(self.DEFAULT_LANGUAGES.items()):
            var = tk.BooleanVar(value=True)
            self.visible_languages_vars[code] = var

            cb = ttk.Checkbutton(visible_grid, text=f"{code} ({name})", variable=var)
            cb.grid(row=i // 3, column=i % 3, sticky="w", padx=10, pady=3)

    def _create_prompts_tab(self, parent):
        """Crée l'onglet de configuration des prompts"""
        # Container avec scrollbar
        canvas = tk.Canvas(parent, borderwidth=0, background="#f0f0f0")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

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

    def _load_values(self):
        """Charge les valeurs depuis la configuration"""
        # Langues connues (affichage seulement, pas modifiable pour l'instant)
        self.known_languages = self.config.get("known_languages", self.DEFAULT_LANGUAGES.copy())

        # Langues cibles
        target_langs = self.config.get("target_languages", ["fr", "en", "es"])
        self.target_languages_var.set(", ".join(target_langs))

        # Langues visibles
        visible_langs = self.config.get("visible_languages", target_langs)
        for code, var in self.visible_languages_vars.items():
            var.set(code in visible_langs)

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
        # Valider et parser les langues cibles
        target_input = self.target_languages_var.get().strip()
        target_langs = [lang.strip() for lang in target_input.split(",") if lang.strip()]

        if not target_langs:
            messagebox.showerror("Erreur", "Vous devez spécifier au moins une langue cible!")
            return

        # Vérifier que les codes sont valides
        invalid = [lang for lang in target_langs if lang not in self.known_languages]
        if invalid:
            messagebox.showerror("Erreur",
                f"Codes de langue invalides: {', '.join(invalid)}\n\n"
                f"Codes valides: {', '.join(self.known_languages.keys())}")
            return

        # Récupérer les langues visibles
        visible_langs = [code for code, var in self.visible_languages_vars.items() if var.get()]

        if not visible_langs:
            messagebox.showerror("Erreur", "Vous devez cocher au moins une langue visible!")
            return

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
        self.config["known_languages"] = self.known_languages
        self.config["target_languages"] = target_langs
        self.config["visible_languages"] = visible_langs
        self.config["prompts"] = prompts

        # Sauvegarder
        if self.save_config():
            messagebox.showinfo("Succès", "Configuration sauvegardée avec succès!")

            # Appeler le callback si fourni
            if self.on_save_callback:
                self.on_save_callback(self.config)

            self.destroy()

    def _on_reset(self):
        """Réinitialise aux valeurs par défaut"""
        if messagebox.askyesno("Confirmer",
                "Voulez-vous vraiment réinitialiser toutes les options aux valeurs par défaut?"):
            self.config = self.load_config()
            self.config = {
                "known_languages": self.DEFAULT_LANGUAGES.copy(),
                "target_languages": ["fr", "en", "es"],
                "visible_languages": ["fr", "en", "es"],
                "prompts": self.config["prompts"]  # Garder les prompts par défaut du load_config
            }
            self._load_values()
            messagebox.showinfo("Info", "Options réinitialisées (non sauvegardées)")


def test_dialog():
    """Test de la fenêtre d'options"""
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
