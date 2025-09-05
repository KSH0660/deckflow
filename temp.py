import os
import time

import dotenv
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from langchain_openai import ChatOpenAI

# .env 파일에서 환경 변수를 로드합니다.
dotenv.load_dotenv()

# --- 1. LLM 캐시 설정 ---
# SQLiteCache를 사용하여 데이터베이스 파일에 캐시를 저장합니다.
# "langchain.db" 파일이 없으면 자동으로 생성됩니다.
print("✅ LLM 캐시를 'SQLiteCache'로 설정합니다. (DB 파일: langchain.db)")
set_llm_cache(SQLiteCache(database_path="langchain.db"))

# --- 2. LLM 초기화 ---
# 캐시가 설정된 후에 LLM을 초기화해야 캐시 기능이 적용됩니다.
llm = ChatOpenAI(
    model="gpt-5-nano", api_key=os.getenv("OPENAI_API_KEY"), temperature=0.7
)

# --- 3. 캐시 동작 확인 ---

prompt = "우주에서 가장 큰 별은 무엇인가요?"

# 첫 번째 실행 (또는 새로운 질문)
print("\n--- 🚀 첫 번째 호출 (API 또는 캐시) ---")
start_time = time.time()
response_1 = llm.invoke(prompt)
end_time = time.time()

print(f"질문: {prompt}")
print(f"답변: {response_1.content}")
print(f"소요 시간: {end_time - start_time:.4f}초")
print(
    "💡 스크립트를 처음 실행했거나 DB에 없는 질문이면 API를 호출하고, 아니라면 캐시를 사용합니다."
)
print("------------------------------------\n")


# 동일한 질문으로 다시 호출
print("--- 🔄 두 번째 호출 (캐시 사용 예상) ---")
start_time = time.time()
response_2 = llm.invoke(prompt)
end_time = time.time()

print(f"질문: {prompt}")
print(f"답변: {response_2.content}")
print(f"소요 시간: {end_time - start_time:.4f}초")
print("💡 매우 빠른 속도로 응답을 받았습니다. SQLite DB에 저장된 캐시를 사용했습니다.")
print("------------------------------------")
