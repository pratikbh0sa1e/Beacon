"""
Quota Management System for Free-Tier Cloud Deployment

Tracks and enforces API usage limits for:
- Google Gemini Embeddings: 1,500 requests/day
- Google Cloud Speech-to-Text: 60 minutes/month  
- Google Cloud Vision OCR: 1,000 requests/month

Prevents exceeding free tiers by showing "limit exceeded" errors.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Setup logging
logger = logging.getLogger(__name__)

class QuotaService(Enum):
    """Supported quota services"""
    GEMINI_EMBEDDINGS = "gemini_embeddings"
    GEMINI_CHAT = "gemini_chat"
    GOOGLE_SPEECH = "google_speech"
    GOOGLE_VISION = "google_vision"
    OPENROUTER = "openrouter"

@dataclass
class QuotaLimit:
    """Quota limit configuration"""
    service: str
    limit: int
    period: str  # "daily", "monthly"
    unit: str    # "requests", "minutes", "characters"
    reset_time: Optional[datetime] = None

@dataclass
class QuotaUsage:
    """Current quota usage"""
    service: str
    used: int
    limit: int
    period: str
    unit: str
    reset_time: datetime
    last_updated: datetime

class QuotaManager:
    """
    Manages API quota limits for free-tier cloud services
    
    Features:
    - Tracks usage across multiple services
    - Enforces daily/monthly limits
    - Automatic quota reset
    - Persistent storage
    - User-friendly error messages
    """
    
    def __init__(self, storage_path: str = "data/quota_usage.json"):
        """
        Initialize quota manager
        
        Args:
            storage_path: Path to store quota usage data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Define quota limits for free tiers
        self.quota_limits = {
            QuotaService.GEMINI_EMBEDDINGS: QuotaLimit(
                service="gemini_embeddings",
                limit=1500,  # 1,500 requests/day
                period="daily",
                unit="requests"
            ),
            QuotaService.GEMINI_CHAT: QuotaLimit(
                service="gemini_chat", 
                limit=1500,  # 1,500 requests/day (shared with embeddings)
                period="daily",
                unit="requests"
            ),
            QuotaService.GOOGLE_SPEECH: QuotaLimit(
                service="google_speech",
                limit=60,    # 60 minutes/month
                period="monthly", 
                unit="minutes"
            ),
            QuotaService.GOOGLE_VISION: QuotaLimit(
                service="google_vision",
                limit=1000,  # 1,000 requests/month
                period="monthly",
                unit="requests"
            ),
            QuotaService.OPENROUTER: QuotaLimit(
                service="openrouter",
                limit=200,   # 200 requests/day (free tier)
                period="daily",
                unit="requests"
            )
        }
        
 