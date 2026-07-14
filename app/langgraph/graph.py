from langgraph.graph import END, StateGraph

from app.langgraph.edges import (
    route_after_context_grader,
    route_after_critic,
    route_after_final_decision,
    route_after_intent,
)
from app.langgraph.nodes.answer_generator import answer_generator_node
from app.langgraph.nodes.context_grader import context_grader_node
from app.langgraph.nodes.critic import critic_node
from app.langgraph.nodes.final_decision import final_decision_node
from app.langgraph.nodes.intent_router import intent_router_node
from app.langgraph.nodes.query_rewriter import query_rewriter_node
from app.langgraph.nodes.re_retriever import re_retriever_node
from app.langgraph.nodes.regenerator import regenerator_node
from app.langgraph.nodes.retriever import retriever_node
from app.langgraph.state import GraphState


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("intent_router", intent_router_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("context_grader", context_grader_node)
    graph.add_node("answer_generator", answer_generator_node)
    graph.add_node("critic", critic_node)
    graph.add_node("query_rewriter", query_rewriter_node)
    graph.add_node("re_retriever", re_retriever_node)
    graph.add_node("regenerator", regenerator_node)
    graph.add_node("final_decision", final_decision_node)

    graph.set_entry_point("intent_router")

    graph.add_conditional_edges(
        "intent_router",
        route_after_intent,
        {
            "retriever": "retriever",
            "answer_generator": "answer_generator",
        },
    )

    graph.add_edge("retriever", "context_grader")

    graph.add_conditional_edges(
        "context_grader",
        route_after_context_grader,
        {
            "answer_generator": "answer_generator",
            "query_rewriter": "query_rewriter",
        },
    )

    graph.add_edge("answer_generator", "critic")

    graph.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "final_decision": "final_decision",
            "query_rewriter": "query_rewriter",
        },
    )

    graph.add_edge("query_rewriter", "re_retriever")
    graph.add_edge("re_retriever", "regenerator")
    graph.add_edge("regenerator", "critic")

    graph.add_conditional_edges(
        "final_decision",
        route_after_final_decision,
        {
            "end": END,
            "query_rewriter": "query_rewriter",
        },
    )

    return graph.compile()


_rag_graph = None


def get_rag_graph():
    global _rag_graph
    if _rag_graph is None:
        _rag_graph = build_graph()
    return _rag_graph


async def run_rag_workflow(initial_state: dict) -> dict:
    graph = get_rag_graph()
    result = await graph.ainvoke(initial_state)
    return result
