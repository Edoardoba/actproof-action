"""
Loader per documenti legali (EU AI Act, ISO/IEC 42001, etc.)
"""

from pathlib import Path
from typing import List, Dict, Any
import re


class DocumentLoader:
    """Carica e processa documenti legali"""

    def __init__(self):
        self.supported_formats = [".txt", ".md", ".pdf"]

    def load_text_file(self, file_path: Path) -> str:
        """Carica file di testo"""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def load_markdown_file(self, file_path: Path) -> str:
        """Carica file Markdown"""
        return self.load_text_file(file_path)

    def load_pdf_file(self, file_path: Path) -> str:
        """Carica file PDF (richiede pypdf)"""
        try:
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise ImportError("pypdf richiesto per caricare PDF. Esegui: pip install pypdf")

    def load_document(self, file_path: Path) -> str:
        """Carica documento in base all'estensione"""
        ext = file_path.suffix.lower()
        
        if ext == ".txt" or ext == ".md":
            return self.load_text_file(file_path)
        elif ext == ".pdf":
            return self.load_pdf_file(file_path)
        else:
            raise ValueError(f"Formato non supportato: {ext}")

    def chunk_document(
        self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200
    ) -> List[str]:
        """
        Divide documento in chunk per indicizzazione
        
        Args:
            text: Testo da dividere
            chunk_size: Dimensione chunk (caratteri)
            chunk_overlap: Overlap tra chunk
        
        Returns:
            Lista di chunk
        """
        # Dividi per paragrafi quando possibile
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Se il paragrafo è troppo grande, dividilo
            if len(para) > chunk_size:
                # Aggiungi chunk corrente se esiste
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # Dividi paragrafo grande
                words = para.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 > chunk_size:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                        temp_chunk = word
                    else:
                        temp_chunk += " " + word if temp_chunk else word
                if temp_chunk:
                    current_chunk = temp_chunk
            else:
                # Se aggiungere questo paragrafo supera chunk_size, salva chunk corrente
                if len(current_chunk) + len(para) + 2 > chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    # Mantieni overlap
                    words = current_chunk.split()
                    overlap_words = words[-chunk_overlap // 10:] if len(words) > chunk_overlap // 10 else words
                    current_chunk = " ".join(overlap_words) + "\n\n" + para
                else:
                    current_chunk += "\n\n" + para if current_chunk else para
        
        # Aggiungi ultimo chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def load_directory(
        self, directory: Path, recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Carica tutti i documenti da una directory
        
        Args:
            directory: Directory da scansionare
            recursive: Se scansionare ricorsivamente
        
        Returns:
            Lista di documenti con metadati
        """
        documents = []
        
        pattern = "**/*" if recursive else "*"
        for file_path in directory.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                try:
                    text = self.load_document(file_path)
                    chunks = self.chunk_document(text)
                    
                    for i, chunk in enumerate(chunks):
                        documents.append({
                            "text": chunk,
                            "metadata": {
                                "source": str(file_path),
                                "filename": file_path.name,
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                            },
                        })
                except Exception as e:
                    print(f"Errore nel caricamento di {file_path}: {e}")
        
        return documents
