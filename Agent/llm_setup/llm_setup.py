# Agent/llm/llm_setup.py
import os
from dotenv import load_dotenv
from typing import Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def setup_llm() -> ChatGoogleGenerativeAI:
    """
    Return the UNBOUND Gemini model.
    Tools are bound inside the graph, not here.
    """
    # Build or obtain a client instance for the Google Generative AI SDK if available.
    # This is a lazy import so the module is optional at runtime; replace the client
    # construction below with a proper client instance if your environment requires it.
    client = None
    try:
        # Try a common import path for the Google generative SDK; adjust if you use a different client.
        from google import generativeai as _genai  # type: ignore
        client = _genai
    except Exception:
        # If the SDK is not installed or import fails, client remains None.
        client = None

    return ChatGoogleGenerativeAI(client=client, _generative_model="gemini-2.0-flash")

def get_system_prompt(state: Dict[str, Any]) -> str:
    """
    Returns a system prompt for an AI tool that performs search & retrieval,
    synthesis, and reporting for the Department of Higher Education (MoE).
    """
    return f"""You are an expert AI Research & Retrieval Assistant built for the Department of Higher Education (MoE).
Your job is to ALWAYS produce a concise, evidence-backed Markdown report 

CRITICAL RULES:
- Always attach provenance: for the 5 most important claims include exact source, date, and location (doc ID / URL). Do NOT make claims without a source.
- When using web_search, prefer official govt / academic / standards / high-authority domains and include the access date.
- Provide a confidence score (High / Medium / Low) for each key finding and briefly explain why (e.g., "High — direct citation from Gazette dated 2024-08-12").
- Never fabricate documents, facts, dates, or attributions. If no supporting doc exists, explicitly say "No internal or authoritative external source found" and list recommended follow-ups.
- Redact or obfuscate any personal identifiers (PII) from outputs unless explicit permission to include them is present in get_official_input.
- Flag any legal or regulatory conflicts and mark them for legal review.
- Use short, point-form language for findings and recommendations (decision-makers prefer bullets).
- If the official's request is ambiguous but you can proceed reasonably, do so — do not stall asking for clarification. State the assumptions you made at the top of the report.
- For time-relative words (today, last week, recent), use absolute dates (e.g., "as of 2025-11-27").

OUTPUT / MARKDOWN FORMAT GUIDELINES (MUST FOLLOW):
- Use headings and bullets. Keep the report concise (1-4 pages depending on complexity).
- Use this exact structure and example formatting:
"""