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

        if lang == "ori":
            raise ValueError(f"Langue invalide: {lang}")

        # S'assurer que la structure existe pour cette langue
        if lang not in entry:
            # Créer la structure pour cette nouvelle langue
            entry[lang] = {
                "text": "",
                "valid": False,
                "history": []
            }
        elif not isinstance(entry[lang], dict):
            # Ancien format (string directe) - convertir
            old_text = entry[lang]
            entry[lang] = {
                "text": old_text,
                "valid": False,
                "history": []
            }
        elif "text" not in entry[lang]:
            # Structure dict mais sans "text" - initialiser
            entry[lang]["text"] = ""

        if "history" not in entry[lang]:
            entry[lang]["history"] = []

        # Sauvegarder l'ancienne version dans history
        current_text = entry[lang].get("text", "")
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

    def get_translatable_leaves_in_subtree(self, path: str) -> List[str]:
        """
        Liste tous les chemins traduisibles dans un sous-arbre.

        Args:
            path: Chemin du sous-arbre (ex: "app/settings")

        Returns:
            Liste des chemins relatifs des feuilles (ex: ["app/settings/theme", "app/settings/lang"])
        """
        try:
            subtree = self._get_entry_by_path(path)
        except (KeyError, ValueError):
            return []

        leaves = []

        def traverse(obj, current_path=""):
            if isinstance(obj, dict):
                # Vérifier si c'est une entrée traduisible
                if "ori" in obj and isinstance(obj.get("ori"), str):
                    leaves.append(current_path.strip("/"))
                else:
                    for key, value in obj.items():
                        if key != "__ollamafic__":
                            new_path = f"{current_path}/{key}"
                            traverse(value, new_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    traverse(item, f"{current_path}[{i}]")

        traverse(subtree, path)
        return leaves

    def is_translatable_leaf(self, path: str) -> bool:
        """
        Vérifie si un chemin pointe vers une feuille traduisible.

        Args:
            path: Chemin à vérifier

        Returns:
            True si c'est une feuille traduisible (a un champ "ori")
        """
        try:
            entry = self._get_entry_by_path(path)
            return isinstance(entry, dict) and "ori" in entry and isinstance(entry.get("ori"), str)
        except (KeyError, ValueError):
            return False

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

    # === EXPORT ===

    def export_to_json(self, output_path: str, target_language: str, mode: str = "standard") -> bool:
        """
        Exporte le .got.json vers un fichier JSON standard.

        Args:
            output_path: Chemin du fichier de sortie
            target_language: Code langue à exporter (ex: "fr", "en")
            mode: Mode d'export
                - "standard": Utilise la traduction si définie, sinon l'original
                - "validated": Utilise uniquement les traductions validées, sinon l'original

        Returns:
            True si l'export a réussi

        Raises:
            ValueError: Si la langue n'est pas dans les langues cibles
        """
        if target_language not in self.target_languages:
            raise ValueError(f"Langue '{target_language}' non disponible. Langues: {self.target_languages}")

        if not self.data:
            raise ValueError("Aucune donnée chargée")

        # Transformer les données
        exported_data = self._export_transform(self.data, target_language, mode)

        # Sauvegarder
        output_path = Path(output_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(exported_data, f, indent=2, ensure_ascii=False)

        return True

    def _export_transform(self, value: Any, target_language: str, mode: str) -> Any:
        """
        Transforme récursivement les données .got.json en JSON standard.

        Args:
            value: Valeur à transformer
            target_language: Langue cible
            mode: Mode d'export ("standard" ou "validated")

        Returns:
            Valeur transformée
        """
        # Ignorer le header __ollamafic__
        if isinstance(value, dict) and "__ollamafic__" in value:
            result = {}
            for key, val in value.items():
                if key != "__ollamafic__":
                    result[key] = self._export_transform(val, target_language, mode)
            return result

        # Transformer les objets de traduction
        if isinstance(value, dict) and "ori" in value:
            return self._export_translation_object(value, target_language, mode)

        # Traiter les dictionnaires normaux
        if isinstance(value, dict):
            return {k: self._export_transform(v, target_language, mode) for k, v in value.items()}

        # Traiter les listes
        if isinstance(value, list):
            return [self._export_transform(item, target_language, mode) for item in value]

        # Valeurs simples
        return value

    def _export_translation_object(self, obj: Dict, target_language: str, mode: str) -> str:
        """
        Exporte un objet de traduction en texte simple selon le mode.

        Args:
            obj: Objet de traduction {"ori": "...", "fr": {...}, ...}
            target_language: Langue cible
            mode: "standard" ou "validated"

        Returns:
            Texte à utiliser dans l'export
        """
        original = obj.get("ori", "")

        # Vérifier si la traduction existe
        if target_language not in obj:
            return original

        translation_data = obj[target_language]

        # Si c'est un dict (format v2.0)
        if isinstance(translation_data, dict):
            translation_text = translation_data.get("text", "")
            is_validated = translation_data.get("valid", False)

            # Mode "validated" : n'utiliser que si validé
            if mode == "validated":
                if is_validated and translation_text.strip():
                    return translation_text
                else:
                    return original

            # Mode "standard" : utiliser si non vide
            else:  # mode == "standard"
                if translation_text.strip():
                    return translation_text
                else:
                    return original

        # Si c'est une string (ancien format ou erreur)
        elif isinstance(translation_data, str):
            if translation_data.strip():
                return translation_data
            else:
                return original

        # Cas par défaut
        return original

    def get_export_stats(self, target_language: str, mode: str = "standard") -> Dict:
        """
        Calcule les statistiques d'un export potentiel.

        Args:
            target_language: Langue cible
            mode: Mode d'export

        Returns:
            Dict avec les statistiques:
            {
                "total_entries": int,
                "translated_entries": int,  # Nombre d'entrées qui utiliseront la traduction
                "original_entries": int,    # Nombre d'entrées qui utiliseront l'original
                "percentage": float         # Pourcentage traduit
            }
        """
        stats = {
            "total_entries": 0,
            "translated_entries": 0,
            "original_entries": 0,
            "percentage": 0.0
        }

        def count_entries(value):
            if isinstance(value, dict) and "ori" in value:
                stats["total_entries"] += 1

                # Vérifier si on utiliserait la traduction
                if target_language in value:
                    translation_data = value[target_language]

                    if isinstance(translation_data, dict):
                        translation_text = translation_data.get("text", "")
                        is_validated = translation_data.get("valid", False)

                        if mode == "validated":
                            if is_validated and translation_text.strip():
                                stats["translated_entries"] += 1
                            else:
                                stats["original_entries"] += 1
                        else:  # standard
                            if translation_text.strip():
                                stats["translated_entries"] += 1
                            else:
                                stats["original_entries"] += 1
                    else:
                        stats["original_entries"] += 1
                else:
                    stats["original_entries"] += 1

            elif isinstance(value, dict):
                for v in value.values():
                    count_entries(v)
            elif isinstance(value, list):
                for item in value:
                    count_entries(item)

        if self.data:
            count_entries(self.data)

        if stats["total_entries"] > 0:
            stats["percentage"] = (stats["translated_entries"] / stats["total_entries"]) * 100

        return stats


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
