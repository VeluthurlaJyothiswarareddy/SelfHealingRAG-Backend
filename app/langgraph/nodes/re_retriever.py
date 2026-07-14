from app.langgraph.nodes.retriever import retriever_node


async def re_retriever_node(state: dict) -> dict:
    return await retriever_node(state)
