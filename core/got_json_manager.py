"""
Gestionnaire du format .got.json enrichi avec historique et validation.

Ce module gère la transformation des fichiers JSON standards vers le format
.got.json enrichi qui supporte:
- Historique des traductions
- État de validation par langue
- Métadonnées de version et correspondance
"""

import json
import json5
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class GotJsonManager:
    """
    Gestionnaire du format .got.json enrichi avec historique et validation.

    Le format .got.json transforme les strings traduisibles en objets structurés:

    Avant (JSON):
        {"title": "Hello"}

    Après (.got.json):
        {
            "__ollamafic__": {...},
            "title": {
                "ori": "Hello",
                "fr": {"text": "Bonjour", "history": [], "valid": true}
            }
        }
    """

    VERSION = "2.0"

    def __init__(self, target_languages: List[str] = None):
        """
        Args:
            target_languages: Liste des langues cibles (ex: ["fr", "es", "de"])
                             Par défaut: ["fr"]
        """
        self.target_languages = target_languages or ["fr"]
        self.data = None
        self.original_filename = None
        self.filepath = None

    # === VALIDATION ===

    def is_valid_got_json(self, data: Dict) -> bool:
        """
        Vérifie si un dict est un .got.json valide.

        Returns:
            True si le dict contient __ollamafic__ avec version et original_file
        """
        if not isinstance(data, dict):
            return False

        if "__ollamafic__" not in data:
            return False

        header = data["__ollamafic__"]
        return (
            "version" in header and
            "original_file" in header and
            header["version"] == self.VERSION
        )

    def validate_correspondence(self, got_data: Dict, json_filename: str) -> bool:
        """
        Vérifie que le .got.json correspond au .json source.

        Args:
            got_data: Données du fichier .got.json
            json_filename: Nom du fichier .json source (ex: "messages.json")

        Returns:
            True si original_file correspond
        """
        if not self.is_valid_got_json(got_data):
            return False

        return got_data["__ollamafic__"]["original_file"] == json_filename

    # === TRANSFORMATION ===

    def is_translatable(self, value: Any) -> bool:
        """
        Détermine si une valeur doit être transformée en objet traduisible.

        Returns:
            True pour les strings non vides, False sinon
        """
        return isinstance(value, str) and len(value.strip()) > 0

    def create_translation_object(self, original_text: str) -> Dict:
        """
        Crée un objet de traduction vide pour toutes les langues cibles.

        Args:
            original_text: Texte original

        Returns:
            {
                "ori": "...",
                "fr": {"text": "", "history": [], "valid": false},
                ...
            }
        """
        result = {"ori": original_text}

        for lang in self.target_languages:
            result[lang] = {
                "text": "",
                "history": [],
                "valid": False
            }

        return result

    def transform_value(self, value: Any) -> Any:
        """
        Transforme récursivement une valeur JSON en format .got.json.

        Args:
            value: Valeur à transformer

        Returns:
            Valeur transformée
        """
        # String traduisible → objet de traduction
        if self.is_translatable(value):
            return self.create_translation_object(value)

        # Dict → transformation récursive
        elif isinstance(value, dict):
            return {
                key: self.transform_value(val)
                for key, val in value.items()
            }

        # List → transformation récursive
        elif isinstance(value, list):
            return [self.transform_value(item) for item in value]

        # Autres types → inchangé
        else:
            return value

    def create_from_json(self, json_data: Dict, original_filename: str) -> Dict:
        """
        Crée un .got.json complet à partir d'un JSON source.

        Args:
            json_data: Données du fichier .json
            original_filename: Nom du fichier source (ex: "messages.json")

        Returns:
            Dict au format .got.json
        """
        now = datetime.now().isoformat()

        # Créer le header
        got_data = {
            "__ollamafic__": {
                "version": self.VERSION,
                "original_file": original_filename,
                "created": now,
                "last_modified": now
            }
        }

        # Transformer le contenu
        for key, value in json_data.items():
            got_data[key] = self.transform_value(value)

        self.data = got_data
        self.original_filename = original_filename
        return got_data

    # === GESTION DES TRADUCTIONS ===

    def update_translation(self, path: str, lang: str, new_text: str) -> None:
        """
        Met à jour une traduction avec gestion de l'historique.

        Args:
            path: Chemin vers l'entrée (ex: "app/title")
            lang: Code langue (ex: "fr")
            new_text: Nouveau texte
        """
        entry = self._get_entry_by_path(path)

        if lang not in entry or lang == "ori":
            raise ValueError(f"Langue invalide: {lang}")

        # Sauvegarder l'ancienne version dans history
        current_text = entry[lang]["text"]
        if current_text != "":
            entry[lang]["history"].insert(0, current_text)

        # Limiter l'historique à 10 entrées
        if len(entry[lang]["history"]) > 10:
            entry[lang]["history"] = entry[lang]["history"][:10]

        # Mettre à jour
        entry[lang]["text"] = new_text
        entry[lang]["valid"] = False  # Invalider automatiquement

        # Mettre à jour last_modified
        self.data["__ollamafic__"]["last_modified"] = datetime.now().isoformat()

    def rollback_translation(self, path: str, lang: str) -> Optional[str]:
        """
        Retour en arrière vers la version précédente de l'historique.

        Args:
            path: Chemin vers l'entrée
            lang: Code langue

        Returns:
            Le texte restauré, ou None si pas d'historique
        """
        entry = self._get_entry_by_path(path)

        if lang not in entry or lang == "ori":
            raise ValueError(f"Langue invalide: {lang}")

        if len(entry[lang]["history"]) == 0:
            return None

        # Sauvegarder l'actuel
        current = entry[lang]["text"]

        # Restaurer l'avant-dernier
        entry[lang]["text"] = entry[lang]["history"].pop(0)

        # Ajouter l'actuel à la fin de l'historique
        entry[lang]["history"].append(current)

        # Mettre à jour last_modified
        self.data["__ollamafic__"]["last_modified"] = datetime.now().isoformat()

        return entry[lang]["text"]

    def validate_translation(self, path: str, lang: str, valid: bool) -> None:
        """
        Change l'état de validation d'une traduction.

        Args:
            path: Chemin vers l'entrée
            lang: Code langue
            valid: État de validation
        """
        entry = self._get_entry_by_path(path)

        if lang not in entry or lang == "ori":
            raise ValueError(f"Langue invalide: {lang}")

        entry[lang]["valid"] = valid
        self.data["__ollamafic__"]["last_modified"] = datetime.now().isoformat()

    # === ÉTAT DE VALIDATION ===

    def get_validation_state(self, path: str) -> str:
        """
        Calcule l'état de validation d'une entrée.

        Returns:
            "green": Toutes validées
            "orange": Partiellement validées
            "red": Aucune validée ou traductions non vides non validées
            "none": Pas de traductions
        """
        entry = self._get_entry_by_path(path)

        if not isinstance(entry, dict) or "ori" not in entry:
            return "none"

        states = []
        has_any_text = False

        for lang in self.target_languages:
            if lang in entry:
                lang_data = entry[lang]
                if lang_data["text"] != "":
                    has_any_text = True
                    states.append(lang_data["valid"])

        # Si aucune traduction n'existe, c'est "none" (noir)
        if not has_any_text:
            return "none"

        # Si au moins une traduction existe
        if len(states) == 0:
            return "none"  # Cas bizarre, mais sécurité

        if all(states):
            return "green"   # Toutes les traductions sont validées
        elif any(states):
            return "orange"  # Certaines validées, d'autres non
        else:
            return "red"     # Aucune traduction validée (mais texte existe)

    def get_translation_stats(self) -> Dict[str, Any]:
        """
        Calcule des statistiques globales sur les traductions.

        Returns:
            {
                "total_entries": 150,
                "by_language": {
                    "fr": {"translated": 120, "validated": 80, "percentage": 80.0},
                    "es": {"translated": 50, "validated": 30, "percentage": 33.3}
                },
                "validation_states": {
                    "green": 45,
                    "orange": 30,
                    "red": 25,
                    "none": 50
                }
            }
        """
        stats = {
            "total_entries": 0,
            "by_language": {},
            "validation_states": {
                "green": 0,
                "orange": 0,
                "red": 0,
                "none": 0
            }
        }

        # Initialiser les stats par langue
        for lang in self.target_languages:
            stats["by_language"][lang] = {
                "translated": 0,
                "validated": 0,
                "percentage": 0.0
            }

        # Parcourir toutes les entrées
        paths = self.get_all_translatable_paths()
        stats["total_entries"] = len(paths)

        for path in paths:
            entry = self._get_entry_by_path(path)

            # États de validation
            state = self.get_validation_state(path)
            stats["validation_states"][state] += 1

            # Stats par langue
            for lang in self.target_languages:
                if lang in entry:
                    lang_data = entry[lang]
                    if lang_data["text"] != "":
                        stats["by_language"][lang]["translated"] += 1
                        if lang_data["valid"]:
                            stats["by_language"][lang]["validated"] += 1

        # Calculer les pourcentages
        if stats["total_entries"] > 0:
            for lang in self.target_languages:
                translated = stats["by_language"][lang]["translated"]
                stats["by_language"][lang]["percentage"] = (
                    translated / stats["total_entries"] * 100
                )

        return stats

    def get_all_translatable_paths(self) -> List[str]:
        """
        Liste tous les chemins vers des entrées traduisibles.

        Returns:
            ["app/title", "app/settings/theme", ...]
        """
        paths = []

        def traverse(obj, current_path=""):
            if isinstance(obj, dict):
                # Vérifier si c'est une entrée traduisible
                if "ori" in obj and isinstance(obj.get("ori"), str):
                    paths.append(current_path.strip("/"))
                else:
                    for key, value in obj.items():
                        if key != "__ollamafic__":  # Ignorer le header
                            new_path = f"{current_path}/{key}"
                            traverse(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    traverse(item, f"{current_path}[{i}]")

        if self.data:
            traverse(self.data)

        return paths

    # === HELPERS ===

    def _get_entry_by_path(self, path: str) -> Dict:
        """
        Récupère une entrée par son chemin.

        Args:
            path: Chemin séparé par / (ex: "app/settings/theme")

        Returns:
            Dict de l'entrée
        """
        if not self.data:
            raise ValueError("Aucune donnée chargée")

        parts = path.strip("/").split("/")
        current = self.data

        for part in parts:
            # Gérer les index de liste [n]
            if "[" in part and "]" in part:
                key, index = part.split("[")
                index = int(index.rstrip("]"))
                if key:
                    current = current[key]
                current = current[index]
            else:
                if part in current:
                    current = current[part]
                else:
                    raise KeyError(f"Chemin invalide: {path}")

        return current

    # === SAUVEGARDE/CHARGEMENT ===

    def load_from_file(self, filepath: str) -> Dict:
        """
        Charge un fichier .got.json.

        Args:
            filepath: Chemin du fichier

        Returns:
            Données chargées
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            self.data = json5.load(f)

        self.filepath = filepath

        if self.is_valid_got_json(self.data):
            self.original_filename = self.data["__ollamafic__"]["original_file"]

        return self.data

    def save_to_file(self, filepath: str = None) -> None:
        """
        Sauvegarde le .got.json.

        Args:
            filepath: Chemin de destination (optionnel)
        """
        if filepath is None:
            filepath = self.filepath

        if filepath is None:
            raise ValueError("Aucun chemin de fichier spécifié")

        # Mettre à jour last_modified
        if self.data and "__ollamafic__" in self.data:
            self.data["__ollamafic__"]["last_modified"] = datetime.now().isoformat()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

        self.filepath = filepath


def migrate_old_to_new(old_got_path: str) -> None:
    """
    Migre un ancien .got.json vers le nouveau format.

    Ancien format:
        {"title": {"ori": "Hello", "fr": "Bonjour"}}

    Nouveau format:
        {"title": {"ori": "Hello", "fr": {"text": "Bonjour", "history": [], "valid": false}}}

    Args:
        old_got_path: Chemin vers l'ancien fichier .got.json
    """
    import os

    with open(old_got_path, 'r', encoding='utf-8') as f:
        old_data = json5.load(f)

    def transform_entry(value):
        if isinstance(value, dict) and "ori" in value:
            result = {"ori": value["ori"]}
            for key, val in value.items():
                if key != "ori" and isinstance(val, str):
                    result[key] = {
                        "text": val,
                        "history": [],
                        "valid": False
                    }
                else:
                    result[key] = val
            return result
        elif isinstance(value, dict):
            return {k: transform_entry(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [transform_entry(item) for item in value]
        else:
            return value

    new_data = transform_entry(old_data)

    # Ajouter header si absent
    if "__ollamafic__" not in new_data:
        new_data["__ollamafic__"] = {
            "version": "2.0",
            "original_file": "unknown.json",
            "created": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat()
        }

    # Mettre à jour la version si présente
    if "__ollamafic__" in new_data:
        new_data["__ollamafic__"]["version"] = "2.0"

    backup_path = old_got_path + ".backup"
    os.rename(old_got_path, backup_path)

    with open(old_got_path, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Migration effectuée. Backup: {backup_path}")
