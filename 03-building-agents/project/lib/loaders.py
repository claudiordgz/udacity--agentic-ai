from typing import List
import os
import json
import glob
import pdfplumber
from lib.documents import Corpus, Document


class PDFLoader:
    """
    Document loader for extracting text content from PDF files.
    
    This class provides functionality to parse PDF documents and convert them
    into a structured format suitable for vector storage and retrieval. Each
    page of the PDF becomes a separate Document object, enabling page-level
    search and retrieval in RAG applications.
    
    The loader uses pdfplumber for robust PDF text extraction, handling:
    - Multi-page PDF documents
    - Text extraction with layout preservation
    - Automatic page numbering and identification
    - Filtering of empty or whitespace-only pages
    
    Example:
        >>> loader = PDFLoader("research_paper.pdf")
        >>> corpus = loader.load()
        >>> print(f"Loaded {len(corpus)} pages")
        >>> print(f"First page content: {corpus[0].content[:100]}...")
    """
    def __init__(self, pdf_path:str):
        self.pdf_path = pdf_path

    def load(self) -> Document:
        corpus = Corpus()

        with pdfplumber.open(self.pdf_path) as pdf:
            for num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    corpus.append(
                        Document(
                            id=str(num),
                            content=text
                        )
                    )
        return corpus


class JSONLoader:
    """
    Document loader for reading one or many JSON files and producing a Corpus.

    Expected file structure (example keys):
      {
        "Name": "Gran Turismo",
        "Platform": "PlayStation 1",
        "Genre": "Racing",
        "Publisher": "Sony Computer Entertainment",
        "Description": "A realistic racing simulator...",
        "YearOfRelease": 1997
      }

    Each JSON becomes a Document where:
      - id: filename stem (e.g., "001")
      - content: flattened textual summary built from key fields
      - metadata: the full JSON record
    """

    def __init__(self, path: str):
        self.path = path

    def _iter_file_paths(self) -> List[str]:
        if os.path.isdir(self.path):
            return sorted(glob.glob(os.path.join(self.path, "*.json")))
        return [self.path]

    def _to_content(self, record: dict) -> str:
        name = record.get("Name", "")
        platform = record.get("Platform", "")
        genre = record.get("Genre", "")
        publisher = record.get("Publisher", "")
        year = record.get("YearOfRelease", record.get("Year", ""))
        description = record.get("Description", "")
        parts = [
            f"Name: {name}",
            f"Platform: {platform}",
            f"Genre: {genre}",
            f"Publisher: {publisher}",
            f"Year: {year}",
            f"Description: {description}",
        ]
        return "\n".join(p for p in parts if p and not p.endswith(": "))

    def load(self) -> Corpus:
        corpus = Corpus()
        for file_path in self._iter_file_paths():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                doc_id = os.path.splitext(os.path.basename(file_path))[0]
                content = self._to_content(data)
                corpus.append(
                    Document(
                        id=doc_id,
                        content=content,
                        metadata=data,
                    )
                )
            except Exception as e:
                # Skip bad files but continue loading others
                print(f"Skipping {file_path}: {e}")
        return corpus
