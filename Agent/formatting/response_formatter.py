"""
Response Formatter Module

Formats agent responses into structured data based on intent and tool outputs.
Supports: comparison tables, document counts, document lists, and standard text.
"""

import logging
import re
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """
    Formats agent responses into structured data for frontend rendering.
    
    Format Types:
    - comparison: Comparison table with document columns
    - count: Document count with action button
    - list: Document list with metadata cards
    - text: Standard text response (default)
    """
    
    def __init__(self):
        """Initialize the response formatter"""
        logger.info("Response formatter initialized")
    
    def format_response(
        self,
        intent: str,
        response_text: str,
        tool_outputs: List[Dict[str, Any]],
        citations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Format response based on intent and tool outputs.
        
        Args:
            intent: Query intent ("comparison", "count", "list", "qa")
            response_text: Agent's text response
            tool_outputs: List of tool execution results
            citations: List of document citations
        
        Returns:
            Formatted response with structure:
            {
                "answer": str,
                "format": str,
                "data": dict,
                "citations": list
            }
        """
        logger.info(f"Formatting response for intent: {intent}")
        
        try:
            # Route to appropriate formatter based on intent
            if intent == "comparison":
                return self._format_comparison(response_text, tool_outputs, citations)
            elif intent == "count":
                return self._format_count(response_text, tool_outputs, citations)
            elif intent == "list":
                return self._format_list(response_text, tool_outputs, citations)
            else:
                # Default to text format
                return self._format_text(response_text, citations)
        
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}")
            # Fallback to text format on error
            return self._format_text(response_text, citations)
    
    def _format_comparison(
        self,
        response_text: str,
        tool_outputs: List[Dict[str, Any]],
        citations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format comparison response with table structure"""
        logger.info("Formatting comparison response")
        
        # Extract comparison table from markdown
        table_data = self._extract_comparison_table(response_text)
        
        if table_data:
            return {
                "answer": response_text,
                "format": "comparison",
                "data": table_data,
                "citations": citations
            }
        else:
            # Fallback to text if table extraction fails
            logger.warning("Could not extract comparison table, falling back to text")
            return self._format_text(response_text, citations)
    
    def _format_count(
        self,
        response_text: str,
        tool_outputs: List[Dict[str, Any]],
        citations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format count response with action button"""
        logger.info("Formatting count response")
        
        # Extract count from response
        count_data = self._extract_count_data(response_text)
        
        if count_data:
            return {
                "answer": response_text,
                "format": "count",
                "data": count_data,
                "citations": citations
            }
        else:
            # Fallback to text if count extraction fails
            logger.warning("Could not extract count data, falling back to text")
            return self._format_text(response_text, citations)
    
    def _format_list(
        self,
        response_text: str,
        tool_outputs: List[Dict[str, Any]],
        citations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format list response with document cards"""
        logger.info("Formatting list response")
        
        # Extract document list from response
        list_data = self._extract_list_data(response_text)
        
        if list_data:
            return {
                "answer": response_text,
                "format": "list",
                "data": list_data,
                "citations": citations
            }
        else:
            # Fallback to text if list extraction fails
            logger.warning("Could not extract list data, falling back to text")
            return self._format_text(response_text, citations)
    
    def _format_text(
        self,
        response_text: str,
        citations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Format standard text response"""
        logger.info("Formatting text response")
        
        return {
            "answer": response_text,
            "format": "text",
            "data": None,
            "citations": citations
        }
    
    def _extract_comparison_table(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract comparison table data from markdown text.
        
        Looks for markdown table format:
        | Document ID | Title | Status | Confidence | Key Content |
        """
        try:
            # Find the markdown table
            table_pattern = r'\|[^\n]+\|[^\n]+\n\|[-:\s|]+\n((?:\|[^\n]+\n)+)'
            match = re.search(table_pattern, text)
            
            if not match:
                return None
            
            # Extract table rows
            table_content = match.group(0)
            lines = table_content.strip().split('\n')
            
            # Parse header
            header_line = lines[0]
            headers = [h.strip() for h in header_line.split('|')[1:-1]]
            
            # Parse rows (skip header and separator)
            rows = []
            for line in lines[2:]:
                if line.strip():
                    cells = [c.strip() for c in line.split('|')[1:-1]]
                    if len(cells) == len(headers):
                        row_dict = dict(zip(headers, cells))
                        rows.append(row_dict)
            
            # Extract document metadata from detailed sections
            documents = []
            doc_pattern = r'#### Document ID: (\d+)[^\n]*\n\*\*Title:\*\* ([^\n]+)\n\*\*Source:\*\* ([^\n]+)\n\*\*Approval Status:\*\* ([^\n]+)'
            for match in re.finditer(doc_pattern, text):
                documents.append({
                    "id": int(match.group(1)),
                    "title": match.group(2).strip(),
                    "source": match.group(3).strip(),
                    "approval_status": match.group(4).strip()
                })
            
            # Extract aspect being compared
            aspect_match = re.search(r"## 📊 Comparison: '([^']+)'", text)
            aspect = aspect_match.group(1) if aspect_match else "comparison"
            
            return {
                "aspect": aspect,
                "table": rows,
                "documents": documents
            }
        
        except Exception as e:
            logger.error(f"Error extracting comparison table: {str(e)}")
            return None
    
    def _extract_count_data(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract count data from response text.
        
        Looks for patterns like:
        **Total Documents Found: 45**
        """
        try:
            # Extract count
            count_match = re.search(r'\*\*Total Documents Found:\s*(\d+)\*\*', text)
            if not count_match:
                # Try alternative pattern
                count_match = re.search(r'Found (\d+) documents', text)
            
            if not count_match:
                return None
            
            count = int(count_match.group(1))
            
            # Extract filters
            filters = {}
            filter_pattern = r'- (Language|Type|From Year|To Year): ([^\n]+)'
            for match in re.finditer(filter_pattern, text):
                filter_key = match.group(1).lower().replace(' ', '_')
                filter_value = match.group(2).strip()
                filters[filter_key] = filter_value
            
            # Extract access level
            access_match = re.search(r'\*\*Access Level:\*\* ([^\n]+)', text)
            access_level = access_match.group(1).strip() if access_match else "public"
            
            return {
                "count": count,
                "filters": filters,
                "access_level": access_level,
                "action": {
                    "label": "View All Documents",
                    "type": "list_documents",
                    "params": filters
                }
            }
        
        except Exception as e:
            logger.error(f"Error extracting count data: {str(e)}")
            return None
    
    def _extract_list_data(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract document list data from response text.
        
        Looks for patterns like:
        1. Document ID: 123 [✅ Approved]
           Title: ...
        """
        try:
            # Extract total count
            total_match = re.search(r'Found (\d+) documents', text)
            if not total_match:
                return None
            
            total = int(total_match.group(1))
            
            # Extract showing count
            showing_match = re.search(r'Showing (\d+) of \d+', text)
            showing = int(showing_match.group(1)) if showing_match else total
            
            # Extract documents
            documents = []
            doc_pattern = r'(\d+)\. Document ID: (\d+) \[([^\]]+)\]\n\s+Title: ([^\n]+)\n\s+Source: ([^\n]+)\n\s+Type: ([^\n]+)\n\s+Language: ([^\n]+)\n\s+Uploaded: ([^\n]+)\n\s+Approval Status: ([^\n]+)'
            
            for match in re.finditer(doc_pattern, text):
                # Extract summary if present
                summary = ""
                summary_pattern = rf'{match.group(0)}[^\n]*\n\s+\*\*Summary:\*\* ([^\n]+)'
                summary_match = re.search(summary_pattern, text)
                if summary_match:
                    summary = summary_match.group(1).strip()
                
                documents.append({
                    "id": int(match.group(2)),
                    "title": match.group(4).strip(),
                    "filename": match.group(5).strip(),
                    "type": match.group(6).strip(),
                    "language": match.group(7).strip(),
                    "uploaded_at": match.group(8).strip(),
                    "approval_status": match.group(9).strip(),
                    "status_badge": match.group(3).strip(),
                    "summary": summary
                })
            
            if not documents:
                return None
            
            return {
                "documents": documents,
                "total": total,
                "showing": showing,
                "has_more": showing < total
            }
        
        except Exception as e:
            logger.error(f"Error extracting list data: {str(e)}")
            return None


# Global formatter instance
_formatter = None


def get_formatter() -> ResponseFormatter:
    """Get or create the global response formatter instance"""
    global _formatter
    if _formatter is None:
        _formatter = ResponseFormatter()
    return _formatter


def format_response(
    intent: str,
    response_text: str,
    tool_outputs: List[Dict[str, Any]],
    citations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Convenience function to format response.
    
    Args:
        intent: Query intent
        response_text: Agent's text response
        tool_outputs: Tool execution results
        citations: Document citations
    
    Returns:
        Formatted response dictionary
    """
    formatter = get_formatter()
    return formatter.format_response(intent, response_text, tool_outputs, citations)
