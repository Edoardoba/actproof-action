"""Sistema RAG per EU AI Act e standard correlati"""

# Lazy imports to avoid requiring heavy dependencies if RAG is not used
# Import these directly from submodules when needed:
# from actproof.rag.vector_store import VectorStore
# from actproof.rag.rag_engine import RAGEngine
# from actproof.rag.document_loader import DocumentLoader

__all__ = ["VectorStore", "RAGEngine", "DocumentLoader"]

def __getattr__(name):
    """Lazy import for RAG components"""
    if name == "VectorStore":
        from actproof.rag.vector_store import VectorStore
        return VectorStore
    elif name == "RAGEngine":
        from actproof.rag.rag_engine import RAGEngine
        return RAGEngine
    elif name == "DocumentLoader":
        from actproof.rag.document_loader import DocumentLoader
        return DocumentLoader
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
