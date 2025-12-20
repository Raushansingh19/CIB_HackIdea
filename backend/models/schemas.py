"""
Pydantic data models (schemas) for request/response validation.

These schemas define the structure of API requests and responses,
ensuring type safety and automatic validation in FastAPI.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class TextChatRequest(BaseModel):
    """
    Request schema for text-based chat endpoint.
    
    Fields:
        message: The user's text message/question
        session_id: Optional session identifier for conversation tracking
        policy_type: Optional filter to focus on specific policy types (health, car, bike)
        region: Optional filter for region-specific policies
    """
    message: str = Field(..., description="User's text message or question")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    policy_type: Optional[str] = Field(None, description="Filter by policy type: health, car, or bike")
    region: Optional[str] = Field(None, description="Filter by region (e.g., 'US', 'UK', 'IN')")


class PolicySuggestion(BaseModel):
    """
    Schema for a policy suggestion returned to the user.
    
    Fields:
        policy_id: Unique identifier for the policy
        policy_type: Type of policy (health, car, bike)
        title: Human-readable policy title (includes company name)
        reason: Brief explanation with company name and website
    """
    policy_id: str = Field(..., description="Unique policy identifier")
    policy_type: str = Field(..., description="Type of policy: health, car, or bike")
    title: str = Field(..., description="Policy title with company name (e.g., 'HealthGuard - Comprehensive Plan')")
    reason: str = Field(..., description="Why this policy is suggested, including company name and website link")


class SourceChunk(BaseModel):
    """
    Schema for a source chunk that was used to generate the answer.
    
    This provides transparency by showing which policy documents
    and specific clauses were referenced in the response.
    
    Fields:
        policy_id: ID of the policy document
        policy_type: Type of policy (health, car, bike)
        clause_type: Type of clause (e.g., "coverage", "exclusion", "limit")
        text_snippet: Excerpt from the policy document
    """
    policy_id: str = Field(..., description="ID of the source policy")
    policy_type: str = Field(..., description="Type of policy: health, car, or bike")
    clause_type: str = Field(..., description="Type of clause (coverage, exclusion, limit, etc.)")
    text_snippet: str = Field(..., description="Relevant excerpt from the policy document")


class TextChatResponse(BaseModel):
    """
    Response schema for text-based chat endpoint.
    
    Fields:
        answer: The bot's answer to the user's question
        policy_suggestions: List of up to 3 relevant policy suggestions
        sources: List of source chunks that were used to generate the answer
        session_id: Session ID for maintaining conversation context
    """
    answer: str = Field(..., description="Bot's answer to the user's question")
    policy_suggestions: List[PolicySuggestion] = Field(
        default_factory=list,
        description="List of suggested policies (up to 3)"
    )
    sources: List[SourceChunk] = Field(
        default_factory=list,
        description="Source chunks used to generate the answer"
    )
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")


class AudioChatResponse(BaseModel):
    """
    Response schema for audio-based chat endpoint.
    
    Extends TextChatResponse with audio-specific fields:
        transcript: The transcribed text from the user's audio input
        audio_url: URL or path to the generated TTS audio file
        session_id: Session ID for maintaining conversation context
    """
    transcript: str = Field(..., description="Transcribed text from user's audio input")
    answer: str = Field(..., description="Bot's answer to the user's question")
    policy_suggestions: List[PolicySuggestion] = Field(
        default_factory=list,
        description="List of suggested policies (up to 3)"
    )
    sources: List[SourceChunk] = Field(
        default_factory=list,
        description="Source chunks used to generate the answer"
    )
    audio_url: str = Field(..., description="URL to the generated TTS audio file")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")

