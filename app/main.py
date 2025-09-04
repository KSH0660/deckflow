from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from contextlib import asynccontextmanager

from app.api.v1 import deck
from app.core.config import settings 
from app.core.logging import configure_logging

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션의 수명 주기 동안 실행되는 컨텍스트 매니저입니다.
    서버 시작 시 템플릿 데이터 초기화를 수행합니다.
    """ 
    yield
    # Shutdown
    print("애플리케이션이 종료됩니다.")


app = FastAPI(
    title="Presto API",
    description="AI-powered presentation slide generator.",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:8000",  # For local development
    "http://127.0.0.1:8000",  # For local development
    "http://localhost:5173",  # Default Vite dev server port
    "http://127.0.0.1:5173",  # Default Vite dev server port
    "*",  # Allow all origins for development, be more restrictive in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers
)
 


@app.get("/")
async def read_root():
    return {"message": "Welcome to Presto API"}


 