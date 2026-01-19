"""
Cloud-optimized OCR service with quota management
Uses Google Cloud Vision API with free tier limits (1,000 requests/month)
"""
import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import base64

from backend.utils.quota_manager import get_quota_manager, QuotaExceededException

logger = logging.getLogger(__name__)

class CloudOCRService:
    """
    Cloud-optimized OCR service with quota management
    
    DEPLOYMENT MODE: Cloud-only for free deployment
    - Uses Google Cloud Vision API (1,000 requests/month)
    - Automatic quota management and error handling
    - Fallback to Tesseract when quota exceeded
    
    For local development, set CLOUD_ONLY_MODE=false in .env
    """
    
    def __init__(self):
        """Initialize OCR service with cloud-first approach"""
        # Check if cloud-only mode is enabled (default for deployment)
        self.cloud_only = os.getenv("CLOUD_ONLY_MODE", "true").lower() == "true"
        
        # Initialize quota manager
        self.quota_manager = get_quota_manager()
        
        # Initialize services
        self.vision_client = None
        self.tesseract_available = False
        
        if self.cloud_only:
            logger.info("Cloud-only mode enabled - using Google Cloud Vision API")
            self._init_vision_api()
        else:
            # Development mode - try both
            self._init_vision_api()
            self._init_tesseract()
        
        logger.info("CloudOCRService initialized successfully")
    
    def _init_vision_api(self):
        """Initialize Google Cloud Vision API"""
        try:
            from google.cloud import vision
            
            # Use the same API key as other Google services
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.warning("GOOGLE_API_KEY not found - Vision API unavailable")
                return
            
            # For Vision API, we can use the REST API directly with the API key
            # This avoids the need for service account credentials
            self.vision_client = "rest_api"  # Flag to use REST API
            logger.info("Google Cloud Vision API initialized with quota management")
            
        except ImportError:
            logger.warning("google-cloud-vision not installed - Vision API unavailable")
    
    def _init_tesseract(self):
        """Initialize Tesseract OCR as fallback (development only)"""
        if self.cloud_only:
            return
        
        try:
            import pytesseract
            from PIL import Image
            
            # Test if Tesseract is available
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
            logger.info("Tesseract OCR available as fallback")
            
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
    
    def extract_text_from_image(
        self,
        image_path: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Extract text from image with quota management
        
        Args:
            image_path: Path to image file
            language: Language code for OCR (e.g., 'en', 'hi')
        
        Returns:
            Dict with extracted text and metadata:
            {
                "text": "extracted text",
                "confidence": 0.95,
                "engine": "google-vision",
                "language": "en",
                "word_count": 150
            }
        """
        logger.info(f"Extracting text from image: {image_path}")
        
        try:
            # Try Google Cloud Vision API first
            if self.vision_client:
                try:
                    return self._extract_with_vision_api(image_path, language)
                except QuotaExceededException as e:
                    logger.warning(f"Vision API quota exceeded: {e}")
                    # Fall back to Tesseract if available
                    if self.tesseract_available:
                        logger.info("Falling back to Tesseract OCR")
                        return self._extract_with_tesseract(image_path, language)
                    else:
                        raise ValueError("Monthly OCR quota exceeded. Please try again next month.")
                except Exception as e:
                    logger.error(f"Vision API failed: {e}")
                    # Fall back to Tesseract if available
                    if self.tesseract_available:
                        logger.info("Falling back to Tesseract OCR due to API error")
                        return self._extract_with_tesseract(image_path, language)
                    else:
                        raise ValueError(f"OCR service temporarily unavailable: {str(e)}")
            
            # Use Tesseract if Vision API not available
            elif self.tesseract_available:
                return self._extract_with_tesseract(image_path, language)
            
            else:
                raise ValueError("No OCR service available")
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise
    
    def _extract_with_vision_api(
        self,
        image_path: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Extract text using Google Cloud Vision API with quota management"""
        # Check quota before making API call
        try:
            allowed, error_msg, quota_info = self.quota_manager.check_quota("vision_ocr", 1)
            if not allowed:
                raise QuotaExceededException("vision_ocr", quota_info)
            
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_content = image_file.read()
            
            # Use REST API to avoid service account requirements
            import requests
            import json
            
            api_key = os.getenv("GOOGLE_API_KEY")
            url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            # Prepare request
            request_data = {
                "requests": [
                    {
                        "image": {
                            "content": image_base64
                        },
                        "features": [
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 1
                            }
                        ],
                        "imageContext": {
                            "languageHints": [language]
                        }
                    }
                ]
            }
            
            # Make API call
            response = requests.post(url, json=request_data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Consume quota after successful API call
            self.quota_manager.consume_quota("vision_ocr", 1)
            
            # Extract text from response
            if "responses" in result and result["responses"]:
                response_data = result["responses"][0]
                
                if "textAnnotations" in response_data and response_data["textAnnotations"]:
                    # Get full text from first annotation
                    full_text = response_data["textAnnotations"][0]["description"]
                    
                    # Calculate average confidence from all annotations
                    confidences = []
                    for annotation in response_data["textAnnotations"]:
                        if "confidence" in annotation:
                            confidences.append(annotation["confidence"])
                    
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.9
                    
                    return {
                        "text": full_text.strip(),
                        "confidence": avg_confidence,
                        "engine": "google-vision",
                        "language": language,
                        "word_count": len(full_text.split())
                    }
                else:
                    # No text detected
                    return {
                        "text": "",
                        "confidence": 0.0,
                        "engine": "google-vision",
                        "language": language,
                        "word_count": 0
                    }
            else:
                raise ValueError("Invalid response from Vision API")
                
        except QuotaExceededException:
            raise  # Re-raise quota exceptions
        except Exception as e:
            logger.error(f"Google Cloud Vision API failed: {e}")
            raise ValueError(f"Vision API error: {str(e)}")
    
    def _extract_with_tesseract(
        self,
        image_path: str,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Extract text using Tesseract OCR (fallback)"""
        if self.cloud_only:
            raise ValueError("Tesseract not available in cloud-only mode")
        
        try:
            import pytesseract
            from PIL import Image
            
            logger.info("Using Tesseract OCR for text extraction")
            
            # Map language codes
            lang_map = {
                "en": "eng",
                "hi": "hin",
                "es": "spa",
                "fr": "fra",
                "de": "deu"
            }
            tesseract_lang = lang_map.get(language, "eng")
            
            # Open and process image
            image = Image.open(image_path)
            
            # Extract text with confidence data
            data = pytesseract.image_to_data(
                image,
                lang=tesseract_lang,
                output_type=pytesseract.Output.DICT
            )
            
            # Get text and calculate confidence
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > 0:  # Only include confident detections
                    word = data['text'][i].strip()
                    if word:
                        text_parts.append(word)
                        confidences.append(int(conf))
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            
            return {
                "text": full_text,
                "confidence": avg_confidence,
                "engine": "tesseract",
                "language": language,
                "word_count": len(text_parts)
            }
            
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            raise ValueError(f"Tesseract error: {str(e)}")
    
    def extract_text_from_bytes(
        self,
        image_bytes: bytes,
        file_extension: str = "jpg",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Extract text from image bytes (useful for API uploads)
        
        Args:
            image_bytes: Image file as bytes
            file_extension: File extension (jpg, png, etc.)
            language: Language code for OCR
        
        Returns:
            OCR result dict
        """
        # Save to temporary file
        with tempfile.NamedTemporaryFile(
            suffix=f".{file_extension}",
            delete=False
        ) as temp_file:
            temp_file.write(image_bytes)
            temp_path = temp_file.name
        
        try:
            # Extract text
            result = self.extract_text_from_image(temp_path, language)
            return result
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def get_quota_status(self) -> dict:
        """Get current quota status for OCR"""
        return self.quota_manager.get_quota_status("vision_ocr")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about available OCR services"""
        return {
            "cloud_only": self.cloud_only,
            "vision_api_available": bool(self.vision_client),
            "tesseract_available": self.tesseract_available,
            "quota_status": self.get_quota_status()
        }


# Global OCR service instance
_ocr_service = None

def get_ocr_service() -> CloudOCRService:
    """Get or create global OCR service instance"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = CloudOCRService()
    return _ocr_service