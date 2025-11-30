"""
Voice query router for speech-to-text and RAG integration
Allows users to ask questions via voice/audio
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, AsyncGenerator
import logging
import json
from datetime import datetime

from backend.database import get_db, User
from backend.routers.auth_router import get_current_user
from Agent.voice.transcription_service import get_transcription_service
from Agent.voice.speech_config import is_format_supported, get_engine_info, ACTIVE_ENGINE

# Import RAG agent
from Agent.rag_agent.react_agent import PolicyRAGAgent
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/voice", tags=["voice"])

logger = logging.getLogger(__name__)


async def generate_voice_stream(
    transcribed_text: str,
    thread_id: str,
    detected_language: str,
    confidence: float
) -> AsyncGenerator[str, None]:
    """Generate SSE stream for voice query response"""
    try:
        # First send transcription info
        transcription_data = {
            "type": "transcription",
            "text": transcribed_text,
            "language": detected_language,
            "confidence": confidence,
            "engine": ACTIVE_ENGINE
        }
        yield f"data: {json.dumps(transcription_data)}\n\n"
        
        # Initialize agent
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not configured")
        
        agent = PolicyRAGAgent(google_api_key=google_api_key, temperature=0.1)
        
        # Stream the response
        async for chunk in agent.query_stream(transcribed_text, thread_id):
            yield f"data: {json.dumps(chunk)}\n\n"
        
        # Send done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        error_data = {
            "type": "error",
            "message": str(e),
            "recoverable": False
        }
        yield f"data: {json.dumps(error_data)}\n\n"


@router.post("/query/stream")
async def voice_query_stream(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    thread_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process voice query with streaming response (SSE)
    
    Args:
        audio: Audio file (MP3, WAV, M4A, OGG, FLAC)
        language: Language code (e.g., 'en', 'hi') or None for auto-detect
        thread_id: Optional conversation thread ID
        
    Returns:
        Server-Sent Events stream with transcription and AI response
    """
    try:
        # Validate file format
        file_ext = audio.filename.split(".")[-1].lower()
        if not is_format_supported(file_ext):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}"
            )
        
        logger.info(f"Processing streaming voice query from user {current_user.id}")
        
        # Normalize language parameter
        if language:
            language = language.strip().lower()
            if language in ["null", "none", ""]:
                language = None
            elif language == "english":
                language = "en"
            elif language == "hindi":
                language = "hi"
            elif len(language) > 2:
                logger.warning(f"Invalid language format '{language}', using auto-detect")
                language = None
        
        # Read audio bytes
        audio_bytes = await audio.read()
        
        # Get transcription service
        transcription_service = get_transcription_service()
        
        # Transcribe audio
        logger.info(f"Transcribing audio with language: {language or 'auto-detect'}...")
        transcription_result = transcription_service.transcribe_from_bytes(
            audio_bytes=audio_bytes,
            file_extension=file_ext,
            language=language
        )
        
        transcribed_text = transcription_result["text"]
        detected_language = transcription_result["language"]
        confidence = transcription_result.get("confidence")
        
        logger.info(f"✅ Transcription: '{transcribed_text}'")
        
        if not transcribed_text:
            raise HTTPException(
                status_code=400,
                detail="No speech detected in audio file"
            )
        
        # Use thread_id if provided
        if not thread_id:
            thread_id = f"voice_{current_user.id}_{int(datetime.now().timestamp())}"
        
        # Return streaming response
        return StreamingResponse(
            generate_voice_stream(transcribed_text, thread_id, detected_language, confidence),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice query stream failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Voice query processing failed: {str(e)}"
        )


