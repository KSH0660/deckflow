
from app.adapter.llm.langchain import LangchainLLM
from app.adapter.db.in_memory import InMemoryRepository

def current_llm():
    return LangchainLLM()

def current_repo():
    return InMemoryRepository()