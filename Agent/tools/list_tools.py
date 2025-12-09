"""
List Tools - Tools for listing documents with filters

Provides list_documents tool for the AI agent to retrieve lists of documents
matching specific criteria with role-based access control.
"""

import logging
from typing import Optional
from pathlib import Path

# Setup logging
log_dir = Path("Agent/agent_logs")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "list_tools.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def list_documents(
    language: Optional[str] = None,
    document_type: Optional[str] = None,
    year_from: Optional[str] = None,
    year_to: Optional[str] = None,
    limit: int = 10,
    user_role: Optional[str] = None,
    user_institution_id: Optional[int] = None
) -> str:
    """
    List documents matching specific criteria with role-based access control.
    
    Args:
        language: Filter by language (e.g., "Hindi", "English")
        document_type: Filter by document type (e.g., "Policy", "Guideline")
        year_from: Filter by start year (e.g., "2018")
        year_to: Filter by end year (e.g., "2021")
        limit: Maximum number of documents to return (default: 10, max: 50)
        user_role: User's role for access control
        user_institution_id: User's institution ID
    
    Returns:
        Formatted string with document list and metadata
    """
    logger.info(f"Listing documents with filters: language={language}, type={document_type}, "
                f"year_from={year_from}, year_to={year_to}, limit={limit}, role={user_role}")
    
    # Enforce limit bounds
    limit = min(max(1, limit), 50)  # Between 1 and 50
    
    try:
        from backend.database import SessionLocal, Document, DocumentMetadata
        from backend.constants.roles import DEVELOPER, MINISTRY_ADMIN, UNIVERSITY_ADMIN
        from sqlalchemy import or_, and_, extract
        
        db = SessionLocal()
        
        # Build base query
        query = db.query(Document, DocumentMetadata).join(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        )
        
        # Apply role-based access control
        if user_role == DEVELOPER:
            # Developer can see all documents
            pass
        elif user_role == MINISTRY_ADMIN:
            # Ministry admin can see public, restricted, and institution_only
            query = query.filter(
                Document.visibility_level.in_(['public', 'restricted', 'institution_only'])
            )
        elif user_role == UNIVERSITY_ADMIN:
            # University admin can see public and their institution's documents
            query = query.filter(
                or_(
                    Document.visibility_level == 'public',
                    and_(
                        Document.visibility_level.in_(['institution_only', 'restricted']),
                        Document.institution_id == user_institution_id
                    )
                )
            )
        else:
            # Other roles can see public and their institution's documents
            filters = [Document.visibility_level == 'public']
            if user_institution_id:
                filters.append(
                    and_(
                        Document.visibility_level == 'institution_only',
                        Document.institution_id == user_institution_id
                    )
                )
            query = query.filter(or_(*filters))
        
        # Apply filters
        filters_applied = []
        
        if language:
            # Detect language by Unicode script in title and key_topics
            from sqlalchemy import func, text
            
            if language.lower() == 'hindi':
                # Hindi uses Devanagari script (U+0900 to U+097F)
                # Filter documents with Devanagari characters in title OR key_topics
                query = query.filter(
                    or_(
                        DocumentMetadata.title.op('~')(r'[\u0900-\u097F]'),
                        func.array_to_string(DocumentMetadata.key_topics, ' ').op('~')(r'[\u0900-\u097F]')
                    )
                )
            elif language.lower() == 'english':
                # English uses Latin script - filter for primarily Latin text
                query = query.filter(
                    and_(
                        DocumentMetadata.title.op('~')(r'[a-zA-Z]'),
                        ~DocumentMetadata.title.op('~')(r'[\u0900-\u097F]'),  # Exclude Hindi in title
                        or_(
                            DocumentMetadata.key_topics == None,
                            ~func.array_to_string(DocumentMetadata.key_topics, ' ').op('~')(r'[\u0900-\u097F]')  # Exclude Hindi in topics
                        )
                    )
                )
            else:
                # Fallback: search in keywords, title, summary (case-insensitive)
                language_lower = language.lower()
                query = query.filter(
                    or_(
                        func.lower(func.array_to_string(DocumentMetadata.keywords, ' ')).contains(language_lower),
                        func.lower(DocumentMetadata.title).contains(language_lower),
                        func.lower(DocumentMetadata.summary).contains(language_lower)
                    )
                )
            
            filters_applied.append(f"Language: {language}")
        
        if document_type:
            query = query.filter(DocumentMetadata.document_type.ilike(f"%{document_type}%"))
            filters_applied.append(f"Type: {document_type}")
        
        if year_from:
            try:
                year_int = int(year_from)
                query = query.filter(extract('year', Document.uploaded_at) >= year_int)
                filters_applied.append(f"From Year: {year_from}")
            except ValueError:
                logger.warning(f"Invalid year_from: {year_from}")
        
        if year_to:
            try:
                year_int = int(year_to)
                query = query.filter(extract('year', Document.uploaded_at) <= year_int)
                filters_applied.append(f"To Year: {year_to}")
            except ValueError:
                logger.warning(f"Invalid year_to: {year_to}")
        
        # Order by upload date (newest first)
        query = query.order_by(Document.uploaded_at.desc())
        
        # Get total count before limiting
        total_count = query.count()
        
        # Apply limit
        results = query.limit(limit).all()
        
        db.close()
        
        if not results:
            if filters_applied:
                filters_str = ", ".join(filters_applied)
                return f"No documents found matching criteria: {filters_str}"
            else:
                return "No documents found accessible to your role."
        
        # Format response
        response = f"Found {total_count} documents"
        if filters_applied:
            filters_str = ", ".join(filters_applied)
            response += f" matching criteria: {filters_str}"
        response += f"\n\nShowing {len(results)} of {total_count}:\n\n"
        
        for i, (doc, meta) in enumerate(results, 1):
            # Format upload date
            upload_date = doc.uploaded_at.strftime("%Y-%m-%d") if doc.uploaded_at else "Unknown"
            
            # Get language from keywords
            doc_language = "Unknown"
            if meta.keywords:
                # Look for language keywords
                languages = ["Hindi", "English", "Tamil", "Telugu", "Bengali", "Marathi", 
                           "Gujarati", "Kannada", "Malayalam", "Punjabi", "Urdu", "Odia"]
                for lang in languages:
                    if lang in meta.keywords or lang.lower() in [k.lower() for k in meta.keywords]:
                        doc_language = lang
                        break
            
            # Approval status badge
            approval_badge = "✅ Approved" if doc.approval_status == 'approved' else "⏳ Pending"
            
            response += f"{i}. Document ID: {doc.id} [{approval_badge}]\n"
            response += f"   Title: {meta.title or doc.filename}\n"
            response += f"   Source: {doc.filename}\n"
            response += f"   Type: {meta.document_type or 'Unknown'}\n"
            response += f"   Language: {doc_language}\n"
            response += f"   Uploaded: {upload_date}\n"
            response += f"   Approval Status: {doc.approval_status}\n"
            
            # Add summary if available (truncated)
            if meta.summary:
                summary_preview = meta.summary[:150] + "..." if len(meta.summary) > 150 else meta.summary
                response += f"   **Summary:** {summary_preview}\n"
            
            response += "\n"
        
        if total_count > limit:
            response += f"\n(Showing {limit} of {total_count} documents. Use filters to narrow results.)"
        
        logger.info(f"Listed {len(results)} of {total_count} documents")
        return response
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        return f"Error listing documents: {str(e)}"


def list_documents_wrapper(args: str, user_role: Optional[str] = None, user_institution_id: Optional[int] = None) -> str:
    """
    Wrapper function for list_documents tool to be used by the agent.
    Parses string arguments and calls list_documents.
    
    Args:
        args: String representation of arguments (e.g., "{'language': 'Hindi', 'limit': 10}")
        user_role: User's role for access control
        user_institution_id: User's institution ID
    
    Returns:
        Formatted document list
    """
    try:
        # Parse arguments
        if not args or args.strip() in ["{}", "", "None"]:
            parsed_args = {}
        else:
            parsed_args = eval(args)
        
        # Extract parameters
        language = parsed_args.get('language')
        document_type = parsed_args.get('document_type')
        year_from = parsed_args.get('year_from')
        year_to = parsed_args.get('year_to')
        limit = parsed_args.get('limit', 10)
        
        # Call list_documents
        return list_documents(
            language=language,
            document_type=document_type,
            year_from=year_from,
            year_to=year_to,
            limit=limit,
            user_role=user_role,
            user_institution_id=user_institution_id
        )
        
    except Exception as e:
        logger.error(f"Error in list_documents_wrapper: {str(e)}")
        return f"Error parsing arguments: {str(e)}"
