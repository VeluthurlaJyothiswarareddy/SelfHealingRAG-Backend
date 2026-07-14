import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.utils.errors import LLMError

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.settings = get_settings()
        self._llm = ChatOpenAI(
            model=self.settings.chat_model,
            temperature=self.settings.chat_temperature,
            openai_api_key=self.settings.chat_api_key,
            openai_api_base=self.settings.chat_api_base,
        )

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = await self._llm.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )
            return response.content.strip()
        except Exception as exc:
            logger.exception("LLM generation failed")
            raise LLMError(str(exc)) from exc

    async def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        text = await self.generate(
            system_prompt + "\nRespond with valid JSON only. No markdown fences.",
            user_prompt,
        )
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text[:-3]
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMError("Failed to parse LLM JSON response") from exc


_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
