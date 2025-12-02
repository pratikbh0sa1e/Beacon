"""ReAct agent with LangGraph for policy Q&A"""
import logging
from typing import TypedDict, Annotated, Sequence, AsyncGenerator
from pathlib import Path
import operator
import time
import asyncio

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub
from langchain.callbacks.base import BaseCallbackHandler

from Agent.tools.lazy_search_tools import (
    search_documents_lazy,
    search_specific_document_lazy
)
from Agent.tools.search_tools import get_document_metadata
from Agent.tools.analysis_tools import compare_policies, summarize_document

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
    response: str
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
        
        # Initialize Gemini Flash
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=google_api_key,
            temperature=temperature,
            streaming=True,
            convert_system_message_to_human=True
        )
        
        # User context for role-based access (will be set per query)
        self.current_user_role = None
        self.current_user_institution_id = None
        
        # Define tools (using lazy search with role-based access)
        self.tools = [
            Tool(
                name="search_documents",
                func=self._search_documents_wrapper,
                description=(
                    "Search across ALL documents to find information. Use this as your PRIMARY and FIRST tool for ANY question. "
                    "Input: just the search query as a string (e.g., 'Pranav Waikar' or 'admission policy'). "
                    "Returns: Top 5 relevant results with document IDs, sources, and approval status. "
                    "IMPORTANT: This tool usually provides enough information to answer the question - check results carefully before using other tools."
                )
            ),
            Tool(
                name="search_specific_document",
                func=self._search_specific_document_wrapper,
                description=(
                    "Search WITHIN a specific document when you already know the document ID from a previous search. "
                    "Input: {'document_id': int, 'query': str} "
                    "Only use this if search_documents found a relevant document but you need MORE details from that specific document."
                )
            ),
            Tool(
                name="compare_policies",
                func=lambda args: compare_policies(**eval(args)),
                description=(
                    "Compare TWO OR MORE documents on a specific aspect. "
                    "Input: {'document_ids': [int, int], 'aspect': str} "
                    "Only use when user explicitly asks to COMPARE multiple documents."
                )
            ),
            Tool(
                name="get_document_metadata",
                func=lambda args="": get_document_metadata() if not args or str(args).strip() in ["{}", "", "None"] else get_document_metadata(int(args)),
                description=(
                    "Get a LIST of all available documents in the system. "
                    "Input: leave empty or pass nothing. "
                    "Use this ONLY when user asks 'what documents do you have' or 'list all documents'. "
                    "DO NOT use this for searching - use search_documents instead."
                )
            ),
            Tool(
                name="summarize_document",
                func=lambda args: summarize_document(**eval(args)),
                description=(
                    "Generate a SUMMARY of an entire document. "
                    "Input: {'document_id': int, 'focus': str} "
                    "Only use when user explicitly asks for a summary or overview of a document."
                )
            )
        ]
        
        # Create ReAct agent
        prompt = hub.pull("hwchase17/react")
        self.agent = create_react_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15,  # Increased from 5 to handle complex queries
            max_execution_time=20,  # 20 second timeout for safety
            return_intermediate_steps=True  # Enable intermediate steps for citations
        )
        
        # Setup LangGraph with memory
        self.memory = MemorySaver()
        self.graph = self._create_graph()
        
        logger.info("PolicyRAGAgent initialized successfully")
    
    def _search_documents_wrapper(self, query: str) -> str:
        """Wrapper to inject user context into search_documents_lazy"""
        return search_documents_lazy(
            query=query,
            user_role=self.current_user_role,
            user_institution_id=self.current_user_institution_id
        )
    
    def _search_specific_document_wrapper(self, args: str) -> str:
        """Wrapper to inject user context into search_specific_document_lazy"""
        parsed_args = eval(args)
        return search_specific_document_lazy(
            document_id=parsed_args['document_id'],
            query=parsed_args['query'],
            user_role=self.current_user_role,
            user_institution_id=self.current_user_institution_id
        )
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("process_query", self._process_query)
        workflow.add_node("generate_response", self._generate_response)
        
        # Add edges
        workflow.set_entry_point("process_query")
        workflow.add_edge("process_query", "generate_response")
        workflow.add_edge("generate_response", END)
        
        # Compile with memory
        return workflow.compile(checkpointer=self.memory)
    
    def _process_query(self, state: AgentState) -> AgentState:
        """Process the user query using ReAct agent"""
        logger.info(f"Processing query: {state['query']}")
        
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
    
    def query(self, question: str, thread_id: str = "default", user_role: str = None, user_institution_id: int = None) -> dict:
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
        logger.info(f"Query received: '{question}' (role={user_role}, institution={user_institution_id})")
        
        # Set user context for this query
        self.current_user_role = user_role
        self.current_user_institution_id = user_institution_id
        
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
                    "response": "",
                    "citations": [],
                    "confidence": 0.0
                }
            else:
                # First message in conversation
                new_state = {
                    "messages": [{"role": "user", "content": question}],
                    "query": question,
                    "response": "",
                    "citations": [],
                    "confidence": 0.0
                }
            
            result = self.graph.invoke(new_state, config)
            
            return {
                "answer": result["response"],
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
