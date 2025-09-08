import time
from datetime import datetime

from app.logging import get_logger
from app.service.content_creation import SlideContent, write_content

logger = get_logger(__name__)


async def modify_slide(
    deck_id,
    slide_order: int,
    modification_prompt: str,
    llm,
    repo,
    progress_callback=None,
):
    """
    개별 슬라이드를 수정하는 서비스 함수

    Args:
        deck_id: 덱 ID
        slide_order: 수정할 슬라이드 순서 (1부터 시작)
        modification_prompt: 수정 요청 프롬프트
        llm: Language model instance
        repo: Repository instance
        progress_callback: 진행상황 콜백 함수
    """
    start_time = time.time()

    async def update_progress(step: str, progress: int):
        """Internal progress updater"""
        if progress_callback:
            await progress_callback(step, progress)

    logger.info(
        "✏️ [MODIFY_SLIDE] 슬라이드 수정 시작",
        deck_id=str(deck_id),
        slide_order=slide_order,
        modification_prompt=modification_prompt[:100],
    )

    try:
        # 덱 데이터 가져오기
        await update_progress("Loading deck data...", 10)
        deck = await repo.get_deck(deck_id)
        if not deck:
            raise ValueError("Deck not found")

        slides = deck.get("slides", [])
        if slide_order < 1 or slide_order > len(slides):
            raise ValueError("Invalid slide order")

        # 수정할 슬라이드 찾기 (0-based index)
        slide_index = slide_order - 1
        target_slide = slides[slide_index]

        await update_progress("Analyzing slide content...", 30)

        # 덱 컨텍스트 준비
        deck_context = {
            "deck_title": deck.get("deck_title", ""),
            "audience": deck.get("audience", ""),
            "core_message": deck.get("core_message", ""),
            "goal": deck.get("goal", ""),
            "color_theme": deck.get("color_theme", ""),
        }

        # 현재 슬라이드 정보와 수정 요청을 결합한 새로운 슬라이드 계획 생성
        current_slide_plan = target_slide.get("plan", {})

        # 수정된 슬라이드 계획 생성
        modified_slide_plan = {
            **current_slide_plan,
            "modification_request": modification_prompt,
            "slide_title": current_slide_plan.get("slide_title", ""),
            "key_points": current_slide_plan.get("key_points", []),
            "layout_type": current_slide_plan.get("layout_type", "title_and_content"),
        }

        await update_progress("Generating modified slide content...", 60)

        # 수정된 슬라이드 콘텐츠 생성
        modified_content: SlideContent = await write_content(
            modified_slide_plan,
            deck_context,
            llm,
            is_modification=True,
            modification_prompt=modification_prompt,
        )

        await update_progress("Updating slide in deck...", 90)

        # 슬라이드 업데이트
        updated_slide = {
            "order": slide_order,
            "content": modified_content.model_dump(),
            "plan": modified_slide_plan,
        }

        # 덱의 슬라이드 리스트 업데이트
        slides[slide_index] = updated_slide
        deck["slides"] = slides
        deck["status"] = "completed"  # 수정 완료 후 다시 completed 상태로
        deck["updated_at"] = datetime.now()
        deck["step"] = None  # step 초기화
        deck["progress"] = None  # progress 초기화

        # 덱 저장
        await repo.save_deck(deck_id, deck)

        await update_progress("Slide modification completed", 100)

        duration = time.time() - start_time
        logger.info(
            "✅ [MODIFY_SLIDE] 슬라이드 수정 완료",
            deck_id=str(deck_id),
            slide_order=slide_order,
            duration_seconds=round(duration, 2),
        )

    except Exception as e:
        logger.error(
            "❌ [MODIFY_SLIDE] 슬라이드 수정 실패",
            deck_id=str(deck_id),
            slide_order=slide_order,
            error=str(e),
        )
        # 덱 상태를 원래대로 복원
        try:
            deck = await repo.get_deck(deck_id)
            if deck:
                deck["status"] = "completed"
                deck["updated_at"] = datetime.now()
                deck["step"] = None  # step 초기화
                deck["progress"] = None  # progress 초기화
                await repo.save_deck(deck_id, deck)
        except Exception as restore_error:
            logger.error(
                "❌ [MODIFY_SLIDE] 덱 상태 복원 실패",
                deck_id=str(deck_id),
                error=str(restore_error),
            )
        raise e
