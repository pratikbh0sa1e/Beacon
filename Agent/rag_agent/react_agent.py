"""ReAct agent with LangGraph for policy Q&A"""
import logging
from typing import TypedDict, Annotated, Sequence, AsyncGenerator, List
from pathlib import Path
import operator
import time
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool, StructuredTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.callbacks.base import BaseCallbackHandler
from pydantic import BaseModel, Field
from typing import Optional

from Agent.tools.lazy_search_tools import (
    search_documents_lazy,
    search_specific_document_lazy
)
from Agent.rag_enhanced.family_aware_retriever import enhanced_search_documents

def search_documents_with_metadata_fallback(query: str, top_k: int = 5, user_role: Optional[str] = None, user_institution_id: Optional[int] = None) -> str:
    """Enhanced search with intelligent metadata fallback"""
    logger.info(f"Enhanced search with metadata fallback for query: '{query}'")
    
    try:
        # Step 1: Determine if this query should prioritize metadata search
        query_lower = query.lower()
        
        # Keywords that indicate specific document/program names (should use metadata first)
        metadata_priority_keywords = [
            'indo-norwegian', 'incp2', 'unesco', 'cooperation programme', 
            'call for applications', 'public notice', 'scholarship programme',
            'stipendium hungaricum', 'michel batisse', 'hamdan prize'
        ]
        
        should_prioritize_metadata = any(keyword in query_lower for keyword in metadata_priority_keywords)
        
        if should_prioritize_metadata:
            logger.info("Query contains specific program/document names, prioritizing metadata search")
            
            # Try metadata search first for specific queries
            metadata_result = _perform_metadata_search(query, top_k, user_role, user_institution_id)
            if metadata_result and "No documents found" not in metadata_result:
                logger.info("Metadata search successful for priority query")
                return metadata_result
        
        # Step 2: Try enhanced vector search
        vector_results = enhanced_search_documents(
            query=query,
            top_k=top_k,
            user_role=user_role,
            user_institution_id=user_institution_id,
            prefer_latest=True
        )
        
        # Step 3: Check if vector search found truly relevant results
        if "No relevant documents found" not in vector_results and len(vector_results.strip()) > 50:
            # Strict relevance check for vector results
            query_words = [word.lower() for word in query.split() if len(word) > 3]
            vector_lower = vector_results.lower()
            
            # Check for exact matches of important query terms
            exact_matches = sum(1 for word in query_words if word in vector_lower)
            
            # For specific program names, require high precision
            if should_prioritize_metadata:
                required_match_ratio = 0.8  # 80% of words must match
            else:
                required_match_ratio = 0.4  # 40% for general queries
            
            if len(query_words) > 0 and (exact_matches / len(query_words)) >= required_match_ratio:
                logger.info(f"Vector search successful ({exact_matches}/{len(query_words)} words matched)")
                return vector_results
            else:
                logger.info(f"Vector search results not relevant ({exact_matches}/{len(query_words)} words matched), trying metadata search...")
        else:
            logger.info("Vector search failed, trying metadata-based search...")
        
        # Step 4: Fallback to metadata search
        metadata_result = _perform_metadata_search(query, top_k, user_role, user_institution_id)
        if metadata_result:
            return metadata_result
        
        # Step 5: Last resort - return vector results even if not perfect
        if "No relevant documents found" not in vector_results:
            logger.info("Returning vector results as last resort")
            return vector_results + "\n\n(Note: Results may not be perfectly relevant. Try different keywords if needed.)"
        
        return f"No documents found matching '{query}'. Try using different keywords or check the document title exactly."
        
    except Exception as e:
        logger.error(f"Error in enhanced search with metadata fallback: {str(e)}")
        return f"Error searching documents: {str(e)}"


