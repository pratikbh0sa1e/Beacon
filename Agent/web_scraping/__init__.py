"""
Web Scraping Module for Government Policy Documents

This module provides automated web scraping capabilities for government websites,
enabling automatic document ingestion with full provenance tracking.
"""

from .scraper import WebScraper
from .pdf_downloader import PDFDownloader
from .provenance_tracker import ProvenanceTracker
from .web_source_manager import WebSourceManager

__all__ = [
    'WebScraper',
    'PDFDownloader',
    'ProvenanceTracker',
    'WebSourceManager'
]
