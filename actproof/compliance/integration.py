"""
Integrazione Fase 1 (AI-BOM) con Fase 2 (Compliance)
Collega scanner repository con valutazione conformità
"""

from pathlib import Path
from typing import Optional
from actproof.scanner import RepositoryScanner
from actproof.compliance import PolicyEngine, ComplianceResult, DocumentGenerator
from actproof.models.ai_bom import AIBOM
from actproof.rag import RAGEngine, VectorStore


class CompliancePipeline:
    """
    Pipeline completa: Scansione -> AI-BOM -> Documentazione -> Compliance
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        openai_api_key: Optional[str] = None,
    ):
        """
        Inizializza pipeline
        
        Args:
            vector_store: Vector store per RAG (None = crea nuovo)
            openai_api_key: API key OpenAI per LLM (opzionale)
        """
        self.policy_engine = PolicyEngine()
        
        # Inizializza RAG se necessario
        self.rag_engine = None
        if vector_store:
            self.rag_engine = RAGEngine(vector_store=vector_store, openai_api_key=openai_api_key)
        
        self.document_generator = DocumentGenerator(rag_engine=self.rag_engine)

    async def full_pipeline(
        self,
        repository_path: Path,
        generate_documentation: bool = True,
        openai_api_key: Optional[str] = None,
    ) -> ComplianceResult:
        """
        Esegue pipeline completa: scan -> bom -> compliance
        
        Args:
            repository_path: Percorso repository da analizzare
            generate_documentation: Se generare documentazione automaticamente
            openai_api_key: API key OpenAI per generazione documentazione
        
        Returns:
            Risultato valutazione conformità
        """
        # Fase 1: Scansione repository
        print("🔍 Fase 1: Scansione repository...")
        scanner = RepositoryScanner(repository_path)
        scan_results = scanner.scan()
        ai_bom = scan_results["ai_bom"]
        
        print(f"   ✅ Trovati {len(ai_bom.models)} modelli, {len(ai_bom.datasets)} dataset")
        
        # Fase 2: Generazione documentazione tecnica
        technical_doc = None
        if generate_documentation:
            print("📝 Fase 2: Generazione documentazione tecnica...")
            technical_doc = await self.document_generator.generate_from_bom(
                ai_bom=ai_bom,
                openai_api_key=openai_api_key,
            )
            print("   ✅ Documentazione tecnica generata")
        
        # Fase 3: Valutazione conformità
        print("⚖️  Fase 3: Valutazione conformità...")
        compliance_result = self.policy_engine.evaluate_compliance(
            ai_bom=ai_bom,
            technical_doc=technical_doc,
            system_id=ai_bom.spdx_id,
        )
        
        print(f"   ✅ Conformità: {compliance_result.compliant}")
        print(f"   📊 Score: {compliance_result.requirements_check.compliance_score:.2%}")
        
        return compliance_result

    def scan_and_compliance(
        self,
        repository_path: Path,
        ai_bom_path: Optional[Path] = None,
    ) -> ComplianceResult:
        """
        Versione sincrona della pipeline (senza generazione documentazione LLM)
        
        Args:
            repository_path: Percorso repository
            ai_bom_path: Percorso AI-BOM esistente (opzionale)
        
        Returns:
            Risultato conformità
        """
        # Carica o genera AI-BOM
        if ai_bom_path and ai_bom_path.exists():
            import json
            with open(ai_bom_path, "r") as f:
                bom_data = json.load(f)
            ai_bom = AIBOM(**bom_data)
        else:
            scanner = RepositoryScanner(repository_path)
            scan_results = scanner.scan()
            ai_bom = scan_results["ai_bom"]
        
        # Valuta conformità
        compliance_result = self.policy_engine.evaluate_compliance(
            ai_bom=ai_bom,
            system_id=ai_bom.spdx_id,
        )
        
        return compliance_result