def _perform_metadata_search(query: str, top_k: int, user_role: Optional[str], user_institution_id: Optional[int]) -> str:
    """Perform metadata-based search with BM25 ranking"""
    from backend.database import SessionLocal, DocumentMetadata, Document
    from sqlalchemy import or_, and_
    from rank_bm25 import BM25Okapi
    
    db = SessionLocal()
    
    try:
        query_words = query.lower().split()
        
        # Build query for metadata search
        metadata_query = db.query(Document, DocumentMetadata).outerjoin(
            DocumentMetadata, Document.id == DocumentMetadata.document_id
        ).filter(
            Document.approval_status.in_(['approved', 'pending'])
        )
        
        # Apply role-based filters
        from backend.constants.roles import DEVELOPER, MINISTRY_ADMIN, UNIVERSITY_ADMIN
        if user_role == DEVELOPER:
            pass  # Can access all
        elif user_role == MINISTRY_ADMIN:
            metadata_query = metadata_query.filter(
                Document.visibility_level.in_(['public', 'restricted', 'institution_only'])
            )
        elif user_role == UNIVERSITY_ADMIN:
            metadata_query = metadata_query.filter(
                or_(
                    Document.visibility_level == 'public',
                    and_(
                        Document.visibility_level.in_(['institution_only', 'restricted']),
                        Document.institution_id == user_institution_id
                    )
                )
            )
        else:
            filters = [Document.visibility_level == 'public']
            if user_institution_id:
                filters.append(
                    and_(
                        Document.visibility_level == 'institution_only',
                        Document.institution_id == user_institution_id
                    )
                )
            metadata_query = metadata_query.filter(or_(*filters))
        
        # Search in metadata fields with fuzzy matching
        search_conditions = []
        for word in query_words:
            if len(word) > 2:  # Skip very short words
                word_conditions = [
                    DocumentMetadata.title.ilike(f'%{word}%'),
                    DocumentMetadata.summary.ilike(f'%{word}%'),
                    DocumentMetadata.bm25_keywords.ilike(f'%{word}%'),
                    Document.filename.ilike(f'%{word}%')
                ]
                search_conditions.extend(word_conditions)
        
        if search_conditions:
            metadata_query = metadata_query.filter(or_(*search_conditions))
        
        metadata_results = metadata_query.all()
        
        if not metadata_results:
            return None
        
        # Rank results using BM25 on metadata
        documents = []
        corpus = []
        
        for doc, meta in metadata_results:
            doc_dict = {
                "doc": doc,
                "meta": meta,
                "id": doc.id,
                "title": meta.title if meta and meta.title else doc.filename,
                "filename": doc.filename
            }
            documents.append(doc_dict)
            
            # Create searchable text from metadata (handle None values)
            title = meta.title if meta and meta.title else ""
            summary = meta.summary if meta and meta.summary else ""
            keywords = meta.bm25_keywords if meta and meta.bm25_keywords else ""
            filename = doc.filename if doc.filename else ""
            
            searchable_text = f"{title} {summary} {keywords} {filename}".lower()
            corpus.append(searchable_text.split())
        
        # Rank using BM25
        bm25 = BM25Okapi(corpus)
        query_tokens = query.lower().split()
        bm25_scores = bm25.get_scores(query_tokens)
        
        # Sort by relevance score
        ranked_indices = bm25_scores.argsort()[::-1]  # Descending order
        top_results = [documents[i] for i in ranked_indices[:top_k]]
        
        # Format results
        formatted = f"Found {len(top_results)} relevant results (metadata search):\n\n"
        
        for i, doc_dict in enumerate(top_results, 1):
            doc = doc_dict['doc']
            meta = doc_dict['meta']
            score = bm25_scores[ranked_indices[i-1]]
            
            approval_badge = "Approved" if doc.approval_status == 'approved' else "Pending Approval"
            
            formatted += f"**Result {i}** (Relevance Score: {score:.2f}) [{approval_badge}]\n"
            formatted += f"Source: {doc.filename}\n"
            formatted += f"Document ID: {doc.id}\n"
            formatted += f"Document: {meta.title if meta and meta.title else doc.filename}\n"
            formatted += f"Approval Status: {doc.approval_status}\n"
            formatted += f"Visibility: {doc.visibility_level}\n"
            
            if meta and meta.summary:
                formatted += f"Summary: {meta.summary[:300]}...\n"
            
            formatted += "\n"
        
        logger.info(f"Metadata search returned {len(top_results)} results")
        return formatted
        
    finally:
        db.close()
from Agent.tools.search_tools import get_document_metadata
from Agent.tools.analysis_tools import compare_policies, summarize_document
from Agent.tools.count_tools import count_documents_wrapper
from Agent.tools.list_tools import list_documents_wrapper
from Agent.intent.classifier import classify_intent
from Agent.formatting.response_formatter import format_response

