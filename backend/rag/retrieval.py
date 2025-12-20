"""
RAG Retrieval Module: Semantic search over policy documents.

This module implements the retrieval component of RAG:
1. Loads the FAISS vector index and metadata
2. Embeds user queries using the same embedding model
3. Performs similarity search to find relevant chunks
4. Optionally filters by policy_type and region
5. Returns top-k most relevant chunks with metadata

How similarity search works:
- User query is embedded into the same vector space as document chunks
- FAISS computes cosine similarity (or L2 distance) between query and all chunks
- Top-k chunks with highest similarity are returned
- Metadata filtering can be applied post-retrieval or pre-retrieval (if using FAISS filtering)
"""

import faiss
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any
import pickle
from sentence_transformers import SentenceTransformer

import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings


class RetrievedChunk:
    """
    Represents a retrieved chunk with similarity score and metadata.
    
    Attributes:
        text: The chunk text
        policy_id: Source policy ID
        policy_type: Type of policy
        region: Geographic region
        clause_type: Type of clause
        similarity_score: Similarity score from FAISS search
        metadata: Full metadata dictionary
    """
    def __init__(self, text: str, policy_id: str, policy_type: str,
                 region: str, clause_type: str, similarity_score: float,
                 metadata: Dict[str, Any]):
        self.text = text
        self.policy_id = policy_id
        self.policy_type = policy_type
        self.region = region
        self.clause_type = clause_type
        self.similarity_score = similarity_score
        self.metadata = metadata


class PolicyRetriever:
    """
    Handles retrieval of relevant policy chunks using FAISS.
    
    This class manages:
    - Loading the FAISS index and metadata
    - Embedding queries
    - Performing similarity search
    - Filtering results by metadata
    """
    
    def __init__(self, index_path: Optional[str] = None, 
                 metadata_path: Optional[str] = None,
                 embedding_model_name: Optional[str] = None):
        """
        Initialize the retriever.
        
        Args:
            index_path: Path to FAISS index file (defaults to settings)
            metadata_path: Path to metadata pickle file (defaults to settings)
            embedding_model_name: Name of embedding model (defaults to settings)
        """
        # Use settings defaults if not provided
        # Convert to Path objects for easier manipulation
        base_path = Path(settings.VECTOR_STORE_PATH)
        self.index_path = Path(index_path) if index_path else base_path / f"{settings.FAISS_INDEX_NAME}.index"
        self.metadata_path = Path(metadata_path) if metadata_path else base_path / f"{settings.FAISS_INDEX_NAME}_metadata.pkl"
        self.embedding_model_name = embedding_model_name or settings.EMBEDDING_MODEL_NAME
        
        # Load index and metadata
        self.index = None
        self.metadata = None
        self.embedding_model = None
        
        self._load_index()
        self._load_metadata()
        self._load_embedding_model()
    
    def _load_index(self) -> None:
        """Load FAISS index from disk."""
        index_path_obj = Path(self.index_path)
        if not index_path_obj.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {self.index_path}. "
                f"Please run the ingestion pipeline first: python -m rag.ingest"
            )
        try:
            self.index = faiss.read_index(str(self.index_path))
            print(f"Loaded FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load FAISS index from {self.index_path}: {str(e)}. "
                f"Please rebuild the index by running: python -m rag.ingest"
            ) from e
    
    def _load_metadata(self) -> None:
        """Load metadata from pickle file."""
        metadata_path_obj = Path(self.metadata_path)
        if not metadata_path_obj.exists():
            raise FileNotFoundError(
                f"Metadata file not found at {self.metadata_path}. "
                f"Please run the ingestion pipeline first: python -m rag.ingest"
            )
        try:
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            print(f"Loaded metadata for {len(self.metadata)} chunks")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load metadata from {self.metadata_path}: {str(e)}. "
                f"Please rebuild the index by running: python -m rag.ingest"
            ) from e
    
    def _load_embedding_model(self) -> None:
        """Load the embedding model."""
        try:
            print(f"Loading embedding model: {self.embedding_model_name}")
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            print("Embedding model loaded successfully")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load embedding model '{self.embedding_model_name}': {str(e)}. "
                f"Please ensure sentence-transformers is installed: pip install sentence-transformers"
            ) from e
    
    def retrieve_relevant_chunks(
        self,
        query: str,
        policy_type: Optional[str] = None,
        region: Optional[str] = None,
        k: int = 5
    ) -> List[RetrievedChunk]:
        """
        Retrieve top-k relevant chunks for a query.
        
        This method NEVER raises exceptions - it always returns a list (possibly empty).
        
        Process:
        1. Embed the query
        2. Search FAISS index for top-k similar chunks
        3. Optionally filter by policy_type and region
        4. Return RetrievedChunk objects with metadata
        
        Args:
            query: User's question or search query
            policy_type: Optional filter for policy type (health, car, bike)
            region: Optional filter for region
            k: Number of chunks to retrieve (default: 5)
            
        Returns:
            List of RetrievedChunk objects, sorted by similarity (highest first)
            Returns empty list if any error occurs
        """
        try:
            if not query or not query.strip():
                print("⚠️ Empty query received by retriever")
                return []

            if not self.index or not self.metadata or not self.embedding_model:
                print("⚠️ Retriever not properly initialized")
                return []

            # Embed the query
            query_embedding = self.embedding_model.encode(
                [query],
                show_progress_bar=False,
                convert_to_numpy=True
            ).astype('float32')
            
            # Normalize for cosine similarity (must match how index was built)
            faiss.normalize_L2(query_embedding)
            
            # Search for top-k results (we retrieve more if filtering is needed)
            search_k = min(k * 4 if (policy_type or region) else k * 2, max(1, self.index.ntotal))
            
            # Perform similarity search
            distances, indices = self.index.search(query_embedding, search_k)
            
            # Build results with metadata
            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx == -1:  # FAISS returns -1 for invalid indices
                    continue
                
                # Defensive metadata access
                if idx >= len(self.metadata):
                    continue
                    
                chunk_metadata = self.metadata[idx] or {}
                text = chunk_metadata.get("text") or ""
                if not text.strip():
                    # Skip empty chunks but keep searching
                    continue
                
                # Apply filters if specified
                if policy_type and chunk_metadata.get("policy_type") != policy_type:
                    continue
                if region and chunk_metadata.get("region") != region:
                    continue
                
                # Convert distance to similarity score (for L2: lower is better, for cosine: higher is better)
                # Since we normalized, we're using cosine similarity
                # FAISS L2 on normalized vectors = 2 - 2*cosine_similarity
                # So similarity = 1 - (distance / 2)
                similarity = 1 - (distance / 2) if distance <= 2 else 0
                
                retrieved_chunk = RetrievedChunk(
                    text=text,
                    policy_id=chunk_metadata.get("policy_id", "unknown_policy"),
                    policy_type=chunk_metadata.get("policy_type", "unknown"),
                    region=chunk_metadata.get("region", "unspecified"),
                    clause_type=chunk_metadata.get("clause_type", "general"),
                    similarity_score=similarity,
                    metadata=chunk_metadata
                )
                results.append(retrieved_chunk)
                
                # Stop if we have enough results
                if len(results) >= k:
                    break
            
            if not results:
                print("⚠️ Retriever returned zero chunks after filtering")
            return results
            
        except Exception as e:
            # NEVER raise - always return empty list
            print(f"⚠️ Error in retrieve_relevant_chunks: {str(e)}")
            import traceback
            traceback.print_exc()
            return []


