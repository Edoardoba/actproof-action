"""
RAG Engine per query su EU AI Act e standard
Usa LangChain per orchestrazione RAG
Con citazioni obbligatorie e logging audit-grade
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json

# Lazy imports to avoid requiring langchain if not used
try:
    from langchain.chains import RetrievalQA
    from langchain.llms.base import LLM
    from langchain.prompts import PromptTemplate
    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False
    RetrievalQA = None  # type: ignore
    LLM = None  # type: ignore
    PromptTemplate = None  # type: ignore

from actproof.rag.vector_store import VectorStore


class RAGEngine:
    """
    Engine RAG audit-grade per query su documentazione legale
    Features:
    - Citazioni obbligatorie (min 2 per risposta)
    - Mode strict con fallback "Insufficient sources"
    - Logging retrieval per audit trail
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm: Optional[Any] = None,
        openai_api_key: Optional[str] = None,
        min_citations: int = 2,
        audit_middleware: Optional[Any] = None,
    ):
        """
        Inizializza RAG Engine

        Args:
            vector_store: Vector store con documenti indicizzati
            llm: LLM da usare (None = usa OpenAI se API key fornita)
            openai_api_key: API key OpenAI (opzionale)
            min_citations: Numero minimo citazioni richieste (default: 2)
            audit_middleware: Middleware per logging (opzionale)
        """
        if not _LANGCHAIN_AVAILABLE:
            raise ImportError(
                "langchain is required for RAGEngine. "
                "Install it with: pip install langchain langchain-openai langchain-community"
            )
        
        self.vector_store = vector_store
        self.min_citations = min_citations
        self.audit_middleware = audit_middleware

        # Query log per audit trail
        self.query_log: List[Dict[str, Any]] = []

        # Inizializza LLM
        if llm is None and openai_api_key:
            try:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model_name="gpt-4",
                    temperature=0,
                    openai_api_key=openai_api_key,
                )
            except ImportError:
                raise ImportError("langchain-openai richiesto. Esegui: pip install langchain-openai")
        elif llm:
            self.llm = llm
        else:
            # Fallback: usa modello locale o mock
            self.llm = None

    def query(
        self,
        question: str,
        context_limit: int = 5,
        return_sources: bool = True,
        mode: str = "normal",
        include_debug: bool = False,
    ) -> Dict[str, Any]:
        """
        Esegue query RAG con citazioni obbligatorie

        Args:
            question: Domanda da porre
            context_limit: Numero di documenti contestuali da recuperare
            return_sources: Se restituire fonti
            mode: "normal" o "strict" (strict richiede min_citations)
            include_debug: Include retrieval debug info (solo admin)

        Returns:
            Risposta con contesto, fonti e citazioni verificabili
        """
        query_start_time = datetime.utcnow()

        # Recupera documenti rilevanti
        relevant_docs = self.vector_store.search(question, n_results=context_limit)

        # Prepara citazioni verificabili
        citations = self._extract_citations(relevant_docs)

        # Log retrieval per audit trail
        retrieval_log = {
            "query": question,
            "timestamp": query_start_time.isoformat(),
            "top_k": context_limit,
            "retrieved_count": len(relevant_docs),
            "citations_count": len(citations),
            "retrieval_scores": [
                {
                    "doc_id": self._get_doc_id(doc),
                    "score": 1.0 - doc.get("distance", 1.0),
                    "chunk_hash": self._hash_chunk(doc.get("document", "")),
                }
                for doc in relevant_docs
            ],
        }

        # Verifica soglia citazioni
        citations_sufficient = len(citations) >= self.min_citations

        if not relevant_docs:
            answer = "Nessun documento rilevante trovato."
            citations = []
            result = {
                "answer": answer,
                "sources": [],
                "context": [],
                "citations": [],
                "citations_sufficient": False,
            }
        elif mode == "strict" and not citations_sufficient:
            # Mode strict: NON inventare
            answer = f"Insufficient sources: Found {len(citations)} citations but require at least {self.min_citations}. Please refine your question or provide additional context."
            suggestion = self._generate_search_suggestion(question)
            result = {
                "answer": answer,
                "sources": citations,
                "context": [doc["document"] for doc in relevant_docs[:2]],  # Solo estratti
                "citations": citations,
                "citations_sufficient": False,
                "suggestion": suggestion,
            }
        else:
            # Mode normal o citations sufficienti
            # Costruisci contesto
            context = "\n\n".join([doc["document"] for doc in relevant_docs])

            # Se LLM disponibile, genera risposta
            if self.llm:
                prompt = self._build_prompt_with_citations(question, context, citations)
                try:
                    response = self.llm.invoke(prompt)
                    # Gestisci diversi tipi di risposta LLM
                    if hasattr(response, 'content'):
                        answer = response.content
                    elif isinstance(response, str):
                        answer = response
                    else:
                        answer = str(response)
                except Exception as e:
                    answer = f"Errore nella generazione risposta: {e}. Contesto rilevante: {context[:500]}..."
            else:
                # Fallback: restituisci contesto rilevante con citazioni
                answer = f"Basato sulla documentazione EU AI Act:\n\n{context[:500]}...\n\nCitazioni: {len(citations)}"

            result = {
                "answer": answer,
                "context": [doc["document"] for doc in relevant_docs],
                "sources": citations if return_sources else [],
                "citations": citations,
                "citations_sufficient": citations_sufficient,
            }

        # Aggiungi debug info se richiesto (solo admin)
        if include_debug:
            result["retrieval_debug"] = retrieval_log

        # Salva nel query log
        query_record = {
            **retrieval_log,
            "answer": result["answer"],
            "citations": citations,
            "mode": mode,
        }
        self.query_log.append(query_record)

        # Log in audit trail se disponibile
        if self.audit_middleware:
            try:
                from actproof.integrations import AuditEventType
                self.audit_middleware.log_event(
                    event_type=AuditEventType.API_REQUEST,
                    operation="rag_query",
                    success=True,
                    input_data={"question": question, "mode": mode},
                    output_data={
                        "citations_count": len(citations),
                        "citations_sufficient": citations_sufficient,
                    },
                )
            except Exception as e:
                # Non bloccare se audit log fallisce
                pass

        return result

    def _extract_citations(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Estrae citazioni verificabili dai documenti

        Args:
            docs: Documenti retrieved

        Returns:
            Lista citazioni con metadata verificabili
        """
        citations = []

        for i, doc in enumerate(docs):
            metadata = doc.get("metadata", {})
            document_text = doc.get("document", "")

            citation = {
                "doc_id": self._get_doc_id(doc),
                "doc_version": metadata.get("version", "unknown"),
                "section": metadata.get("section", f"chunk_{i}"),
                "article": metadata.get("article", "Unknown"),
                "chunk_id": f"chunk_{i}",
                "chunk_hash": self._hash_chunk(document_text),
                "source": metadata.get("source", "Unknown"),
                "filename": metadata.get("filename", "Unknown"),
                "relevance_score": 1.0 - doc.get("distance", 1.0),
            }

            citations.append(citation)

        return citations

    def _get_doc_id(self, doc: Dict[str, Any]) -> str:
        """Estrae doc ID da metadata"""
        metadata = doc.get("metadata", {})
        return metadata.get("doc_id", metadata.get("filename", "unknown"))

    def _hash_chunk(self, text: str) -> str:
        """Calcola hash SHA-256 di un chunk"""
        return hashlib.sha256(text.encode()).hexdigest()[:16]  # Short hash

    def _generate_search_suggestion(self, question: str) -> str:
        """Genera suggerimento per raffinare la ricerca"""
        return f"Try searching for specific articles or requirements related to '{question}'"

    def _build_prompt(self, question: str, context: str) -> str:
        """Costruisce prompt per LLM"""
        template = """Sei un assistente esperto in conformità normativa EU AI Act.

Contesto dalla documentazione EU AI Act e standard correlati:
{context}

Domanda: {question}

Rispondi in modo chiaro e preciso basandoti solo sul contesto fornito. Se il contesto non contiene informazioni sufficienti, indica che servono ulteriori dettagli.

Risposta:"""

        return template.format(context=context, question=question)

    def _build_prompt_with_citations(self, question: str, context: str, citations: List[Dict[str, Any]]) -> str:
        """Costruisce prompt con enfasi su citazioni"""
        citations_text = "\n".join([
            f"[{i+1}] {c['article']} ({c['source']}) - {c['section']}"
            for i, c in enumerate(citations[:5])
        ])

        template = """Sei un assistente esperto in conformità normativa EU AI Act.

Contesto dalla documentazione EU AI Act e standard correlati:
{context}

Citazioni disponibili:
{citations}

Domanda: {question}

IMPORTANTE: Basa la tua risposta SOLO sul contesto fornito. Cita esplicitamente gli articoli e le fonti quando possibile. NON inventare informazioni non presenti nel contesto.

Risposta:"""

        return template.format(context=context, question=question, citations=citations_text)

    def check_requirement(
        self, requirement_text: str, system_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verifica se un requisito è soddisfatto
        
        Args:
            requirement_text: Testo del requisito da verificare
            system_description: Descrizione del sistema da valutare
        
        Returns:
            Risultato verifica con riferimenti legali
        """
        query = f"Requisito: {requirement_text}"
        if system_description:
            query += f"\nSistema: {system_description}"
        
        result = self.query(query, context_limit=3)
        
        return {
            "requirement": requirement_text,
            "analysis": result["answer"],
            "legal_references": result.get("sources", []),
            "compliance_guidance": result.get("context", []),
        }

    def get_article_info(self, article_number: int) -> Dict[str, Any]:
        """Ottiene informazioni su un articolo specifico dell'AI Act"""
        query = f"Articolo {article_number} EU AI Act"
        result = self.query(query, context_limit=3)

        return {
            "article": article_number,
            "content": result["answer"],
            "sources": result.get("sources", []),
        }

    def get_query_log(self) -> List[Dict[str, Any]]:
        """
        Restituisce query log per audit

        Returns:
            Lista query eseguite con metadata
        """
        return self.query_log

    def export_query_log_jsonl(self, output_path: str):
        """
        Esporta query log in formato JSONL

        Args:
            output_path: Percorso file output
        """
        from pathlib import Path
        output = Path(output_path)

        with open(output, "w") as f:
            for record in self.query_log:
                f.write(json.dumps(record) + "\n")
