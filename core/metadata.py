import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import hashlib

@dataclass
class FileMetadata:
    """Métadonnées pour un fichier JSON"""
    file_path: str
    file_hash: str
    tags: List[str] = field(default_factory=list)
    context: str = ""
    last_modified: str = field(default_factory=lambda: datetime.now().isoformat())
    processing_notes: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProcessingSession:
    """Session de traitement avec historique"""
    session_id: str
    file_path: str
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    operations: List[Dict[str, Any]] = field(default_factory=list)
    model_used: str = ""
    context_used: str = ""
    status: str = "active"  # active, completed, error

class MetadataManager:
    """Gestionnaire de métadonnées pour les fichiers JSON"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.sessions_dir = self.data_dir / "sessions"

        # Créer le répertoire sessions si nécessaire (pour les sessions globales)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_hash(self, file_path: str) -> str:
        """Calcule le hash MD5 d'un fichier"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""

    def _get_metadata_file(self, file_path: str) -> Path:
        """Retourne le chemin du fichier journal (.otjnl) à côté du fichier JSON"""
        json_file = Path(file_path)
        # Créer le fichier journal dans le même répertoire avec l'extension .otjnl
        journal_file = json_file.parent / f"{json_file.stem}.otjnl"
        return journal_file

    def get_metadata(self, file_path: str) -> FileMetadata:
        """Récupère les métadonnées d'un fichier"""
        file_path_str = str(file_path)  # S'assurer que c'est une chaîne
        metadata_file = self._get_metadata_file(file_path_str)

        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return FileMetadata(**data)
            except Exception as e:
                print(f"Erreur lors du chargement des métadonnées: {e}")

        # Créer de nouvelles métadonnées
        return FileMetadata(
            file_path=file_path_str,
            file_hash=self._get_file_hash(file_path_str)
        )

    def save_metadata(self, metadata: FileMetadata) -> None:
        """Sauvegarde les métadonnées"""
        metadata_file = self._get_metadata_file(metadata.file_path)

        try:
            # Convertir en dictionnaire et s'assurer que tous les paths sont des chaînes
            metadata_dict = asdict(metadata)
            metadata_dict['file_path'] = str(metadata_dict['file_path'])

            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Erreur lors de la sauvegarde des métadonnées: {e}")

    def add_tag(self, file_path: str, tag: str) -> None:
        """Ajoute un tag à un fichier"""
        metadata = self.get_metadata(file_path)
        if tag not in metadata.tags:
            metadata.tags.append(tag)
            self.save_metadata(metadata)

    def remove_tag(self, file_path: str, tag: str) -> None:
        """Supprime un tag d'un fichier"""
        metadata = self.get_metadata(file_path)
        if tag in metadata.tags:
            metadata.tags.remove(tag)
            self.save_metadata(metadata)

    def set_context(self, file_path: str, context: str) -> None:
        """Définit le contexte d'un fichier"""
        metadata = self.get_metadata(file_path)
        metadata.context = context
        self.save_metadata(metadata)

    def add_processing_note(self, file_path: str, note: str) -> None:
        """Ajoute une note de traitement"""
        metadata = self.get_metadata(file_path)
        timestamp = datetime.now().isoformat()
        metadata.processing_notes.append(f"[{timestamp}] {note}")
        self.save_metadata(metadata)

    def start_session(self, file_path: str, model: str = "", context: str = "") -> str:
        """Démarre une nouvelle session de traitement"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        session = ProcessingSession(
            session_id=session_id,
            file_path=str(file_path),  # S'assurer que c'est une chaîne
            model_used=model,
            context_used=context
        )

        self._save_session(session)
        return session_id

    def add_operation(self, session_id: str, operation_type: str, details: Dict[str, Any]) -> None:
        """Ajoute une opération à une session"""
        session = self._load_session(session_id)
        if session:
            operation = {
                'timestamp': datetime.now().isoformat(),
                'type': operation_type,
                'details': details
            }
            session.operations.append(operation)
            self._save_session(session)

    def end_session(self, session_id: str, status: str = "completed") -> None:
        """Termine une session"""
        session = self._load_session(session_id)
        if session:
            session.end_time = datetime.now().isoformat()
            session.status = status
            self._save_session(session)

    def _save_session(self, session: ProcessingSession) -> None:
        """Sauvegarde une session"""
        session_file = self.sessions_dir / f"{session.session_id}.json"
        try:
            # Convertir en dictionnaire et s'assurer que tous les paths sont des chaînes
            session_dict = asdict(session)
            session_dict['file_path'] = str(session_dict['file_path'])

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_dict, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la session: {e}")

    def _load_session(self, session_id: str) -> Optional[ProcessingSession]:
        """Charge une session"""
        session_file = self.sessions_dir / f"{session_id}.json"
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return ProcessingSession(**data)
            except Exception as e:
                print(f"Erreur lors du chargement de la session: {e}")
        return None

    def list_sessions(self, file_path: Optional[str] = None) -> List[ProcessingSession]:
        """Liste les sessions (optionnellement filtrées par fichier)"""
        sessions = []

        for session_file in self.sessions_dir.glob("*.json"):
            session = self._load_session(session_file.stem)
            if session:
                if file_path is None or session.file_path == file_path:
                    sessions.append(session)

        return sorted(sessions, key=lambda s: s.start_time, reverse=True)

    def get_files_by_tag(self, tag: str) -> List[str]:
        """Récupère tous les fichiers ayant un tag spécifique"""
        # TODO: Avec le nouveau système .otjnl, cette méthode nécessite une réécriture
        # pour parcourir les fichiers dans différents répertoires
        return []

    def search_files(self, query: str) -> List[FileMetadata]:
        """Recherche dans les métadonnées"""
        # TODO: Avec le nouveau système .otjnl, cette méthode nécessite une réécriture
        # pour parcourir les fichiers dans différents répertoires
        return []

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Nettoie les anciennes sessions"""
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        removed_count = 0

        for session_file in self.sessions_dir.glob("*.json"):
            if session_file.stat().st_mtime < cutoff_date:
                try:
                    session_file.unlink()
                    removed_count += 1
                except:
                    pass

        return removed_count