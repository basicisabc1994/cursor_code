"""FAISS vector store for document embeddings."""

import os
import pickle
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

import faiss

from .config import settings
from .text_splitter import DocumentChunk

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for document embeddings."""
    
    def __init__(self, dimension: int = None, index_path: Optional[Path] = None):
        """Initialize FAISS vector store.
        
        Args:
            dimension: Embedding dimension
            index_path: Path to save/load index
        """
        self.dimension = int(dimension or settings.embedding_dimension)
        self.index_path = index_path or settings.faiss_index_path
        
        # Initialize FAISS index
        self.index = None
        self.documents = []
        self.metadata = []
        
        # Create or load index
        if self.index_path.exists():
            self.load()
        else:
            self.create_index()
    
    def create_index(self):
        """Create a new FAISS index."""
        # Use IndexFlatIP for inner product (cosine similarity after normalization)
        self.index = faiss.IndexFlatIP(self.dimension)
        
        # Optionally wrap with IDMap to track document IDs
        self.index = faiss.IndexIDMap(self.index)
        
        logger.info(f"Created new FAISS index with dimension {self.dimension}")
    
    def add_embeddings(self, embeddings: np.ndarray, chunks: List[DocumentChunk]):
        """Add embeddings and documents to the index.
        
        Args:
            embeddings: Numpy array of embeddings
            chunks: List of DocumentChunk objects
        """
        if self.index is None:
            self.create_index()
        
        # Ensure correct dtype and shape then normalize for cosine similarity
        if embeddings is None or len(embeddings) == 0:
            return
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension mismatch: got {embeddings.shape[1]}, expected {self.dimension}")
        faiss.normalize_L2(embeddings)
        
        # Generate IDs for documents
        start_id = len(self.documents)
        ids = np.arange(start_id, start_id + len(chunks)).astype('int64')
        
        # Add to index
        self.index.add_with_ids(embeddings, ids)
        
        # Store documents and metadata
        for chunk in chunks:
            self.documents.append(chunk.content)
            self.metadata.append(chunk.metadata)
        
        logger.info(f"Added {len(chunks)} documents to index. Total documents: {len(self.documents)}")
    
    def search(self, query_embedding: np.ndarray, k: int = None) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of tuples (document, score, metadata)
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index is empty")
            return []
        
        k = k or settings.top_k_results
        k = min(k, self.index.ntotal)
        
        # Normalize query embedding
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        if query_embedding.shape[1] != self.dimension:
            raise ValueError(f"Query embedding dimension mismatch: got {query_embedding.shape[1]}, expected {self.dimension}")
        faiss.normalize_L2(query_embedding)
        
        # Search
        distances, indices = self.index.search(query_embedding, k)
        
        # Prepare results
        results = []
        for i in range(len(indices[0])):
            idx = indices[0][i]
            if idx >= 0:  # Valid index
                results.append((
                    self.documents[idx],
                    float(distances[0][i]),
                    self.metadata[idx]
                ))
        
        return results
    
    def save(self, index_path: Optional[Path] = None):
        """Save index and metadata to disk.
        
        Args:
            index_path: Path to save index (uses default if not provided)
        """
        save_path = index_path or self.index_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path))
        
        # Save documents and metadata
        metadata_path = save_path.with_suffix('.meta')
        with open(metadata_path, 'wb') as f:
            pickle.dump({
                'documents': self.documents,
                'metadata': self.metadata,
                'dimension': self.dimension
            }, f)
        
        logger.info(f"Saved index to {save_path}")
    
    def load(self, index_path: Optional[Path] = None):
        """Load index and metadata from disk.
        
        Args:
            index_path: Path to load index from
        """
        load_path = index_path or self.index_path
        
        if not load_path.exists():
            logger.warning(f"Index file not found: {load_path}")
            return
        
        # Load FAISS index
        self.index = faiss.read_index(str(load_path))
        
        # Load documents and metadata
        metadata_path = load_path.with_suffix('.meta')
        if metadata_path.exists():
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data['documents']
                self.metadata = data['metadata']
                self.dimension = data['dimension']
        
        logger.info(f"Loaded index from {load_path} with {len(self.documents)} documents")
    
    def clear(self):
        """Clear the index."""
        self.create_index()
        self.documents = []
        self.metadata = []
        logger.info("Cleared index")
    
    def delete(self):
        """Delete the index files."""
        if self.index_path.exists():
            self.index_path.unlink()
        
        metadata_path = self.index_path.with_suffix('.meta')
        if metadata_path.exists():
            metadata_path.unlink()
        
        logger.info("Deleted index files")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_type": type(self.index).__name__ if self.index else None,
            "memory_usage_mb": self.index.ntotal * self.dimension * 4 / (1024 * 1024) if self.index else 0
        }