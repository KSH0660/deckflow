import asyncio
import time
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel

from app.core.config import settings
from app.logging import get_logger
from app.metrics import (
    active_deck_generations,
    deck_generation_duration_seconds,
    deck_generation_total,
    slide_generation_total,
)
from app.service.module.plan_deck import DeckPlan, plan_deck
from app.service.module.write_slide_content import SlideContent, write_content

logger = get_logger(__name__)


class Slide(BaseModel):
    order: int
    content: SlideContent
    plan: dict  # Store slide plan information


class GeneratedDeck(BaseModel):
    deck_id: str
    title: str
    status: str
    slides: list[Slide]
    created_at: datetime
    completed_at: datetime


# Global concurrency controls (configured via app.core.config)
deck_semaphore = asyncio.Semaphore(max(1, settings.max_decks))


async def generate_deck(
    prompt: str, llm, repo, progress_callback=None, deck_id=None, files=None
) -> str:
    """Main orchestrator for deck generation following: deck plan > layout select > write content

    Args:
        prompt: 사용자 입력 프롬프트
        llm: Language model instance
        repo: Repository instance
        progress_callback: 진행상황 콜백 함수
        deck_id: 덱 ID (optional)
        files: 업로드된 파일 정보 리스트 (optional)

    Concurrency limits:
    - Global deck-level semaphore controls how many decks can generate in parallel.
    - Per-deck slide semaphore (env DECKFLOW_MAX_SLIDE_CONCURRENCY) limits concurrent slide generations for this deck.
    """
    deck_id = deck_id or uuid4()

    # 파일 내용이 있으면 프롬프트와 결합
    enhanced_prompt = prompt
    if files:
        logger.info(
            "📎 [GENERATE_DECK] 파일 기반 덱 생성 요청",
            deck_id=str(deck_id),
            file_count=len(files),
            files=[{
                "filename": f.filename,
                "content_type": f.content_type,
                "size_kb": round(f.size / 1024, 2),
                "text_length": len(f.extracted_text)
            } for f in files]
        )
        
        file_contents = []
        total_file_text_length = 0
        
        for file_info in files:
            file_text_length = len(file_info.extracted_text)
            total_file_text_length += file_text_length
            
            logger.debug(
                "📎 [GENERATE_DECK] 파일 내용 처리",
                filename=file_info.filename,
                content_type=file_info.content_type,
                size_bytes=file_info.size,
                extracted_text_length=file_text_length,
                text_preview=file_info.extracted_text[:100] + ("..." if file_text_length > 100 else "")
            )
            
            file_content = f"""

=== File: {file_info.filename} ===
File type: {file_info.content_type}
Size: {file_info.size} bytes

Content:
{file_info.extracted_text}

=== End of File ===
"""
            file_contents.append(file_content)

        enhanced_prompt = f"""{prompt}

Please generate a presentation based on the content of the following uploaded files:
{''.join(file_contents)}

Please create a more specific and detailed presentation based on the content of these files."""
        
        logger.info(
            "📎 [GENERATE_DECK] 향상된 프롬프트 생성 완료",
            deck_id=str(deck_id),
            original_prompt_length=len(prompt),
            total_file_text_length=total_file_text_length,
            enhanced_prompt_length=len(enhanced_prompt)
        )
    else:
        logger.info(
            "📝 [GENERATE_DECK] 기본 프롬프트 기반 덱 생성 요청",
            deck_id=str(deck_id),
            prompt_length=len(prompt)
        )

    async def update_progress(step: str, progress: int, slide_data: dict = None):
        """Internal progress updater with real-time data"""
        if progress_callback:
            if asyncio.iscoroutinefunction(progress_callback):
                await progress_callback(step, progress, slide_data)
            else:
                progress_callback(step, progress)

    # Initialize metrics tracking
    start_time = time.time()
    active_deck_generations.inc()

    logger.info(
        "🎯 [GENERATE_DECK] 전체 덱 생성 시작",
        deck_id=str(deck_id),
        prompt_preview=prompt[:100],
    )

    class GenerationCancelled(Exception):
        pass

    async def check_cancelled():
        deck = await repo.get_deck(deck_id)
        if deck and deck.get("status") == "cancelled":
            raise GenerationCancelled("Deck generation was cancelled")

    try:
        # Enforce global deck concurrency (queue if saturated)
        async with deck_semaphore:
            # Early cancellation check on entry
            await check_cancelled()
            # Step 1: Generate deck plan
            await update_progress("Planning presentation structure...", 30)
            logger.info("📋 [GENERATE_DECK] 덱 계획 단계 시작")
            deck_plan: DeckPlan = await plan_deck(enhanced_prompt, llm)
            logger.info(
                "📋 [GENERATE_DECK] 덱 계획 단계 완료",
                slide_count=len(deck_plan.slides),
            )

            # Send deck plan details
            await update_progress(
                "Deck plan completed",
                35,
                {
                    "deck_title": deck_plan.deck_title,
                    "slide_count": len(deck_plan.slides),
                    "goal": deck_plan.goal.value,
                    "theme": deck_plan.color_theme.value,
                },
            )

            # Initialize deck in repository
            await update_progress("Initializing deck data...", 40)
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

            # Step 2 & 3: For each slide, select layout and generate content (with real-time updates)
            await update_progress("Starting slide generation...", 50)

            # Prepare deck context (shared across all slides)
            deck_context = {
                "deck_title": deck_plan.deck_title,
                "audience": deck_plan.audience,
                "core_message": deck_plan.core_message,
                "goal": deck_plan.goal.value,
                "color_theme": deck_plan.color_theme.value,
            }

            total_slides = len(deck_plan.slides)
            logger.info(
                "🎨 [GENERATE_DECK] 슬라이드 콘텐츠 생성 단계 시작",
                slide_count=total_slides,
            )

            # Shared progress tracking for parallel execution
            completed_count = 0
            completed_slides_data = {}
            progress_lock = asyncio.Lock()

            # Per-deck slide concurrency limit
            slide_semaphore = asyncio.Semaphore(max(1, settings.max_slide_concurrency))

            async def generate_slide_content_with_progress(i: int, slide_plan) -> Slide:
                """Generate content for a single slide with real-time progress updates"""
                nonlocal completed_count

                slide_info = slide_plan.model_dump()
                slide_title = slide_info.get("slide_title", "Untitled")

                # Start notification
                await update_progress(
                    f"Starting slide {i+1}/{total_slides}: {slide_title}", 60
                )

                # Cancellation check before heavy work
                await check_cancelled()

                # Generate slide content
                async with slide_semaphore:
                    content: SlideContent = await write_content(
                        slide_info, deck_context, llm
                    )

                slide = Slide(
                    order=i + 1,
                    content=content,
                    plan=slide_info,
                )

                # Update completed count atomically
                async with progress_lock:
                    completed_count += 1
                    completed_slides_data[i + 1] = {
                        "slide_order": i + 1,
                        "slide_title": slide_title,
                        "html_preview": (
                            content.html_content[:500] + "..."
                            if len(content.html_content) > 500
                            else content.html_content
                        ),
                    }

                    # Calculate progress (60% to 85% range for slide generation)
                    progress = 60 + (completed_count * 25 // total_slides)

                    # Send real-time update
                    await update_progress(
                        f"Completed slide {i+1}/{total_slides}: {slide_title}",
                        progress,
                        {
                            "slide_order": i + 1,
                            "slide_title": slide_title,
                            "html_preview": (
                                content.html_content[:500] + "..."
                                if len(content.html_content) > 500
                                else content.html_content
                            ),
                            "completed_slides": completed_count,
                            "total_slides": total_slides,
                        },
                    )

                return slide

            # Create tasks for parallel execution (restored performance!)
            slide_tasks = [
                generate_slide_content_with_progress(i, slide_plan)
                for i, slide_plan in enumerate(deck_plan.slides)
            ]

            # Execute all slide generation tasks in parallel
            await update_progress("Generating all slides in parallel...", 60)
            slides = await asyncio.gather(*slide_tasks)

            logger.info(
                "🎨 [GENERATE_DECK] 슬라이드 콘텐츠 생성 단계 완료",
                generated_slides=len(slides),
            )

            # Update deck with completed slides
            await update_progress("Finalizing presentation...", 95)
            deck_data["slides"] = [slide.model_dump() for slide in slides]
            deck_data["status"] = "completed"
            deck_data["completed_at"] = datetime.now()

            await repo.save_deck(deck_id, deck_data)

            logger.info(
                "🎉 [GENERATE_DECK] 전체 덱 생성 완료",
                deck_id=str(deck_id),
                total_slides=len(slides),
            )

            # Record successful completion metrics
            duration = time.time() - start_time
            deck_generation_duration_seconds.observe(duration)
            deck_generation_total.labels(status="completed").inc()
            slide_generation_total.inc(len(slides))

            return str(deck_id)

    except GenerationCancelled:
        logger.info("🛑 덱 생성 취소됨", deck_id=str(deck_id))
        # Record cancellation metrics
        deck_generation_total.labels(status="cancelled").inc()
        # Do not overwrite status; API will have marked as cancelled
        return str(deck_id)
    except Exception as e:
        # Record failure metrics
        deck_generation_total.labels(status="failed").inc()
        # Mark as failed
        await repo.update_deck_status(deck_id, "failed")
        raise e
    finally:
        # Always decrement active counter
        active_deck_generations.dec()
