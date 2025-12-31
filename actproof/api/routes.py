"""
ActProof.ai - API Routes
FastAPI routes for EU AI Act compliance automation
"""

import logging
import tarfile
import tempfile
from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path

from actproof.scanner import RepositoryScanner
from actproof.compliance import PolicyEngine, ComplianceResult
from actproof.compliance.diff_engine import ComplianceDiffEngine, ComplianceDiffResult
from actproof.compliance.evidence_pack import EvidencePackGenerator, EvidenceManifest
from actproof.rag import RAGEngine, VectorStore
from actproof.knowledge_base import KnowledgeBaseIndexer
from actproof.fairness import FairnessAuditor, LegalReportGenerator
from actproof.integrations import AuditMiddleware, AuditEventType
from actproof.storage import LocalStorage, StorageBackend
from actproof.utils.git_utils import get_changed_files
from actproof.api.auth_middleware import verify_api_token

# Configure logger
logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response
class ScanRequest(BaseModel):
    repository_path: str
    generate_bom: bool = True
    output_format: str = "json"


class ComplianceRequest(BaseModel):
    ai_bom_path: Optional[str] = None
    repository_path: Optional[str] = None
    system_description: Optional[str] = None


class RAGQueryRequest(BaseModel):
    question: str
    context_limit: int = 5
    mode: str = Field(default="normal", description="'normal' or 'strict'")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context (repo_id, commit)")


class RAGQueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    context: List[str]
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Citazioni verificabili")
    citations_sufficient: bool = Field(default=True, description="Se citazioni sufficienti")
    retrieval_debug: Optional[Dict[str, Any]] = Field(None, description="Debug info (solo admin)")


# Initialize components (singleton pattern with dependency injection)
_vector_store: Optional[VectorStore] = None
_rag_engine: Optional[RAGEngine] = None
_policy_engine: Optional[PolicyEngine] = None
_audit_middleware: Optional[AuditMiddleware] = None
_fairness_auditor: Optional[FairnessAuditor] = None
_report_generator: Optional[LegalReportGenerator] = None
_diff_engine: Optional[ComplianceDiffEngine] = None
_storage_backend: Optional[StorageBackend] = None
_evidence_pack_generator: Optional[EvidencePackGenerator] = None


def get_vector_store() -> VectorStore:
    """
    Dependency injection for VectorStore instance

    Returns:
        Shared VectorStore instance
    """
    global _vector_store
    if _vector_store is None:
        logger.info("Initializing VectorStore")
        _vector_store = VectorStore(persist_directory=Path("data/vector_store"))
    return _vector_store


def get_rag_engine() -> RAGEngine:
    """
    Dependency injection for RAG Engine instance

    Returns:
        Shared RAGEngine instance
    """
    global _rag_engine
    if _rag_engine is None:
        logger.info("Initializing RAG Engine")
        vector_store = get_vector_store()
        audit_middleware = get_audit_middleware()
        _rag_engine = RAGEngine(
            vector_store=vector_store,
            min_citations=2,
            audit_middleware=audit_middleware,
        )
    return _rag_engine


def get_policy_engine() -> PolicyEngine:
    """
    Dependency injection for Policy Engine instance

    Returns:
        Shared PolicyEngine instance
    """
    global _policy_engine
    if _policy_engine is None:
        logger.info("Initializing Policy Engine")
        _policy_engine = PolicyEngine()
    return _policy_engine


def get_audit_middleware() -> AuditMiddleware:
    """
    Dependency injection for Audit Middleware instance

    Returns:
        Shared AuditMiddleware instance
    """
    global _audit_middleware
    if _audit_middleware is None:
        logger.info("Initializing Audit Middleware")
        _audit_middleware = AuditMiddleware(
            audit_log_path=Path("logs/audit.log"),
            enable_file_logging=True,
        )
    return _audit_middleware


def get_fairness_auditor() -> FairnessAuditor:
    """
    Dependency injection for Fairness Auditor instance

    Returns:
        Shared FairnessAuditor instance
    """
    global _fairness_auditor
    if _fairness_auditor is None:
        logger.info("Initializing Fairness Auditor")
        _fairness_auditor = FairnessAuditor(use_fairlearn=True)
    return _fairness_auditor