# Setup logging
log_dir = Path("Agent/agent_logs")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming LLM tokens"""
    
    def __init__(self):
        self.tokens = []
        self.token_queue = asyncio.Queue()
        
    def on_llm_new_token(self, token: str, **kwargs):
        """Called when LLM generates a new token"""
        self.tokens.append(token)
        # Put token in queue for async consumption
        try:
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(self.token_queue.put_nowait, token)
        except:
            pass
    
    async def get_token(self):
        """Get next token from queue"""
        return await self.token_queue.get()
    
    def has_tokens(self):
        """Check if there are tokens in queue"""
        return not self.token_queue.empty()


class AgentState(TypedDict):
    """State for the agent"""
    messages: Annotated[Sequence[dict], operator.add]
    query: str
    intent: str  # Query intent: "comparison" | "count" | "list" | "qa"
    intent_confidence: float  # Classification confidence
    extracted_params: dict  # Extracted parameters (language, type, etc.)
    response: str
    format_type: str  # Response format type
    structured_data: dict  # Format-specific structured data
    citations: list
    confidence: float


class PolicyRAGAgent:
    """ReAct agent for policy document Q&A"""
    
    def __init__(self, google_api_key: str, temperature: float = 0.1):
        """
        Initialize the RAG agent
        
        Args:
            google_api_key: Google API key for Gemini
            temperature: LLM temperature (0.1 for precise answers)
        """
        logger.info("Initializing PolicyRAGAgent")
        
        # Initialize Gemini Flash with tool calling support
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=google_api_key,
            temperature=temperature,
            streaming=False,  # Disable streaming for tool calling reliability
            convert_system_message_to_human=False  # Keep system messages for better tool calling
        )
        
        # User context for role-based access (will be set per query)
        self.current_user_role = None
        self.current_user_institution_id = None
        
        # Define input schemas for structured tools
        class CountDocumentsInput(BaseModel):
            language: Optional[str] = Field(None, description="Filter by language (e.g., 'Hindi', 'English')")
            document_type: Optional[str] = Field(None, description="Filter by document type (e.g., 'Policy', 'Guideline')")
            year_from: Optional[str] = Field(None, description="Filter by start year (e.g., '2018')")
            year_to: Optional[str] = Field(None, description="Filter by end year (e.g., '2021')")
        
        class ListDocumentsInput(BaseModel):
            language: Optional[str] = Field(None, description="Filter by language (e.g., 'Hindi', 'English')")
            document_type: Optional[str] = Field(None, description="Filter by document type (e.g., 'Policy', 'Guideline')")
            year_from: Optional[str] = Field(None, description="Filter by start year (e.g., '2018')")
            year_to: Optional[str] = Field(None, description="Filter by end year (e.g., '2021')")
            limit: Optional[int] = Field(10, description="Maximum number of documents to return (default: 10, max: 50)")
        
        class ComparePoliciesInput(BaseModel):
            document_ids: List[int] = Field(..., description="List of document IDs to compare (e.g., [123, 124])")
            aspect: str = Field(..., description="The aspect to compare (e.g., 'eligibility criteria', 'purpose', 'requirements')")
        
        class SummarizeDocumentInput(BaseModel):
            document_id: int = Field(..., description="The document ID to summarize")
            focus: str = Field("general", description="Focus area for summary (e.g., 'general', 'key points', 'requirements')")
        
        class SearchSpecificDocumentInput(BaseModel):
            document_id: int = Field(..., description="The document ID to search within")
            query: str = Field(..., description="The search query to find relevant content in the document")
        
        # Define tools (using lazy search with role-based access)
        self.tools = [
            StructuredTool.from_function(
                func=self._search_documents_wrapper,
                name="search_documents",
                description=(
                    "Search across ALL documents to find information by content using vector similarity. "
                    "Input: search query as a plain string like 'eligibility criteria' or 'scholarship policy'. "
                    "Returns: Top 5 relevant results with document IDs. "
                    "IMPORTANT: If this returns no results or irrelevant results, you MUST immediately try list_documents "
                    "to browse by title/type as a fallback. Never stop after just one failed search."
                )
            ),
            StructuredTool.from_function(
                func=self._search_specific_document_structured,
                name="search_specific_document",
                description=(
                    "Search WITHIN a specific document to extract relevant content. Use this when: "
                    "1) You have a document ID from list_documents and need to answer questions about its content, "
                    "2) search_documents found a document but you need MORE specific details, "
                    "3) User asks about a specific document's content. "
                    "This tool will automatically embed the document if needed and return relevant chunks."
                ),
                args_schema=SearchSpecificDocumentInput
            ),
            StructuredTool.from_function(
                func=self._count_documents_structured,
                name="count_documents",
                description="Count documents matching specific criteria. Use when user asks 'how many' or 'count' documents.",
                args_schema=CountDocumentsInput
            ),
            StructuredTool.from_function(
                func=self._list_documents_structured,
                name="list_documents",
                description=(
                    "List documents matching specific criteria by browsing database directly. "
                    "Use when: 1) User asks to 'show', 'list', or 'fetch' documents, "
                    "2) search_documents returns no results (FALLBACK), "
                    "3) You need to find documents by title keywords or type. "
                    "This is more reliable than search_documents for finding documents by metadata."
                ),
                args_schema=ListDocumentsInput
            ),
            StructuredTool.from_function(
                func=self._compare_policies_structured,
                name="compare_policies",
                description=(
                    "Compare TWO OR MORE documents on a specific aspect. "
                    "IMPORTANT: You MUST have document IDs before using this tool. "
                    "If user asks to compare documents by topic (e.g., 'compare scholarship documents'), "
                    "you MUST first use 'search_documents' or 'list_documents' to find the document IDs, "
                    "then use this tool with those IDs. "
                    "Example workflow: 1) search_documents('scholarship') to get IDs, 2) compare_policies with those IDs."
                ),
                args_schema=ComparePoliciesInput
            ),
            StructuredTool.from_function(
                func=self._get_document_metadata_wrapper,
                name="get_document_metadata",
                description=(
                    "Get a LIST of all available documents in the system. "
                    "Use this ONLY when user asks 'what documents do you have' or 'list all documents'. "
                    "DO NOT use this for searching - use search_documents or list_documents instead."
                )
            ),
            StructuredTool.from_function(
                func=self._summarize_document_structured,
                name="summarize_document",
                description=(
                    "Generate a SUMMARY of an entire document. "
                    "Only use when user explicitly asks for a summary or overview of a document."
                ),
                args_schema=SummarizeDocumentInput
            )
        ]
        
        # Create tool-calling agent with simplified, action-oriented prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a proactive policy document assistant. You have tools to search, list, count, and compare documents.

CRITICAL RULES:
1. ALWAYS use your tools to answer questions - never ask the user if they want you to search
2. If search_documents returns no results or irrelevant results, IMMEDIATELY use list_documents as fallback
3. After finding documents with list_documents, use search_specific_document to get detailed content
4. Try multiple search strategies automatically before giving up
5. Present results directly - don't ask permission to search

SEARCH STRATEGY:
- For specific queries: try search_documents with the main keywords
- If no results: try search_documents with alternative keywords
- If still no results: use list_documents to browse by document type or title keywords
- After list_documents finds documents: use search_specific_document to extract relevant content
- Example: "scholarship guidelines" → search "scholarship" → if no results → list_documents → search_specific_document

TOOL USAGE:
- search_documents: For content-based search across all documents (first attempt)
- list_documents: For browsing by title/type (fallback when search fails) - returns document IDs
- search_specific_document: For extracting content from a specific document ID (use after list_documents)
- count_documents: When user asks "how many"
- compare_policies: After finding document IDs via search or list
- summarize_document: For generating summaries of specific documents

IMPORTANT: list_documents only shows metadata (title, type, etc.). To answer questions about document content,
you MUST use search_specific_document with the document ID to retrieve the actual content.

Be proactive and exhaustive in your search before concluding documents don't exist."""),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_execution_time=60,  # Increased timeout for embedding operations
            return_intermediate_steps=True
        )
        
        # Setup LangGraph with memory
        self.memory = MemorySaver()
        self.graph = self._create_graph()
        
        logger.info("PolicyRAGAgent initialized successfully")
    
    def _search_documents_wrapper(self, query: str) -> str:
        """Wrapper to inject user context into enhanced search with metadata fallback"""
        return search_documents_with_metadata_fallback(
            query=query,
            user_role=self.current_user_role,
            user_institution_id=self.current_user_institution_id
        )
    
    def _get_document_metadata_wrapper(self) -> str:
        """Wrapper for get_document_metadata - returns list of all documents"""
        return get_document_metadata()
    
    def _search_specific_document_structured(
        self,
        document_id: int,
        query: str
    ) -> str:
        """Structured wrapper for search_specific_document with proper argument handling"""
        return search_specific_document_lazy(
            document_id=int(document_id),
            query=query,
            user_role=self.current_user_role,
            user_institution_id=self.current_user_institution_id
        )
    
    def _count_documents_structured(
        self,
        language: Optional[str] = None,
        document_type: Optional[str] = None,
        year_from: Optional[str] = None,
        year_to: Optional[str] = None
    ) -> str:
        """Structured wrapper for count_documents with proper argument handling"""
        from Agent.tools.count_tools import count_documents
        return count_documents(
            language=language,
            document_type=document_type,
            year_from=year_from,
            year_to=year_to,
            user_role=self.current_user_role,
            user_institution_id=self.current_user_institution_id
        )
    
    def _list_documents_structured(
        self,
        language: Optional[str] = None,
        document_type: Optional[str] = None,
        year_from: Optional[str] = None,
        year_to: Optional[str] = None,
        limit: int = 10
    ) -> str:
        """Structured wrapper for list_documents with proper argument handling"""
        from Agent.tools.list_tools import list_documents
        return list_documents(
            language=language,
            document_type=document_type,
            year_from=year_from,
            year_to=year_to,
            limit=limit,
            user_role=self.current_user_role,
            user_institution_id=self.current_user_institution_id
        )
    
    def _compare_policies_structured(
        self,
        document_ids: list,
        aspect: str
    ) -> str:
        """Structured wrapper for compare_policies with proper argument handling"""
        # Convert float IDs to integers (LLM sometimes returns floats)
        document_ids = [int(doc_id) for doc_id in document_ids]
        return compare_policies(document_ids=document_ids, aspect=aspect)
    
    def _summarize_document_structured(
        self,
        document_id: int,
        focus: str = "general"
    ) -> str:
        """Structured wrapper for summarize_document with proper argument handling"""
        return summarize_document(document_id=int(document_id), focus=focus)
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("process_query", self._process_query)
        workflow.add_node("format_response", self._format_response)
        workflow.add_node("generate_response", self._generate_response)
        
        # Add edges
        workflow.set_entry_point("classify_intent")
        workflow.add_edge("classify_intent", "process_query")
        workflow.add_edge("process_query", "format_response")
        workflow.add_edge("format_response", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Compile with memory
        return workflow.compile(checkpointer=self.memory)
    
    def _classify_intent(self, state: AgentState) -> AgentState:
        """Classify the intent of the user query"""
        try:
            logger.info(f"Classifying intent for query: {state['query'][:50]}...")
        except (UnicodeEncodeError, UnicodeDecodeError):
            logger.info(f"Classifying intent for query: [Unicode query - {len(state['query'])} chars]")
        
        try:
            # Classify the query intent
            result = classify_intent(state['query'])
            
            state['intent'] = result.intent
            state['intent_confidence'] = result.confidence
            state['extracted_params'] = result.extracted_params
            
            logger.info(f"Intent classified as '{result.intent}' with confidence {result.confidence:.2f}")
            if result.extracted_params:
                logger.info(f"Extracted parameters: {result.extracted_params}")
            
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            # Default to Q&A on error
            state['intent'] = 'qa'
            state['intent_confidence'] = 0.5
            state['extracted_params'] = {}
        
        return state
    
    def _process_query(self, state: AgentState) -> AgentState:
        """Process the user query using ReAct agent"""
        # Safe Unicode logging
        try:
            logger.info(f"Processing query: {state['query']}")
        except (UnicodeEncodeError, UnicodeDecodeError):
            logger.info(f"Processing query: [Unicode query - {len(state['query'])} chars]")
        
        try:
            # Build context from previous messages for conversation continuity
            chat_history = state.get("messages", [])
            
            # Format chat history for context (last 5 messages to avoid token limits)
            context_messages = chat_history[-10:] if len(chat_history) > 10 else chat_history
            
            # Build input with conversation context
            if len(context_messages) > 1:  # More than just current message
                history_text = "\n".join([
                    f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                    for msg in context_messages[:-1]  # Exclude current message
                ])
                input_with_context = f"Previous conversation:\n{history_text}\n\nCurrent question: {state['query']}"
            else:
                input_with_context = state["query"]
            
            result = self.agent_executor.invoke({"input": input_with_context})
            
            # Check if agent hit iteration limit
            if "intermediate_steps" in result and len(result["intermediate_steps"]) >= 15:
                logger.warning(f"⚠️ Agent hit iteration limit (15) for query: {state['query'][:50]}...")
            
            state["response"] = result.get("output", "No response generated")
            state["messages"].append({
                "role": "assistant",
                "content": state["response"]
            })
            
            # Extract citations from intermediate steps
            citations = []
            if "intermediate_steps" in result:
                logger.info(f"Found {len(result['intermediate_steps'])} intermediate steps")
                for action, observation in result["intermediate_steps"]:
                    logger.debug(f"Tool: {action.tool}, Observation length: {len(str(observation))}")
                    
                    # Extract document IDs, sources, and approval status from tool outputs
                    observation_str = str(observation)
                    if "Document ID:" in observation_str:
                        lines = observation_str.split("\n")
                        for i, line in enumerate(lines):
                            if "Document ID:" in line:
                                doc_id = line.split("Document ID:")[1].strip()
                                source = "Unknown"
                                approval_status = "unknown"
                                
                                # Look for source filename and approval status in nearby lines
                                for j in range(max(0, i-5), min(len(lines), i+5)):
                                    if "Source:" in lines[j]:
                                        source = lines[j].split("Source:")[1].strip()
                                    if "Approval Status:" in lines[j]:
                                        approval_status = lines[j].split("Approval Status:")[1].strip()
                                
                                citation = {
                                    "document_id": doc_id,
                                    "source": source,
                                    "approval_status": approval_status,
                                    "tool": action.tool
                                }
                                # Avoid duplicates
                                if not any(c["document_id"] == doc_id and c["source"] == source for c in citations):
                                    citations.append(citation)
                                    logger.info(f"Added citation: Doc {doc_id} - {source} (Status: {approval_status})")
            else:
                logger.warning("No intermediate_steps found in result")
            
            state["citations"] = citations
            logger.info(f"Total citations extracted: {len(citations)}")
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            state["response"] = f"Error: {str(e)}"
            state["citations"] = []
        
        return state
    
    def _format_response(self, state: AgentState) -> AgentState:
        """Format the response based on intent"""
        logger.info(f"Formatting response for intent: {state.get('intent', 'qa')}")
        
        try:
            # Get tool outputs from intermediate steps (if available)
            tool_outputs = []
            # Note: tool_outputs would need to be extracted from agent_executor results
            # For now, we'll work with the response text
            
            # Format the response
            formatted = format_response(
                intent=state.get('intent', 'qa'),
                response_text=state['response'],
                tool_outputs=tool_outputs,
                citations=state.get('citations', [])
            )
            
            # Update state with formatted data
            state['format_type'] = formatted['format']
            state['structured_data'] = formatted.get('data')
            
            # Update response if formatter modified it
            if formatted.get('answer'):
                state['response'] = formatted['answer']
            
            logger.info(f"Response formatted as: {state['format_type']}")
            
        except Exception as e:
            logger.error(f"Error in format_response node: {str(e)}")
            # Fallback to text format on error
            state['format_type'] = 'text'
            state['structured_data'] = None
        
        return state
    
    def _generate_response(self, state: AgentState) -> AgentState:
        """Format the final response with citations"""
        logger.info("Generating final response")
        
        # Calculate confidence based on number of citations
        num_citations = len(state.get("citations", []))
        if num_citations >= 3:
            state["confidence"] = 0.95
        elif num_citations >= 2:
            state["confidence"] = 0.90
        elif num_citations >= 1:
            state["confidence"] = 0.85
        else:
            state["confidence"] = 0.70
        
        return state
    
    def query(self, question: str, thread_id: str = None, user_role: str = None, user_institution_id: int = None) -> dict:
        """
        Query the agent with user context for role-based access
        
        Args:
            question: User question
            thread_id: Thread ID for conversation memory
            user_role: User's role for access control
            user_institution_id: User's institution ID
        
        Returns:
            Response dict with answer, citations, and confidence
        """
        # Safe Unicode logging
        try:
            logger.info(f"Query received: '{question}' (role={user_role}, institution={user_institution_id})")
        except (UnicodeEncodeError, UnicodeDecodeError):
            logger.info(f"Query received: [Unicode query - {len(question)} chars] (role={user_role}, institution={user_institution_id})")
        
        # Set user context for this query
        self.current_user_role = user_role
        self.current_user_institution_id = user_institution_id
        
        # Use unique thread_id per query to avoid Gemini function calling history issues
        # TODO: Re-enable conversation memory once LangChain fixes Gemini function calling history
        import uuid
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            # Get current state from memory (if exists)
            current_state = None
            try:
                # Try to get the last state from checkpointer using get_tuple
                checkpoint_tuple = self.memory.get_tuple(config)
                if checkpoint_tuple and checkpoint_tuple.checkpoint:
                    # Extract the state values from the checkpoint
                    current_state = checkpoint_tuple.checkpoint.get("channel_values", {})
                    if current_state and "messages" in current_state:
                        logger.info(f"Loaded previous state with {len(current_state.get('messages', []))} messages")
            except Exception as e:
                logger.info(f"No previous state found, starting fresh: {e}")
            
            # Build new state by appending to existing messages
            if current_state and "messages" in current_state:
                # Append new user message to existing conversation
                new_state = {
                    "messages": current_state["messages"] + [{"role": "user", "content": question}],
                    "query": question,
                    "intent": "",
                    "intent_confidence": 0.0,
                    "extracted_params": {},
                    "response": "",
                    "format_type": "text",
                    "structured_data": None,
                    "citations": [],
                    "confidence": 0.0
                }
            else:
                # First message in conversation
                new_state = {
                    "messages": [{"role": "user", "content": question}],
                    "query": question,
                    "intent": "",
                    "intent_confidence": 0.0,
                    "extracted_params": {},
                    "response": "",
                    "format_type": "text",
                    "structured_data": None,
                    "citations": [],
                    "confidence": 0.0
                }
            
            result = self.graph.invoke(new_state, config)
            
            return {
                "answer": result["response"],
                "format": result.get("format_type", "text"),
                "data": result.get("structured_data"),
                "citations": result["citations"],
                "confidence": result["confidence"],
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in query: {str(e)}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "citations": [],
                "confidence": 0.0,
                "status": "error"
            }
    
    async def query_stream(self, question: str, thread_id: str = "default", user_role: str = None, user_institution_id: int = None) -> AsyncGenerator[dict, None]:
        """
        Query the agent with streaming response
        
        Args:
            question: User question
            thread_id: Thread ID for conversation memory
        
        Yields:
            Stream events:
            - {"type": "content", "token": "...", "timestamp": ...}
            - {"type": "citation", "citation": {...}, "timestamp": ...}
            - {"type": "metadata", "confidence": 0.95, "status": "success", "timestamp": ...}
        
        Note: This uses the graph with MemorySaver checkpointer to maintain conversation history
        """
        logger.info(f"Streaming query received: '{question}'")
        
        try:
            # Use the query method which properly uses the graph with memory
            # The graph.invoke() with thread_id config enables conversation memory via MemorySaver
            result = await asyncio.to_thread(self.query, question, thread_id, user_role, user_institution_id)
            
            # Get the answer
            answer = result.get("answer", "")
            citations = result.get("citations", [])
            confidence = result.get("confidence", 0.0)
            
            # Stream the answer word by word
            words = answer.split()
            for i, word in enumerate(words):
                # Add space except for first word
                token = word if i == 0 else f" {word}"
                
                yield {
                    "type": "content",
                    "token": token,
                    "timestamp": time.time()
                }
                
                # Small delay to simulate streaming (adjust for faster/slower streaming)
                await asyncio.sleep(0.05)
            
            # Send citations
            for citation in citations:
                yield {
                    "type": "citation",
                    "citation": citation,
                    "timestamp": time.time()
                }
            
            # Send final metadata
            yield {
                "type": "metadata",
                "confidence": confidence,
                "format": result.get("format", "text"),
                "data": result.get("data"),
                "status": result.get("status", "success"),
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error in streaming query: {str(e)}")
            yield {
                "type": "error",
                "message": str(e),
                "recoverable": False,
                "timestamp": time.time()
            }
