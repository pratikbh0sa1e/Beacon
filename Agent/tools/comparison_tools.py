"""Policy comparison tools using LLM for structured analysis"""
import logging
from typing import List, Dict, Optional
import google.generativeai as genai
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PolicyComparisonTool:
    """Tool for comparing multiple policy documents using LLM"""
    
    def __init__(self, google_api_key: str):
        """
        Initialize the comparison tool
        
        Args:
            google_api_key: Google API key for Gemini
        """
        genai.configure(api_key=google_api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("PolicyComparisonTool initialized with Gemini 2.0 Flash")
    
    def compare_policies(
        self, 
        documents: List[Dict],
        comparison_aspects: Optional[List[str]] = None
    ) -> Dict:
        """
        Compare multiple policy documents
        
        Args:
            documents: List of document dicts with 'id', 'title', 'text', 'metadata'
            comparison_aspects: Optional list of aspects to compare
                              Default: objectives, scope, beneficiaries, budget, timeline
        
        Returns:
            Structured comparison matrix with extracted information
        """
        try:
            if not documents or len(documents) < 2:
                return {
                    "error": "At least 2 documents required for comparison",
                    "status": "failed"
                }
            
            if len(documents) > 5:
                return {
                    "error": "Maximum 5 documents can be compared at once",
                    "status": "failed"
                }
            
            # Default comparison aspects
            if not comparison_aspects:
                comparison_aspects = [
                    "objectives",
                    "scope",
                    "beneficiaries",
                    "budget",
                    "timeline",
                    "key_provisions",
                    "implementation_strategy"
                ]
            
            # Build comparison prompt
            prompt = self._build_comparison_prompt(documents, comparison_aspects)
            
            # Get LLM response
            logger.info(f"Comparing {len(documents)} documents using LLM")
            response = self.model.generate_content(prompt)
            
            # Parse response
            comparison_result = self._parse_comparison_response(
                response.text, 
                documents, 
                comparison_aspects
            )
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"Error in compare_policies: {str(e)}")
            return {
                "error": f"Comparison failed: {str(e)}",
                "status": "failed"
            }
    
    def _build_comparison_prompt(
        self, 
        documents: List[Dict], 
        aspects: List[str]
    ) -> str:
        """Build the comparison prompt for LLM"""
        
        prompt = """You are a policy analysis expert. Compare the following policy documents and extract structured information.

DOCUMENTS TO COMPARE:
"""
        
        # Add each document
        for i, doc in enumerate(documents, 1):
            prompt += f"\n--- DOCUMENT {i}: {doc['title']} ---\n"
            # Limit text to first 3000 chars to avoid token limits
            text = doc.get('text', '')[:3000]
            prompt += f"{text}\n"
            
            # Add metadata if available
            if doc.get('metadata'):
                meta = doc['metadata']
                if meta.get('summary'):
                    prompt += f"\nSummary: {meta['summary']}\n"
        
        prompt += f"""

COMPARISON ASPECTS:
Extract and compare the following aspects from each document:
{', '.join(aspects)}

INSTRUCTIONS:
1. For each aspect, extract relevant information from EACH document
2. If information is not found, write "Not specified"
3. Be concise but accurate
4. Highlight key differences between documents
5. Use bullet points for clarity

OUTPUT FORMAT (JSON):
{{
  "comparison_matrix": {{
    "objectives": {{
      "document_1": "...",
      "document_2": "...",
      "differences": "..."
    }},
    "scope": {{
      "document_1": "...",
      "document_2": "...",
      "differences": "..."
    }},
    ... (for each aspect)
  }},
  "summary": {{
    "key_similarities": ["...", "..."],
    "key_differences": ["...", "..."],
    "recommendations": ["...", "..."]
  }}
}}

Provide ONLY the JSON output, no additional text.
"""
        
        return prompt
    
    def _parse_comparison_response(
        self, 
        response_text: str, 
        documents: List[Dict],
        aspects: List[str]
    ) -> Dict:
        """Parse LLM response into structured format"""
        
        try:
            import json
            import re
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                # Try to find JSON object
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_text = json_match.group(0)
                else:
                    json_text = response_text
            
            # Parse JSON
            parsed = json.loads(json_text)
            
            # Build structured result
            result = {
                "status": "success",
                "documents": [
                    {
                        "id": doc['id'],
                        "title": doc['title'],
                        "filename": doc.get('filename', ''),
                        "approval_status": doc.get('approval_status', 'unknown')
                    }
                    for doc in documents
                ],
                "comparison_matrix": parsed.get('comparison_matrix', {}),
                "summary": parsed.get('summary', {}),
                "aspects_compared": aspects,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            
            # Fallback: return raw text analysis
            return {
                "status": "partial_success",
                "documents": [
                    {
                        "id": doc['id'],
                        "title": doc['title'],
                        "filename": doc.get('filename', '')
                    }
                    for doc in documents
                ],
                "raw_analysis": response_text,
                "note": "Could not parse structured JSON, returning raw analysis",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error parsing comparison response: {str(e)}")
            return {
                "status": "failed",
                "error": f"Failed to parse comparison: {str(e)}",
                "raw_response": response_text[:500]
            }
    
    def quick_compare(
        self, 
        documents: List[Dict],
        focus_area: Optional[str] = None
    ) -> Dict:
        """
        Quick comparison focusing on specific area
        
        Args:
            documents: List of documents to compare
            focus_area: Specific area to focus on (e.g., "budget", "timeline")
        
        Returns:
            Focused comparison result
        """
        try:
            if focus_area:
                aspects = [focus_area]
            else:
                aspects = ["objectives", "key_provisions"]
            
            return self.compare_policies(documents, aspects)
            
        except Exception as e:
            logger.error(f"Error in quick_compare: {str(e)}")
            return {
                "error": f"Quick comparison failed: {str(e)}",
                "status": "failed"
            }
    
    def find_conflicts(self, documents: List[Dict]) -> Dict:
        """
        Find potential conflicts between policies
        
        Args:
            documents: List of documents to analyze
        
        Returns:
            List of potential conflicts
        """
        try:
            prompt = f"""Analyze the following {len(documents)} policy documents and identify potential CONFLICTS or CONTRADICTIONS.

DOCUMENTS:
"""
            
            for i, doc in enumerate(documents, 1):
                prompt += f"\n--- DOCUMENT {i}: {doc['title']} ---\n"
                text = doc.get('text', '')[:2000]
                prompt += f"{text}\n"
            
            prompt += """

TASK:
Identify any conflicts, contradictions, or inconsistencies between these documents.

OUTPUT FORMAT (JSON):
{
  "conflicts": [
    {
      "type": "contradiction|overlap|inconsistency",
      "severity": "high|medium|low",
      "description": "...",
      "affected_documents": [1, 2],
      "recommendation": "..."
    }
  ],
  "overall_assessment": "..."
}

Provide ONLY the JSON output.
"""
            
            response = self.model.generate_content(prompt)
            
            # Parse response
            import json
            import re
            
            json_match = re.search(r'```json\s*(.*?)\s*```', response.text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                json_text = json_match.group(0) if json_match else response.text
            
            parsed = json.loads(json_text)
            
            return {
                "status": "success",
                "documents": [
                    {"id": doc['id'], "title": doc['title']}
                    for doc in documents
                ],
                "conflicts": parsed.get('conflicts', []),
                "overall_assessment": parsed.get('overall_assessment', ''),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in find_conflicts: {str(e)}")
            return {
                "status": "failed",
                "error": f"Conflict detection failed: {str(e)}"
            }


# Convenience function for easy import
def create_comparison_tool(google_api_key: str) -> PolicyComparisonTool:
    """Create and return a PolicyComparisonTool instance"""
    return PolicyComparisonTool(google_api_key)
