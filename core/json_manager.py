import json
import json5
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
import copy
from dataclasses import dataclass, asdict
import re

@dataclass
class JsonPath:
    """Représente un chemin dans un JSON comme un système de fichier"""
    path: str

    def __post_init__(self):
        self.path = self.path.strip('/')

    @property
    def parts(self) -> List[str]:
        if not self.path:
            return []
        return self.path.split('/')

    @property
    def parent(self) -> 'JsonPath':
        parts = self.parts[:-1] if self.parts else []
        return JsonPath('/'.join(parts))

    @property
    def name(self) -> str:
        return self.parts[-1] if self.parts else ""

    def __str__(self) -> str:
        return f"/{self.path}" if self.path else "/"

class JsonManager:
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = Path(file_path) if file_path else None
        self.data: Dict[str, Any] = {}
        self.original_data: Dict[str, Any] = {}
        self.modifications: List[Dict[str, Any]] = []

        # Répertoire courant dans la structure JSON
        self.current_path: str = ""

        # Système de suivi des modifications
        self.modified_paths: Dict[str, str] = {}  # path -> état ("MOD", "SAVED", etc.)
        self.pending_modifications: Dict[str, Any] = {}  # path -> valeur modifiée non sauvée

        # Hook pour le système d'historique
        self.operation_hook: Optional[Callable] = None

        if file_path and Path(file_path).exists():
            self.load_file(file_path)

    def set_operation_hook(self, hook: Callable):
        """Définit un hook qui sera appelé lors des modifications"""
        self.operation_hook = hook

    def get_current_path(self) -> str:
        """Retourne le répertoire courant"""
        return self.current_path

    def set_current_path(self, path: str) -> None:
        """Définit le répertoire courant"""
        # Valider que le chemin existe
        resolved_path = self._resolve_path(path)
        if self._path_exists(resolved_path):
            self.current_path = resolved_path
        else:
            raise ValueError(f"Le chemin '{path}' n'existe pas")

    def get_current_path_display(self) -> str:
        """Retourne le chemin courant pour l'affichage (avec /)"""
        return f"/{self.current_path}" if self.current_path else "/"

    def _resolve_path(self, path: str) -> str:
        """Résout un chemin relatif ou absolu par rapport au chemin courant avec support . et .."""
        if not path or path == "/":
            return ""

        if path.startswith('/'):
            # Chemin absolu depuis la racine
            resolved_path = path[1:] if len(path) > 1 else ""
        else:
            # Chemin relatif depuis le chemin courant
            if self.current_path:
                resolved_path = f"{self.current_path}/{path}"
            else:
                resolved_path = path

        # Résoudre les . et .. dans le chemin
        if '.' in resolved_path:
            parts = resolved_path.split('/') if resolved_path else []
            resolved_parts = []

            for part in parts:
                if part == '.' or part == '':
                    # Ignorer les . et les parties vides
                    continue
                elif part == '..':
                    # Remonter d'un niveau
                    if resolved_parts:
                        resolved_parts.pop()
                else:
                    resolved_parts.append(part)

            resolved_path = '/'.join(resolved_parts)

        return resolved_path

    def _has_wildcards(self, path: str) -> bool:
        """Check if path contains wildcards"""
        return any(char in path for char in ['*', '?', '#'])

    def _expand_wildcards(self, path: str) -> List[str]:
        """Expand wildcards (*, ?, #) in path to actual paths
        * = any sequence of characters
        ? = any single character
        # = any single digit
        """
        if not self._has_wildcards(path) and path != '.':
            return [path]

        expanded_paths = []

        # Handle current directory shortcut
        if path == '.':
            return [self.current_path]

        # Split path into parts
        parts = path.split('/')

        def _expand_recursive(current_data: Any, current_path: str, remaining_parts: List[str]) -> List[str]:
            if not remaining_parts:
                return [current_path]

            part = remaining_parts[0]
            rest = remaining_parts[1:]
            results = []

            if part == '*':
                # Wildcard - match all keys/indices at this level
                if isinstance(current_data, dict):
                    for key in current_data.keys():
                        next_path = f"{current_path}/{key}" if current_path else key
                        try:
                            next_data = current_data[key]
                            results.extend(_expand_recursive(next_data, next_path, rest))
                        except (KeyError, TypeError):
                            continue
                elif isinstance(current_data, list):
                    for i in range(len(current_data)):
                        next_path = f"{current_path}/{i}" if current_path else str(i)
                        try:
                            next_data = current_data[i]
                            results.extend(_expand_recursive(next_data, next_path, rest))
                        except (IndexError, TypeError):
                            continue
            elif '?' in part or '#' in part or ('*' in part and part != '*'):
                # Pattern matching with ? and #
                import re

                # Convert wildcard pattern to regex
                # D'abord échapper les caractères regex spéciaux, puis remplacer nos jokers
                pattern = re.escape(part)
                pattern = pattern.replace(r'\?', '.').replace(r'\#', r'\d').replace(r'\*', '.*')
                regex = re.compile(f"^{pattern}$")

                if isinstance(current_data, dict):
                    for key in current_data.keys():
                        if regex.match(key):
                            next_path = f"{current_path}/{key}" if current_path else key
                            try:
                                next_data = current_data[key]
                                results.extend(_expand_recursive(next_data, next_path, rest))
                            except (KeyError, TypeError):
                                continue
                elif isinstance(current_data, list):
                    for i in range(len(current_data)):
                        if regex.match(str(i)):
                            next_path = f"{current_path}/{i}" if current_path else str(i)
                            try:
                                next_data = current_data[i]
                                results.extend(_expand_recursive(next_data, next_path, rest))
                            except (IndexError, TypeError):
                                continue
            else:
                # Regular part (exact match)
                if isinstance(current_data, dict) and part in current_data:
                    next_path = f"{current_path}/{part}" if current_path else part
                    next_data = current_data[part]
                    results.extend(_expand_recursive(next_data, next_path, rest))
                elif isinstance(current_data, list):
                    try:
                        index = int(part)
                        if 0 <= index < len(current_data):
                            next_path = f"{current_path}/{index}" if current_path else str(index)
                            next_data = current_data[index]
                            results.extend(_expand_recursive(next_data, next_path, rest))
                    except (ValueError, IndexError):
                        pass

            return results

        # Start expansion from current context
        if path.startswith('/'):
            # Absolute path
            start_data = self.data
            start_path = ""
            parts = parts[1:] if parts and parts[0] == '' else parts
        else:
            # Relative path
            if self.current_path:
                try:
                    start_data = self.navigate_to_path(self.current_path)
                    start_path = self.current_path
                except:
                    start_data = self.data
                    start_path = ""
            else:
                start_data = self.data
                start_path = ""

        expanded_paths = _expand_recursive(start_data, start_path, parts)
        return expanded_paths

    def _path_exists(self, path: str) -> bool:
        """Vérifie si un chemin existe dans la structure JSON"""
        if not path:  # Racine
            return True

        try:
            self.navigate_to_path(path)
            return True
        except:
            return False

    def load_file(self, file_path: str) -> None:
        """Charge un fichier JSON/JSON5"""
        self.file_path = Path(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                try:
                    # Essai JSON5 d'abord (plus permissif)
                    self.data = json5.loads(content)
                except:
                    # Fallback vers JSON standard
                    self.data = json.loads(content)

            self.original_data = copy.deepcopy(self.data)
            print(f"Fichier chargé: {file_path}")
            print(f"Nombre d'éléments racine: {len(self.data) if isinstance(self.data, dict) else 'N/A'}")

        except Exception as e:
            raise Exception(f"Erreur lors du chargement du fichier {file_path}: {e}")

    def save_file(self, file_path: Optional[str] = None) -> None:
        """Sauvegarde le JSON dans un fichier"""
        target_path = Path(file_path) if file_path else self.file_path

        if not target_path:
            raise Exception("Aucun chemin de fichier spécifié")

        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            print(f"Fichier sauvegardé: {target_path}")
        except Exception as e:
            raise Exception(f"Erreur lors de la sauvegarde: {e}")

    def navigate_to_path(self, json_path: Union[str, JsonPath]) -> Any:
        """Navigue vers un chemin dans le JSON"""
        if isinstance(json_path, str):
            json_path = JsonPath(json_path)

        current = self.data

        for part in json_path.parts:
            if isinstance(current, dict):
                if part not in current:
                    raise KeyError(f"Clé '{part}' non trouvée dans {json_path}")
                current = current[part]
            elif isinstance(current, list):
                try:
                    index = int(part)
                    if index >= len(current):
                        raise IndexError(f"Index {index} hors limites pour la liste")
                    current = current[index]
                except ValueError:
                    raise ValueError(f"'{part}' n'est pas un index valide pour une liste")
            else:
                raise TypeError(f"Impossible de naviguer dans {type(current)} avec '{part}'")

        return current

    def list_contents(self, json_path: Union[str, JsonPath] = "") -> List[Dict[str, Any]]:
        """Liste le contenu d'un chemin (comme ls)"""
        if isinstance(json_path, str):
            json_path = JsonPath(json_path)

        try:
            current = self.navigate_to_path(json_path)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            return []

        contents = []

        if isinstance(current, dict):
            for key, value in current.items():
                contents.append({
                    'name': key,
                    'type': 'dict' if isinstance(value, dict) else
                           'list' if isinstance(value, list) else 'value',
                    'size': len(value) if isinstance(value, (dict, list, str)) else 1,
                    'preview': str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                })
        elif isinstance(current, list):
            for i, value in enumerate(current):
                contents.append({
                    'name': str(i),
                    'type': 'dict' if isinstance(value, dict) else
                           'list' if isinstance(value, list) else 'value',
                    'size': len(value) if isinstance(value, (dict, list, str)) else 1,
                    'preview': str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                })

        return contents

    def get_value(self, json_path: Union[str, JsonPath]) -> Any:
        """Récupère une valeur à un chemin donné"""
        return self.navigate_to_path(json_path)

    def set_value(self, json_path: Union[str, JsonPath], value: Any) -> None:
        """Définit une valeur à un chemin donné"""
        if isinstance(json_path, str):
            json_path = JsonPath(json_path)

        # Enregistrer la modification
        old_value = None
        try:
            old_value = copy.deepcopy(self.get_value(json_path))
        except:
            pass

        self.modifications.append({
            'action': 'set',
            'path': str(json_path),
            'old_value': old_value,
            'new_value': value
        })

        # Naviguer jusqu'au parent et définir la valeur
        if not json_path.parts:
            self.data = value
        else:
            parent_path = json_path.parent
            parent = self.navigate_to_path(parent_path)
            key = json_path.name

            if isinstance(parent, dict):
                parent[key] = value
            elif isinstance(parent, list):
                index = int(key)
                if index < len(parent):
                    parent[index] = value
                else:
                    # Étendre la liste si nécessaire
                    parent.extend([None] * (index - len(parent) + 1))
                    parent[index] = value

        # Appeler le hook d'historique si défini
        if self.operation_hook:
            try:
                self.operation_hook(
                    operation_type="edit",
                    affected_data={str(json_path): (old_value, copy.deepcopy(value))},
                    user_input={"path": str(json_path), "action": "set_value"}
                )
            except Exception as e:
                # Ne pas faire échouer l'opération si le hook échoue
                print(f"Erreur dans le hook d'historique: {e}")

    def search(self, pattern: str, search_keys: bool = True, search_values: bool = True) -> List[Dict[str, Any]]:
        """Recherche dans le JSON avec un pattern"""
        results = []
        regex = re.compile(pattern, re.IGNORECASE)

        def _search_recursive(obj: Any, path: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}/{key}" if path else key

                    if search_keys and regex.search(key):
                        results.append({
                            'path': current_path,
                            'type': 'key',
                            'match': key,
                            'value': value
                        })

                    if search_values and isinstance(value, str) and regex.search(value):
                        results.append({
                            'path': current_path,
                            'type': 'value',
                            'match': value,
                            'key': key
                        })

                    _search_recursive(value, current_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}/{i}" if path else str(i)
                    _search_recursive(item, current_path)

        _search_recursive(self.data)
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le JSON"""
        def _count_recursive(obj: Any) -> Dict[str, int]:
            counts = {'dicts': 0, 'lists': 0, 'values': 0, 'total_items': 0}

            if isinstance(obj, dict):
                counts['dicts'] += 1
                counts['total_items'] += len(obj)
                for value in obj.values():
                    sub_counts = _count_recursive(value)
                    for key in counts:
                        counts[key] += sub_counts[key]
            elif isinstance(obj, list):
                counts['lists'] += 1
                counts['total_items'] += len(obj)
                for item in obj:
                    sub_counts = _count_recursive(item)
                    for key in counts:
                        counts[key] += sub_counts[key]
            else:
                counts['values'] += 1

            return counts

        stats = _count_recursive(self.data)
        stats['modifications'] = len(self.modifications)
        stats['file_path'] = str(self.file_path) if self.file_path else None

        return stats

    def set_pending_modification(self, path: str, value: Any) -> None:
        """Marque une modification comme en attente (non sauvegardée)"""
        if isinstance(path, JsonPath):
            path = str(path)

        self.pending_modifications[path] = value
        self.modified_paths[path] = "MOD"

    def commit_pending_modification(self, path: str) -> bool:
        """Applique une modification en attente et la marque comme sauvegardée"""
        if path in self.pending_modifications:
            value = self.pending_modifications[path]
            try:
                self.set_value(path, value)
                del self.pending_modifications[path]
                self.modified_paths[path] = "SAVED"
                return True
            except Exception:
                return False
        return False

    def reject_pending_modification(self, path: str) -> bool:
        """Rejette une modification en attente"""
        if path in self.pending_modifications:
            del self.pending_modifications[path]
            if path in self.modified_paths:
                del self.modified_paths[path]
            return True
        return False

    def get_modification_state(self, path: str) -> Optional[str]:
        """Retourne l'état de modification d'un chemin"""
        return self.modified_paths.get(path)

    def get_pending_modifications(self) -> Dict[str, Any]:
        """Retourne toutes les modifications en attente"""
        return self.pending_modifications.copy()

    def clear_pending_modifications(self) -> None:
        """Efface toutes les modifications en attente"""
        self.pending_modifications.clear()
        # Garder seulement les modifications sauvegardées
        self.modified_paths = {k: v for k, v in self.modified_paths.items() if v == "SAVED"}

    def get_translatable_paths(self) -> List[str]:
        """
        Liste tous les chemins vers des entrées traduisibles dans un fichier .got.json.

        Returns:
            Liste de chemins ["app/title", "app/settings/theme", ...]
        """
        paths = []

        def traverse(obj, current_path=""):
            if isinstance(obj, dict):
                # Vérifier si c'est une entrée traduisible (a une clé "ori")
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

        traverse(self.data)
        return paths