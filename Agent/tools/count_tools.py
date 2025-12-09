"""
Count Tools - Tools for counting documents with filters

Provides count_documents tool for the AI agent to count documents
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
        logging.FileHandler(log_dir / "count_tools.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def count_documents(
    language: Optional[str] = None,
    document_type: Optional[str] = None,
    year_from: Optional[str] = None,
    year_to: Optional[str] = None,
    user_role: Optional[str] = None,
    user_institution_id: Optional[int] = None
) -> str:
    """
    Count documents matching specific criteria with role-based access control.
    
    Args:
        language: Filter by language (e.g., "Hindi", "English")
        document_type: Filter by document type (e.g., "Policy", "Guideline")
        year_from: Filter by start year (e.g., "2018")
        year_to: Filter by end year (e.g., "2021")
        user_role: User's role for access control
        user_institution_id: User's institution ID
    
    Returns:
        Formatted string with count and filter details
    """
    logger.info(f"Counting documents with filters: language={language}, type={document_type}, "
                f"year_from={year_from}, year_to={year_to}, role={user_role}")
    
    try:
        from backend.database import SessionLocal, Document, DocumentMetadata
        from backend.constants.roles import DEVELOPER, MINISTRY_ADMIN, UNIVERSITY_ADMIN
        from sqlalchemy import or_, and_, extract
        
        db = SessionLocal()
        
        # Build base query
        query = db.query(Document).join(
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
            # Other roles (student, public_viewer, etc.) can see public and their institution's documents
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
        
        # Get count
        count = query.count()
        
        db.close()
        
        # Format response with clear structure for agent
        response = f"📊 **DOCUMENT COUNT RESULT**\n\n"
        response += f"**Total Documents Found: {count}**\n\n"
        
        if filters_applied:
            response += "**Filters Applied:**\n"
            for filter_item in filters_applied:
                response += f"- {filter_item}\n"
            response += f"\n**Access Level:** {user_role or 'public'}\n"
        else:
            response += f"**Access Level:** {user_role or 'public'} (all accessible documents)\n"
        
        # Add suggestion to list documents
        if count > 0 and count <= 50:
            response += f"\n💡 *Tip: Use 'list_documents' tool to see details of these {count} documents*"
        
        logger.info(f"Count result: {count} documents")
        return response
        
    except Exception as e:
        logger.error(f"Error counting documents: {str(e)}")
        return f"Error counting documents: {str(e)}"


def count_documents_wrapper(args: str, user_role: Optional[str] = None, user_institution_id: Optional[int] = None) -> str:
    """
    Wrapper function for count_documents tool to be used by the agent.
    Parses string arguments and calls count_documents.
    
    Args:
        args: String representation of arguments (e.g., "{'language': 'Hindi'}")
        user_role: User's role for access control
        user_institution_id: User's institution ID
    
    Returns:
        Formatted count result
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
        
        # Call count_documents
        return count_documents(
            language=language,
            document_type=document_type,
            year_from=year_from,
            year_to=year_to,
            user_role=user_role,
            user_institution_id=user_institution_id
        )
        
    except Exception as e:
        logger.error(f"Error in count_documents_wrapper: {str(e)}")
        return f"Error parsing arguments: {str(e)}"
