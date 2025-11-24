"""
RAG Ingestion Pipeline: Load, chunk, and index policy documents.

This module handles:
1. Loading policy documents from JSON files
2. Chunking text into overlapping segments
3. Creating embeddings using sentence transformers
4. Building and saving a FAISS vector index with metadata

Why chunking?
- Large documents don't fit in LLM context windows
- Chunking allows retrieval of specific relevant sections
- Overlapping chunks preserve context at boundaries

Chunk size: 500 characters (balance between context and granularity)
Overlap: 50 characters (prevents losing context at chunk boundaries)
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle

import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings


class PolicyDocument:
    """
    Represents a single insurance policy document.
    
    Attributes:
        policy_id: Unique identifier
        policy_type: Type (health, car, bike)
        region: Geographic region
        title: Policy title
        terms_and_conditions: Full text content
    """
    def __init__(self, policy_id: str, policy_type: str, region: str, 
                 title: str, terms_and_conditions: str):
        self.policy_id = policy_id
        self.policy_type = policy_type
        self.region = region
        self.title = title
        self.terms_and_conditions = terms_and_conditions


def load_policy_documents(data_dir: str) -> List[PolicyDocument]:
    """
    Load all policy documents from JSON files in the data directory.
    
    Args:
        data_dir: Path to directory containing policy JSON files
        
    Returns:
        List of PolicyDocument objects
    """
    policies = []
    data_path = Path(data_dir)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Policy data directory not found: {data_dir}")
    
    # Load all JSON files in the policies directory
    policy_files = list(data_path.glob("*.json"))
    
    if not policy_files:
        raise ValueError(f"No policy JSON files found in {data_dir}")
    
    for policy_file in policy_files:
        with open(policy_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        policy = PolicyDocument(
            policy_id=data.get("policy_id", policy_file.stem),
            policy_type=data.get("policy_type", "unknown"),
            region=data.get("region", "global"),
            title=data.get("title", "Untitled Policy"),
            terms_and_conditions=data.get("terms_and_conditions", "")
        )
        policies.append(policy)
        print(f"Loaded policy: {policy.policy_id} ({policy.policy_type})")
    
    return policies


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
    """
    Split text into overlapping chunks with metadata.
    
    Args:
        text: The text to chunk
        chunk_size: Maximum characters per chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of dictionaries, each containing:
            - text: The chunk text
            - start_idx: Starting character index in original text
            - end_idx: Ending character index in original text
    """
    chunks = []
    
    if len(text) <= chunk_size:
        # Text fits in one chunk
        return [{"text": text, "start_idx": 0, "end_idx": len(text)}]
    
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_text_segment = text[start:end]
        
        chunks.append({
            "text": chunk_text_segment,
            "start_idx": start,
            "end_idx": end
        })
        
        # Move start forward, accounting for overlap
        start = end - overlap
        
        # Prevent infinite loop if overlap >= chunk_size
        if start <= chunks[-1].get("start_idx", 0):
            start = end
    
    return chunks


def build_faiss_index(policies: List[PolicyDocument], 
                      embedding_model: SentenceTransformer,
                      output_dir: str) -> None:
    """
    Build FAISS vector index from policy documents.
    
    Process:
    1. Chunk each policy's terms_and_conditions
    2. Generate embeddings for each chunk
    3. Store embeddings in FAISS index
    4. Save metadata mapping (index position -> chunk info)
    5. Save index and metadata to disk
    
    Args:
        policies: List of PolicyDocument objects
        embedding_model: SentenceTransformer model for generating embeddings
        output_dir: Directory to save the index and metadata
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    all_chunks = []
    all_embeddings = []
    metadata = []
    
    print(f"Processing {len(policies)} policies...")
    
    for policy in policies:
        # Chunk the policy text
        chunks = chunk_text(
            policy.terms_and_conditions,
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP
        )
        
        print(f"  Policy {policy.policy_id}: {len(chunks)} chunks")
        
        # Generate embeddings for each chunk
        chunk_texts = [chunk["text"] for chunk in chunks]
        chunk_embeddings = embedding_model.encode(
            chunk_texts,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Store embeddings and metadata
        for i, chunk in enumerate(chunks):
            all_embeddings.append(chunk_embeddings[i])
            
            # Determine clause type from chunk content (simple heuristic)
            clause_type = "general"
            chunk_lower = chunk["text"].lower()
            if any(word in chunk_lower for word in ["exclude", "not cover", "exception"]):
                clause_type = "exclusion"
            elif any(word in chunk_lower for word in ["cover", "coverage", "includes"]):
                clause_type = "coverage"
            elif any(word in chunk_lower for word in ["limit", "maximum", "up to"]):
                clause_type = "limit"
            
            metadata.append({
                "policy_id": policy.policy_id,
                "policy_type": policy.policy_type,
                "region": policy.region,
                "title": policy.title,
                "clause_type": clause_type,
                "chunk_id": f"{policy.policy_id}_chunk_{i}",
                "text": chunk["text"],
                "start_idx": chunk["start_idx"],
                "end_idx": chunk["end_idx"]
            })
    
    # Convert to numpy array for FAISS
    embeddings_array = np.array(all_embeddings).astype('float32')
    dimension = embeddings_array.shape[1]
    
    print(f"\nCreating FAISS index with {len(embeddings_array)} vectors (dim={dimension})...")
    
    # Create FAISS index (L2 distance - can use cosine similarity with normalization)
    # Using IndexFlatL2 for simplicity (exact search)
    # For larger datasets, consider IndexIVFFlat or IndexHNSW
    index = faiss.IndexFlatL2(dimension)
    
    # Normalize embeddings for cosine similarity (optional but recommended)
    faiss.normalize_L2(embeddings_array)
    index.add(embeddings_array)
    
    # Save index
    index_path = output_path / f"{settings.FAISS_INDEX_NAME}.index"
    faiss.write_index(index, str(index_path))
    print(f"Saved FAISS index to {index_path}")
    
    # Save metadata
    metadata_path = output_path / f"{settings.FAISS_INDEX_NAME}_metadata.pkl"
    with open(metadata_path, 'wb') as f:
        pickle.dump(metadata, f)
    print(f"Saved metadata to {metadata_path}")
    
    print(f"\n✅ Indexing complete! Total chunks: {len(metadata)}")


def main():
    """
    Main function to run the ingestion pipeline.
    
    Usage:
        python -m rag.ingest
    """
    print("=" * 60)
    print("Insurance Policy RAG Ingestion Pipeline")
    print("=" * 60)
    
    # Load embedding model
    print(f"\nLoading embedding model: {settings.EMBEDDING_MODEL_NAME}")
    embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    
    # Load policy documents
    policies_dir = "data/policies"
    print(f"\nLoading policies from: {policies_dir}")
    policies = load_policy_documents(policies_dir)
    
    # Build and save index
    print(f"\nBuilding FAISS index...")
    build_faiss_index(
        policies=policies,
        embedding_model=embedding_model,
        output_dir=settings.VECTOR_STORE_PATH
    )
    
    print("\n" + "=" * 60)
    print("✅ Ingestion pipeline completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()

