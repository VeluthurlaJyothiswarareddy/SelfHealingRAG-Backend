from app.langgraph.prompts import INSUFFICIENT_MESSAGE
from app.services.llm_service import get_llm_service


async def critic_node(state: dict) -> dict:
    if state.get("conversational"):
        return {
            "critique": {"verdict": "PASS", "confidence": 100, "reason": "Conversational"},
            "confidence": 100.0,
            "final_verdict": "PASS",
        }

    answer = state.get("answer", "")
    docs = state.get("retrieved_docs", [])

    if not docs or INSUFFICIENT_MESSAGE.lower() in answer.lower():
        return {
            "critique": {
                "verdict": "FAIL",
                "confidence": 0,
                "reason": "No relevant context retrieved",
            },
            "confidence": 0.0,
            "final_verdict": "FAIL",
        }

    llm = get_llm_service()
    context = "\n\n".join(
        f"[{d.get('source_file')}] {d.get('chunk_text', '')[:500]}" for d in docs[:5]
    )

    system = """You are a critic evaluating RAG answers.
Evaluate groundedness, hallucination risk, completeness, citation validity.
Return JSON:
{
  "verdict": "PASS" or "FAIL",
  "confidence": 0-100,
  "reason": "..."
}"""

    user = f"""Question: {state['question']}
Context: {context}
Answer: {answer}"""

    critique = await llm.generate_json(system, user)
    verdict = critique.get("verdict", "FAIL").upper()
    confidence = float(critique.get("confidence", 0))

    return {
        "critique": critique,
        "confidence": confidence,
        "final_verdict": verdict,
    }
