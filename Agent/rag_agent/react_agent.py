"""ReAct agent with LangGraph for policy Q&A"""
import logging
from typing import TypedDict, Annotated, Sequence
from pathlib import Path
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub

from Agent.tools.search_tools import (
    search_documents,
    search_specific_document,
    get_document_metadata
)
from Agent.tools.analysis_tools import compare_policies, summarize_document
from Agent.tools.web_search_tool import web_search

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
        
        # Define tools
        self.tools = [
            Tool(
                name="search_documents",
                func=search_documents,
                description="Search across all policy documents using semantic and keyword search. Use this for general questions about policies."
            ),
            Tool(
                name="search_specific_document",
                func=lambda args: search_specific_document(**eval(args)),
                description="Search within a specific document by ID. Use when you know which document to search. Input: {'document_id': int, 'query': str}"
            ),
            Tool(
                name="compare_policies",
                func=lambda args: compare_policies(**eval(args)),
                description="Compare multiple documents on a specific aspect. Input: {'document_ids': [int, int], 'aspect': str}"
            ),
            Tool(
                name="get_document_metadata",
                func=get_document_metadata,
                description="Get metadata about documents. Pass document_id or leave empty for all documents."
            ),
            Tool(
                name="summarize_document",
                func=lambda args: summarize_document(**eval(args)),
                description="Generate a summary of a document. Input: {'document_id': int, 'focus': str}"
            ),
            Tool(
                name="web_search",
                func=web_search,
                description="Search the web for additional information. Use when document search doesn't provide enough context."
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
            max_iterations=5,
            return_intermediate_steps=True  # Enable intermediate steps for citations
        )
        
        # Setup LangGraph with memory
        self.memory = MemorySaver()
        self.graph = self._create_graph()
        
        logger.info("PolicyRAGAgent initialized successfully")
    
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
            result = self.agent_executor.invoke({"input": state["query"]})
            
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
                    
                    # Extract document IDs and sources from tool outputs
                    observation_str = str(observation)
                    if "Document ID:" in observation_str:
                        lines = observation_str.split("\n")
                        for i, line in enumerate(lines):
                            if "Document ID:" in line:
                                doc_id = line.split("Document ID:")[1].strip()
                                source = "Unknown"
                                # Look for source filename
                                for j in range(max(0, i-3), min(len(lines), i+3)):
                                    if "Source:" in lines[j]:
                                        source = lines[j].split("Source:")[1].strip()
                                        break
                                
                                citation = {
                                    "document_id": doc_id,
                                    "source": source,
                                    "tool": action.tool
                                }
                                # Avoid duplicates
                                if not any(c["document_id"] == doc_id and c["source"] == source for c in citations):
                                    citations.append(citation)
                                    logger.info(f"Added citation: Doc {doc_id} - {source}")
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
    
    def query(self, question: str, thread_id: str = "default") -> dict:
        """
        Query the agent
        
        Args:
            question: User question
            thread_id: Thread ID for conversation memory
        
        Returns:
            Response dict with answer, citations, and confidence
        """
        logger.info(f"Query received: '{question}'")
        
        initial_state = {
            "messages": [{"role": "user", "content": question}],
            "query": question,
            "response": "",
            "citations": [],
            "confidence": 0.0
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            result = self.graph.invoke(initial_state, config)
            
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
