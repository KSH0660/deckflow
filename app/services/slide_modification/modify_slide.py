import time
from datetime import datetime

from app.logging import get_logger
from app.services.content_creation import SlideContent, write_content

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

        # 슬라이드 업데이트 (기존 버전 히스토리 보존)
        current_time = datetime.now()

        # 기존 버전 히스토리 가져오기 (없으면 빈 리스트)
        existing_versions = target_slide.get("versions", [])

        # 모든 기존 버전을 current가 아니도록 설정
        for version in existing_versions:
            version["is_current"] = False

        # 새로운 버전 생성
        new_version = {
            "version_id": f"v{len(existing_versions) + 1}_{int(current_time.timestamp())}",
            "content": modified_content.html_content,
            "timestamp": current_time.isoformat(),
            "is_current": True,
            "created_by": "user",
        }

        # 새로운 버전을 히스토리에 추가
        updated_versions = existing_versions + [new_version]

        # 최대 10개 버전만 유지
        if len(updated_versions) > 10:
            updated_versions = updated_versions[-10:]

        # 업데이트된 슬라이드 콘텐츠 준비
        updated_content = modified_content.model_dump()
        updated_content["current_version_id"] = new_version["version_id"]
        updated_content["updated_at"] = current_time.isoformat()

        updated_slide = {
            "order": slide_order,
            "content": updated_content,
            "plan": modified_slide_plan,
            "versions": updated_versions,
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
