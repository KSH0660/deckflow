"""파일 내용 요약을 위한 청킹 기반 모듈"""

import asyncio

from app.adapter.llm.langchain_client import LangchainLLM
from app.core.config import settings
from app.logging import get_logger

from .models import ChunkSummary

logger = get_logger(__name__)


class FileSummarizer:
    """청킹 기반 파일 내용 요약 클래스"""

    # 요약이 필요한 최소 텍스트 길이 (8KB)
    MIN_TEXT_LENGTH_FOR_SUMMARY = 8000

    # 청크 크기 (4KB)
    CHUNK_SIZE = 4000

    # 청크 간 오버랩 (200자)
    CHUNK_OVERLAP = 200

    def __init__(self):
        """요약용 LLM 초기화"""
        self.llm = LangchainLLM(model=settings.summarization_model)
        logger.info(
            "🧠 [FILE_SUMMARIZER] 청킹 기반 파일 요약기 초기화 완료",
            model=settings.summarization_model,
            min_length_for_summary=self.MIN_TEXT_LENGTH_FOR_SUMMARY,
            chunk_size=self.CHUNK_SIZE,
            chunk_overlap=self.CHUNK_OVERLAP,
        )

    def split_into_chunks(self, text: str) -> list[str]:
        """텍스트를 청크로 분할 (문장 경계 고려)"""

        if len(text) <= self.CHUNK_SIZE:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.CHUNK_SIZE

            # 마지막 청크인 경우
            if end >= len(text):
                chunks.append(text[start:])
                break

            # 문장 경계에서 자르기 시도
            chunk_text = text[start:end]

            # 마지막 문장 끝 찾기 (마침표, 느낌표, 물음표)
            last_sentence_end = max(
                chunk_text.rfind("."),
                chunk_text.rfind("!"),
                chunk_text.rfind("?"),
                chunk_text.rfind("\n"),
            )

            # 적절한 문장 끝을 찾았다면 거기서 자르기
            if last_sentence_end > self.CHUNK_SIZE * 0.7:  # 너무 짧지 않다면
                actual_end = start + last_sentence_end + 1
                chunks.append(text[start:actual_end])
                start = actual_end - self.CHUNK_OVERLAP
            else:
                # 문장 끝을 찾지 못했다면 그냥 자르기
                chunks.append(text[start:end])
                start = end - self.CHUNK_OVERLAP

        logger.debug(
            "📄 [FILE_SUMMARIZER] 텍스트 청킹 완료",
            total_length=len(text),
            chunk_count=len(chunks),
            avg_chunk_size=sum(len(chunk) for chunk in chunks) // len(chunks),
        )

        return chunks

    async def summarize_chunk(self, chunk: str, chunk_index: int, filename: str) -> str:
        """단일 청크를 요약"""

        prompt = f"""Summarize the following text chunk in a concise manner suitable for presentation creation. Focus on key information and important details. Keep the summary around 500 characters.

Filename: {filename}
Chunk: {chunk_index + 1}

Content:
{chunk}"""

        try:
            result: ChunkSummary = await self.llm.generate_structured(
                prompt, schema=ChunkSummary
            )

            logger.debug(
                "✅ [FILE_SUMMARIZER] 청크 요약 완료",
                filename=filename,
                chunk_index=chunk_index,
                original_length=len(chunk),
                summary_length=len(result.summary),
            )

            return result.summary.strip()

        except Exception as e:
            logger.warning(
                "⚠️ [FILE_SUMMARIZER] 청크 요약 실패 - 원본 일부 반환",
                filename=filename,
                chunk_index=chunk_index,
                error=str(e),
            )
            # 요약 실패시 원본의 일부만 반환
            return chunk[:500] + "..." if len(chunk) > 500 else chunk

    def merge_summaries(self, summaries: list[str], filename: str) -> str:
        """여러 청크 요약을 하나로 병합"""

        merged = f"""파일 '{filename}' 요약:

{chr(10).join(f"• {summary}" for summary in summaries if summary.strip())}"""

        logger.info(
            "🔗 [FILE_SUMMARIZER] 청크 요약 병합 완료",
            filename=filename,
            chunk_count=len(summaries),
            merged_length=len(merged),
        )

        return merged

    async def should_summarize(self, text: str) -> bool:
        """텍스트가 요약이 필요한 길이인지 확인"""
        return len(text) > self.MIN_TEXT_LENGTH_FOR_SUMMARY

    async def summarize_for_presentation(self, text: str, filename: str) -> str:
        """청킹 기반으로 파일 내용을 프레젠테이션에 적합하게 요약"""

        if not await self.should_summarize(text):
            logger.info(
                "📄 [FILE_SUMMARIZER] 요약 불필요 - 원본 텍스트 반환",
                filename=filename,
                text_length=len(text),
            )
            return text

        logger.info(
            "📄 [FILE_SUMMARIZER] 청킹 기반 파일 요약 시작",
            filename=filename,
            original_length=len(text),
        )

        try:
            # 1. 청킹
            chunks = self.split_into_chunks(text)

            # 2. 병렬 요약
            logger.info(
                "🔄 [FILE_SUMMARIZER] 청크 병렬 요약 시작",
                filename=filename,
                chunk_count=len(chunks),
            )

            chunk_summaries = await asyncio.gather(
                *[
                    self.summarize_chunk(chunk, i, filename)
                    for i, chunk in enumerate(chunks)
                ]
            )

            # 3. 병합
            final_summary = self.merge_summaries(chunk_summaries, filename)

            logger.info(
                "✅ [FILE_SUMMARIZER] 청킹 기반 요약 완료",
                filename=filename,
                original_length=len(text),
                final_summary_length=len(final_summary),
                chunk_count=len(chunks),
                compression_ratio=round(len(final_summary) / len(text), 2),
            )

            return final_summary

        except Exception as e:
            logger.error(
                "❌ [FILE_SUMMARIZER] 청킹 요약 실패 - 텍스트 절단으로 폴백",
                filename=filename,
                error=str(e),
            )
            # 요약 실패시 원본 텍스트의 앞부분만 사용
            fallback_length = 6000
            return (
                text[:fallback_length] + "..." if len(text) > fallback_length else text
            )


# 전역 인스턴스
_summarizer_instance = None


async def get_file_summarizer() -> FileSummarizer:
    """FileSummarizer 싱글톤 인스턴스 반환"""
    global _summarizer_instance
    if _summarizer_instance is None:
        _summarizer_instance = FileSummarizer()
    return _summarizer_instance


async def summarize_file_content(text: str, filename: str) -> str:
    """파일 내용을 청킹 기반으로 요약하는 헬퍼 함수"""
    summarizer = await get_file_summarizer()
    return await summarizer.summarize_for_presentation(text, filename)
