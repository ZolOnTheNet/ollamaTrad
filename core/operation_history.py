"""
Système d'historique détaillé des opérations avec support undo/redo
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime
import hashlib
import copy

@dataclass
class OperationSnapshot:
    """Snapshot d'une valeur avant/après une opération"""
    path: str
    value_before: Any
    value_after: Any
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    operation_id: str = ""

@dataclass
class DetailedOperation:
    """Opération détaillée avec toutes les informations pour undo/redo"""
    operation_id: str
    operation_type: str  # translate, process, ia_chat, internal_command, edit
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Informations contextuelles
    user_input: Dict[str, Any] = field(default_factory=dict)  # Paramètres de l'opération
    provider_info: Dict[str, Any] = field(default_factory=dict)  # Provider utilisé
    session_variables: Dict[str, Any] = field(default_factory=dict)  # Variables au moment de l'op

    # Données pour undo/redo
    affected_paths: List[OperationSnapshot] = field(default_factory=list)

    # Résultats
    result: Any = None
    success: bool = True
    error_message: str = ""

    # Navigation
    parent_operation_id: Optional[str] = None  # Pour les opérations liées
    execution_time_ms: float = 0.0

@dataclass
class SessionHistory:
    """Historique complet d'une session avec navigation"""
    session_id: str
    file_path: str
    file_hash_initial: str
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None

    # Historique ordonné des opérations
    operations: List[DetailedOperation] = field(default_factory=list)

    # Navigation dans l'historique
    current_position: int = -1  # Position actuelle dans l'historique (-1 = à jour)

    # Métadonnées de session
    tags: List[str] = field(default_factory=list)
    context: str = ""
    notes: List[str] = field(default_factory=list)

    # Statistiques
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0