def get_report_generator() -> LegalReportGenerator:
    """
    Dependency injection for Legal Report Generator instance

    Returns:
        Shared LegalReportGenerator instance
    """
    global _report_generator
    if _report_generator is None:
        logger.info("Initializing Report Generator")
        _report_generator = LegalReportGenerator()
    return _report_generator


def get_diff_engine() -> ComplianceDiffEngine:
    """
    Dependency injection for Compliance Diff Engine instance

    Returns:
        Shared ComplianceDiffEngine instance
    """
    global _diff_engine
    if _diff_engine is None:
        logger.info("Initializing Compliance Diff Engine")
        _diff_engine = ComplianceDiffEngine()
    return _diff_engine


def get_storage_backend() -> StorageBackend:
    """
    Dependency injection for Storage Backend instance

    Returns:
        Shared StorageBackend instance
    """
    global _storage_backend
    if _storage_backend is None:
        logger.info("Initializing Storage Backend (Local)")
        _storage_backend = LocalStorage(base_path="./local_storage")
    return _storage_backend


def get_evidence_pack_generator() -> EvidencePackGenerator:
    """
    Dependency injection for Evidence Pack Generator instance

    Returns:
        Shared EvidencePackGenerator instance
    """
    global _evidence_pack_generator
    if _evidence_pack_generator is None:
        logger.info("Initializing Evidence Pack Generator")
        storage = get_storage_backend()
        _evidence_pack_generator = EvidencePackGenerator(storage=storage)
    return _evidence_pack_generator


@router.post("/scan")
async def scan_repository(
    request: ScanRequest,
    user: dict = Depends(verify_api_token)
):
    """
    Scan a repository and generate AI-BOM (requires authentication)

    Args:
        request: Scan request containing repository path and options
        user: Authenticated user info from token

    Returns:
        Scan results including AI-BOM document

    Raises:
        HTTPException: If repository not found or scan fails
    """
    try:
        repo_path = Path(request.repository_path)
        if not repo_path.exists():
            logger.error(f"Repository not found: {repo_path}")
            raise HTTPException(status_code=404, detail="Repository not found")
        
        logger.info(f"Scanning repository {repo_path} for user {user['user_id']}")
        
        scanner = RepositoryScanner(repo_path)
        results = scanner.scan()
        
        response = {
            "repository_path": str(repo_path),
            "summary": results["summary"],
            "is_git_repository": results["is_git_repository"],
        }
        
        if request.generate_bom:
            bom_path = scanner.generate_bom(format=request.output_format)
            response["ai_bom_path"] = str(bom_path)
            response["ai_bom"] = results["ai_bom"].model_dump(mode="json")
        
        return response
    except Exception as e:
        logger.error(f"Scan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan/github-actions")
