"""
Policy Suggestion Service: Rank and suggest relevant insurance policies.

This module analyzes user queries and retrieved chunks to suggest
the most relevant insurance policies (health, car, bike).

Scoring logic:
1. Count how many chunks each policy contributed to the answer
2. Check if policy_type matches keywords in user query
3. Rank policies by relevance score
4. Return top 3 suggestions with brief reasons
"""

from typing import List, Dict, Any
import sys
from pathlib import Path
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from rag.retrieval import RetrievedChunk
from models.schemas import PolicySuggestion


# Policy metadata with company names and websites (in production, this would come from a database)
POLICY_DATABASE = {
    "health_policy_1": {
        "policy_id": "health_policy_1",
        "policy_type": "health",
        "title": "Comprehensive Health Insurance Plan",
        "company_name": "HealthGuard Insurance",
        "website": "https://www.healthguard.com/comprehensive-plan",
        "region": "US",
        "description": "Full coverage health insurance with comprehensive benefits"
    },
    "health_policy_2": {
        "policy_id": "health_policy_2",
        "policy_type": "health",
        "title": "Basic Health Insurance Plan",
        "company_name": "MediCare Plus",
        "website": "https://www.medicareplus.com/basic-plan",
        "region": "US",
        "description": "Affordable basic health coverage for essential needs"
    },
    "car_policy_1": {
        "policy_id": "car_policy_1",
        "policy_type": "car",
        "title": "Full Coverage Auto Insurance",
        "company_name": "AutoSecure Insurance",
        "website": "https://www.autosecure.com/full-coverage",
        "region": "US",
        "description": "Complete auto insurance with comprehensive and collision coverage"
    },
    "car_policy_2": {
        "policy_id": "car_policy_2",
        "policy_type": "car",
        "title": "Liability-Only Auto Insurance",
        "company_name": "BudgetAuto Insurance",
        "website": "https://www.budgetauto.com/liability",
        "region": "US",
        "description": "Affordable liability-only coverage meeting state requirements"
    },
    "bike_policy_1": {
        "policy_id": "bike_policy_1",
        "policy_type": "bike",
        "title": "Motorcycle Insurance Plan",
        "company_name": "RideSafe Insurance",
        "website": "https://www.ridesafe.com/motorcycle",
        "region": "US",
        "description": "Comprehensive motorcycle insurance with full protection"
    },
    "bike_policy_2": {
        "policy_id": "bike_policy_2",
        "policy_type": "bike",
        "title": "Bicycle Theft Protection",
        "company_name": "CycleGuard Insurance",
        "website": "https://www.cycleguard.com/theft-protection",
        "region": "US",
        "description": "Specialized bicycle insurance for theft and damage protection"
    }
}


def extract_policy_keywords(query: str) -> List[str]:
    """
    Extract policy type keywords from user query.
    
    This is a simple keyword matching approach. In production,
    you might use more sophisticated NLP techniques.
    
    Args:
        query: User's query text
        
    Returns:
        List of detected policy types (health, car, bike)
    """
    query_lower = query.lower()
    detected_types = []
    
    # Health insurance keywords
    health_keywords = ["health", "medical", "hospital", "doctor", "treatment", "illness", "surgery"]
    if any(keyword in query_lower for keyword in health_keywords):
        detected_types.append("health")
    
    # Car insurance keywords
    car_keywords = ["car", "auto", "vehicle", "automobile", "accident", "collision", "driving"]
    if any(keyword in query_lower for keyword in car_keywords):
        detected_types.append("car")
    
    # Bike insurance keywords
    bike_keywords = ["bike", "bicycle", "motorcycle", "two-wheeler", "scooter"]
    if any(keyword in query_lower for keyword in bike_keywords):
        detected_types.append("bike")
    
    return detected_types


def score_policy(policy_id: str, retrieved_chunks: List[RetrievedChunk], 
                query_keywords: List[str]) -> float:
    """
    Score a policy based on relevance to the query.
    
    Scoring factors:
    1. Number of chunks from this policy (higher = more relevant)
    2. Average similarity score of chunks from this policy
    3. Keyword match bonus (if policy type matches query keywords)
    
    Args:
        policy_id: ID of the policy to score
        retrieved_chunks: List of retrieved chunks
        query_keywords: List of policy types detected in query
        
    Returns:
        Relevance score (higher = more relevant)
    """
    # Count chunks from this policy
    policy_chunks = [chunk for chunk in retrieved_chunks if chunk.policy_id == policy_id]
    chunk_count = len(policy_chunks)
    
    if chunk_count == 0:
        return 0.0
    
    # Calculate average similarity score
    avg_similarity = sum(chunk.similarity_score for chunk in policy_chunks) / chunk_count
    
    # Base score: chunk count * average similarity
    base_score = chunk_count * avg_similarity
    
    # Keyword match bonus
    policy_info = POLICY_DATABASE.get(policy_id, {})
    policy_type = policy_info.get("policy_type", "")
    
    keyword_bonus = 0.0
    if policy_type in query_keywords:
        keyword_bonus = 0.5  # Bonus for matching query intent
    
    return base_score + keyword_bonus


def suggest_policies(user_query: str, retrieved_chunks: List[RetrievedChunk]) -> List[PolicySuggestion]:
    """
    Suggest relevant policies based on user query and retrieved chunks.
    
    Process:
    1. Extract policy type keywords from query
    2. Score all policies that appear in retrieved chunks
    3. Rank by score
    4. Return top 3 with reasons
    
    Args:
        user_query: User's question or query
        retrieved_chunks: List of retrieved chunks from RAG
        
    Returns:
        List of PolicySuggestion objects (up to 3)
    """
    if not retrieved_chunks:
        return []
    
    # Extract keywords from query
    query_keywords = extract_policy_keywords(user_query)
    
    # Get all unique policy IDs from retrieved chunks
    policy_ids = list(set([chunk.policy_id for chunk in retrieved_chunks]))
    
    # Score each policy
    policy_scores = {}
    for policy_id in policy_ids:
        score = score_policy(policy_id, retrieved_chunks, query_keywords)
        policy_scores[policy_id] = score
    
    # Sort by score (descending)
    sorted_policies = sorted(policy_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Build suggestions (top 3)
    suggestions = []
    for policy_id, score in sorted_policies[:3]:
        policy_info = POLICY_DATABASE.get(policy_id, {})
        
        # Generate reason based on score, context, and user requirements
        chunk_count = len([c for c in retrieved_chunks if c.policy_id == policy_id])
        company_name = policy_info.get("company_name", "Insurance Provider")
        website = policy_info.get("website", "#")
        description = policy_info.get("description", "")
        
        # Create helpful reason with company name and website
        if chunk_count > 0:
            reason = f"Recommended: {company_name} - {description}. Visit {website} for details."
        else:
            reason = f"Suggested: {company_name} - {description}. Check {website} for eligibility and pricing."
        
        suggestion = PolicySuggestion(
            policy_id=policy_id,
            policy_type=policy_info.get("policy_type", "unknown"),
            title=f"{company_name} - {policy_info.get('title', 'Unknown Policy')}",
            reason=reason
        )
        suggestions.append(suggestion)
    
    return suggestions

