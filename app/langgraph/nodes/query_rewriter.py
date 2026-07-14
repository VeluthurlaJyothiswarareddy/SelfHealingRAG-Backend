from app.services.llm_service import get_llm_service


async def query_rewriter_node(state: dict) -> dict:
    llm = get_llm_service()
    critique = state.get("critique", {})

    system = """Rewrite the user question into 2-4 retrieval-friendly search queries.
Return JSON: {"retrieval_queries": ["...", "..."]}"""

    user = f"""Original question: {state['question']}
Critique reason: {critique.get('reason', '')}
Current queries: {state.get('retrieval_queries', [])}"""

    result = await llm.generate_json(system, user)
    queries = result.get("retrieval_queries") or [state["question"]]
    retry_count = state.get("retry_count", 0) + 1
    return {"retrieval_queries": queries, "retry_count": retry_count}