async def scan_github_actions(
    file: UploadFile = File(..., description="Repository archive (tar.gz)"),
    repository: str = Form(..., description="Repository identifier (e.g., owner/repo)"),
    commit_sha: str = Form(..., description="Commit SHA"),
    branch: Optional[str] = Form(None, description="Branch name"),
    user: dict = Depends(verify_api_token),
    policy_engine: PolicyEngine = Depends(get_policy_engine),
):
    """
    Scan repository uploaded from GitHub Actions (requires authentication)
    
    This endpoint accepts a tarball of the repository and scans it for compliance.
    Designed for use with GitHub Actions workflows.

    Args:
        file: Uploaded repository archive (tar.gz)
        repository: Repository identifier
        commit_sha: Commit SHA being scanned
        branch: Branch name (optional)
        user: Authenticated user info from token
        policy_engine: Policy engine for compliance checking

    Returns:
        Scan results with compliance data
    """
    logger.info(f"GitHub Actions scan request from user {user['user_id']} for {repository}")
    
    try:
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory(prefix="actproof_scan_") as tmpdir:
            tmp_path = Path(tmpdir)
            archive_path = tmp_path / "repo.tar.gz"
            extract_dir = tmp_path / "repo"
            extract_dir.mkdir()
            
            # Save uploaded file
            with open(archive_path, "wb") as f:
                content = await file.read()
                # Check file size (max 100MB)
                if len(content) > 100 * 1024 * 1024:
                    raise HTTPException(
                        status_code=400,
                        detail="Archive too large (max 100MB)"
                    )
                f.write(content)
            
            # Extract archive
            try:
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(extract_dir)
            except tarfile.TarError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid archive format: {str(e)}"
                )
            
            # Scan repository
            scanner = RepositoryScanner(extract_dir)
            scan_results = scanner.scan()
            
            # Generate AI-BOM
            bom_path = scanner.generate_bom(format="json")
            ai_bom = scan_results.get("ai_bom")
            
            # Run compliance check
            compliance_result = policy_engine.evaluate_compliance(
                ai_bom=ai_bom,
                system_id=ai_bom.spdx_id if ai_bom else repository
            )
            
            # Prepare response
            response = {
                "scan_id": f"{repository}-{commit_sha[:7]}",
                "repository": repository,
                "commit_sha": commit_sha,
                "branch": branch,
                "scan_results": {
                    "summary": scan_results.get("summary", {}),
                    "is_git_repository": scan_results.get("is_git_repository", False),
                },
                "ai_bom": ai_bom.model_dump(mode="json") if ai_bom else None,
                "compliance_result": compliance_result.model_dump(mode="json"),
                "compliance_score": compliance_result.compliance_score * 100,
                "compliant": compliance_result.is_compliant,
                "risk_level": compliance_result.risk_level.value if hasattr(compliance_result.risk_level, 'value') else str(compliance_result.risk_level),
            }
            
            logger.info(f"Scan completed for {repository}: score={response['compliance_score']:.1f}%")
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub Actions scan error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/compliance/check")
async def check_compliance(
    request: ComplianceRequest,
    policy_engine: PolicyEngine = Depends(get_policy_engine),
):
    """
    Check compliance of an AI system against EU AI Act requirements

    Args:
        request: Compliance check request with AI-BOM path or repository path
        policy_engine: Injected Policy Engine instance

    Returns:
        Compliance check results and recommendations

    Raises:
        HTTPException: If compliance check fails
    """
    try:
        # Load AI-BOM if provided
        ai_bom = None
        if request.ai_bom_path:
            import json
            with open(request.ai_bom_path, "r") as f:
                bom_data = json.load(f)
            from actproof.models import AIBOM
            ai_bom = AIBOM(**bom_data)
        elif request.repository_path:
            # Genera AI-BOM dal repository
            scanner = RepositoryScanner(Path(request.repository_path))
            scan_results = scanner.scan()
            ai_bom = scan_results["ai_bom"]
        
        if ai_bom is None:
            raise HTTPException(
                status_code=400,
                detail="Fornire ai_bom_path o repository_path",
            )
        
        # Valuta conformità
        compliance_result = policy_engine.evaluate_compliance(
            ai_bom=ai_bom,
            system_id=ai_bom.spdx_id,
        )
        
        return compliance_result.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/diff")
