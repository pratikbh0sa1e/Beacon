"""Compliance checking tools using LLM for document verification"""
import logging
from typing import List, Dict, Optional
import google.generativeai as genai
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceChecker:
    """Tool for checking document compliance against criteria using LLM"""
    
    def __init__(self, google_api_key: str):
        """
        Initialize the compliance checker
        
        Args:
            google_api_key: Google API key for Gemini
        """
        genai.configure(api_key=google_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        logger.info("ComplianceChecker initialized with Gemini 2.0 Flash")
    
    def check_compliance(
        self,
        document: Dict,
        checklist: List[str],
        strict_mode: bool = False
    ) -> Dict:
        """
        Check if document complies with given criteria
        
        Args:
            document: Document dict with 'id', 'title', 'text', 'metadata'
            checklist: List of compliance criteria to check
            strict_mode: If True, requires explicit evidence for each item
        
        Returns:
            Compliance report with pass/fail for each criterion and evidence
        """
        try:
            if not checklist:
                return {
                    "error": "Checklist cannot be empty",
                    "status": "failed"
                }
            
            if len(checklist) > 20:
                return {
                    "error": "Maximum 20 checklist items allowed",
                    "status": "failed"
                }
            
            # Build compliance check prompt
            prompt = self._build_compliance_prompt(document, checklist, strict_mode)
            
            # Get LLM response
            logger.info(f"Checking compliance for document {document['id']} against {len(checklist)} criteria")
            response = self.model.generate_content(prompt)
            
            # Parse response
            compliance_result = self._parse_compliance_response(
                response.text,
                document,
                checklist
            )
            
            return compliance_result
            
        except Exception as e:
            logger.error(f"Error in check_compliance: {str(e)}")
            return {
                "error": f"Compliance check failed: {str(e)}",
                "status": "failed"
            }
    
    def _build_compliance_prompt(
        self,
        document: Dict,
        checklist: List[str],
        strict_mode: bool
    ) -> str:
        """Build the compliance check prompt for LLM"""
        
        prompt = f"""You are a compliance verification expert. Analyze the following document and verify if it meets the specified compliance criteria.

DOCUMENT TO ANALYZE:
Title: {document['title']}
"""
        
        # Add metadata if available
        if document.get('metadata'):
            meta = document['metadata']
            if meta.get('summary'):
                prompt += f"Summary: {meta['summary']}\n"
            if meta.get('department'):
                prompt += f"Department: {meta['department']}\n"
            if meta.get('document_type'):
                prompt += f"Type: {meta['document_type']}\n"
        
        # Smart text extraction for long documents
        full_text = document.get('text', '')
        extracted_text = self._extract_relevant_sections(full_text, checklist)
        
        prompt += f"\nDocument Content:\n{extracted_text}\n"
        
        prompt += f"""

COMPLIANCE CHECKLIST:
Verify if the document meets the following criteria:
"""
        
        for i, item in enumerate(checklist, 1):
            prompt += f"{i}. {item}\n"
        
        prompt += f"""

INSTRUCTIONS:
1. For EACH criterion, determine if the document complies (true/false)
2. Provide specific EVIDENCE from the document (quote relevant text)
3. If evidence is not found, clearly state "Not found" or "Not specified"
4. Be {"strict - require explicit evidence" if strict_mode else "reasonable - infer from context if clear"}
5. Quote exact text from document as evidence

OUTPUT FORMAT (JSON):
{{
  "compliance_results": [
    {{
      "criterion": "criterion text",
      "compliant": true/false,
      "evidence": "exact quote from document or explanation",
      "confidence": "high|medium|low",
      "location": "section/paragraph where found"
    }}
  ],
  "overall_compliance": {{
    "total_criteria": {len(checklist)},
    "criteria_met": number,
    "compliance_percentage": percentage,
    "status": "compliant|partially_compliant|non_compliant"
  }},
  "recommendations": ["suggestion 1", "suggestion 2"]
}}

Provide ONLY the JSON output, no additional text.
"""
        
        return prompt
    
    def _extract_relevant_sections(
        self,
        full_text: str,
        checklist: List[str]
    ) -> str:
        """
        Extract relevant sections from long documents based on checklist keywords
        
        Strategy:
        1. If document is short (<10000 chars), return full text
        2. If long, extract:
           - First 2000 chars (introduction)
           - Sections matching checklist keywords
           - Last 1000 chars (conclusion)
        """
        if len(full_text) <= 10000:
            return full_text
        
        # Extract keywords from checklist
        keywords = []
        for item in checklist:
            # Extract important words (lowercase, remove common words)
            words = item.lower().split()
            keywords.extend([w for w in words if len(w) > 3 and w not in ['has', 'the', 'and', 'with', 'for', 'from']])
        
        # Start with introduction
        extracted = full_text[:2000]
        extracted += "\n\n[... middle sections ...]\n\n"
        
        # Find relevant sections (search for keyword matches)
        lines = full_text.split('\n')
        relevant_sections = []
        context_window = 5  # Lines before and after match
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            # Check if line contains any keyword
            if any(keyword in line_lower for keyword in keywords):
                # Extract context around this line
                start = max(0, i - context_window)
                end = min(len(lines), i + context_window + 1)
                section = '\n'.join(lines[start:end])
                
                if section not in relevant_sections:
                    relevant_sections.append(section)
                    
                    # Limit total extracted text
                    if len('\n\n'.join(relevant_sections)) > 6000:
                        break
        
        if relevant_sections:
            extracted += '\n\n'.join(relevant_sections)
        
        # Add conclusion
        extracted += "\n\n[... end sections ...]\n\n"
        extracted += full_text[-1000:]
        
        logger.info(f"Extracted {len(extracted)} chars from {len(full_text)} chars document")
        return extracted
    
    def _parse_compliance_response(
        self,
        response_text: str,
        document: Dict,
        checklist: List[str]
    ) -> Dict:
        """Parse LLM response into structured compliance report"""
        
        try:
            import json
            import re
            
            # Extract JSON from response
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
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
                "document": {
                    "id": document['id'],
                    "title": document['title'],
                    "filename": document.get('filename', '')
                },
                "compliance_results": parsed.get('compliance_results', []),
                "overall_compliance": parsed.get('overall_compliance', {}),
                "recommendations": parsed.get('recommendations', []),
                "checklist": checklist,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            
            # Fallback: return raw text analysis
            return {
                "status": "partial_success",
                "document": {
                    "id": document['id'],
                    "title": document['title']
                },
                "raw_analysis": response_text,
                "note": "Could not parse structured JSON, returning raw analysis",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error parsing compliance response: {str(e)}")
            return {
                "status": "failed",
                "error": f"Failed to parse compliance check: {str(e)}",
                "raw_response": response_text[:500]
            }
    
    def quick_check(
        self,
        document: Dict,
        criterion: str
    ) -> Dict:
        """
        Quick check for a single criterion
        
        Args:
            document: Document to check
            criterion: Single criterion to verify
        
        Returns:
            Simple pass/fail result with evidence
        """
        try:
            result = self.check_compliance(document, [criterion])
            
            if result.get('status') == 'success' and result.get('compliance_results'):
                first_result = result['compliance_results'][0]
                return {
                    "status": "success",
                    "criterion": criterion,
                    "compliant": first_result.get('compliant', False),
                    "evidence": first_result.get('evidence', ''),
                    "confidence": first_result.get('confidence', 'unknown')
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in quick_check: {str(e)}")
            return {
                "error": f"Quick check failed: {str(e)}",
                "status": "failed"
            }
    
    def batch_check(
        self,
        documents: List[Dict],
        checklist: List[str]
    ) -> Dict:
        """
        Check multiple documents against same checklist
        
        Args:
            documents: List of documents to check
            checklist: Compliance criteria
        
        Returns:
            Batch compliance report
        """
        try:
            if len(documents) > 10:
                return {
                    "error": "Maximum 10 documents allowed in batch check",
                    "status": "failed"
                }
            
            results = []
            for doc in documents:
                result = self.check_compliance(doc, checklist)
                results.append(result)
            
            # Calculate aggregate statistics
            total_docs = len(documents)
            compliant_docs = sum(
                1 for r in results 
                if r.get('status') == 'success' and 
                r.get('overall_compliance', {}).get('status') == 'compliant'
            )
            
            return {
                "status": "success",
                "batch_results": results,
                "summary": {
                    "total_documents": total_docs,
                    "compliant_documents": compliant_docs,
                    "compliance_rate": round((compliant_docs / total_docs) * 100, 2) if total_docs > 0 else 0
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in batch_check: {str(e)}")
            return {
                "error": f"Batch check failed: {str(e)}",
                "status": "failed"
            }
    
    def generate_compliance_report(
        self,
        document: Dict,
        checklist: List[str]
    ) -> Dict:
        """
        Generate detailed compliance report with recommendations
        
        Args:
            document: Document to analyze
            checklist: Compliance criteria
        
        Returns:
            Detailed report with actionable recommendations
        """
        try:
            # Run compliance check
            result = self.check_compliance(document, checklist, strict_mode=True)
            
            if result.get('status') != 'success':
                return result
            
            # Enhance with detailed recommendations
            compliance_results = result.get('compliance_results', [])
            non_compliant = [
                r for r in compliance_results 
                if not r.get('compliant', False)
            ]
            
            report = {
                "status": "success",
                "document": result['document'],
                "compliance_summary": result['overall_compliance'],
                "detailed_results": compliance_results,
                "non_compliant_items": non_compliant,
                "recommendations": result.get('recommendations', []),
                "action_required": len(non_compliant) > 0,
                "priority": "high" if len(non_compliant) > len(checklist) / 2 else "medium" if len(non_compliant) > 0 else "low",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}")
            return {
                "error": f"Report generation failed: {str(e)}",
                "status": "failed"
            }


# Convenience function for easy import
def create_compliance_checker(google_api_key: str) -> ComplianceChecker:
    """Create and return a ComplianceChecker instance"""
    return ComplianceChecker(google_api_key)
