"""RAG (Retrieval-Augmented Generation) pipeline."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from .pdf_parser import PDFParser, ParsedDocument
from .text_splitter import TextSplitter, DocumentChunk
from .embeddings import NomicEmbeddings, LocalEmbeddings
from .vector_store import FAISSVectorStore
from .config import settings

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Complete RAG pipeline for PDF documents."""
    
    def __init__(
        self,
        use_local_embeddings: bool = False,
        embedding_model: Optional[str] = None,
        index_path: Optional[Path] = None
    ):
        """Initialize RAG pipeline.
        
        Args:
            use_local_embeddings: Use local embeddings instead of Nomic
            embedding_model: Embedding model to use
            index_path: Path to FAISS index
        """
        # Initialize components
        self.pdf_parser = PDFParser()
        self.text_splitter = TextSplitter()
        
        # Initialize embeddings
        if use_local_embeddings:
            self.embedder = LocalEmbeddings(model_name=embedding_model or "all-MiniLM-L6-v2")
        else:
            self.embedder = NomicEmbeddings(model=embedding_model)
        
        # Initialize vector store
        self.vector_store = FAISSVectorStore(index_path=index_path)
        
        # Store processed documents
        self.processed_documents = []
        
        logger.info("RAG Pipeline initialized")
    
    def process_pdf(self, file_path: str, save_markdown: bool = True) -> ParsedDocument:
        """Process a single PDF file.
        
        Args:
            file_path: Path to PDF file
            save_markdown: Whether to save markdown output
            
        Returns:
            ParsedDocument object
        """
        # Parse PDF
        parsed_doc = self.pdf_parser.parse_pdf(file_path)
        
        # Save markdown if requested
        if save_markdown:
            self.pdf_parser.save_markdown(parsed_doc)
        
        # Split into chunks
        chunks = self.text_splitter.split_markdown(
            parsed_doc.markdown,
            parsed_doc.file_path,
            {"title": parsed_doc.title, "pages": parsed_doc.pages}
        )
        
        # Generate embeddings
        embeddings = self.embedder.embed_chunks(chunks)
        
        # Add to vector store
        self.vector_store.add_embeddings(embeddings, chunks)
        
        # Store processed document
        self.processed_documents.append(parsed_doc)
        
        logger.info(f"Processed PDF: {file_path} -> {len(chunks)} chunks")
        
        return parsed_doc
    
    def process_directory(self, directory_path: str, pattern: str = "*.pdf", save_markdown: bool = True) -> List[ParsedDocument]:
        """Process all PDFs in a directory.
        
        Args:
            directory_path: Path to directory
            pattern: File pattern to match
            save_markdown: Whether to save markdown outputs
            
        Returns:
            List of ParsedDocument objects
        """
        directory_path = Path(directory_path)
        
        # Parse all PDFs
        parsed_docs = self.pdf_parser.parse_directory(directory_path, pattern)
        
        all_chunks = []
        
        for doc in parsed_docs:
            # Save markdown if requested
            if save_markdown:
                self.pdf_parser.save_markdown(doc)
            
            # Split into chunks
            chunks = self.text_splitter.split_markdown(
                doc.markdown,
                doc.file_path,
                {"title": doc.title, "pages": doc.pages}
            )
            
            all_chunks.extend(chunks)
            self.processed_documents.append(doc)
        
        # Generate embeddings in batch
        if all_chunks:
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
            embeddings = self.embedder.embed_chunks(all_chunks)
            
            # Add to vector store
            self.vector_store.add_embeddings(embeddings, all_chunks)
        
        logger.info(f"Processed {len(parsed_docs)} PDFs -> {len(all_chunks)} total chunks")
        
        return parsed_docs
    
    def search(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, k)
        
        # Format results
        formatted_results = []
        for content, score, metadata in results:
            formatted_results.append({
                "content": content,
                "score": score,
                "metadata": metadata
            })
        
        return formatted_results
    
    def query(self, question: str, k: int = None, return_context: bool = True) -> Dict[str, Any]:
        """Query the RAG system.
        
        Args:
            question: Question to answer
            k: Number of documents to retrieve
            return_context: Whether to return retrieved context
            
        Returns:
            Dictionary with answer and optionally context
        """
        # Search for relevant documents
        search_results = self.search(question, k)
        
        # Prepare context
        context = "\n\n".join([result["content"] for result in search_results])
        
        # Prepare response
        response = {
            "question": question,
            "num_results": len(search_results)
        }
        
        if return_context:
            response["context"] = context
            response["sources"] = [
                {
                    "content": result["content"][:200] + "...",
                    "score": result["score"],
                    "source": result["metadata"].get("source", "Unknown")
                }
                for result in search_results
            ]
        
        # Note: For actual answer generation, you would integrate with an LLM here
        # For now, we return the retrieved context
        response["answer"] = f"Based on the retrieved documents, here are the {len(search_results)} most relevant passages to your question."
        
        return response
    
    def save_index(self, path: Optional[Path] = None):
        """Save the vector store index.
        
        Args:
            path: Path to save index
        """
        self.vector_store.save(path)
        logger.info(f"Saved index to {path or self.vector_store.index_path}")
    
    def load_index(self, path: Optional[Path] = None):
        """Load a vector store index.
        
        Args:
            path: Path to load index from
        """
        self.vector_store.load(path)
        logger.info(f"Loaded index from {path or self.vector_store.index_path}")
    
    def clear_index(self):
        """Clear the vector store index."""
        self.vector_store.clear()
        self.processed_documents = []
        logger.info("Cleared index and processed documents")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the RAG pipeline.
        
        Returns:
            Dictionary with statistics
        """
        stats = self.vector_store.get_statistics()
        stats.update({
            "processed_documents": len(self.processed_documents),
            "total_pages": sum(doc.pages for doc in self.processed_documents),
            "embedding_model": getattr(self.embedder, 'model', 'Unknown')
        })
        return stats