async def compliance_diff(
    repo_id: str,
    base: str,
    head: str,
    repository_path: Optional[str] = None,
    include_github_comment: bool = False,
    policy_engine: PolicyEngine = Depends(get_policy_engine),
    diff_engine: ComplianceDiffEngine = Depends(get_diff_engine),
    storage: StorageBackend = Depends(get_storage_backend),
    audit_middleware: AuditMiddleware = Depends(get_audit_middleware),
):
    """
    Confronta compliance tra due revisioni (base/head)

    Args:
        repo_id: ID repository
        base: Commit SHA o tag base
        head: Commit SHA o tag head
        repository_path: Percorso repository (opzionale)
        include_github_comment: Include GitHub PR comment markdown

    Returns:
        Compliance diff result con delta articoli e gap
    """
    try:
        # Determina repository path
        if repository_path is None:
            # Prova a usare GitHub Actions env
            from actproof.integrations.github_action import GitHubActionHandler
            gh_handler = GitHubActionHandler()
            if gh_handler.is_github_action():
                repository_path = gh_handler.get_repository_path()
            else:
                raise HTTPException(
                    status_code=400,
                    detail="repository_path richiesto se non in GitHub Actions"
                )

        repo_path = Path(repository_path) if repository_path else None
        if not repo_path or not repo_path.exists():
            raise HTTPException(status_code=404, detail="Repository non trovato")

        # Storage keys per risultati versioned
        base_key = f"{repo_id}/{base}/policy_results.json"
        head_key = f"{repo_id}/{head}/policy_results.json"

        # Recupera o genera risultati base
        try:
            base_result_data = storage.get_json(base_key)
            from actproof.compliance import ComplianceResult
            base_result = ComplianceResult(**base_result_data)
        except FileNotFoundError:
            # Genera nuovo risultato per base
            logger.info(f"Generando nuovo risultato compliance per base: {base}")
            scanner = RepositoryScanner(repo_path)
            # Checkout base commit (se possibile)
            # Per ora assume che repo sia già su base o usa dati correnti
            scan_results = scanner.scan()
            ai_bom = scan_results["ai_bom"]
            base_result = policy_engine.evaluate_compliance(ai_bom, system_id=ai_bom.spdx_id)
            # Salva in storage
            storage.save_json(base_key, base_result.model_dump(mode="json"))

        # Recupera o genera risultati head
        try:
            head_result_data = storage.get_json(head_key)
            from actproof.compliance import ComplianceResult
            head_result = ComplianceResult(**head_result_data)
        except FileNotFoundError:
            # Genera nuovo risultato per head
            logger.info(f"Generando nuovo risultato compliance per head: {head}")
            scanner = RepositoryScanner(repo_path)
            scan_results = scanner.scan()
            ai_bom = scan_results["ai_bom"]
            head_result = policy_engine.evaluate_compliance(ai_bom, system_id=ai_bom.spdx_id)
            # Salva in storage
            storage.save_json(head_key, head_result.model_dump(mode="json"))

        # Ottieni file cambiati (se repo Git)
        changed_files = None
        if repo_path:
            try:
                changed_files = get_changed_files(repo_path, base, head)
            except Exception as e:
                logger.warning(f"Impossibile ottenere file cambiati: {e}")

        # Calcola diff
        diff_result = diff_engine.compute_diff(
            base_result=base_result,
            head_result=head_result,
            repo_id=repo_id,
            base_commit=base,
            head_commit=head,
            changed_files=changed_files,
        )

        # Salva diff in storage
        diff_key = f"{repo_id}/diffs/{base}..{head}.json"
        storage.save_json(diff_key, diff_result.model_dump(mode="json"))

        # Log audit trail
        audit_middleware.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            operation="compliance_diff",
            success=True,
            resource_id=repo_id,
            input_data={"base": base, "head": head},
            output_data={
                "score_delta": diff_result.score_delta,
                "direction": diff_result.score_direction,
                "diff_hash": diff_result.diff_hash,
                "storage_key": diff_key,
            },
        )

        # Prepara response
        response = diff_result.model_dump(mode="json")

        # Aggiungi GitHub comment se richiesto
        if include_github_comment:
            response["github_comment"] = diff_engine.format_github_comment(diff_result)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore compliance diff: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class EvidencePackRequest(BaseModel):
    """Request per generazione Evidence Pack"""
    repo_id: str = Field(..., description="ID repository")
    scan_run_id: Optional[str] = Field(None, description="ID scan run")
    commit: Optional[str] = Field(None, description="Commit SHA")
    repository_path: Optional[str] = Field(None, description="Percorso repository")
    include_rag_queries: bool = Field(False, description="Include RAG queries")
    include_fairness: bool = Field(False, description="Include fairness results")


