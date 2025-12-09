"""
Document Analysis Router - Analyze scraped documents with AI
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
import logging
from datetime import datetime

from backend.database import get_db, User
from backend.routers.auth_router import get_current_user
from Agent.web_scraping.pdf_downloader import PDFDownloader
from Agent.document_processing.text_extraction_service import TextExtractionService
from Agent.document_processing.progress_manager import get_progress_manager
from Agent.rag_agent.react_agent import PolicyRAGAgent
import os
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/document-analysis", tags=["Document Analysis"])

# Initialize components
pdf_downloader = PDFDownloader()
text_extractor = TextExtractionService(
    quality_threshold=100,
    char_ratio_threshold=0.7,
    max_pages_for_ocr=50,
    enable_ocr=True
)
google_api_key = os.getenv("GOOGLE_API_KEY")
rag_agent = PolicyRAGAgent(google_api_key=google_api_key) if google_api_key else None


class AnalyzeDocumentsRequest(BaseModel):
    document_urls: List[str]
    document_titles: List[str]
    analysis_type: str = "decision_support"


class AnalyzeDocumentsResponse(BaseModel):
    analysis: str
    documents_processed: int
    total_chunks: int
    analysis_id: Optional[int] = None
    ocr_used_count: Optional[int] = 0
    extraction_details: Optional[List[dict]] = []


@router.post("/analyze", response_model=AnalyzeDocumentsResponse)
async def analyze_documents(
    request: AnalyzeDocumentsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download, extract, and analyze multiple documents with AI
    
    Args:
        request: Document URLs and titles to analyze
        current_user: Authenticated user
        db: Database session
    
    Returns:
        AI analysis with metadata
    """
    if not rag_agent:
        raise HTTPException(status_code=500, detail="AI agent not configured")
    
    if not request.document_urls:
        raise HTTPException(status_code=400, detail="No documents provided")
    
    logger.info(f"Analyzing {len(request.document_urls)} documents for user {current_user.id}")
    
    # Initialize progress tracking
    session_id = str(uuid.uuid4())
    progress_mgr = get_progress_manager()
    progress_mgr.start_operation(
        session_id=session_id,
        operation_type='analysis',
        total=len(request.document_urls),
        message=f"Starting analysis of {len(request.document_urls)} documents"
    )
    
    try:
        # Step 1: Download and extract text from all documents
        all_text_chunks = []
        processed_docs = []
        extraction_details = []
        ocr_used_count = 0
        
        for i, (url, title) in enumerate(zip(request.document_urls, request.document_titles)):
            try:
                # Update progress
                progress_mgr.update_progress(
                    session_id=session_id,
                    current=i,
                    message=f"Processing document {i+1}/{len(request.document_urls)}",
                    current_item=title
                )
                
                logger.info(f"Processing document {i+1}/{len(request.document_urls)}: {title}")
                
                # Download PDF
                progress_mgr.update_progress(
                    session_id=session_id,
                    current=i,
                    message=f"Downloading: {title}",
                    current_item=title
                )
                logger.info(f"Downloading: {title}")
                result = pdf_downloader.download_document(url, title)
                
                if result['status'] != 'success':
                    error_detail = result.get('error', 'Unknown error')
                    logger.warning(f"Failed to download {title}: {error_detail}")
                    # Check if it's a 403 error
                    if '403' in error_detail or 'Forbidden' in error_detail:
                        logger.info(f"Document blocked by source website: {title}")
                    continue
                
                if result['status'] == 'success':
                    file_path = result['filepath']
                    
                    # Extract text with intelligent OCR fallback
                    progress_mgr.update_progress(
                        session_id=session_id,
                        current=i,
                        message=f"Extracting text from: {title}",
                        current_item=title
                    )
                    logger.info(f"Extracting text from: {title}")
                    
                    def progress_callback(stage, message):
                        logger.info(f"[{title}] {stage}: {message}")
                        # Update progress with extraction stage
                        if stage == 'ocr':
                            progress_mgr.update_progress(
                                session_id=session_id,
                                current=i,
                                message=f"Applying OCR to: {title}",
                                current_item=title
                            )
                    
                    extraction_result = text_extractor.extract_text(
                        file_path,
                        progress_callback=progress_callback
                    )
                    
                    # Check if extraction was successful
                    if extraction_result.get('error'):
                        logger.error(f"Extraction failed for {title}: {extraction_result['error']}")
                        continue
                    
                    text = extraction_result['text']
                    
                    # Track OCR usage
                    if extraction_result['ocr_triggered']:
                        ocr_used_count += 1
                        logger.info(f"OCR was used for: {title}")
                    
                    # Store extraction details
                    extraction_details.append({
                        'title': title,
                        'method': extraction_result['extraction_method'],
                        'quality_score': extraction_result['quality_score'],
                        'chars_per_page': extraction_result['chars_per_page'],
                        'ocr_used': extraction_result['ocr_triggered'],
                        'processing_time_ms': extraction_result['processing_time_ms']
                    })
                    
                    # Chunk the text (simple chunking - 2000 chars per chunk)
                    chunk_size = 2000
                    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
                    
                    for chunk_idx, chunk in enumerate(chunks[:5]):  # Limit to 5 chunks per doc
                        all_text_chunks.append({
                            'doc_title': title,
                            'doc_url': url,
                            'chunk_index': chunk_idx,
                            'text': chunk
                        })
                    
                    processed_docs.append(title)
                    logger.info(
                        f"Extracted {len(chunks[:5])} chunks from {title} "
                        f"(method: {extraction_result['extraction_method']}, "
                        f"quality: {extraction_result['quality_score']:.1f})"
                    )
                    
            except Exception as e:
                logger.error(f"Error processing {title}: {str(e)}")
                continue
        
        if not all_text_chunks:
            # Provide helpful error message
            error_msg = f"Failed to extract text from any documents. "
            if len(processed_docs) == 0:
                error_msg += "All documents failed to download. This may be due to: " \
                           "1) The source website blocking direct downloads (403 Forbidden), " \
                           "2) Network connectivity issues, or " \
                           "3) Invalid document URLs. " \
                           "Try opening the document URLs directly in your browser first."
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Step 2: Create analysis prompt with document context
        context = "\n\n".join([
            f"Document: {chunk['doc_title']}\nChunk {chunk['chunk_index']+1}:\n{chunk['text'][:1000]}..."
            for chunk in all_text_chunks[:20]  # Limit total chunks
        ])
        
        analysis_prompt = f"""Analyze these policy documents and provide comprehensive decision support:

Documents Analyzed: {', '.join(processed_docs)}

Document Content:
{context}

Provide a structured analysis with:
1. Executive Summary
2. Key Findings (from each document)
3. Policy Recommendations
4. Risk Assessment
5. Compliance Considerations

Be specific and reference the documents by name."""

        # Step 3: Get AI analysis
        progress_mgr.update_progress(
            session_id=session_id,
            current=len(processed_docs),
            message="Analyzing documents with AI...",
            current_item="AI Analysis"
        )
        logger.info("Sending to AI for analysis...")
        
        # Set user context for RAG agent
        rag_agent.current_user_role = current_user.role
        rag_agent.current_user_institution_id = current_user.institution_id
        
        # Query the agent
        response = rag_agent.query(analysis_prompt)
        analysis_text = response.get('response', 'Analysis failed')
        
        # Step 4: Save analysis to database (optional - implement if needed)
        # For now, we'll just return the analysis
        
        # Mark operation as complete
        progress_mgr.complete_operation(
            session_id=session_id,
            message=f"Analysis complete: {len(processed_docs)} documents processed"
        )
        
        logger.info(
            f"Analysis complete: {len(analysis_text)} characters, "
            f"{ocr_used_count}/{len(processed_docs)} documents used OCR"
        )
        
        return AnalyzeDocumentsResponse(
            analysis=analysis_text,
            documents_processed=len(processed_docs),
            total_chunks=len(all_text_chunks),
            analysis_id=None,  # TODO: Save to DB and return ID
            ocr_used_count=ocr_used_count,
            extraction_details=extraction_details
        )
        
    except Exception as e:
        # Mark operation as error
        progress_mgr.error_operation(
            session_id=session_id,
            error_message=str(e)
        )
        logger.error(f"Error in document analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/progress/{session_id}")
async def get_analysis_progress(session_id: str):
    """Get progress for an analysis operation"""
    progress_mgr = get_progress_manager()
    progress = progress_mgr.get_progress(session_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return progress


@router.get("/health")
async def health_check():
    """Check if analysis service is ready"""
    return {
        "status": "healthy",
        "rag_agent_available": rag_agent is not None,
        "pdf_downloader_available": pdf_downloader is not None,
        "text_extractor_available": text_extractor is not None,
        "ocr_enabled": text_extractor.enable_ocr if text_extractor else False
    }
