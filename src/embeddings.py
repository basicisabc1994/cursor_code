"""Embedding generation using Nomic."""

import os
import logging
from typing import List, Dict, Any, Optional
import numpy as np

from nomic import embed
import nomic

from .config import settings

logger = logging.getLogger(__name__)


class NomicEmbeddings:
    """Generate embeddings using Nomic models."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize Nomic embeddings.
        
        Args:
            api_key: Nomic API key
            model: Model name to use
        """
        self.api_key = api_key or settings.nomic_api_key
        self.model = model or settings.embedding_model
        
        if not self.api_key:
            raise ValueError("Nomic API key is required. Set NOMIC_API_KEY in .env file")
        
        # Login to Nomic
        nomic.login(self.api_key)
        
        logger.info(f"Initialized Nomic embeddings with model: {self.model}")
    
    def embed_texts(self, texts: List[str], task_type: str = "search_document") -> np.ndarray:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            task_type: Task type for embedding (search_document, search_query, etc.)
            
        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        try:
            # Generate embeddings
            result = embed.text(
                texts=texts,
                model=self.model,
                task_type=task_type,
                dimensionality=settings.embedding_dimension
            )
            
            embeddings = np.array(result['embeddings'])
            logger.info(f"Generated embeddings for {len(texts)} texts")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Numpy array of embedding
        """
        embeddings = self.embed_texts([query], task_type="search_query")
        return embeddings[0] if len(embeddings) > 0 else np.array([])
    
    def embed_documents(self, documents: List[str]) -> np.ndarray:
        """Generate embeddings for documents.
        
        Args:
            documents: List of document texts
            
        Returns:
            Numpy array of embeddings
        """
        return self.embed_texts(documents, task_type="search_document")
    
    def embed_chunks(self, chunks: List[Any]) -> np.ndarray:
        """Generate embeddings for document chunks.
        
        Args:
            chunks: List of DocumentChunk objects
            
        Returns:
            Numpy array of embeddings
        """
        texts = [chunk.content for chunk in chunks]
        return self.embed_documents(texts)


class LocalEmbeddings:
    """Alternative: Generate embeddings using local sentence-transformers."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize local embeddings.
        
        Args:
            model_name: Name of the sentence-transformer model
        """
        from sentence_transformers import SentenceTransformer
        
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        
        logger.info(f"Initialized local embeddings with model: {model_name}")
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        logger.info(f"Generated embeddings for {len(texts)} texts")
        
        return embeddings
    
    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for a search query.
        
        Args:
            query: Search query text
            
        Returns:
            Numpy array of embedding
        """
        return self.model.encode([query], convert_to_numpy=True)[0]
    
    def embed_documents(self, documents: List[str]) -> np.ndarray:
        """Generate embeddings for documents.
        
        Args:
            documents: List of document texts
            
        Returns:
            Numpy array of embeddings
        """
        return self.embed_texts(documents)
    
    def embed_chunks(self, chunks: List[Any]) -> np.ndarray:
        """Generate embeddings for document chunks.
        
        Args:
            chunks: List of DocumentChunk objects
            
        Returns:
            Numpy array of embeddings
        """
        texts = [chunk.content for chunk in chunks]
        return self.embed_documents(texts)