class OperationHistoryManager:
    """Gestionnaire d'historique détaillé avec support undo/redo"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.history_dir = self.data_dir / "history"
        self.snapshots_dir = self.data_dir / "snapshots"

        # Créer les répertoires si nécessaire
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        self.current_session: Optional[SessionHistory] = None
        self.max_operations_in_memory = 1000  # Limite pour éviter la surcharge mémoire

    def start_session(self, file_path: str, session_id: Optional[str] = None) -> str:
        """Démarre une nouvelle session d'historique"""
        if session_id is None:
            session_id = f"session_{int(time.time())}_{hash(file_path) % 10000:04d}"

        file_hash = self._calculate_file_hash(file_path)

        self.current_session = SessionHistory(
            session_id=session_id,
            file_path=file_path,
            file_hash_initial=file_hash
        )

        # Sauvegarder immédiatement
        self._save_session()

        return session_id

    def end_session(self):
        """Termine la session actuelle"""
        if self.current_session:
            self.current_session.end_time = datetime.now().isoformat()
            self._save_session()
            self.current_session = None

    def record_operation(self,
                        operation_type: str,
                        user_input: Dict[str, Any],
                        affected_data: Dict[str, tuple],  # path -> (before, after)
                        result: Any = None,
                        provider_info: Dict[str, Any] = None,
                        session_variables: Dict[str, Any] = None,
                        parent_operation_id: Optional[str] = None) -> str:
        """
        Enregistre une opération détaillée

        Args:
            operation_type: Type d'opération (translate, process, etc.)
            user_input: Paramètres fournis par l'utilisateur
            affected_data: Dictionnaire path -> (valeur_avant, valeur_après)
            result: Résultat de l'opération
            provider_info: Informations sur le provider utilisé
            session_variables: Variables de session au moment de l'opération
            parent_operation_id: ID de l'opération parente si applicable

        Returns:
            ID unique de l'opération créée
        """
        if not self.current_session:
            raise Exception("Aucune session active. Appelez start_session() d'abord.")

        start_time = time.time()
        operation_id = f"op_{int(start_time * 1000)}_{len(self.current_session.operations)}"

        # Créer les snapshots pour chaque chemin affecté
        snapshots = []
        for path, (before, after) in affected_data.items():
            snapshot = OperationSnapshot(
                path=path,
                value_before=copy.deepcopy(before),
                value_after=copy.deepcopy(after),
                operation_id=operation_id
            )
            snapshots.append(snapshot)

        # Créer l'opération détaillée
        operation = DetailedOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            user_input=copy.deepcopy(user_input or {}),
            provider_info=copy.deepcopy(provider_info or {}),
            session_variables=copy.deepcopy(session_variables or {}),
            affected_paths=snapshots,
            result=copy.deepcopy(result),
            success=True,
            parent_operation_id=parent_operation_id,
            execution_time_ms=(time.time() - start_time) * 1000
        )

        # Ajouter à l'historique de session
        self.current_session.operations.append(operation)
        self.current_session.total_operations += 1
        self.current_session.successful_operations += 1
        self.current_session.current_position = len(self.current_session.operations) - 1

        # Nettoyer si nécessaire
        self._cleanup_old_operations()

        # Sauvegarder périodiquement
        if len(self.current_session.operations) % 10 == 0:
            self._save_session()

        return operation_id

    def record_failed_operation(self,
                               operation_type: str,
                               user_input: Dict[str, Any],
                               error_message: str,
                               provider_info: Dict[str, Any] = None) -> str:
        """Enregistre une opération qui a échoué"""
        if not self.current_session:
            raise Exception("Aucune session active.")

        operation_id = f"op_failed_{int(time.time() * 1000)}_{len(self.current_session.operations)}"

        operation = DetailedOperation(
            operation_id=operation_id,
            operation_type=operation_type,
            user_input=copy.deepcopy(user_input or {}),
            provider_info=copy.deepcopy(provider_info or {}),
            success=False,
            error_message=error_message
        )

        self.current_session.operations.append(operation)
        self.current_session.total_operations += 1
        self.current_session.failed_operations += 1

        return operation_id

    def can_undo(self) -> bool:
        """Vérifie si un undo est possible"""
        if not self.current_session:
            return False
        return self.current_session.current_position >= 0

    def can_redo(self) -> bool:
        """Vérifie si un redo est possible"""
        if not self.current_session:
            return False
        return self.current_session.current_position < len(self.current_session.operations) - 1

    def get_undo_info(self) -> Optional[Dict[str, Any]]:
        """Retourne les informations sur l'opération qui sera annulée"""
        if not self.can_undo():
            return None

        operation = self.current_session.operations[self.current_session.current_position]
        return {
            "operation_id": operation.operation_id,
            "operation_type": operation.operation_type,
            "timestamp": operation.timestamp,
            "user_input": operation.user_input,
            "affected_paths": [s.path for s in operation.affected_paths],
            "description": self._format_operation_description(operation)
        }

    def get_redo_info(self) -> Optional[Dict[str, Any]]:
        """Retourne les informations sur l'opération qui sera refaite"""
        if not self.can_redo():
            return None

        operation = self.current_session.operations[self.current_session.current_position + 1]
        return {
            "operation_id": operation.operation_id,
            "operation_type": operation.operation_type,
            "timestamp": operation.timestamp,
            "user_input": operation.user_input,
            "affected_paths": [s.path for s in operation.affected_paths],
            "description": self._format_operation_description(operation)
        }

    def undo_last_operation(self) -> Dict[str, Any]:
        """
        Annule la dernière opération

        Returns:
            Dictionnaire avec les changements à appliquer au JSON
        """
        if not self.can_undo():
            raise Exception("Aucune opération à annuler")

        operation = self.current_session.operations[self.current_session.current_position]

        # Préparer les changements à appliquer (revenir aux valeurs "avant")
        changes_to_apply = {}
        for snapshot in operation.affected_paths:
            changes_to_apply[snapshot.path] = snapshot.value_before

        # Reculer la position dans l'historique
        self.current_session.current_position -= 1

        # Sauvegarder l'état
        self._save_session()

        return {
            "operation_undone": operation.operation_id,
            "operation_type": operation.operation_type,
            "changes": changes_to_apply,
            "description": self._format_operation_description(operation)
        }

    def redo_next_operation(self) -> Dict[str, Any]:
        """
        Refait la prochaine opération annulée

        Returns:
            Dictionnaire avec les changements à appliquer au JSON
        """
        if not self.can_redo():
            raise Exception("Aucune opération à refaire")

        # Avancer la position dans l'historique
        self.current_session.current_position += 1
        operation = self.current_session.operations[self.current_session.current_position]

        # Préparer les changements à appliquer (valeurs "après")
        changes_to_apply = {}
        for snapshot in operation.affected_paths:
            changes_to_apply[snapshot.path] = snapshot.value_after

        # Sauvegarder l'état
        self._save_session()

        return {
            "operation_redone": operation.operation_id,
            "operation_type": operation.operation_type,
            "changes": changes_to_apply,
            "description": self._format_operation_description(operation)
        }

    def get_operation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retourne l'historique des opérations avec métadonnées"""
        if not self.current_session:
            return []

        history = []
        operations = self.current_session.operations[-limit:] if limit > 0 else self.current_session.operations

        for i, operation in enumerate(operations):
            is_current = i <= self.current_session.current_position

            history.append({
                "operation_id": operation.operation_id,
                "operation_type": operation.operation_type,
                "timestamp": operation.timestamp,
                "description": self._format_operation_description(operation),
                "affected_paths": [s.path for s in operation.affected_paths],
                "success": operation.success,
                "is_current": is_current,
                "can_undo_to": is_current,
                "execution_time_ms": operation.execution_time_ms
            })

        return history

    def jump_to_operation(self, operation_id: str) -> Dict[str, Any]:
        """Navigue directement à une opération spécifique"""
        if not self.current_session:
            raise Exception("Aucune session active")

        # Trouver l'index de l'opération
        target_index = -1
        for i, op in enumerate(self.current_session.operations):
            if op.operation_id == operation_id:
                target_index = i
                break

        if target_index == -1:
            raise Exception(f"Opération {operation_id} non trouvée")

        # Calculer les changements nécessaires
        current_pos = self.current_session.current_position
        changes_to_apply = {}

        if target_index < current_pos:
            # Annuler des opérations
            for i in range(current_pos, target_index, -1):
                operation = self.current_session.operations[i]
                for snapshot in operation.affected_paths:
                    changes_to_apply[snapshot.path] = snapshot.value_before

        elif target_index > current_pos:
            # Refaire des opérations
            for i in range(current_pos + 1, target_index + 1):
                operation = self.current_session.operations[i]
                for snapshot in operation.affected_paths:
                    changes_to_apply[snapshot.path] = snapshot.value_after

        # Mettre à jour la position
        self.current_session.current_position = target_index
        self._save_session()

        return {
            "jumped_to": operation_id,
            "changes": changes_to_apply,
            "new_position": target_index
        }

    def get_session_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la session actuelle"""
        if not self.current_session:
            return {}

        return {
            "session_id": self.current_session.session_id,
            "file_path": self.current_session.file_path,
            "start_time": self.current_session.start_time,
            "duration": self._calculate_session_duration(),
            "total_operations": self.current_session.total_operations,
            "successful_operations": self.current_session.successful_operations,
            "failed_operations": self.current_session.failed_operations,
            "current_position": self.current_session.current_position,
            "can_undo": self.can_undo(),
            "can_redo": self.can_redo(),
            "tags": self.current_session.tags,
            "context": self.current_session.context
        }

    def add_session_tag(self, tag: str):
        """Ajoute un tag à la session actuelle"""
        if self.current_session and tag not in self.current_session.tags:
            self.current_session.tags.append(tag)

    def get_operations_list(self) -> List[Any]:
        """Retourne la liste des opérations de la session actuelle"""
        if not self.current_session:
            return []
        return self.current_session.operations

    def get_current_position(self) -> int:
        """Retourne la position actuelle dans l'historique"""
        if not self.current_session:
            return -1
        return self.current_session.current_position

    def undo(self, steps: int = 1) -> List[Any]:
        """Annule les dernières opérations et retourne les opérations annulées"""
        undone_operations = []
        for _ in range(steps):
            if self.can_undo():
                result = self.undo_last_operation()
                if result.get("success"):
                    undone_operations.append(result.get("operation"))
        return undone_operations

    def redo(self, steps: int = 1) -> List[Any]:
        """Refait les opérations annulées et retourne les opérations refaites"""
        # Pour l'instant, pas d'implémentation de redo dans SessionHistory
        # On retourne une liste vide
        return []

    def jump_to_position(self, position: int) -> Dict[str, Any]:
        """Saute à une position spécifique dans l'historique"""
        if not self.current_session:
            return {"success": False, "error": "Aucune session active"}

        # Pour l'instant, implémentation basique
        return {"success": True, "position": position}

    def set_session_context(self, context: str):
        """Définit le contexte de la session actuelle"""
        if self.current_session:
            self.current_session.context = context
            self._save_session()

    def _format_operation_description(self, operation: DetailedOperation) -> str:
        """Formate une description lisible de l'opération"""
        op_type = operation.operation_type
        user_input = operation.user_input

        if op_type == "translate":
            source_lang = user_input.get("source_lang", "auto")
            target_lang = user_input.get("target_lang", "unknown")
            path = user_input.get("path", "")
            return f"Traduction {source_lang}→{target_lang} de {path}"

        elif op_type == "process":
            instruction = user_input.get("instruction", "")[:50]
            path = user_input.get("path", "")
            return f"Traitement de {path}: {instruction}..."

        elif op_type == "ia_chat":
            message = user_input.get("message", "")[:50]
            provider = operation.provider_info.get("name", "unknown")
            return f"Dialogue [{provider}]: {message}..."

        elif op_type == "internal_command":
            command = user_input.get("command", "")
            return f"Commande interne: {command}"

        elif op_type == "edit":
            path = user_input.get("path", "")
            return f"Édition manuelle de {path}"

        else:
            return f"Opération {op_type}"

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcule le hash MD5 d'un fichier"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""

    def _calculate_session_duration(self) -> str:
        """Calcule la durée de la session"""
        if not self.current_session:
            return "0"

        start = datetime.fromisoformat(self.current_session.start_time)
        end = datetime.now()
        if self.current_session.end_time:
            end = datetime.fromisoformat(self.current_session.end_time)

        duration = end - start
        return str(duration).split('.')[0]  # Enlever les microsecondes

    def _cleanup_old_operations(self):
        """Nettoie les anciennes opérations si trop nombreuses"""
        if not self.current_session:
            return

        if len(self.current_session.operations) > self.max_operations_in_memory:
            # Garder seulement les dernières opérations
            operations_to_keep = self.max_operations_in_memory // 2
            self.current_session.operations = self.current_session.operations[-operations_to_keep:]
            self.current_session.current_position = min(self.current_session.current_position, len(self.current_session.operations) - 1)

    def _save_session(self):
        """Sauvegarde la session actuelle"""
        if not self.current_session:
            return

        session_file = self.history_dir / f"{self.current_session.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.current_session), f, indent=2, ensure_ascii=False)

    def load_session(self, session_id: str) -> bool:
        """Charge une session existante"""
        session_file = self.history_dir / f"{session_id}.json"
        if not session_file.exists():
            return False

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Reconstruire les objets
            operations = []
            for op_data in data.get('operations', []):
                snapshots = []
                for snap_data in op_data.get('affected_paths', []):
                    snapshots.append(OperationSnapshot(**snap_data))

                op_data['affected_paths'] = snapshots
                operations.append(DetailedOperation(**op_data))

            data['operations'] = operations
            self.current_session = SessionHistory(**data)

            return True
        except Exception as e:
            print(f"Erreur lors du chargement de la session: {e}")
            return False