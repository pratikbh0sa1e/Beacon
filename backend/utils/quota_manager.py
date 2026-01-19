"""
Quota Management System for Free-Tier Cloud APIs
Tracks and enforces usage limits for Google Cloud services
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class QuotaManager:
    """
    Manages API quotas for free-tier cloud services
    
    Free Tier Limits:
    - Google Gemini Embeddings: 1,500 requests/day
    - Google Gemini Chat: 15 requests/minute, 1,500 requests/day  
    - Google Cloud Speech-to-Text: 60 minutes/month
    - Google Cloud Vision OCR: 1,000 requests/month
    """
    
    def __init__(self, quota_file: str = "data/quota_usage.json"):
        self.quota_file = Path(quota_file)
        self.quota_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Free tier limits
        self.limits = {
            "gemini_embeddings": {
                "daily_limit": 1500,
                "minute_limit": 15,
                "reset_period": "daily"
            },
            "gemini_chat": {
                "daily_limit": 1500,
                "minute_limit": 15,
                "reset_period": "daily"
            },
            "speech_to_text": {
                "monthly_limit": 60,  # minutes
                "reset_period": "monthly"
            },
            "vision_ocr": {
                "monthly_limit": 1000,
                "reset_period": "monthly"
            }
        }
        
        self.usage = self._load_usage()
    
    def _load_usage(self) -> Dict[str, Any]:
        """Load usage data from file"""
        if self.quota_file.exists():
            try:
                with open(self.quota_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading quota file: {e}")
        
        # Initialize empty usage
        return {
            "gemini_embeddings": {"daily": {}, "minute": {}},
            "gemini_chat": {"daily": {}, "minute": {}},
            "speech_to_text": {"monthly": {}},
            "vision_ocr": {"monthly": {}}
        }
    
    def _save_usage(self):
        """Save usage data to file"""
        try:
            with open(self.quota_file, 'w') as f:
                json.dump(self.usage, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving quota file: {e}")
    
    def _get_current_period_key(self, period: str) -> str:
        """Get current period key for tracking"""
        now = datetime.now()
        
        if period == "daily":
            return now.strftime("%Y-%m-%d")
        elif period == "monthly":
            return now.strftime("%Y-%m")
        elif period == "minute":
            return now.strftime("%Y-%m-%d %H:%M")
        else:
            raise ValueError(f"Unknown period: {period}")
    
    def _cleanup_old_data(self, service: str):
        """Remove old usage data to keep file size manageable"""
        now = datetime.now()
        
        # Clean daily data (keep last 7 days)
        if "daily" in self.usage[service]:
            cutoff_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            self.usage[service]["daily"] = {
                k: v for k, v in self.usage[service]["daily"].items()
                if k >= cutoff_date
            }
        
        # Clean minute data (keep last 2 hours)
        if "minute" in self.usage[service]:
            cutoff_time = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
            self.usage[service]["minute"] = {
                k: v for k, v in self.usage[service]["minute"].items()
                if k >= cutoff_time
            }
        
        # Clean monthly data (keep last 13 months)
        if "monthly" in self.usage[service]:
            cutoff_month = (now - timedelta(days=400)).strftime("%Y-%m")
            self.usage[service]["monthly"] = {
                k: v for k, v in self.usage[service]["monthly"].items()
                if k >= cutoff_month
            }
    
    def check_quota(self, service: str, amount: int = 1) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Check if quota allows the requested usage
        
        Args:
            service: Service name (gemini_embeddings, gemini_chat, etc.)
            amount: Amount to consume (default: 1)
        
        Returns:
            (allowed, error_message, quota_info)
        """
        if service not in self.limits:
            return True, "", {}
        
        limits = self.limits[service]
        service_usage = self.usage.get(service, {})
        
        # Check daily limit
        if "daily_limit" in limits:
            daily_key = self._get_current_period_key("daily")
            daily_used = service_usage.get("daily", {}).get(daily_key, 0)
            
            if daily_used + amount > limits["daily_limit"]:
                return False, f"Daily quota exceeded for {service}. Used: {daily_used}/{limits['daily_limit']}", {
                    "service": service,
                    "period": "daily",
                    "used": daily_used,
                    "limit": limits["daily_limit"],
                    "remaining": limits["daily_limit"] - daily_used
                }
        
        # Check minute limit
        if "minute_limit" in limits:
            minute_key = self._get_current_period_key("minute")
            minute_used = service_usage.get("minute", {}).get(minute_key, 0)
            
            if minute_used + amount > limits["minute_limit"]:
                return False, f"Rate limit exceeded for {service}. Used: {minute_used}/{limits['minute_limit']} requests/minute", {
                    "service": service,
                    "period": "minute",
                    "used": minute_used,
                    "limit": limits["minute_limit"],
                    "remaining": limits["minute_limit"] - minute_used
                }
        
        # Check monthly limit
        if "monthly_limit" in limits:
            monthly_key = self._get_current_period_key("monthly")
            monthly_used = service_usage.get("monthly", {}).get(monthly_key, 0)
            
            if monthly_used + amount > limits["monthly_limit"]:
                return False, f"Monthly quota exceeded for {service}. Used: {monthly_used}/{limits['monthly_limit']}", {
                    "service": service,
                    "period": "monthly",
                    "used": monthly_used,
                    "limit": limits["monthly_limit"],
                    "remaining": limits["monthly_limit"] - monthly_used
                }
        
        return True, "", {}
    
    def consume_quota(self, service: str, amount: int = 1) -> bool:
        """
        Consume quota for a service
        
        Args:
            service: Service name
            amount: Amount to consume
        
        Returns:
            True if quota was consumed, False if quota exceeded
        """
        allowed, error_msg, quota_info = self.check_quota(service, amount)
        
        if not allowed:
            logger.warning(f"Quota exceeded: {error_msg}")
            return False
        
        # Initialize service usage if not exists
        if service not in self.usage:
            self.usage[service] = {}
        
        limits = self.limits[service]
        
        # Update daily usage
        if "daily_limit" in limits:
            daily_key = self._get_current_period_key("daily")
            if "daily" not in self.usage[service]:
                self.usage[service]["daily"] = {}
            self.usage[service]["daily"][daily_key] = self.usage[service]["daily"].get(daily_key, 0) + amount
        
        # Update minute usage
        if "minute_limit" in limits:
            minute_key = self._get_current_period_key("minute")
            if "minute" not in self.usage[service]:
                self.usage[service]["minute"] = {}
            self.usage[service]["minute"][minute_key] = self.usage[service]["minute"].get(minute_key, 0) + amount
        
        # Update monthly usage
        if "monthly_limit" in limits:
            monthly_key = self._get_current_period_key("monthly")
            if "monthly" not in self.usage[service]:
                self.usage[service]["monthly"] = {}
            self.usage[service]["monthly"][monthly_key] = self.usage[service]["monthly"].get(monthly_key, 0) + amount
        
        # Cleanup old data and save
        self._cleanup_old_data(service)
        self._save_usage()
        
        logger.info(f"Consumed {amount} quota for {service}")
        return True
    
    def get_quota_status(self, service: str = None) -> Dict[str, Any]:
        """
        Get current quota status for service(s)
        
        Args:
            service: Specific service name, or None for all services
        
        Returns:
            Dictionary with quota status information
        """
        if service:
            services = [service]
        else:
            services = list(self.limits.keys())
        
        status = {}
        
        for svc in services:
            if svc not in self.limits:
                continue
            
            limits = self.limits[svc]
            service_usage = self.usage.get(svc, {})
            svc_status = {"service": svc, "limits": limits}
            
            # Daily status
            if "daily_limit" in limits:
                daily_key = self._get_current_period_key("daily")
                daily_used = service_usage.get("daily", {}).get(daily_key, 0)
                svc_status["daily"] = {
                    "used": daily_used,
                    "limit": limits["daily_limit"],
                    "remaining": limits["daily_limit"] - daily_used,
                    "percentage": (daily_used / limits["daily_limit"]) * 100
                }
            
            # Minute status
            if "minute_limit" in limits:
                minute_key = self._get_current_period_key("minute")
                minute_used = service_usage.get("minute", {}).get(minute_key, 0)
                svc_status["minute"] = {
                    "used": minute_used,
                    "limit": limits["minute_limit"],
                    "remaining": limits["minute_limit"] - minute_used,
                    "percentage": (minute_used / limits["minute_limit"]) * 100
                }
            
            # Monthly status
            if "monthly_limit" in limits:
                monthly_key = self._get_current_period_key("monthly")
                monthly_used = service_usage.get("monthly", {}).get(monthly_key, 0)
                svc_status["monthly"] = {
                    "used": monthly_used,
                    "limit": limits["monthly_limit"],
                    "remaining": limits["monthly_limit"] - monthly_used,
                    "percentage": (monthly_used / limits["monthly_limit"]) * 100
                }
            
            status[svc] = svc_status
        
        return status
    
    def reset_quota(self, service: str, period: str = None):
        """
        Reset quota for testing purposes
        
        Args:
            service: Service name
            period: Specific period to reset (daily, monthly, minute) or None for all
        """
        if service not in self.usage:
            return
        
        if period:
            if period in self.usage[service]:
                self.usage[service][period] = {}
        else:
            self.usage[service] = {}
        
        self._save_usage()
        logger.info(f"Reset quota for {service}" + (f" ({period})" if period else ""))


