"""
Indicizzatore per Knowledge Base
Carica e indicizza EU AI Act, ISO/IEC 42001, etc.
"""

from pathlib import Path
from typing import Optional, Dict, Any
from actproof.rag.vector_store import VectorStore
from actproof.rag.document_loader import DocumentLoader


class KnowledgeBaseIndexer:
    """Indicizza documenti legali nella knowledge base"""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        persist_directory: Optional[Path] = None,
    ):
        """
        Inizializza indicizzatore
        
        Args:
            vector_store: Vector store da usare (None = crea nuovo)
            persist_directory: Directory per persistenza
        """
        if vector_store is None:
            persist_path = persist_directory or Path("data/vector_store")
            persist_path.mkdir(parents=True, exist_ok=True)
            self.vector_store = VectorStore(persist_directory=persist_path)
        else:
            self.vector_store = vector_store
        
        self.document_loader = DocumentLoader()

    def index_directory(
        self, directory: Path, metadata_prefix: Optional[str] = None
    ) -> int:
        """
        Indicizza tutti i documenti in una directory
        
        Args:
            directory: Directory da indicizzare
            metadata_prefix: Prefisso per metadati (es. "ai_act", "iso_42001")
        
        Returns:
            Numero di documenti indicizzati
        """
        if not directory.exists():
            print(f"Directory non trovata: {directory}")
            return 0
        
        # Carica documenti
        documents_data = self.document_loader.load_directory(directory, recursive=True)
        
        if not documents_data:
            print(f"Nessun documento trovato in {directory}")
            return 0
        
        # Prepara dati per indicizzazione
        documents = []
        metadatas = []
        ids = []
        
        for i, doc_data in enumerate(documents_data):
            documents.append(doc_data["text"])
            
            metadata = doc_data["metadata"].copy()
            if metadata_prefix:
                metadata["source_type"] = metadata_prefix
            metadatas.append(metadata)
            
            doc_id = f"{metadata_prefix}_{i}" if metadata_prefix else f"doc_{i}"
            ids.append(doc_id)
        
        # Indicizza
        self.vector_store.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        
        print(f"Indicizzati {len(documents)} chunk da {directory}")
        return len(documents)

    def index_ai_act(self, ai_act_directory: Optional[Path] = None) -> int:
        """
        Indicizza EU AI Act
        
        Args:
            ai_act_directory: Directory con documenti AI Act (None = usa default)
        
        Returns:
            Numero di documenti indicizzati
        """
        if ai_act_directory is None:
            ai_act_directory = Path("data/ai_act")
        
        return self.index_directory(ai_act_directory, metadata_prefix="ai_act")

    def index_iso_42001(self, iso_directory: Optional[Path] = None) -> int:
        """
        Indicizza ISO/IEC 42001
        
        Args:
            iso_directory: Directory con documenti ISO (None = usa default)
        
        Returns:
            Numero di documenti indicizzati
        """
        if iso_directory is None:
            iso_directory = Path("data/standards")
        
        return self.index_directory(iso_directory, metadata_prefix="iso_42001")

    def index_all(self) -> Dict[str, int]:
        """
        Indicizza tutti i documenti disponibili
        
        Returns:
            Dizionario con conteggi per tipo
        """
        results = {}
        
        # Indicizza AI Act
        ai_act_path = Path("data/ai_act")
        if ai_act_path.exists():
            results["ai_act"] = self.index_ai_act(ai_act_path)
        else:
            print(f"Directory AI Act non trovata: {ai_act_path}")
            results["ai_act"] = 0
        
        # Indicizza ISO/IEC 42001
        iso_path = Path("data/standards")
        if iso_path.exists():
            results["iso_42001"] = self.index_iso_42001(iso_path)
        else:
            print(f"Directory ISO non trovata: {iso_path}")
            results["iso_42001"] = 0
        
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Ottiene statistiche sulla knowledge base"""
        info = self.vector_store.get_collection_info()
        return {
            "total_documents": info["document_count"],
            "embedding_model": info["embedding_model"],
            "collection_name": info["collection_name"],
        }