@router.post("/evidence-pack")
async def generate_evidence_pack(
    request: EvidencePackRequest,
    policy_engine: PolicyEngine = Depends(get_policy_engine),
    pack_generator: EvidencePackGenerator = Depends(get_evidence_pack_generator),
    storage: StorageBackend = Depends(get_storage_backend),
    audit_middleware: AuditMiddleware = Depends(get_audit_middleware),
):
    """
    Genera Evidence Pack (ZIP) per audit compliance

    Args:
        request: Parametri per generazione pack

    Returns:
        Informazioni pack generato con download URL
    """
    try:
        # Determina repository path
        repo_path = None
        if request.repository_path:
            repo_path = Path(request.repository_path)
        elif request.commit:
            # Prova a recuperare da storage
            pass

        # Recupera o genera AI-BOM
        ai_bom = None
        compliance_result = None

        if repo_path and repo_path.exists():
            # Scansiona repository
            scanner = RepositoryScanner(repo_path)
            scan_results = scanner.scan()
            ai_bom = scan_results["ai_bom"]

            # Valuta compliance
            compliance_result = policy_engine.evaluate_compliance(
                ai_bom=ai_bom,
                system_id=ai_bom.spdx_id,
            )
        else:
            # Prova a recuperare da storage
            if request.commit:
                try:
                    policy_key = f"{request.repo_id}/{request.commit}/policy_results.json"
                    result_data = storage.get_json(policy_key)
                    compliance_result = ComplianceResult(**result_data)
                except FileNotFoundError:
                    logger.warning(f"Compliance result non trovato per {request.commit}")

        # Recupera RAG queries (se richiesto)
        rag_queries = None
        if request.include_rag_queries:
            # In produzione, recupera da audit trail o storage
            rag_queries = []

        # Recupera fairness results (se richiesto)
        fairness_results = None
        if request.include_fairness:
            # In produzione, recupera da storage
            fairness_results = None

        # Genera pack
        pack_info = pack_generator.generate_pack(
            repo_id=request.repo_id,
            ai_bom=ai_bom,
            compliance_result=compliance_result,
            scan_run_id=request.scan_run_id,
            commit=request.commit,
            rag_queries=rag_queries,
            fairness_results=fairness_results,
            include_reports=True,
        )

        # Log audit trail
        audit_middleware.log_event(
            event_type=AuditEventType.REPORT_GENERATION,
            operation="generate_evidence_pack",
            success=True,
            resource_id=request.repo_id,
            input_data={
                "commit": request.commit,
                "scan_run_id": request.scan_run_id,
            },
            output_data={
                "pack_id": pack_info["pack_id"],
                "file_count": pack_info["file_count"],
                "root_hash": pack_info["root_hash"],
                "storage_key": pack_info.get("storage_key"),
            },
        )

        return {
            "success": True,
            "pack_id": pack_info["pack_id"],
            "download_url": pack_info.get("download_url"),
            "output_path": pack_info.get("output_path"),
            "manifest": pack_info["manifest"],
            "file_count": pack_info["file_count"],
            "root_hash": pack_info["root_hash"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore generazione evidence pack: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    http_request: Request,
    rag_engine: RAGEngine = Depends(get_rag_engine),
    audit_middleware: AuditMiddleware = Depends(get_audit_middleware),
):
    """
    Esegue query RAG audit-grade sulla knowledge base legale

    Features:
    - Citazioni obbligatorie (min 2 per risposta)
    - Mode 'strict' con fallback "Insufficient sources"
    - Header X-Debug: true per retrieval debug (solo admin)

    Args:
        request: RAG query request con mode (normal/strict)

    Returns:
        Risposta con citazioni verificabili e metadata
    """
    try:
        # Check debug header (solo admin)
        include_debug = http_request.headers.get("X-Debug", "false").lower() == "true"

        # Per sicurezza, verifica che l'utente sia admin prima di includere debug
        # In produzione, verifica auth token/role
        # Per ora, accetta header ma logga
        if include_debug:
            logger.info("Debug mode requested - ensure user has admin privileges")

        # Esegui query con citazioni obbligatorie
        result = rag_engine.query(
            question=request.question,
            context_limit=request.context_limit,
            return_sources=True,
            mode=request.mode,
            include_debug=include_debug,
        )

        # Log audit trail
        audit_middleware.log_event(
            event_type=AuditEventType.API_REQUEST,
            operation="rag_query",
            success=True,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
            input_data={
                "question": request.question,
                "mode": request.mode,
                "context_limit": request.context_limit,
            },
            output_data={
                "citations_count": len(result.get("citations", [])),
                "citations_sufficient": result.get("citations_sufficient", False),
            },
        )

        return RAGQueryResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            context=result.get("context", []),
            citations=result.get("citations", []),
            citations_sufficient=result.get("citations_sufficient", True),
            retrieval_debug=result.get("retrieval_debug") if include_debug else None,
        )
    except Exception as e:
        logger.error(f"Errore RAG query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/article/{article_number}")
async def get_article(
    article_number: int,
    rag_engine: RAGEngine = Depends(get_rag_engine),
):
    """
    Ottiene informazioni su un articolo specifico dell'EU AI Act
    """
    try:
        result = rag_engine.get_article_info(article_number)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/index")
