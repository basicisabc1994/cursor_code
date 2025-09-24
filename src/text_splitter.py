"""Text splitting utilities for chunking documents."""

import re
from typing import List, Dict, Any
from dataclasses import dataclass

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter
)

from .config import settings


@dataclass
class DocumentChunk:
    """Represents a chunk of a document."""
    
    content: str
    metadata: Dict[str, Any]
    chunk_id: int
    source_file: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "chunk_id": self.chunk_id,
            "source_file": self.source_file
        }


class TextSplitter:
    """Handles text splitting for documents."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """Initialize text splitter.
        
        Args:
            chunk_size: Maximum size of chunks
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        # Initialize splitters
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
            length_function=len
        )
        
        # Markdown header splitter for structured documents
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
            ]
        )
    
    def split_text(self, text: str, source_file: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """Split text into chunks.
        
        Args:
            text: Text to split
            source_file: Source file path
            metadata: Additional metadata
            
        Returns:
            List of DocumentChunk objects
        """
        metadata = metadata or {}
        
        # Split text
        chunks = self.text_splitter.split_text(text)
        
        # Create DocumentChunk objects
        document_chunks = []
        for idx, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk)
            }
            
            document_chunks.append(
                DocumentChunk(
                    content=chunk,
                    metadata=chunk_metadata,
                    chunk_id=idx,
                    source_file=source_file
                )
            )
        
        return document_chunks
    
    def split_markdown(self, markdown: str, source_file: str, metadata: Dict[str, Any] = None) -> List[DocumentChunk]:
        """Split markdown text preserving structure.
        
        Args:
            markdown: Markdown text to split
            source_file: Source file path
            metadata: Additional metadata
            
        Returns:
            List of DocumentChunk objects
        """
        metadata = metadata or {}
        
        # First split by headers
        header_splits = self.markdown_splitter.split_text(markdown)
        
        # Then split each section if needed
        document_chunks = []
        chunk_id = 0
        
        for doc in header_splits:
            # Extract headers from metadata
            section_metadata = {
                **metadata,
                **doc.metadata
            }
            
            # Further split if section is too large
            if len(doc.page_content) > self.chunk_size:
                sub_chunks = self.text_splitter.split_text(doc.page_content)
                for sub_chunk in sub_chunks:
                    document_chunks.append(
                        DocumentChunk(
                            content=sub_chunk,
                            metadata=section_metadata,
                            chunk_id=chunk_id,
                            source_file=source_file
                        )
                    )
                    chunk_id += 1
            else:
                document_chunks.append(
                    DocumentChunk(
                        content=doc.page_content,
                        metadata=section_metadata,
                        chunk_id=chunk_id,
                        source_file=source_file
                    )
                )
                chunk_id += 1
        
        # Update total chunks in metadata
        for chunk in document_chunks:
            chunk.metadata["total_chunks"] = len(document_chunks)
        
        return document_chunks
    
    def split_documents(self, documents: List[Any], use_markdown: bool = True) -> List[DocumentChunk]:
        """Split multiple documents.
        
        Args:
            documents: List of ParsedDocument objects
            use_markdown: Whether to use markdown splitting
            
        Returns:
            List of all DocumentChunk objects
        """
        all_chunks = []
        
        for doc in documents:
            doc_metadata = {
                "title": doc.title,
                "pages": doc.pages,
                "source": doc.file_path
            }
            
            if use_markdown and hasattr(doc, 'markdown'):
                chunks = self.split_markdown(
                    doc.markdown,
                    doc.file_path,
                    doc_metadata
                )
            else:
                chunks = self.split_text(
                    doc.content,
                    doc.file_path,
                    doc_metadata
                )
            
            all_chunks.extend(chunks)
        
        return all_chunks