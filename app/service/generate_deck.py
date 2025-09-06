import asyncio
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel

from app.service.module.plan_deck import DeckPlan, plan_deck
from app.service.module.write_slide_content import SlideContent, write_content


class Slide(BaseModel):
    order: int
    content: SlideContent


class GeneratedDeck(BaseModel):
    deck_id: str
    title: str
    status: str
    slides: list[Slide]
    created_at: datetime
    completed_at: datetime


async def generate_deck(prompt: str, llm, repo) -> str:
    """Main orchestrator for deck generation following: deck plan > layout select > write content"""
    deck_id = uuid4()

    try:
        # Step 1: Generate deck plan
        deck_plan: DeckPlan = await plan_deck(prompt, llm)

        # Initialize deck in repository
        deck_data = {
            "id": str(deck_id),
            "deck_title": deck_plan.deck_title,
            "goal": deck_plan.goal.value,
            "audience": deck_plan.audience,
            "core_message": deck_plan.core_message,
            "color_theme": deck_plan.color_theme.value,
            "status": "generating",
            "slides": [],
            "created_at": datetime.now(),
            "updated_at": None,
            "completed_at": None,
        }
        await repo.save_deck(deck_id, deck_data)

        # Step 2 & 3: For each slide, select layout and generate content (parallel processing)

        # Prepare deck context (shared across all slides)
        deck_context = {
            "deck_title": deck_plan.deck_title,
            "audience": deck_plan.audience,
            "core_message": deck_plan.core_message,
            "goal": deck_plan.goal.value,
            "color_theme": deck_plan.color_theme.value,
        }

        async def generate_slide_content(i: int, slide_plan) -> Slide:
            """Generate content for a single slide"""
            slide_info = slide_plan.model_dump()  # json
            content: SlideContent = await write_content(slide_info, deck_context, llm)

            return Slide(
                order=i + 1,
                content=content,
            )

        # Create tasks for parallel execution
        slide_tasks = [
            generate_slide_content(i, slide_plan)
            for i, slide_plan in enumerate(deck_plan.slides)
        ]

        # Execute all slide generation tasks in parallel
        slides = await asyncio.gather(*slide_tasks)

        # Update deck with completed slides
        deck_data["slides"] = [slide.model_dump() for slide in slides]
        deck_data["status"] = "completed"
        deck_data["completed_at"] = datetime.now()

        await repo.save_deck(deck_id, deck_data)

        return str(deck_id)

    except Exception as e:
        # Mark as failed
        await repo.update_deck_status(deck_id, "failed")
        raise e