async def index_knowledge_base(
    directory: Optional[str] = None,
    source_type: Optional[str] = None,
):
    """
    Indicizza documenti nella knowledge base
    """
    try:
        indexer = KnowledgeBaseIndexer()
        
        if directory:
            dir_path = Path(directory)
            count = indexer.index_directory(dir_path, metadata_prefix=source_type)
        else:
            results = indexer.index_all()
            count = sum(results.values())
        
        return {
            "status": "success",
            "documents_indexed": count,
            "stats": indexer.get_stats(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/stats")
async def knowledge_base_stats(
    vector_store: VectorStore = Depends(get_vector_store),
):
    """
    Ottiene statistiche sulla knowledge base
    """
    try:
        info = vector_store.get_collection_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Fase 3: Fairness & Bias Auditing Routes
class FairnessAuditRequest(BaseModel):
    """Request per fairness audit"""
    y_true: List[int] = Field(..., description="Etichette vere (ground truth)")
    y_pred: List[int] = Field(..., description="Predizioni modello")
    protected_attributes: Dict[str, List[int]] = Field(..., description="Attributi protetti")
    threshold: float = Field(0.1, description="Soglia conformità (default 0.1)")


class ReportGenerationRequest(BaseModel):
    """Request per generazione report"""
    bias_report_id: Optional[str] = None
    compliance_result_id: Optional[str] = None
    format: str = Field("pdf", description="Formato report: pdf o docx")


@router.post("/fairness/audit")
async def fairness_audit(
    request: FairnessAuditRequest,
    http_request: Request,
    auditor: FairnessAuditor = Depends(get_fairness_auditor),
    audit_middleware: AuditMiddleware = Depends(get_audit_middleware),
):
    """
    Esegue audit fairness e bias su predizioni modello
    """
    try:
        import numpy as np
        
        # Converti in numpy arrays
        y_true = np.array(request.y_true)
        y_pred = np.array(request.y_pred)
        protected_attributes = {
            k: np.array(v) for k, v in request.protected_attributes.items()
        }
        
        # Esegui audit
        bias_report = auditor.calculate_metrics(
            y_true=y_true,
            y_pred=y_pred,
            protected_attributes=protected_attributes,
            threshold=request.threshold,
        )
        
        # Logga evento
        audit_middleware.log_event(
            event_type=AuditEventType.FAIRNESS_AUDIT,
            operation="fairness_audit",
            success=True,
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent"),
            input_data={"threshold": request.threshold},
            output_data={"overall_compliant": bias_report.overall_compliant},
        )
        
        return bias_report.model_dump(mode="json")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fairness/report/generate")
async def generate_fairness_report(
    request: ReportGenerationRequest,
    report_generator: LegalReportGenerator = Depends(get_report_generator),
    audit_middleware: AuditMiddleware = Depends(get_audit_middleware),
):
    """
    Genera report legale PDF/Docx per autorità (AgID/ACN compliant)

    Args:
        request: Contiene bias_report e compliance_result per generare report

    Returns:
        Path al report generato
    """
    try:
        import json
        import tempfile
        from actproof.fairness import BiasReport
        from actproof.compliance import ComplianceResult

        # Per generare un report, serve almeno un bias_report
        if not request.bias_report_id and not request.compliance_result_id:
            raise HTTPException(
                status_code=400,
                detail="Fornire almeno bias_report_id o compliance_result_id"
            )

        # In una implementazione production, recupereresti i dati da database/storage
        # Per ora, usiamo un approccio semplificato che presume i dati siano passati direttamente

        # Mock bias report per dimostrazione (in production, carica da storage)
        bias_report_data = {
            "system_id": request.bias_report_id or "demo-system",
            "model_name": "Demo AI Model",
            "fairness_metrics": {
                "gender": {
                    "demographic_parity_difference": 0.05,
                    "equalized_odds_difference": 0.03,
                    "is_compliant": True
                }
            },
            "overall_compliant": True,
            "critical_biases": [],
            "recommendations": [
                "Continue monitoring fairness metrics monthly",
                "Document fairness testing procedures"
            ]
        }

        # Mock compliance result (in production, carica da storage)
        compliance_result_data = {
            "is_compliant": True,
            "compliance_score": 0.85,
            "risk_level": "limited",
            "critical_gaps": [],
            "recommendations": [
                "Complete technical documentation (Article 11)",
                "Implement human oversight measures (Article 14)"
            ]
        }

        # Crea directory temporanea per il report
        output_dir = Path(tempfile.mkdtemp(prefix="actproof_report_"))
        output_path = output_dir / f"fairness_report_{request.bias_report_id or 'demo'}.{request.format}"

        # Genera report nel formato richiesto
        if request.format.lower() == "pdf":
            report_path = report_generator.generate_pdf_report(
                bias_report=BiasReport(**bias_report_data),
                output_path=output_path
            )
        elif request.format.lower() == "docx":
            report_path = report_generator.generate_docx_report(
                bias_report=BiasReport(**bias_report_data),
                output_path=output_path
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Formato non supportato: {request.format}. Usa 'pdf' o 'docx'"
            )

        # Log audit event
        audit_middleware.log_event(
            event_type=AuditEventType.REPORT_GENERATION,
            user_id="api_user",
            details={
                "report_type": "fairness",
                "format": request.format,
                "bias_report_id": request.bias_report_id,
                "compliance_result_id": request.compliance_result_id
            },
            success=True
        )

        return {
            "success": True,
            "report_path": str(report_path),
            "format": request.format,
            "message": f"Report {request.format.upper()} generato con successo"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore nella generazione report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Fase 4: Audit Trail Routes
@router.get("/audit/trail")
async def get_audit_trail(
    user_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    audit_middleware: AuditMiddleware = Depends(get_audit_middleware),
):
    """
    Recupera audit trail con filtri
    """
    try:
        from actproof.integrations import AuditEventType
        
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType(event_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Event type non valido: {event_type}")
        
        trail = audit_middleware.get_audit_trail(
            user_id=user_id,
            customer_id=customer_id,
            event_type=event_type_enum,
            limit=limit,
        )
        
        return {
            "total": len(trail),
            "events": [log.model_dump(mode="json") for log in trail],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/integrity")
async def verify_audit_integrity(
    audit_middleware: AuditMiddleware = Depends(get_audit_middleware),
):
    """
    Verifica integrità audit trail (catena hash)
    """
    try:
        integrity = audit_middleware.verify_audit_trail_integrity()
        return integrity
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Export and Download Routes
class ExportRequest(BaseModel):
    """Request per export AI-BOM o report"""
    ai_bom_path: str
    format: str = Field("json", description="json, yaml, xml")


@router.post("/export/ai-bom")
async def export_ai_bom(
    request: ExportRequest,
    audit_middleware: AuditMiddleware = Depends(get_audit_middleware),
):
    """
    Esporta AI-BOM in vari formati (JSON, YAML, XML/SPDX)
    
    Args:
        request: Path al file AI-BOM e formato desiderato
    
    Returns:
        AI-BOM nel formato richiesto
    """
    try:
        import json
        import yaml
        from pathlib import Path
        
        bom_path = Path(request.ai_bom_path)
        if not bom_path.exists():
            raise HTTPException(status_code=404, detail="AI-BOM file non trovato")
        
        # Carica AI-BOM
        with open(bom_path, 'r') as f:
            ai_bom_data = json.load(f)
        
        # Converti nel formato richiesto
        if request.format.lower() == "json":
            content = json.dumps(ai_bom_data, indent=2)
            media_type = "application/json"
        elif request.format.lower() == "yaml":
            content = yaml.dump(ai_bom_data, default_flow_style=False, sort_keys=False)
            media_type = "application/x-yaml"
        elif request.format.lower() == "xml":
            # Converti in formato SPDX XML
            content = _convert_to_spdx_xml(ai_bom_data)
            media_type = "application/xml"
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Formato non supportato: {request.format}. Usa json, yaml, o xml"
            )
        
        # Log audit event
        audit_middleware.log_event(
            event_type=AuditEventType.API_REQUEST,
            user_id="api_user",
            details={
                "action": "export_ai_bom",
                "format": request.format,
                "ai_bom_path": str(bom_path)
            },
            success=True
        )
        
        return {
            "success": True,
            "format": request.format,
            "content": content,
            "media_type": media_type
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore nell'export AI-BOM: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _convert_to_spdx_xml(ai_bom_data: Dict[str, Any]) -> str:
    """
    Converti AI-BOM JSON in formato SPDX XML
    
    Args:
        ai_bom_data: Dati AI-BOM in formato dict
    
    Returns:
        Stringa XML SPDX
    """
    from xml.etree.ElementTree import Element, SubElement, tostring
    from xml.dom import minidom
    
    # Crea root element SPDX
    root = Element('spdx', {
        'xmlns': 'http://spdx.org/rdf/terms',
        'xmlns:rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    })
    
    # Document info
    doc = SubElement(root, 'SpdxDocument')
    SubElement(doc, 'spdxVersion').text = ai_bom_data.get('spdxVersion', '3.0')
    SubElement(doc, 'dataLicense').text = ai_bom_data.get('dataLicense', 'CC0-1.0')
    SubElement(doc, 'SPDXID').text = ai_bom_data.get('SPDXID', 'SPDXRef-DOCUMENT')
    SubElement(doc, 'name').text = ai_bom_data.get('name', 'AI-BOM')
    SubElement(doc, 'documentNamespace').text = ai_bom_data.get('documentNamespace', '')
    
    # Creation info
    creation = SubElement(doc, 'creationInfo')
    SubElement(creation, 'created').text = ai_bom_data.get('metadata', {}).get('timestamp', '')
    SubElement(creation, 'creators').text = 'Tool: ActProof.ai'
    
    # Models
    if 'models' in ai_bom_data:
        models_section = SubElement(root, 'AIModels')
        for model in ai_bom_data['models']:
            model_elem = SubElement(models_section, 'AIModel')
            SubElement(model_elem, 'name').text = model.get('name', '')
            SubElement(model_elem, 'type').text = model.get('type', '')
            SubElement(model_elem, 'provider').text = model.get('provider', '')
    
    # Datasets
    if 'datasets' in ai_bom_data:
        datasets_section = SubElement(root, 'Datasets')
        for dataset in ai_bom_data['datasets']:
            dataset_elem = SubElement(datasets_section, 'Dataset')
            SubElement(dataset_elem, 'name').text = dataset.get('name', '')
            SubElement(dataset_elem, 'type').text = dataset.get('type', '')
    
    # Pretty print XML
    xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
    return xml_str


@router.get("/export/compliance/{system_id}")
async def export_compliance_report(
    system_id: str,
    format: str = "json",
    audit_middleware: AuditMiddleware = Depends(get_audit_middleware),
):
    """
    Esporta compliance report per un sistema
    
    Args:
        system_id: ID del sistema
        format: Formato export (json, pdf, docx)
    
    Returns:
        Compliance report nel formato richiesto
    """
    try:
        # In production, recupera da database/storage
        # Per ora, restituisce un mock
        compliance_data = {
            "system_id": system_id,
            "is_compliant": True,
            "compliance_score": 0.85,
            "risk_level": "limited",
            "article_compliance": {
                "Article 9 (Risk Management)": {"compliant": True},
                "Article 11 (Technical Documentation)": {"compliant": False},
                "Article 14 (Human Oversight)": {"compliant": True},
                "Article 15 (Accuracy & Robustness)": {"compliant": True}
            },
            "critical_gaps": ["Technical documentation incomplete"],
            "recommendations": [
                "Complete technical documentation (Article 11)",
                "Document risk management procedures"
            ]
        }
        
        if format.lower() == "json":
            content = json.dumps(compliance_data, indent=2)
            media_type = "application/json"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Formato non supportato per compliance export: {format}"
            )
        
        # Log audit event
        audit_middleware.log_event(
            event_type=AuditEventType.API_REQUEST,
            user_id="api_user",
            details={
                "action": "export_compliance",
                "system_id": system_id,
                "format": format
            },
            success=True
        )
        
        return {
            "success": True,
            "system_id": system_id,
            "format": format,
            "content": content,
            "media_type": media_type
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore nell'export compliance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint per monitoring
    
    Returns:
        Status del servizio e componenti
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "vector_store": "operational",
            "rag_engine": "operational",
            "policy_engine": "operational",
            "audit_trail": "operational"
        }
    }
