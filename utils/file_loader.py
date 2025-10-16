"""
Module de chargement intelligent de fichiers JSON et .got.json

Ce module gère la logique de correspondance entre fichiers .json et .got.json,
avec création automatique et gestion des conflits.
"""

import json
import json5
from pathlib import Path
from typing import Dict, Optional, Tuple
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from core.got_json_manager import GotJsonManager


def load_translation_settings() -> Dict:
    """
    Charge les paramètres de traduction depuis config/translation_settings.json

    Returns:
        Dict avec les paramètres de traduction
    """
    settings_path = Path(__file__).parent.parent / "config" / "translation_settings.json"

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Paramètres par défaut si le fichier n'existe pas
        return {
            "target_languages": ["fr"],
            "language_order": ["ori", "fr"],
            "default_provider": "ollama",
            "history_limit": 10,
            "auto_create_got_json": True,
            "backup_on_conflict": True
        }


def load_file_intelligently(filepath: str, target_languages: Optional[list] = None) -> Tuple[GotJsonManager, str]:
    """
    Charge un fichier .json ou .got.json avec gestion intelligente.

    Logique:
    1. Si le fichier est un .got.json valide → charger directement
    2. Si le fichier est un .json:
       a. Chercher un .got.json correspondant
       b. Si trouvé et correspondant → utiliser le .got.json
       c. Si trouvé mais non correspondant → demander à l'utilisateur
       d. Si non trouvé → créer un nouveau .got.json

    Args:
        filepath: Chemin vers le fichier à charger
        target_languages: Langues cibles (par défaut: depuis config)

    Returns:
        Tuple (GotJsonManager, chemin_got_json_utilisé)

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        ValueError: Si l'opération est annulée par l'utilisateur
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Le fichier {filepath} n'existe pas")

    # Charger les paramètres de traduction
    settings = load_translation_settings()
    if target_languages is None:
        target_languages = settings.get("target_languages", ["fr"])

    # Créer le gestionnaire
    got_manager = GotJsonManager(target_languages=target_languages)

    # Lire le fichier
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json5.load(f)

    # CAS 1: Fichier .got.json valide
    if got_manager.is_valid_got_json(data):
        print(f"✓ Fichier .got.json valide chargé: {filepath}")
        got_manager.data = data
        got_manager.filepath = str(path)
        got_manager.original_filename = data["__ollamafic__"]["original_file"]
        return got_manager, str(path)

    # CAS 2: Fichier .json source
    json_filename = path.name
    got_path = path.with_suffix('.got.json')

    # Sous-cas 2a: Le .got.json existe-t-il ?
    if got_path.exists():
        with open(got_path, 'r', encoding='utf-8') as f:
            got_data = json5.load(f)

        # Vérifier correspondance
        if got_manager.validate_correspondence(got_data, json_filename):
            print(f"✓ Fichier .got.json correspondant trouvé: {got_path}")
            got_manager.data = got_data
            got_manager.filepath = str(got_path)
            got_manager.original_filename = json_filename
            return got_manager, str(got_path)
        else:
            # Sous-cas 2b: Conflit - Le .got.json existe mais ne correspond pas
            print(f"⚠ Le fichier {got_path} existe mais ne correspond pas à {json_filename}")
            print(f"   Le .got.json référence: {got_data.get('__ollamafic__', {}).get('original_file', 'inconnu')}")
            print(f"   Fichier demandé: {json_filename}")
            print()

            if settings.get("backup_on_conflict", True):
                print("Options:")
                print("  [É]craser - Remplacer le .got.json existant par un nouveau")
                print("  [N]ouveau - Créer un nouveau fichier avec un nom différent")
                print("  [A]nnuler - Annuler l'opération")
            else:
                print("Options:")
                print("  [É]craser - Remplacer le .got.json existant")
                print("  [A]nnuler - Annuler l'opération")

            choice = input("\nVotre choix: ").lower()

            if choice == 'é' or choice == 'e':
                # Écraser - créer un backup d'abord
                if settings.get("backup_on_conflict", True):
                    backup_path = got_path.with_suffix('.got.json.backup')
                    counter = 1
                    while backup_path.exists():
                        backup_path = got_path.with_name(f"{got_path.stem}.backup{counter}.got.json")
                        counter += 1
                    import shutil
                    shutil.copy(got_path, backup_path)
                    print(f"✓ Backup créé: {backup_path}")

            elif choice == 'n':
                # Nouveau nom
                counter = 1
                while got_path.exists():
                    got_path = path.with_name(f"{path.stem}_{counter}.got.json")
                    counter += 1
                print(f"✓ Nouveau fichier: {got_path}")

            else:
                raise ValueError("Opération annulée par l'utilisateur")

    # Sous-cas 2c/d: Créer un nouveau .got.json
    if settings.get("auto_create_got_json", True):
        print(f"→ Création d'un nouveau fichier .got.json: {got_path}")
        got_data = got_manager.create_from_json(data, json_filename)
        got_manager.save_to_file(str(got_path))
        print(f"✓ Fichier .got.json créé avec succès")
        return got_manager, str(got_path)
    else:
        # Mode sans création automatique - juste charger le JSON tel quel
        print(f"⚠ Mode sans .got.json - chargement direct du JSON")
        got_manager.data = data
        got_manager.filepath = str(path)
        return got_manager, str(path)


def get_got_json_path(json_path: str) -> Path:
    """
    Retourne le chemin du fichier .got.json correspondant à un .json

    Args:
        json_path: Chemin vers le fichier .json

    Returns:
        Path vers le fichier .got.json
    """
    return Path(json_path).with_suffix('.got.json')


def check_got_json_exists(json_path: str) -> bool:
    """
    Vérifie si un fichier .got.json existe pour un .json donné

    Args:
        json_path: Chemin vers le fichier .json

    Returns:
        True si le .got.json existe
    """
    return get_got_json_path(json_path).exists()


def get_file_info(filepath: str) -> Dict:
    """
    Retourne des informations sur un fichier JSON ou .got.json

    Args:
        filepath: Chemin vers le fichier

    Returns:
        Dict avec les informations du fichier
    """
    path = Path(filepath)

    if not path.exists():
        return {"exists": False}

    info = {
        "exists": True,
        "path": str(path),
        "extension": path.suffix,
        "size": path.stat().st_size,
        "is_got_json": False,
        "original_file": None
    }

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json5.load(f)

        if "__ollamafic__" in data:
            info["is_got_json"] = True
            info["original_file"] = data["__ollamafic__"].get("original_file")
            info["version"] = data["__ollamafic__"].get("version")
            info["created"] = data["__ollamafic__"].get("created")
            info["last_modified"] = data["__ollamafic__"].get("last_modified")

    except Exception as e:
        info["error"] = str(e)

    return info
