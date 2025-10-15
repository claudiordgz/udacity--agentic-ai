from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import copy

from lib.documents import Document
from lib.vector_db import VectorStoreManager
from chromadb.api.types import QueryResult


class SessionNotFoundError(Exception):
    """Raised when attempting to access a session that doesn't exist"""
    pass


@dataclass
class ShortTermMemory():
    """Manage the history of objects across multiple sessions"""
    sessions: Dict[str, List[Any]] = field(default_factory=lambda: {})

    def __post_init__(self):
        """Initialize the default session"""
        self.create_session("default")

    def __str__(self) -> str:
        session_ids = list(self.sessions.keys())
        return f"Memory(sessions={session_ids})"

    def __repr__(self) -> str:
        return self.__str__()

    def create_session(self, session_id: str) -> bool:
        """Create a new session
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            bool: True if session was created, False if it already existed
        """
        if session_id in self.sessions:
            return False
        self.sessions[session_id] = []
        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session
        
        Args:
            session_id: Session to delete
            
        Returns:
            bool: True if session was deleted, False if it didn't exist
            
        Raises:
            ValueError: If attempting to delete the default session
        """
        if session_id == "default":
            raise ValueError("Cannot delete the default session")
        if session_id not in self.sessions:
            return False
        del self.sessions[session_id]
        return True

    def _validate_session(self, session_id: str):
        """Validate that a session exists
        
        Args:
            session_id: Session ID to validate
            
        Raises:
            SessionNotFoundError: If session doesn't exist
        """
        if session_id not in self.sessions:
            raise SessionNotFoundError(f"Session '{session_id}' not found")

    def add(self, object: Any, session_id: Optional[str] = None):
        """Add a new object to the history
        
        Args:
            object: Object to add to history
            session_id: Optional session ID to add to (uses default if None)
            
        Raises:
            SessionNotFoundError: If specified session doesn't exist
        """
        session_id = session_id or "default"
        self._validate_session(session_id)
        self.sessions[session_id].append(copy.deepcopy(object))

    def get_all_objects(self, session_id: Optional[str] = None) -> List[Any]:
        """Get all objects for a session
        
        Args:
            session_id: Optional session ID (uses default if None)
            
        Returns:
            List of objects in the session
            
        Raises:
            SessionNotFoundError: If specified session doesn't exist
        """
        session_id = session_id or "default"
        self._validate_session(session_id)
        return [copy.deepcopy(obj) for obj in self.sessions[session_id]]

    def get_last_object(self, session_id: Optional[str] = None) -> Optional[Any]:
        """Get the most recent object for a session
        
        Args:
            session_id: Optional session ID (uses default if None)
            
        Returns:
            The last object in the session if it exists, None if session is empty
            
        Raises:
            SessionNotFoundError: If specified session doesn't exist
        """
        objects = self.get_all_objects(session_id)
        return objects[-1] if objects else None

    def get_all_sessions(self) -> List[str]:
        """Get all session IDs"""
        return list(self.sessions.keys())

    def reset(self, session_id: Optional[str] = None):
        """Reset memory for a specific session or all sessions
        
        Args:
            session_id: Optional session ID to reset. If None, resets all sessions.
            
        Raises:
            SessionNotFoundError: If specified session doesn't exist
        """
        if session_id is None:
            # Reset all sessions to empty lists
            for sid in self.sessions:
                self.sessions[sid] = []
        else:
            self._validate_session(session_id)
            self.sessions[session_id] = []

    def pop(self, session_id: Optional[str] = None) -> Optional[Any]:
        """Remove and return the last object from a session
        
        Args:
            session_id: Optional session ID to pop from (uses default if None)
            
        Returns:
            The last object in the session if it exists, None if session is empty
            
        Raises:
            SessionNotFoundError: If specified session doesn't exist
        """
        session_id = session_id or "default"
        self._validate_session(session_id)
        
        if not self.sessions[session_id]:
            return None
        return self.sessions[session_id].pop()


# =================== Long-term Memory (Agentic RAG-backed) ===================

@dataclass
class MemoryFragment:
    """
    Represents a single piece of memory information stored in the long-term memory system.

    Attributes:
        content (str): The memory content
        owner (str): Owner identifier (e.g., user id)
        namespace (str): Logical grouping for related memories (default: "default")
        timestamp (int): Unix timestamp when the memory was created
    """
    content: str
    owner: str
    namespace: str = "default"
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp()))


@dataclass
class MemorySearchResult:
    """Container for memory search results and metadata (e.g., distances)."""
    fragments: List[MemoryFragment]
    metadata: Dict


@dataclass
class TimestampFilter:
    """Filter criteria for time-based memory searches."""
    greater_than_value: int = None
    lower_than_value: int = None


class LongTermMemory:
    """
    Manages persistent memory storage and retrieval using vector embeddings.

    - Multi-user isolation via owner
    - Namespace-based organization
    - Time-based filtering
    - Semantic similarity search
    """

    def __init__(self, db: VectorStoreManager):
        # Use get_or_create to persist across notebook/script runs
        self.vector_store = db.get_or_create_store("long_term_memory")

    def get_namespaces(self) -> List[str]:
        """Return all unique namespaces present in the store."""
        results = self.vector_store.get()
        return [r["metadatas"][0]["namespace"] for r in results]

    def register(self, memory_fragment: MemoryFragment, metadata: Optional[Dict[str, str]] = None):
        """Store a new memory fragment with merged metadata."""
        complete_metadata = {
            "owner": memory_fragment.owner,
            "namespace": memory_fragment.namespace,
            "timestamp": memory_fragment.timestamp,
        }
        if metadata:
            complete_metadata.update(metadata)

        self.vector_store.add(
            Document(
                content=memory_fragment.content,
                metadata=complete_metadata,
            )
        )

    def search(
        self,
        query_text: str,
        owner: str,
        limit: int = 3,
        timestamp_filter: Optional[TimestampFilter] = None,
        namespace: Optional[str] = "default",
    ) -> MemorySearchResult:
        """Semantic search for memories filtered by owner/namespace and optional time window."""

        where: Dict[str, Any] = {
            "$and": [
                {"namespace": {"$eq": namespace}},
                {"owner": {"$eq": owner}},
            ]
        }

        if timestamp_filter:
            if timestamp_filter.greater_than_value:
                where["$and"].append({"timestamp": {"$gt": timestamp_filter.greater_than_value}})
            if timestamp_filter.lower_than_value:
                where["$and"].append({"timestamp": {"$lt": timestamp_filter.lower_than_value}})

        result: QueryResult = self.vector_store.query(
            query_texts=[query_text],
            n_results=limit,
            where=where,
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]

        fragments: List[MemoryFragment] = []
        for content, meta in zip(documents, metadatas):
            fragments.append(
                MemoryFragment(
                    content=content,
                    owner=meta.get("owner"),
                    namespace=meta.get("namespace", "default"),
                    timestamp=meta.get("timestamp"),
                )
            )

        result_metadata = {"distances": result.get("distances", [[]])[0]}

        return MemorySearchResult(fragments=fragments, metadata=result_metadata)