# Global quota manager instance
_quota_manager = None

def get_quota_manager() -> QuotaManager:
    """Get or create global quota manager instance"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager


class QuotaExceededException(Exception):
    """Exception raised when API quota is exceeded"""
    
    def __init__(self, service: str, quota_info: Dict[str, Any]):
        self.service = service
        self.quota_info = quota_info
        
        period = quota_info.get("period", "unknown")
        used = quota_info.get("used", 0)
        limit = quota_info.get("limit", 0)
        
        super().__init__(f"Quota exceeded for {service} ({period}): {used}/{limit}")


def check_and_consume_quota(service: str, amount: int = 1):
    """
    Decorator/function to check and consume quota
    
    Args:
        service: Service name
        amount: Amount to consume
    
    Raises:
        QuotaExceededException: If quota is exceeded
    """
    quota_manager = get_quota_manager()
    
    allowed, error_msg, quota_info = quota_manager.check_quota(service, amount)
    if not allowed:
        raise QuotaExceededException(service, quota_info)
    
    success = quota_manager.consume_quota(service, amount)
    if not success:
        raise QuotaExceededException(service, quota_info)


def quota_required(service: str, amount: int = 1):
    """
    Decorator to enforce quota checking on functions
    
    Usage:
        @quota_required("gemini_chat", 1)
        def chat_with_ai(message):
            # Function implementation
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            check_and_consume_quota(service, amount)
            return func(*args, **kwargs)
        return wrapper
    return decorator