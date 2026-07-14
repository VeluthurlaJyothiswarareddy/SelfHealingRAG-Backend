from app.config import get_settings
from app.langgraph.prompts import INSUFFICIENT_MESSAGE


async def final_decision_node(state: dict) -> dict:
    settings = get_settings()
    verdict = state.get("final_verdict", "FAIL")
    retry_count = state.get("retry_count", 0)

    if verdict == "PASS":
        return {}

    if retry_count >= settings.max_retries:
        return {
            "answer": INSUFFICIENT_MESSAGE,
            "sources": [],
            "confidence": 0.0,
            "final_verdict": "FAIL",
            "critique": {
                "verdict": "FAIL",
                "confidence": 0,
                "reason": "Max retries exceeded",
            },
        }

    return {}
