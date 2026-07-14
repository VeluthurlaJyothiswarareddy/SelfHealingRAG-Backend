from app.langgraph.prompts import INSUFFICIENT_MESSAGE
from app.services.llm_service import get_llm_service

ANSWER_SYSTEM_PROMPT = """You are a grounded RAG assistant that answers like ChatGPT.

STRICT RULES:
1. Use ONLY the supplied context. Never invent information.
2. If the answer is not in context, respond exactly:
   I don't have enough information to answer this confidently.
3. Format every answer using clean Markdown so it looks polished in a chat UI.

MARKDOWN FORMATTING (required):
- Start with a short intro sentence, then use ## / ### headings for sections.
- Use bullet lists (- item) and numbered lists (1. item) for steps and features.
- Use Markdown tables whenever comparing fields, endpoints, headers, or request/response params.
  Example table:
  | Field | Type | Required | Description |
  |---|---|---|---|
  | mobileNumber | string | Yes | Mobile number |
- Use `inline code` for endpoints, headers, field names, status codes, and paths.
- Use fenced code blocks for JSON examples when relevant.
- Use **bold** for important labels and endpoints.
- Keep paragraphs short and scannable.
- Do NOT dump long unformatted plain text walls.

CITATIONS:
- Do NOT sprinkle long [Source: filename | chunk id] tags through the body.
- At the end, add a short section:

### Sources
- `filename.md`

Answer structure preference:
1. Brief overview
2. Headings with structured details (lists/tables)
3. Optional notes / errors / caveats
4. Sources section
"""


def _format_context(docs: list) -> str:
    if not docs:
        return "No context available."
    parts = []
    for i, doc in enumerate(docs, 1):
        parts.append(
            f"[Source {i}: {doc.get('source_file', 'unknown')}]\n"
            f"{doc.get('chunk_text', '')}"
        )
    return "\n\n".join(parts)


def _build_sources(docs: list) -> list:
    return [
        {
            "source_file": d.get("source_file", "unknown"),
            "chunk_id": d.get("chunk_id", ""),
            "score": d.get("similarity_score", 0.0),
            "chunk_text": d.get("chunk_text", "")[:300],
        }
        for d in docs
    ]


async def answer_generator_node(state: dict) -> dict:
    if state.get("conversational"):
        llm = get_llm_service()
        answer = await llm.generate(
            "You are a helpful assistant. Respond briefly and naturally to conversational messages.",
            state["question"],
        )
        return {"answer": answer, "sources": [], "confidence": 100.0}

    docs = state.get("retrieved_docs", [])
    if not docs:
        return {
            "answer": INSUFFICIENT_MESSAGE,
            "sources": [],
            "confidence": 0.0,
        }

    llm = get_llm_service()
    history = state.get("chat_history", [])
    context = _format_context(docs)
    files = sorted({d.get("source_file", "unknown") for d in docs})

    user = f"""Conversation history (for tone only; retrieval context has priority):
{history}

Question: {state['question']}

Available source files: {files}

Context:
{context}

Remember: respond in polished Markdown with headings, bullet lists, and tables where useful. Put a short Sources section at the end."""

    answer = await llm.generate(ANSWER_SYSTEM_PROMPT, user)
    sources = _build_sources(docs)
    return {"answer": answer, "sources": sources}
