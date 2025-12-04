"""
Modular speech-to-text transcription service
Supports multiple engines: Whisper (local), Google Cloud, Whisper API
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
    Unified transcription service supporting multiple engines
    
    Supported engines:
    - whisper-local: OpenAI Whisper running locally
    - google-cloud: Google Cloud Speech-to-Text
    - whisper-api: OpenAI Whisper via API
    
    Switch engines by changing ACTIVE_ENGINE in speech_config.py
    """
    
    def __init__(self):
        """Initialize transcription service with configured engine"""
        self.engine_type = get_engine_type()
        self.active_engine = ACTIVE_ENGINE
        
        logger.info(f"Initializing TranscriptionService with engine: {self.active_engine}")
        
        # Validate API key if required
        if validate_api_key():
            logger.info("API key validation passed")
        
        # Initialize the appropriate engine
        if self.engine_type == "whisper":
            self._init_whisper_local()
        elif self.engine_type == "google":
            self._init_google_cloud()
        elif self.engine_type == "whisper-api":
            self._init_whisper_api()
        else:
            raise ValueError(f"Unknown engine type: {self.engine_type}")
        
        logger.info(f"TranscriptionService initialized with {self.active_engine}")
    
    def _init_whisper_local(self):
        """Initialize local Whisper model"""
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
        """Initialize Google Cloud Speech-to-Text"""
        try:
            from google.cloud import speech
            
            # Get API key from environment
            api_key = os.getenv("GOOGLE_CLOUD_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_CLOUD_API_KEY not found in environment")
            
            # Set credentials
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = api_key
            
            self.client = speech.SpeechClient()
            logger.info("Google Cloud Speech-to-Text client initialized")
            
        except ImportError:
            raise ImportError(
                "Google Cloud Speech not installed. Install with: pip install google-cloud-speech"
            )
    
    def _init_whisper_api(self):
        """Initialize OpenAI Whisper API"""
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
    
    def transcribe_audio(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'hi') or None for auto-detect
        
        Returns:
            Dict with transcription results:
            {
                "text": "transcribed text",
                "language": "detected language",
                "confidence": 0.95,
                "engine": "whisper-local"
            }
        """
        logger.info(f"Transcribing audio: {audio_path}")
        
        # Use default language if not specified
        if language is None:
            language = DEFAULT_LANGUAGE
        
        try:
            if self.engine_type == "whisper":
                result = self._transcribe_whisper_local(audio_path, language)
            elif self.engine_type == "google":
                result = self._transcribe_google_cloud(audio_path, language)
            elif self.engine_type == "whisper-api":
                result = self._transcribe_whisper_api(audio_path, language)
            else:
                raise ValueError(f"Unknown engine type: {self.engine_type}")
            
            logger.info(f"Transcription successful: {len(result['text'])} characters")
            return result
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise
    
    def _transcribe_whisper_local(
        self,
        audio_path: str,
        language: Optional[str]
    ) -> Dict[str, Any]:
        """Transcribe using local Whisper model"""
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
            "segments": result.get("segments", [])
        }
    
    def _transcribe_google_cloud(
        self,
        audio_path: str,
        language: Optional[str]
    ) -> Dict[str, Any]:
        """Transcribe using Google Cloud Speech-to-Text"""
        from google.cloud import speech
        
        logger.info("Using Google Cloud Speech-to-Text for transcription")
        
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
        
        # Extract results
        if not response.results:
            return {
                "text": "",
                "language": language or "unknown",
                "confidence": 0.0,
                "engine": "google-cloud"
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
            "engine": "google-cloud"
        }
    
    def _transcribe_whisper_api(
        self,
        audio_path: str,
        language: Optional[str]
    ) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper API"""
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
            "engine": "whisper-api"
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
            "config": get_active_engine_config()
        }


# Singleton instance
_transcription_service = None


def get_transcription_service() -> TranscriptionService:
    """Get or create global transcription service instance"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
