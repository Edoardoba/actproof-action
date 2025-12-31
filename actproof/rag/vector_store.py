"""
Vector Store per indicizzazione documenti legali
Usa ChromaDB per storage vettoriale
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Lazy imports to avoid requiring heavy dependencies if not used
try:
    import chromadb
    from chromadb.config import Settings
    _CHROMADB_AVAILABLE = True
except ImportError:
    _CHROMADB_AVAILABLE = False
    chromadb = None  # type: ignore
    Settings = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    _SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None  # type: ignore


class VectorStore:
    """Vector store per documenti EU AI Act e standard"""

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        collection_name: str = "ai_act_documents",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        """
        Inizializza vector store
        
        Args:
            persist_directory: Directory per persistenza (None = in-memory)
            collection_name: Nome collezione ChromaDB
            embedding_model: Modello per embeddings
        """
        if not _CHROMADB_AVAILABLE:
            raise ImportError(
                "chromadb is required for VectorStore. "
                "Install it with: pip install chromadb"
            )
        
        if not _SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for VectorStore. "
                "Install it with: pip install sentence-transformers"
            )
        
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        
        # Inizializza embedding model
        self.embedder = SentenceTransformer(embedding_model)
        
        # Inizializza ChromaDB
        if persist_directory:
            persist_path = str(persist_directory)
            self.client = chromadb.PersistentClient(path=persist_path)
        else:
            self.client = chromadb.Client()
        
        # Crea o ottieni collezione
        try:
            self.collection = self.client.get_collection(name=collection_name)
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "EU AI Act and related standards"},
            )

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> None:
        """
        Aggiunge documenti al vector store
        
        Args:
            documents: Lista di testi documento
            metadatas: Metadati per ogni documento
            ids: ID univoci per ogni documento
        """
        if not documents:
            return
        
        # Genera embeddings
        embeddings = self.embedder.encode(documents).tolist()
        
        # Genera ID se non forniti
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]
        
        # Metadati di default
        if metadatas is None:
            metadatas = [{}] * len(documents)
        
        # Aggiungi a ChromaDB
        self.collection.add(
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Cerca documenti simili
        
        Args:
            query: Query di ricerca
            n_results: Numero risultati da restituire
            filter_metadata: Filtri metadati
        
        Returns:
            Lista di documenti rilevanti con score
        """
        # Genera embedding query
        query_embedding = self.embedder.encode([query]).tolist()[0]
        
        # Cerca in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata,
        )
        
        # Formatta risultati
        formatted_results = []
        if results["documents"] and len(results["documents"][0]) > 0:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                    "id": results["ids"][0][i] if results["ids"] else None,
                })
        
        return formatted_results

    def get_collection_info(self) -> Dict[str, Any]:
        """Ottiene informazioni sulla collezione"""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "embedding_model": self.embedding_model_name,
        }

    def clear(self) -> None:
        """Svuota la collezione"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "EU AI Act and related standards"},
        )
