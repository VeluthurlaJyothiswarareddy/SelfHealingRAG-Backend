from app.services.llm_service import get_llm_service


async def context_grader_node(state: dict) -> dict:
    if state.get("retrieval_scope") == "none":
        return {"good_context": True}

    docs = state.get("retrieved_docs", [])
    if not docs:
        return {"good_context": False}

    llm = get_llm_service()
    context_preview = "\n\n".join(
        f"[{d.get('source_file')}] {d.get('chunk_text', '')[:400]}" for d in docs[:5]
    )

    system = """Evaluate whether retrieved context is sufficient to answer the question.
Return JSON: {"good_context": true|false, "reason": "..."}"""
    user = f"Question: {state['question']}\n\nContext:\n{context_preview}"

    result = await llm.generate_json(system, user)
    return {"good_context": bool(result.get("good_context", False))}