# Global retriever instance (lazy-loaded)
_retriever_instance = None
_retriever_available = False


def get_retriever() -> Optional[PolicyRetriever]:
    """
    Get or create the global retriever instance.
    
    Returns:
        PolicyRetriever instance if available, None otherwise
    """
    global _retriever_instance, _retriever_available
    
    if _retriever_available:
        return _retriever_instance
    
    if _retriever_instance is None:
        try:
            _retriever_instance = PolicyRetriever()
            _retriever_available = True
            print("✅ Retriever initialized successfully")
        except FileNotFoundError as e:
            print(f"⚠️ Retriever not available: {str(e)}")
            print("   System will use general conversation mode")
            _retriever_instance = None
            _retriever_available = False
        except Exception as e:
            print(f"⚠️ Retriever initialization failed: {str(e)}")
            print("   System will use general conversation mode")
            _retriever_instance = None
            _retriever_available = False
    
    return _retriever_instance


def retrieve_relevant_chunks(
    query: str,
    policy_type: Optional[str] = None,
    region: Optional[str] = None,
    k: int = 5
) -> List[RetrievedChunk]:
    """
    Convenience function to retrieve chunks.
    
    This function NEVER raises exceptions - it always returns a list (possibly empty).
    
    Args:
        query: User's question or search query
        policy_type: Optional filter for policy type
        region: Optional filter for region
        k: Number of chunks to retrieve
        
    Returns:
        List of RetrievedChunk objects (empty list if retrieval fails)
    """
    try:
        retriever = get_retriever()
        if retriever is None:
            print("⚠️ Retriever not available, returning empty chunks")
            return []
        
        return retriever.retrieve_relevant_chunks(query, policy_type, region, k)
    except Exception as e:
        # NEVER raise - always return empty list on any error
        print(f"⚠️ Retrieval error (returning empty): {str(e)}")
        import traceback
        traceback.print_exc()
        return []

