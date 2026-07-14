from app.config import get_settings


def route_after_intent(state: dict) -> str:
    if state.get("conversational") or state.get("retrieval_scope") == "none":
        return "answer_generator"
    return "retriever"


def route_after_context_grader(state: dict) -> str:
    if state.get("conversational") or state.get("retrieval_scope") == "none":
        return "answer_generator"
    if state.get("good_context"):
        return "answer_generator"
    return "query_rewriter"


def route_after_critic(state: dict) -> str:
    settings = get_settings()
    verdict = state.get("final_verdict", "FAIL")
    if verdict == "PASS":
        return "final_decision"
    if state.get("retry_count", 0) >= settings.max_retries:
        return "final_decision"
    return "query_rewriter"


def route_after_final_decision(state: dict) -> str:
    settings = get_settings()
    verdict = state.get("final_verdict", "FAIL")
    retry_count = state.get("retry_count", 0)

    if verdict == "PASS":
        return "end"
    if retry_count >= settings.max_retries:
        return "end"
    return "query_rewriter"
