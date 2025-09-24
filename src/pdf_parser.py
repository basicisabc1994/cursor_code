"""PDF parsing module using Docling."""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocument:
    """Represents a parsed document."""
    
    file_path: str
    title: Optional[str]
    content: str
    markdown: str
    metadata: Dict[str, Any]
    pages: int
    tables: List[Dict[str, Any]]
    images: List[Dict[str, Any]]


class PDFParser:
    """PDF document parser using Docling."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the PDF parser.
        
        Args:
            cache_dir: Directory for caching parsed documents
        """
        self.cache_dir = cache_dir or settings.docling_cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure Docling pipeline
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False  # Set to True if OCR is needed
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True
        
        # Initialize document converter
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend
                )
            }
        )
        
        logger.info("PDF Parser initialized with Docling")
    
    def parse_pdf(self, file_path: str) -> ParsedDocument:
        """Parse a single PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            ParsedDocument object containing parsed content
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        if not file_path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {file_path}")
        
        logger.info(f"Parsing PDF: {file_path}")
        
        try:
            # Convert document
            result = self.converter.convert(str(file_path))
            
            # Extract content
            document = result.document
            
            # Get markdown representation
            markdown_content = document.export_to_markdown()
            
            # Get plain text
            text_content = document.export_to_text()
            
            # Extract metadata
            metadata = {
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
                "page_count": len(document.pages) if hasattr(document, 'pages') else 0,
            }
            
            # Extract tables
            tables = []
            if hasattr(document, 'tables'):
                for table in document.tables:
                    tables.append({
                        "content": table.export_to_dataframe().to_dict() if hasattr(table, 'export_to_dataframe') else str(table),
                        "page": getattr(table, 'page_idx', None)
                    })
            
            # Extract images metadata
            images = []
            if hasattr(document, 'pictures'):
                for idx, picture in enumerate(document.pictures):
                    images.append({
                        "index": idx,
                        "page": getattr(picture, 'page_idx', None),
                        "caption": getattr(picture, 'caption', None)
                    })
            
            parsed_doc = ParsedDocument(
                file_path=str(file_path),
                title=getattr(document, 'title', file_path.stem),
                content=text_content,
                markdown=markdown_content,
                metadata=metadata,
                pages=metadata["page_count"],
                tables=tables,
                images=images
            )
            
            logger.info(f"Successfully parsed {file_path.name}: {parsed_doc.pages} pages, {len(tables)} tables, {len(images)} images")
            
            return parsed_doc
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise
    
    def parse_directory(self, directory_path: str, pattern: str = "*.pdf") -> List[ParsedDocument]:
        """Parse all PDF files in a directory.
        
        Args:
            directory_path: Path to directory containing PDFs
            pattern: File pattern to match (default: "*.pdf")
            
        Returns:
            List of ParsedDocument objects
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        pdf_files = list(directory_path.glob(pattern))
        logger.info(f"Found {len(pdf_files)} PDF files in {directory_path}")
        
        parsed_documents = []
        for pdf_file in pdf_files:
            try:
                parsed_doc = self.parse_pdf(str(pdf_file))
                parsed_documents.append(parsed_doc)
            except Exception as e:
                logger.error(f"Failed to parse {pdf_file}: {str(e)}")
                continue
        
        return parsed_documents
    
    def save_markdown(self, parsed_doc: ParsedDocument, output_dir: str = "./data/processed"):
        """Save parsed document as markdown.
        
        Args:
            parsed_doc: ParsedDocument object
            output_dir: Directory to save markdown files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        input_name = Path(parsed_doc.file_path).stem
        output_path = output_dir / f"{input_name}.md"
        
        # Add metadata header
        markdown_with_metadata = f"""---
title: {parsed_doc.title or input_name}
source: {parsed_doc.file_path}
pages: {parsed_doc.pages}
tables: {len(parsed_doc.tables)}
images: {len(parsed_doc.images)}
---

{parsed_doc.markdown}
"""
        
        # Save to file
        output_path.write_text(markdown_with_metadata, encoding='utf-8')
        logger.info(f"Saved markdown to {output_path}")
        
        return str(output_path)