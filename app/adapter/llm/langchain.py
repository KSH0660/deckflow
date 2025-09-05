# adapter/llm/langchain.py

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import TypeVar

import dotenv
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.logging import get_logger

logger = get_logger(__name__)

if not os.path.exists(".cache"):
    os.makedirs(".cache")

set_llm_cache(SQLiteCache(database_path=".cache/llm_cache.db"))
logger.info("LLM 캐시 초기화 완료", cache_path=".cache/llm_cache.db")

dotenv.load_dotenv()

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Return plain text output."""
        raise NotImplementedError

    async def generate_structured(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        """
        Optional: Return a structured output following the given Pydantic schema.
        Not all LLMs support this—implement where possible.
        """
        raise NotImplementedError


T = TypeVar("T", bound=BaseModel)


class LangchainLLM(LLMProvider):
    """
    LangChain-based LLM adapter with structured output support.

    - Plain text: await generate("...prompt...")
    - Structured: await generate_structured("...prompt...", MySchema)
 
    Env:
      OPENAI_API_KEY must be set if using OpenAI models.
    """

    def __init__(
        self,
        model: str = "gpt-5-nano",
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY 환경변수가 설정되지 않음")
            raise ValueError("OPENAI_API_KEY가 필요합니다")

        self.model = model
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key,
        )
        self._prompt = ChatPromptTemplate.from_messages(
            [("user", "{input}")]
        )

        logger.info("LangChain LLM 초기화 완료", model=model, provider="OpenAI")

    async def generate(self, prompt: str) -> str:
        """Return plain text response."""
        logger.debug("텍스트 생성 요청", model=self.model, prompt_length=len(prompt))

        messages = self._prompt.format_messages(input=prompt)
        resp = await self.llm.ainvoke(messages)
        result = resp.content or ""

        logger.debug("텍스트 생성 완료", response_length=len(result))
        return result

    async def generate_structured(self, prompt: str, schema: type[T]) -> T:
        """
        Return a Pydantic-validated object using LangChain's structured output. 
        """
        logger.debug(
            "구조화된 생성 요청",
            model=self.model,
            schema=schema.__name__,
            prompt_length=len(prompt)
        )

        chain = self._prompt | self.llm.with_structured_output(schema=schema)
        result: T = await chain.ainvoke({"input": prompt})

        logger.debug(
            "구조화된 생성 완료",
            schema=schema.__name__,
            result_type=type(result).__name__
        )
        return result
