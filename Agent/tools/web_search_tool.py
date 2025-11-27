"""Web search tool using DuckDuckGo"""
import logging
from typing import List, Dict
from pathlib import Path
from duckduckgo_search import DDGS

# Setup logging
log_dir = Path("Agent/agent_logs")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "tools.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
    
    Returns:
        Formatted search results
    """
    logger.info(f"web_search called with query: '{query}'")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return "No web results found."
        
        # Format results
        formatted = f"Web search results for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            formatted += f"**Result {i}**\n"
            formatted += f"Title: {result.get('title', 'N/A')}\n"
            formatted += f"URL: {result.get('href', 'N/A')}\n"
            formatted += f"Snippet: {result.get('body', 'N/A')[:200]}...\n\n"
        
        logger.info(f"Returned {len(results)} web results")
        return formatted
        
    except Exception as e:
        logger.error(f"Error in web_search: {str(e)}")
        return f"Error performing web search: {str(e)}"
