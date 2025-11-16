"""
Module de chargement intelligent de fichiers JSON et .got.json

Ce module gère la logique de correspondance entre fichiers .json et .got.json,
avec création automatique et gestion des conflits.
"""

import json
import json5
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Callable
import sys

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from core.got_json_manager import GotJsonManager


def detect_source_change(got_data: Dict, json_data: Dict, json_filename: str) -> Tuple[bool, str]:
    """
    Détecte si le fichier JSON source a changé depuis la création du .got.json.

    Args:
        got_data: Données du fichier .got.json
        json_data: Données du fichier .json actuel
        json_filename: Nom du fichier .json

    Returns:
        Tuple (changed, reason):
        - changed: True si le fichier a changé
        - reason: Description du changement ("filename", "checksum", "none")
    """
    if not isinstance(got_data, dict) or "__ollamafic__" not in got_data:
        return False, "none"

    header = got_data["__ollamafic__"]

    # 1. Vérifier le nom de fichier
    original_file = header.get("original_file", "")
    if original_file != json_filename:
        return True, "filename"

    # 2. Vérifier le checksum
    stored_checksum = header.get("source_checksum", "")
    if stored_checksum:
        current_checksum = GotJsonManager.calculate_checksum(json_data)
        if stored_checksum != current_checksum:
            return True, "checksum"

    return False, "none"


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


def create_backup_with_timestamp(filepath: str) -> str:
    """
    Crée une copie de backup d'un fichier avec un timestamp.

    Format: toto.backup.YYYYMMDD_HHMM.got.json

    Args:
        filepath: Chemin du fichier à sauvegarder

    Returns:
        Chemin du fichier de backup créé

    Raises:
        FileNotFoundError: Si le fichier source n'existe pas
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Le fichier {filepath} n'existe pas")

    # Générer le timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # Construire le nom du backup
    # Exemple: messages.got.json -> messages.backup.20251116_1042.got.json
    if path.suffix == '.json':
        # Gérer le cas .got.json
        if path.stem.endswith('.got'):
            base_name = path.stem[:-4]  # Enlever '.got'
            backup_name = f"{base_name}.backup.{timestamp}.got.json"
        else:
            base_name = path.stem
            backup_name = f"{base_name}.backup.{timestamp}.json"
    else:
        # Autres extensions
        base_name = path.stem
        backup_name = f"{base_name}.backup.{timestamp}{path.suffix}"

    backup_path = path.parent / backup_name

    # Copier le fichier
    shutil.copy2(filepath, backup_path)

    return str(backup_path)


def load_file_with_evolution_check(filepath: str, parent_window=None, target_languages: Optional[list] = None,
                                   progress_callback: Optional[Callable[[int, int], None]] = None) -> Tuple[GotJsonManager, str]:
    """
    Charge un fichier avec détection de changement et gestion de l'évolution.

    Version GUI qui utilise le dialog de choix si le fichier source a changé.

    Args:
        filepath: Chemin vers le fichier à charger
        parent_window: Fenêtre parente pour les dialogs (None = mode console)
        target_languages: Langues cibles
        progress_callback: Callback pour la progression (current, total)

    Returns:
        Tuple (GotJsonManager, chemin_got_json_utilisé)

    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        ValueError: Si l'opération est annulée
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Le fichier {filepath} n'existe pas")

    # Charger les paramètres
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
        got_manager.data = data
        got_manager.filepath = str(path)
        got_manager.original_filename = data["__ollamafic__"]["original_file"]
        return got_manager, str(path)

    # CAS 2: Fichier .json source
    json_filename = path.name
    got_path = path.with_suffix('.got.json')

    # Le .got.json existe-t-il ?
    if got_path.exists():
        with open(got_path, 'r', encoding='utf-8') as f:
            got_data = json5.load(f)

        # Détecter si le fichier source a changé
        changed, reason = detect_source_change(got_data, data, json_filename)

        if changed:
            # Le fichier source a changé - demander à l'utilisateur
            backup_filename = Path(create_backup_with_timestamp(str(got_path))).name

            if parent_window:
                # Mode GUI - utiliser le dialog
                from gui.dialogs import EvolutionChoiceDialog
                dialog = EvolutionChoiceDialog(parent_window, json_filename, got_path.name, backup_filename)
                choice = dialog.show()
            else:
                # Mode console - utiliser input()
                print(f"\n⚠️  Le fichier source a changé ({reason})")
                print(f"   JSON source: {json_filename}")
                print(f"   Got.json: {got_path.name}")
                print(f"   Backup créé: {backup_filename}")
                print("\nOptions:")
                print("  [N]ouveau - Créer un nouveau .got.json")
                print("  [É]volution - Fusionner ancien + nouveau (recommandé)")
                print("  [A]ncien - Utiliser l'ancien .got.json")
                choice_input = input("\nVotre choix [É]: ").lower() or 'é'

                if choice_input in ['n', 'nouveau']:
                    choice = "nouveau"
                elif choice_input in ['a', 'ancien']:
                    choice = "ancien"
                else:
                    choice = "evolution"

            # Traiter le choix
            if choice == "nouveau":
                # Créer un nouveau .got.json
                got_data = got_manager.create_from_json(data, json_filename)
                got_manager.save_to_file(str(got_path))
                return got_manager, str(got_path)

            elif choice == "evolution":
                # Faire évoluer le .got.json
                got_manager.evolve_got_json(got_data, data, json_filename, progress_callback)
                got_manager.save_to_file(str(got_path))
                return got_manager, str(got_path)

            elif choice == "ancien":
                # Utiliser l'ancien .got.json
                got_manager.data = got_data
                got_manager.filepath = str(got_path)
                got_manager.original_filename = json_filename
                return got_manager, str(got_path)

            else:
                # Annulé
                raise ValueError("Opération annulée par l'utilisateur")

        else:
            # Pas de changement détecté - utiliser le .got.json existant
            got_manager.data = got_data
            got_manager.filepath = str(got_path)
            got_manager.original_filename = json_filename
            return got_manager, str(got_path)

    # Le .got.json n'existe pas - créer un nouveau
    if settings.get("auto_create_got_json", True):
        got_data = got_manager.create_from_json(data, json_filename)
        got_manager.save_to_file(str(got_path))
        return got_manager, str(got_path)
    else:
        # Charger le JSON tel quel
        got_manager.data = data
        got_manager.filepath = str(path)
        return got_manager, str(path)
