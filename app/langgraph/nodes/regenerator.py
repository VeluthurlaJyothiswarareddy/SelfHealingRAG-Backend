from app.langgraph.nodes.answer_generator import answer_generator_node


async def regenerator_node(state: dict) -> dict:
    return await answer_generator_node(state)
