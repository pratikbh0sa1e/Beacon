# Agent/graph/graph_setup.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Annotated
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from typing_extensions import TypedDict


TOOLS = [GET_RESUME, GET_JD, WEB_SEARCH, OPTIMIZE_RESUME]


def _agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    llm = setup_llm()
    bound = llm.bind_tools(TOOLS)

    system = SystemMessage(content=_safe_system_text(state))
    messages = _ensure_messages(state.get("messages", []))

    # Ensure at least one HumanMessage (helps Gemini)
    has_human = any(isinstance(m, HumanMessage) and (m.content or "").strip() for m in messages)
    if not has_human:
        messages = [HumanMessage(content=_synthesize_human_prompt(state))]

    ai = bound.invoke([system] + messages)
    if not isinstance(ai, AIMessage):
        ai = AIMessage(content=str(ai))
    
    return {"messages": [ai]}


def _tools_node_callable(state: Dict[str, Any]) -> Dict[str, Any]:
    tools_by_name = {t.name: t for t in TOOLS}

    messages = _ensure_messages(state.get("messages", []))
    last_ai: Optional[AIMessage] = None
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            last_ai = m
            break

    out: List[ToolMessage] = []
    if last_ai and getattr(last_ai, "tool_calls", None):
        for tc in last_ai.tool_calls:
            name = tc.get("name")
            args = tc.get("args", {}) or {}
            tool_call_id = tc.get("id") or tc.get("tool_call_id")

            tool_obj = tools_by_name.get(name)
            if tool_obj is None:
                result_content = {"ok": False, "error": f"Unknown tool '{name}'"}
            else:
                # Handle context retrieval tools specially - return raw text
                if name == "get_resume_text":
                    resume = state.get("resume", "No resume provided.")
                    result_content = f"RESUME TEXT:\n\n{resume}\n\n(End of resume - {len(resume)} characters)"
                elif name == "get_job_description":
                    jd = state.get("job_description", "No job description provided.")
                    result_content = f"JOB DESCRIPTION:\n\n{jd}\n\n(End of job description - {len(jd)} characters)"
                else:
                    # Regular tool invocation
                    try:
                        result_content = tool_obj.invoke(args)
                    except Exception as e:
                        result_content = {"ok": False, "error": str(e)}

            out.append(ToolMessage(name=name, content=result_content, tool_call_id=tool_call_id))

    # Finishing hint if file is ready (helps prevent another loop)
    try:
        if any(
            (getattr(m, "name", None) == "optimize_resume_sections")
            and isinstance(getattr(m, "content", None), dict)
            and m.content.get("output_path")
            for m in out
        ):
            out.append(HumanMessage(content=(
                "The optimized resume file has been generated. "
                "Conclude with a short confirmation and do not call any more tools."
            )))
    except Exception:
        pass

    return {"messages": out}


def _should_continue(state: Dict[str, Any]) -> str:
    # Stop immediately once the final file exists
    if _final_file_ready(state):
        return END

    messages = _ensure_messages(state.get("messages", []))
    
    # Count tool calls to prevent infinite loops
    tool_call_counts = {}
    for m in messages:
        if isinstance(m, ToolMessage):
            name = getattr(m, "name", None)
            if name:
                tool_call_counts[name] = tool_call_counts.get(name, 0) + 1
    
    # Stop if we've called context tools multiple times (they should only be called once each)
    if tool_call_counts.get("get_resume_text", 0) > 1 or tool_call_counts.get("get_job_description", 0) > 1:
        return END
    
    # Allow multiple web_search calls (user might want to search for different things)
    # Only stop if excessive (more than 5 searches)
    if tool_call_counts.get("web_search", 0) > 5:
        return END
    
    # Stop if we've called optimize_resume_sections (should only happen once)
    if tool_call_counts.get("optimize_resume_sections", 0) >= 1:
        return END
    
    last_ai: Optional[AIMessage] = None
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            last_ai = m
            break
    
    if last_ai and getattr(last_ai, "tool_calls", None):
        return "tools"
    
    return END


def build_graph():
    """Compile and return the LangGraph app used by the backend."""
    graph = StateGraph(AgentState)
    graph.add_node("agent", _agent_node)
    graph.add_node("tools", _tools_node_callable)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    memory = MemorySaver()
    # Recursion limit is set at invoke time, not compile time
    return graph.compile(checkpointer=memory)

