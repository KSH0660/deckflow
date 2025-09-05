from app.adapter.db import InMemoryRepository
from app.adapter.llm.langchain import LangchainLLM


def current_llm():
    return LangchainLLM()


def current_repo():
    return InMemoryRepository()