@router.post("/query")
async def voice_query(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    thread_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process voice query: transcribe audio and send to RAG agent
    
    Args:
        audio: Audio file (MP3, WAV, M4A, OGG, FLAC)
        language: Language code (e.g., 'en', 'hi') or None for auto-detect
        thread_id: Optional conversation thread ID
        
    Returns:
        {
            "transcription": "What are the education policy guidelines?",
            "language": "en",
            "confidence": 0.95,
            "engine": "whisper-local",
            "answer": "The education policy guidelines include...",
            "processing_time": 2.5
        }
    """
    start_time = datetime.now()
    
    try:
        # Validate file format
        file_ext = audio.filename.split(".")[-1].lower()
        if not is_format_supported(file_ext):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}. Supported: mp3, wav, m4a, ogg, flac"
            )
        
        logger.info(f"Processing voice query from user {current_user.id}: {audio.filename}")
        
        # Normalize language parameter
        # Handle cases where frontend sends "null", "english", etc.
        if language:
            language = language.strip().lower()
            # Convert common names to language codes
            if language in ["null", "none", ""]:
                language = None
            elif language == "english":
                language = "en"
            elif language == "hindi":
                language = "hi"
            # If it's already a valid 2-letter code, keep it
            elif len(language) > 2:
                # Invalid language format, use auto-detect
                logger.warning(f"Invalid language format '{language}', using auto-detect")
                language = None
        
        # Read audio bytes
        audio_bytes = await audio.read()
        
        # Get transcription service
        transcription_service = get_transcription_service()
        
        # Transcribe audio
        logger.info(f"Transcribing audio with language: {language or 'auto-detect'}...")
        transcription_result = transcription_service.transcribe_from_bytes(
            audio_bytes=audio_bytes,
            file_extension=file_ext,
            language=language
        )
        
        transcribed_text = transcription_result["text"]
        detected_language = transcription_result["language"]
        confidence = transcription_result.get("confidence")
        
        logger.info(f"✅ Transcription: '{transcribed_text}' (language: {detected_language})")
        
        if not transcribed_text:
            raise HTTPException(
                status_code=400,
                detail="No speech detected in audio file"
            )
        
        # Send to RAG agent
        logger.info("Sending transcribed query to RAG agent...")
        
        # Initialize agent
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise HTTPException(
                status_code=500,
                detail="GOOGLE_API_KEY not configured"
            )
        
        agent = PolicyRAGAgent(google_api_key=google_api_key, temperature=0.1)
        
        # Use thread_id if provided, otherwise create new one
        if not thread_id:
            thread_id = f"voice_{current_user.id}_{int(datetime.now().timestamp())}"
        
        # Get answer from agent
        result = agent.query(transcribed_text, thread_id)
        
        # Extract answer
        answer = result.get("answer", "No response generated")
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Voice query processed in {processing_time:.2f}s")
        
        return {
            "status": "success",
            "transcription": transcribed_text,
            "language": detected_language,
            "confidence": confidence,
            "engine": ACTIVE_ENGINE,
            "answer": answer,
            "thread_id": thread_id,
            "processing_time": processing_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice query failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Voice query processing failed: {str(e)}"
        )


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """
    Transcribe audio to text (without RAG query)
    
    Args:
        audio: Audio file (MP3, WAV, M4A, OGG, FLAC)
        language: Language code (e.g., 'en', 'hi') or None for auto-detect
        
    Returns:
        {
            "text": "transcribed text",
            "language": "en",
            "confidence": 0.95,
            "engine": "whisper-local"
        }
    """
    try:
        # Validate file format
        file_ext = audio.filename.split(".")[-1].lower()
        if not is_format_supported(file_ext):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}"
            )
        
        logger.info(f"Transcribing audio: {audio.filename}")
        
        # Normalize language parameter
        if language:
            language = language.strip().lower()
            if language in ["null", "none", ""]:
                language = None
            elif language == "english":
                language = "en"
            elif language == "hindi":
                language = "hi"
            elif len(language) > 2:
                logger.warning(f"Invalid language format '{language}', using auto-detect")
                language = None
        
        # Read audio bytes
        audio_bytes = await audio.read()
        
        # Get transcription service
        transcription_service = get_transcription_service()
        
        # Transcribe
        result = transcription_service.transcribe_from_bytes(
            audio_bytes=audio_bytes,
            file_extension=file_ext,
            language=language
        )
        
        logger.info(f"✅ Transcription complete: {len(result['text'])} characters")
        
        return {
            "status": "success",
            **result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )


@router.get("/engine-info")
async def get_voice_engine_info(current_user: User = Depends(get_current_user)):
    """
    Get information about the active speech-to-text engine
    
    Returns:
        {
            "active_engine": "whisper-local",
            "engine_type": "whisper",
            "config": {...}
        }
    """
    try:
        transcription_service = get_transcription_service()
        info = transcription_service.get_engine_info()
        
        return {
            "status": "success",
            **info,
            "engine_details": get_engine_info()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get engine info: {str(e)}"
        )


@router.get("/health")
async def voice_health_check():
    """
    Check if voice service is operational
    
    Returns:
        {
            "status": "healthy",
            "active_engine": "whisper-local",
            "supported_formats": ["mp3", "wav", "m4a", "ogg", "flac"]
        }
    """
    try:
        from Agent.voice.speech_config import get_supported_formats
        
        transcription_service = get_transcription_service()
        
        return {
            "status": "healthy",
            "active_engine": ACTIVE_ENGINE,
            "supported_formats": get_supported_formats(),
            "service_initialized": True
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
