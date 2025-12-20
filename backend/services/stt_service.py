"""
Speech-to-Text (STT) Service Module.

This module provides a pluggable interface for speech-to-text conversion.
For local development, it includes a mock implementation.
For production, replace with actual STT provider integration.

Supported providers (to be implemented):
- OpenAI Whisper API
- Google Cloud Speech-to-Text
- AWS Transcribe
- Azure Speech Services
"""

import os
from typing import Optional
from config import settings


def transcribe_audio_mock(file_path: str) -> str:
    """
    Mock STT implementation for local development.
    
    This simulates transcription by returning a predefined transcript.
    In production, replace this with actual STT API calls.
    
    Args:
        file_path: Path to the audio file to transcribe
        
    Returns:
        Transcribed text string
    """
    # Check file size to ensure audio was actually recorded
    try:
        file_size = os.path.getsize(file_path)
        print(f"📁 Audio file size: {file_size} bytes")
        
        if file_size < 100:
            print("⚠️ Audio file is too small, might be empty")
            return "I couldn't hear anything. Could you please try recording again?"
        
        # For demo purposes, return a sample transcript based on file
        # In real implementation, this would call an STT API
        # Since this is mock, we return a generic but helpful message
        print("ℹ️ Using mock STT (no real transcription)")
        return "I need help with insurance"  # Generic transcript for mock mode
    except Exception as e:
        print(f"⚠️ Error reading audio file: {e}")
        return "I couldn't process the audio. Could you please try typing your question instead?"


def transcribe_audio_openai_whisper(file_path: str) -> str:
    """
    Transcribe audio using OpenAI Whisper API.
    
    To use this:
    1. Install: pip install openai
    2. Set OPENAI_API_KEY in environment
    3. Set STT_PROVIDER="openai-whisper" in config
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Transcribed text string
    """
    try:
        from openai import OpenAI
        
        if not settings.OPENAI_API_KEY:
            print("⚠️ OpenAI API key not set, falling back to mock STT")
            return transcribe_audio_mock(file_path)
        
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        print(f"🎤 Transcribing audio file: {file_path}")
        
        with open(file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"  # Optional: specify language for better accuracy
            )
        
        transcribed_text = transcript.text.strip()
        print(f"✅ Transcription successful: '{transcribed_text[:100]}...'")
        
        if not transcribed_text:
            print("⚠️ Whisper returned empty transcript, using fallback")
            return transcribe_audio_mock(file_path)
        
        return transcribed_text
        
    except ImportError:
        print("⚠️ OpenAI package not installed, falling back to mock STT")
        print("   Install with: pip install openai")
        return transcribe_audio_mock(file_path)
    except Exception as e:
        print(f"⚠️ Whisper API error: {str(e)}, falling back to mock STT")
        import traceback
        traceback.print_exc()
        return transcribe_audio_mock(file_path)


def transcribe_audio_google_speech(file_path: str) -> str:
    """
    Transcribe audio using Google Cloud Speech-to-Text API.
    
    To use this:
    1. Install: pip install google-cloud-speech
    2. Set up Google Cloud credentials
    3. Set STT_PROVIDER="google-speech" in config
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Transcribed text string
    """
    # TODO: Implement Google Speech-to-Text API call
    # Example implementation:
    # from google.cloud import speech
    # client = speech.SpeechClient()
    # with open(file_path, 'rb') as audio_file:
    #     content = audio_file.read()
    # audio = speech.RecognitionAudio(content=content)
    # config = speech.RecognitionConfig(
    #     encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
    #     sample_rate_hertz=16000,
    #     language_code="en-US",
    # )
    # response = client.recognize(config=config, audio=audio)
    # return response.results[0].alternatives[0].transcript
    
    raise NotImplementedError("Google Speech-to-Text integration not yet implemented. Use mock for local development.")


def transcribe_audio(file_path: str) -> str:
    """
    Main STT function that routes to the appropriate provider.
    
    This function checks the STT_PROVIDER setting and calls the
    corresponding implementation. Defaults to mock for local development.
    
    Args:
        file_path: Path to the audio file to transcribe
        
    Returns:
        Transcribed text string
        
    Raises:
        FileNotFoundError: If audio file doesn't exist
        NotImplementedError: If provider is not implemented
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    provider = settings.STT_PROVIDER.lower()
    
    # Auto-detect: Use Whisper if OpenAI API key is available
    if provider == "auto":
        if settings.OPENAI_API_KEY:
            print("🔍 Auto-detected: Using OpenAI Whisper (API key available)")
            return transcribe_audio_openai_whisper(file_path)
        else:
            print("🔍 Auto-detected: Using mock STT (no API key)")
            return transcribe_audio_mock(file_path)
    elif provider == "mock":
        return transcribe_audio_mock(file_path)
    elif provider == "openai-whisper":
        return transcribe_audio_openai_whisper(file_path)
    elif provider == "google-speech":
        return transcribe_audio_google_speech(file_path)
    else:
        # Default to mock for unknown providers
        print(f"Warning: Unknown STT provider '{provider}', using mock")
        return transcribe_audio_mock(file_path)

