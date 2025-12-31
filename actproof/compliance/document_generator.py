"""
Generatore automatico di documentazione tecnica
Usa LLM per estrarre logica del sistema e popolare dossier tecnico
"""

from typing import Optional, Dict, Any
from actproof.compliance.requirements import TechnicalDocumentation
from actproof.models.ai_bom import AIBOM
from actproof.rag import RAGEngine


class DocumentGenerator:
    """Genera documentazione tecnica automaticamente"""

    def __init__(self, rag_engine: Optional[RAGEngine] = None):
        """
        Inizializza generatore
        
        Args:
            rag_engine: RAG engine per query su requisiti legali
        """
        self.rag_engine = rag_engine

    async def generate_from_bom(
        self,
        ai_bom: AIBOM,
        llm: Optional[Any] = None,
        openai_api_key: Optional[str] = None,
    ) -> TechnicalDocumentation:
        """
        Genera documentazione tecnica da AI-BOM usando LLM
        
        Args:
            ai_bom: AI-BOM del sistema
            llm: LLM da usare (opzionale)
            openai_api_key: API key OpenAI (opzionale)
        
        Returns:
            Documentazione tecnica generata
        """
        # Prepara contesto dal AI-BOM
        bom_summary = self._prepare_bom_summary(ai_bom)
        
        # Se LLM disponibile, usa per estrarre informazioni
        if llm or openai_api_key:
            try:
                from langchain_openai import ChatOpenAI
                if llm is None:
                    llm = ChatOpenAI(
                        model_name="gpt-4",
                        temperature=0,
                        openai_api_key=openai_api_key,
                    )
                
                # Estrai informazioni con LLM
                extracted_info = await self._extract_with_llm(llm, bom_summary)
            except Exception as e:
                print(f"Errore nell'estrazione LLM: {e}")
                extracted_info = {}
        else:
            extracted_info = {}
        
        # Costruisci documentazione tecnica
        doc = TechnicalDocumentation(
            system_name=ai_bom.name.replace("AI-BOM for ", ""),
            system_version="1.0.0",
            general_description=extracted_info.get(
                "general_description",
                f"Sistema AI con {len(ai_bom.models)} modelli e {len(ai_bom.datasets)} dataset",
            ),
            intended_purpose=extracted_info.get(
                "intended_purpose",
                "Da specificare in base all'analisi del codice",
            ),
            context_of_use=extracted_info.get(
                "context_of_use",
                "Da specificare in base all'analisi del codice",
            ),
            logic_description=extracted_info.get(
                "logic_description",
                "Logica del sistema da estrarre dall'analisi del codice sorgente",
            ),
            training_data_description=extracted_info.get("training_data_description"),
            software_dependencies=[d.name for d in ai_bom.dependencies[:20]],
        )
        
        return doc

    def _prepare_bom_summary(self, ai_bom: AIBOM) -> str:
        """Prepara summary del AI-BOM per LLM"""
        summary = f"Sistema AI: {ai_bom.name}\n\n"
        summary += f"Modelli ({len(ai_bom.models)}):\n"
        for model in ai_bom.models[:5]:
            summary += f"  - {model.name} ({model.model_type.value})"
            if model.provider:
                summary += f" da {model.provider}"
            summary += "\n"
        
        summary += f"\nDataset ({len(ai_bom.datasets)}):\n"
        for dataset in ai_bom.datasets[:5]:
            summary += f"  - {dataset.name} ({dataset.dataset_type.value})\n"
        
        summary += f"\nDipendenze principali ({len(ai_bom.dependencies)}):\n"
        ai_deps = [d for d in ai_bom.dependencies if d.is_ai_related][:10]
        for dep in ai_deps:
            summary += f"  - {dep.name} {dep.version or ''}\n"
        
        return summary

    async def _extract_with_llm(
        self, llm: Any, bom_summary: str
    ) -> Dict[str, Any]:
        """Estrae informazioni usando LLM"""
        prompt = f"""Analizza questo sistema AI e estrai le seguenti informazioni:

{bom_summary}

Estrai:
1. Descrizione generale del sistema e del suo scopo
2. Scopo previsto (intended purpose)
3. Contesto d'uso (chi lo usa, quando, come)
4. Descrizione logica del sistema (come funziona)
5. Informazioni sui dati di addestramento se disponibili

Rispondi in formato JSON con chiavi: general_description, intended_purpose, context_of_use, logic_description, training_data_description."""

        try:
            response = llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Parse JSON response (semplificato)
            import json
            # Cerca JSON nel response
            try:
                # Prova a estrarre JSON
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
            except:
                pass
            
            # Fallback: estrai informazioni manualmente
            return {
                "general_description": content[:500] if len(content) > 500 else content,
                "intended_purpose": "Da specificare",
                "context_of_use": "Da specificare",
                "logic_description": content,
            }
        except Exception as e:
            print(f"Errore nell'estrazione LLM: {e}")
            return {}
