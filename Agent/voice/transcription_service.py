"""
Cloud-optimized speech-to-text transcription service with quota management
Supports Google Cloud Speech-to-Text API with free tier limits (60 min/month)
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile

from Agent.voice.speech_config import (
    get_active_engine_config,
    get_engine_type,
    validate_api_key,
    ACTIVE_ENGINE,
    WHISPER_MODEL_SIZE,
    DEFAULT_LANGUAGE,
    AUDIO_CONFIG
)
from backend.utils.quota_manager import get_quota_manager, QuotaExceededException

# Setup logging
log_dir = Path("Agent/agent_logs")
log_dir.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "voice.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Cloud-optimized transcription service with quota management
    
    DEPLOYMENT MODE: Cloud-only for free deployment
    - Uses Google Cloud Speech-to-Text API (60 minutes/month)
    - Automatic quota management and error handling
    - No local Whisper models to reduce memory requirements
    
    For local development, set CLOUD_ONLY_MODE=false in .env
    """
    
    def __init__(self):
        """Initialize transcription service with cloud-first approach"""
        # Check if cloud-only mode is enabled (default for deployment)
        self.cloud_only = os.getenv("CLOUD_ONLY_MODE", "true").lower() == "true"
        
        self.engine_type = "google" if self.cloud_only else get_engine_type()
        self.active_engine = "google-cloud" if self.cloud_only else ACTIVE_ENGINE
        
        logger.info(f"Initializing TranscriptionService with engine: {self.active_engine}")
        
        # Initialize quota manager
        self.quota_manager = get_quota_manager()
        
        # Validate API key if required
        if validate_api_key():
            logger.info("API key validation passed")
        
        # Initialize the appropriate engine
        if self.engine_type == "google" or self.cloud_only:
            self._init_google_cloud()
        elif not self.cloud_only:
            # Only allow local models in development mode
            if self.engine_type == "whisper":
                self._init_whisper_local()
            elif self.engine_type == "whisper-api":
                self._init_whisper_api()
            else:
                raise ValueError(f"Unknown engine type: {self.engine_type}")
        else:
            raise ValueError("Local models not available in cloud-only mode. Set CLOUD_ONLY_MODE=false for development.")
        
        logger.info(f"TranscriptionService initialized with {self.active_engine}")
    
    def _init_whisper_local(self):
        """Initialize local Whisper model (development only)"""
        if self.cloud_only:
            raise ValueError("Whisper local not available in cloud-only mode")
        
        try:
            import whisper
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading Whisper model '{WHISPER_MODEL_SIZE}' on {device}...")
            
            self.model = whisper.load_model(WHISPER_MODEL_SIZE, device=device)
            self.device = device
            
            logger.info(f"Whisper model loaded successfully on {device}")
            
        except ImportError:
            raise ImportError(
                "Whisper not installed. Install with: pip install openai-whisper"
            )
    
    def _init_google_cloud(self):
        """Initialize Google Cloud Speech-to-Text with quota management"""
        try:
            from google.cloud import speech
            
            # Get API key from environment
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment")
            
            # For Google Cloud Speech, we use the same API key as Gemini
            # In production, you might want separate keys
            logger.info("Using Google Cloud Speech-to-Text API key")
            
            # Initialize client (will use GOOGLE_APPLICATION_CREDENTIALS if set)
            self.client = speech.SpeechClient()
            logger.info("Google Cloud Speech-to-Text client initialized with quota management")
            
        except ImportError:
            raise ImportError(
                "Google Cloud Speech not installed. Install with: pip install google-cloud-speech"
            )
    
    def _init_whisper_api(self):
        """Initialize OpenAI Whisper API (development only)"""
        if self.cloud_only:
            raise ValueError("Whisper API not available in cloud-only mode")
        
        try:
            import openai
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            
            openai.api_key = api_key
            self.openai = openai
            
            logger.info("OpenAI Whisper API initialized")
            
        except ImportError:
            raise ImportError(
                "OpenAI not installed. Install with: pip install openai"
            )
    
    def _estimate_audio_duration(self, audio_path: str) -> float:
        """
        Estimate audio duration in minutes for quota management
        This is a simple estimation - in production you might want more accurate detection
        """
        try:
            import os
            # Rough estimation: 1MB ≈ 1 minute of audio (varies by quality)
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            estimated_minutes = max(0.1, file_size_mb)  # Minimum 0.1 minutes
            return estimated_minutes
        except:
            return 1.0  # Default to 1 minute if estimation fails
    
    def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text with quota management
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'hi') or None for auto-detect
        
        Returns:
            Dict with transcription results:
            {
                "text": "transcribed text",
                "language": "detected language",
                "confidence": 0.95,
                "engine": "google-cloud",
                "duration_minutes": 1.5
            }
        """
        logger.info(f"Transcribing audio: {audio_path}")
        
        # Use default language if not specified
        if language is None:
            language = DEFAULT_LANGUAGE
        
        try:
            if self.engine_type == "google" or self.cloud_only:
                result = self._transcribe_google_cloud(audio_path, language)
            elif self.engine_type == "whisper":
                result = self._transcribe_whisper_local(audio_path, language)
            elif self.engine_type == "whisper-api":
                result = self._transcribe_whisper_api(audio_path, language)
            else:
                raise ValueError(f"Unknown engine type: {self.engine_type}")
            
            logger.info(f"Transcription successful: {len(result['text'])} characters")
            return result
            
        except QuotaExceededException as e:
            logger.error(f"Quota exceeded for transcription: {e}")
            raise ValueError(f"Monthly transcription quota exceeded. Please try again next month.")
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    def _transcribe_whisper_local(
        self,
        audio_path: str,
        language: Optional[str]
    ) -> Dict[str, Any]:
        """Transcribe using local Whisper model (development only)"""
        if self.cloud_only:
            raise ValueError("Whisper local not available in cloud-only mode")
        
        logger.info("Using Whisper (local) for transcription")
        
        # Transcribe
        result = self.model.transcribe(
            audio_path,
            language=language,
            fp16=(self.device == "cuda")  # Use FP16 on GPU for speed
        )
        
        return {
            "text": result["text"].strip(),
            "language": result.get("language", "unknown"),
            "confidence": None,  # Whisper doesn't provide confidence
            "engine": "whisper-local",
            "segments": result.get("segments", []),
            "duration_minutes": 0  # No quota consumption for local
        }
    
    def _transcribe_google_cloud(
        self,
        audio_path: str,
        language: Optional[str]
    ) -> Dict[str, Any]:
        """Transcribe using Google Cloud Speech-to-Text with quota management"""
        from google.cloud import speech
        
        logger.info("Using Google Cloud Speech-to-Text for transcription")
        
        # Estimate audio duration for quota checking
        estimated_duration = self._estimate_audio_duration(audio_path)
        
        # Check quota before making API call
        try:
            allowed, error_msg, quota_info = self.quota_manager.check_quota("speech_to_text", estimated_duration)
            if not allowed:
                raise QuotaExceededException("speech_to_text", quota_info)
            
            # Read audio file
            with open(audio_path, "rb") as audio_file:
                content = audio_file.read()
            
            audio = speech.RecognitionAudio(content=content)
            
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                sample_rate_hertz=AUDIO_CONFIG["sample_rate"],
                language_code=language or "en-US",
                enable_automatic_punctuation=True,
                model="default"
            )
            
            # Perform transcription
            response = self.client.recognize(config=config, audio=audio)
            
            # Consume quota after successful API call
            self.quota_manager.consume_quota("speech_to_text", estimated_duration)
            
            # Extract results
            if not response.results:
                return {
                    "text": "",
                    "language": language or "unknown",
                    "confidence": 0.0,
                    "engine": "google-cloud",
                    "duration_minutes": estimated_duration
                }
            
            # Combine all results
            transcript = " ".join([
                result.alternatives[0].transcript
                for result in response.results
            ])
            
            # Get average confidence
            confidences = [
                result.alternatives[0].confidence
                for result in response.results
                if result.alternatives
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                "text": transcript.strip(),
                "language": language or "unknown",
                "confidence": avg_confidence,
                "engine": "google-cloud",
                "duration_minutes": estimated_duration
            }
            
        except QuotaExceededException as e:
            logger.error(f"Quota exceeded for speech-to-text: {e}")
            raise ValueError(f"Monthly speech-to-text quota exceeded. Please try again next month. {error_msg}")
        except Exception as e:
            logger.error(f"Google Cloud Speech-to-Text failed: {e}")
            raise ValueError(f"Speech-to-text service temporarily unavailable: {str(e)}")
    
    def _transcribe_whisper_api(
        self,
        audio_path: str,
        language: Optional[str]
    ) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper API (development only)"""
        if self.cloud_only:
            raise ValueError("Whisper API not available in cloud-only mode")
        
        logger.info("Using OpenAI Whisper API for transcription")
        
        with open(audio_path, "rb") as audio_file:
            transcript = self.openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file,
                language=language
            )
        
        return {
            "text": transcript["text"].strip(),
            "language": language or "unknown",
            "confidence": None,
            "engine": "whisper-api",
            "duration_minutes": 0  # Assuming no quota tracking for OpenAI API
        }
    
    def transcribe_from_bytes(
        self,
        audio_bytes: bytes,
        file_extension: str = "mp3",
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio from bytes (useful for API uploads)
        
        Args:
            audio_bytes: Audio file as bytes
            file_extension: File extension (mp3, wav, etc.)
            language: Language code or None
        
        Returns:
            Transcription result dict
        """
        # Save to temporary file
        with tempfile.NamedTemporaryFile(
            suffix=f".{file_extension}",
            delete=False
        ) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name
        
        try:
            # Transcribe
            result = self.transcribe_audio(temp_path, language)
            return result
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the active engine"""
        return {
            "active_engine": self.active_engine,
            "engine_type": self.engine_type,
            "cloud_only": self.cloud_only,
            "config": get_active_engine_config()
        }
    
    def get_quota_status(self) -> dict:
        """Get current quota status for speech-to-text"""
        return self.quota_manager.get_quota_status("speech_to_text")


# Singleton instance
_transcription_service = None


def get_transcription_service() -> TranscriptionService:
    """Get or create global transcription service instance"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