if __name__ == "__main__":
    import asyncio
    import time
    from typing import Any

    from app.adapter.llm.langchain_client import LangchainLLM
    from app.logging import configure_logging, get_logger

    logger = get_logger(__name__)
    configure_logging(level="DEBUG")

    class MockRepository:
        """테스트용 모의 레포지토리"""

        def __init__(self):
            self.decks: dict[str, dict[str, Any]] = {}

        async def save_deck(self, deck_id, deck_data):
            """덱 데이터 저장"""
            self.decks[str(deck_id)] = deck_data
            logger.debug(
                "덱 저장 완료", deck_id=str(deck_id), status=deck_data.get("status")
            )

        async def update_deck_status(self, deck_id, status):
            """덱 상태 업데이트"""
            if str(deck_id) in self.decks:
                self.decks[str(deck_id)]["status"] = status
                logger.debug("덱 상태 업데이트", deck_id=str(deck_id), status=status)

    async def main():
        """전체 덱 생성 데모 - 장인정신으로 완전한 프레젠테이션을 만들어내자"""
        llm = LangchainLLM()
        repo = MockRepository()

        try:
            logger.info("=== 🎯 전체 덱 생성 데모 시작 ===")
            total_start = time.time()

            test_prompt = "Samsung vs Hynix 메모리 반도체 기술 비교 분석 프레젠테이션"

            logger.info(f"📝 입력 프롬프트: {test_prompt}")

            # 덱 생성 시작
            deck_generation_start = time.time()
            deck_id = await generate_deck(test_prompt, llm, repo)
            deck_generation_end = time.time()
            deck_generation_time = deck_generation_end - deck_generation_start

            total_time = time.time() - total_start

            # 생성된 덱 정보 조회
            generated_deck = repo.decks.get(deck_id)

            if generated_deck:
                slide_count = len(generated_deck.get("slides", []))

                logger.info("🎉 전체 덱 생성 성공!")
                logger.info(f"🆔 덱 ID: {deck_id}")
                logger.info(f"📋 제목: {generated_deck.get('deck_title', 'N/A')}")
                logger.info(f"🎯 목표: {generated_deck.get('goal', 'N/A')}")
                logger.info(f"🎨 테마: {generated_deck.get('color_theme', 'N/A')}")
                logger.info(f"👥 청중: {generated_deck.get('audience', 'N/A')[:50]}...")
                logger.info(
                    f"💬 핵심 메시지: {generated_deck.get('core_message', 'N/A')[:100]}..."
                )
                logger.info(f"📊 생성된 슬라이드 수: {slide_count}개")
                logger.info(f"⏱️  총 생성 시간: {deck_generation_time:.2f}초")
                logger.info(
                    f"🚀 슬라이드당 평균 시간: {deck_generation_time/slide_count:.2f}초"
                    if slide_count > 0
                    else "🚀 슬라이드당 평균 시간: N/A"
                )

                # 생성된 슬라이드 목록
                logger.info("=== 📑 생성된 슬라이드 목록 ===")
                slides = generated_deck.get("slides", [])
                for i, slide in enumerate(slides):
                    slide_content = slide.get("content", {})
                    html_length = (
                        len(slide_content.get("html_content", ""))
                        if slide_content
                        else 0
                    )
                    logger.info(
                        f"  {i+1}. {slide.get('order', 'unknown')} "
                        f"HTML {html_length:,}자)"
                    )

                # 성능 통계
                logger.info("=== ⚡ 성능 통계 ===")
                total_html_chars = sum(
                    len(slide.get("content", {}).get("html_content", ""))
                    for slide in slides
                )

                logger.info(f"  총 HTML 생성량: {total_html_chars:,}자")
                logger.info(
                    f"  생성 속도: {total_html_chars/deck_generation_time:.0f}자/초"
                )
                logger.info(
                    f"  평균 슬라이드 크기: {total_html_chars/slide_count:.0f}자"
                    if slide_count > 0
                    else "  평균 슬라이드 크기: N/A"
                )

                # 품질 지표
                successful_slides = len(
                    [s for s in slides if s.get("content", {}).get("html_content")]
                )
                success_rate = (
                    successful_slides / slide_count * 100 if slide_count > 0 else 0
                )

                logger.info("=== 📊 품질 지표 ===")
                logger.info(
                    f"  성공률: {successful_slides}/{slide_count} ({success_rate:.1f}%)"
                )
                logger.info(f"  덱 상태: {generated_deck.get('status', 'unknown')}")

                # 시간 분석 (추정)
                estimated_planning_time = deck_generation_time * 0.2  # 약 20% 추정
                estimated_content_time = deck_generation_time * 0.8  # 약 80% 추정

                logger.info("=== ⏱️  시간 분석 (추정) ===")
                logger.info(
                    f"  덱 플래닝: ~{estimated_planning_time:.2f}초 ({estimated_planning_time/deck_generation_time*100:.1f}%)"
                )
                logger.info(
                    f"  콘텐츠 생성: ~{estimated_content_time:.2f}초 ({estimated_content_time/deck_generation_time*100:.1f}%)"
                )
                logger.info(f"  전체 시간: {total_time:.2f}초")

            else:
                logger.error("생성된 덱 정보를 찾을 수 없음", deck_id=deck_id)

        except Exception as e:
            logger.error("덱 생성 데모 실행 실패", error=str(e))
            raise

    # 장인의 마음으로 실행
    asyncio.run(main())
