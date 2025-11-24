"""
FastAPI Main Application: Insurance Chatbot Backend.

This module defines the FastAPI application with endpoints for:
1. Health check
2. Text-based chat
3. Audio-based chat (with STT/TTS)

The application integrates:
- RAG pipeline for answering questions
- Policy suggestion service
- STT/TTS services for audio support
- CORS middleware for frontend integration
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os
import uuid
from typing import Optional

import sys
from pathlib import Path
# Ensure we can import from backend modules
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from config import settings
from models.schemas import (
    TextChatRequest, TextChatResponse, AudioChatResponse,
    PolicySuggestion, SourceChunk
)
from rag.retrieval import retrieve_relevant_chunks
from rag.llm_chain import generate_answer_with_rag
from services.stt_service import transcribe_audio
from services.tts_service import synthesize_speech
from services.policy_suggester import suggest_policies

# Initialize FastAPI app
app = FastAPI(
    title="Insurance Chatbot API",
    description="RAG-based insurance chatbot with text and audio support",
    version="1.0.0"
)

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
Path(settings.AUDIO_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.TEMP_UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

# Mount static files directory for serving audio files
# This allows the frontend to access generated TTS audio files
app.mount("/audio", StaticFiles(directory=settings.AUDIO_OUTPUT_DIR), name="audio")


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON with status "ok" if the service is running
    """
    return {"status": "ok"}


@app.post("/api/chat-text", response_model=TextChatResponse)
async def chat_text(request: TextChatRequest):
    """
    Text-based chat endpoint.
    
    Process:
    1. Retrieve relevant chunks using RAG retrieval
    2. Generate answer using LLM with retrieved context
    3. Suggest relevant policies
    4. Format response with answer, suggestions, and sources
    
    Args:
        request: TextChatRequest with user message and optional filters
        
    Returns:
        TextChatResponse with answer, policy suggestions, and sources
    """
    try:
        # Step 1: Retrieve relevant chunks
        try:
            retrieved_chunks = retrieve_relevant_chunks(
                query=request.message,
                policy_type=request.policy_type,
                region=request.region,
                k=settings.RETRIEVAL_K
            )
        except FileNotFoundError as e:
            # Vector index not found - user needs to run ingestion
            return TextChatResponse(
                answer="The policy database is not initialized. Please contact the administrator to set up the system.",
                policy_suggestions=[],
                sources=[]
            )
        except Exception as e:
            print(f"Retrieval error: {str(e)}")
            raise
        
        if not retrieved_chunks:
            return TextChatResponse(
                answer="I couldn't find relevant information in the available policy documents. "
                       "Please try rephrasing your question or contact customer service.",
                policy_suggestions=[],
                sources=[]
            )
        
        # Step 2: Generate answer using RAG
        answer, supporting_info = generate_answer_with_rag(
            user_query=request.message,
            retrieved_chunks=retrieved_chunks,
            policy_type=request.policy_type,
            region=request.region
        )
        
        # Step 3: Suggest policies
        policy_suggestions = suggest_policies(
            user_query=request.message,
            retrieved_chunks=retrieved_chunks
        )
        
        # Step 4: Format sources
        sources = []
        for chunk in retrieved_chunks[:5]:  # Top 5 chunks as sources
            source = SourceChunk(
                policy_id=chunk.policy_id,
                policy_type=chunk.policy_type,
                clause_type=chunk.clause_type,
                text_snippet=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
            )
            sources.append(source)
        
        return TextChatResponse(
            answer=answer,
            policy_suggestions=policy_suggestions,
            sources=sources
        )
        
    except Exception as e:
        # Log error with full traceback for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in chat-text endpoint: {str(e)}")
        print(f"Full traceback:\n{error_trace}")
        
        # Return helpful error message
        return TextChatResponse(
            answer=f"I encountered an issue processing your request. Please try rephrasing your question or contact customer service. Error: {str(e)[:100]}",
            policy_suggestions=[],
            sources=[]
        )


@app.post("/api/chat-audio", response_model=AudioChatResponse)
async def chat_audio(audio_file: UploadFile = File(...)):
    """
    Audio-based chat endpoint.
    
    Process:
    1. Save uploaded audio file temporarily
    2. Transcribe audio to text using STT service
    3. Process transcript through RAG pipeline (same as text chat)
    4. Generate TTS audio from the answer
    5. Return response with transcript, answer, and audio URL
    
    Args:
        audio_file: Uploaded audio file (multipart/form-data)
        
    Returns:
        AudioChatResponse with transcript, answer, suggestions, sources, and audio URL
    """
    temp_file_path = None
    
    try:
        # Step 1: Save uploaded file temporarily
        # Generate unique filename to avoid conflicts
        file_extension = audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'wav'
        temp_filename = f"{uuid.uuid4()}.{file_extension}"
        temp_file_path = os.path.join(settings.TEMP_UPLOAD_DIR, temp_filename)
        
        # Write uploaded file to disk
        with open(temp_file_path, 'wb') as f:
            content = await audio_file.read()
            f.write(content)
        
        print(f"Saved uploaded audio to: {temp_file_path}")
        
        # Step 2: Transcribe audio to text
        transcript = transcribe_audio(temp_file_path)
        print(f"Transcribed text: {transcript}")
        
        # Step 3: Process transcript through RAG pipeline (same as text chat)
        # Retrieve relevant chunks
        retrieved_chunks = retrieve_relevant_chunks(
            query=transcript,
            policy_type=None,  # Could extract from transcript in future
            region=None,
            k=settings.RETRIEVAL_K
        )
        
        if not retrieved_chunks:
            # Still generate TTS even if no chunks found
            answer = "I couldn't find relevant information in the available policy documents. " \
                     "Please try rephrasing your question or contact customer service."
            policy_suggestions = []
            sources = []
        else:
            # Generate answer using RAG
            answer, supporting_info = generate_answer_with_rag(
                user_query=transcript,
                retrieved_chunks=retrieved_chunks,
                policy_type=None,
                region=None
            )
            
            # Suggest policies
            policy_suggestions = suggest_policies(
                user_query=transcript,
                retrieved_chunks=retrieved_chunks
            )
            
            # Format sources
            sources = []
            for chunk in retrieved_chunks[:5]:
                source = SourceChunk(
                    policy_id=chunk.policy_id,
                    policy_type=chunk.policy_type,
                    clause_type=chunk.clause_type,
                    text_snippet=chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
                )
                sources.append(source)
        
        # Step 4: Generate TTS audio from answer
        # Create unique filename for TTS output
        tts_filename = f"{uuid.uuid4()}.wav"
        tts_output_path = os.path.join(settings.AUDIO_OUTPUT_DIR, tts_filename)
        
        synthesize_speech(text=answer, output_path=tts_output_path)
        
        # Generate URL for frontend to access the audio file
        audio_url = f"/audio/{tts_filename}"
        
        return AudioChatResponse(
            transcript=transcript,
            answer=answer,
            policy_suggestions=policy_suggestions,
            sources=sources,
            audio_url=audio_url
        )
        
    except Exception as e:
        # Log error and return user-friendly message
        print(f"Error in chat-audio endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your audio: {str(e)}"
        )
    
    finally:
        # Clean up temporary uploaded file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                print(f"Warning: Could not delete temp file {temp_file_path}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True  # Auto-reload on code changes (for development)
    )

