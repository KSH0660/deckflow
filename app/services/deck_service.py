"""
Service layer for deck operations.

This layer handles business logic and coordinates between the API layer and data layer.
It transforms between request/response models and database models.
"""

from datetime import datetime
from uuid import UUID, uuid4

from app.models.config import DeckGenerationConfig
from app.models.database.deck import DeckDB
from app.models.requests.deck import (
    CreateDeckRequest,
    ModifySlideRequest,
    RevertSlideRequest,
)
from app.models.responses.deck import (
    CreateDeckResponse,
    DeckListItemResponse,
    DeckStatusResponse,
    ModifySlideResponse,
    RevertSlideResponse,
    SaveSlideContentResponse,
    SlideVersionHistoryResponse,
)


class DeckService:
    """Service for deck-related business operations"""

    def __init__(self, repository, llm_provider):
        self.repo = repository
        self.llm = llm_provider

    async def create_deck(
        self, request: CreateDeckRequest, settings=None
    ) -> CreateDeckResponse:
        """Create a new deck and start generation process"""
        import asyncio

        deck_id = uuid4()

        # Create generation config from request
        generation_config = DeckGenerationConfig.from_request_style(request.style)

        # Create initial deck record
        initial_deck = DeckDB(
            id=deck_id,
            deck_title=request.prompt[:60]
            + ("..." if len(request.prompt) > 60 else ""),
            status="generating",
            slides=[],
            progress=1,
            step="Queued",
            created_at=datetime.now(),
        )

        # Save to repository (convert to dict for compatibility)
        await self.repo.save_deck(deck_id, initial_deck.to_dict())

        # Start background generation (business logic belongs in service layer!)
        async def progress_cb(step: str, progress: int, _slide: dict | None = None):
            deck = await self.repo.get_deck(deck_id) or {}
            if deck.get("status") == "cancelled":
                return
            deck.update(
                {
                    "status": "generating",
                    "progress": int(progress),
                    "step": step,
                    "updated_at": datetime.now(),
                }
            )
            await self.repo.save_deck(deck_id, deck)

        # Fire-and-forget background task - service orchestrates business logic
        if settings:  # Only start generation if settings provided
            from app.adapter.factory import current_llm

            asyncio.create_task(
                self._generate_deck(
                    prompt=request.prompt,
                    llm=current_llm(model=settings.llm_model),
                    repo=self.repo,
                    progress_callback=progress_cb,
                    deck_id=deck_id,
                    files=request.files,
                    config=generation_config,
                )
            )

        return CreateDeckResponse(deck_id=str(deck_id), status="generating")

    async def get_deck_status(self, deck_id: UUID) -> DeckStatusResponse:
        """Get deck status by ID"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")

        # Convert dict to database model
        deck = DeckDB.from_dict(deck_data)

        # Convert to response model
        return DeckStatusResponse.from_db_model(deck)

    async def list_decks(self, limit: int = 10) -> list[DeckListItemResponse]:
        """List recent decks"""
        decks_data = await self.repo.list_all_decks(limit=limit)

        # Convert each dict to database model, then to response model
        decks = [DeckDB.from_dict(deck_data) for deck_data in decks_data]
        return [DeckListItemResponse.from_db_model(deck) for deck in decks]

    async def get_deck_data(self, deck_id: UUID) -> dict:
        """Get complete deck data for rendering"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")

        # For now, return raw data for compatibility with existing frontend
        # In the future, this could return a structured response model
        return deck_data

    async def modify_slide(
        self, deck_id: UUID, slide_order: int, request: ModifySlideRequest
    ) -> ModifySlideResponse:
        """Start slide modification process"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")

        deck = DeckDB.from_dict(deck_data)

        # Validate slide exists and deck is in correct state
        if deck.status not in {"completed", "modifying"}:
            raise ValueError(
                f"Can only modify slides in completed or modifying decks. Current status: {deck.status}"
            )

        if slide_order < 1 or slide_order > len(deck.slides):
            raise ValueError("Slide not found")

        # Return immediate response, actual modification happens in background
        return ModifySlideResponse(
            deck_id=str(deck_id), slide_order=slide_order, status="modifying"
        )

    async def get_slide_version_history(
        self, deck_id: UUID, slide_order: int
    ) -> SlideVersionHistoryResponse:
        """Get version history for a specific slide"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")

        deck = DeckDB.from_dict(deck_data)

        # Find the target slide
        target_slide = None
        for slide in deck.slides:
            if slide.order == slide_order:
                target_slide = slide
                break

        if not target_slide:
            raise ValueError(f"Slide {slide_order} not found")

        return SlideVersionHistoryResponse.from_db_slide(
            str(deck_id), slide_order, target_slide
        )

    async def revert_slide_to_version(
        self, deck_id: UUID, slide_order: int, request: RevertSlideRequest
    ) -> RevertSlideResponse:
        """Revert a slide to a specific version"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")

        deck = DeckDB.from_dict(deck_data)

        # Find the target slide
        target_slide = None
        for _i, slide in enumerate(deck.slides):
            if slide.order == slide_order:
                target_slide = slide
                break

        if not target_slide:
            raise ValueError(f"Slide {slide_order} not found")

        # Find the target version
        target_version = None
        if target_slide.versions:
            for version in target_slide.versions:
                if version.version_id == request.version_id:
                    target_version = version
                    break

        if not target_version:
            raise ValueError(f"Version {request.version_id} not found")

        # Update version states
        if target_slide.versions:
            for version in target_slide.versions:
                version.is_current = version.version_id == request.version_id

        # Update slide content
        target_slide.content.html_content = target_version.content
        target_slide.content.current_version_id = target_version.version_id
        target_slide.content.updated_at = datetime.now()

        # Update deck timestamp
        deck.updated_at = datetime.now()

        # Save back to repository
        await self.repo.save_deck(deck_id, deck.to_dict())

        return RevertSlideResponse(
            deck_id=str(deck_id),
            slide_order=slide_order,
            reverted_to_version=request.version_id,
            status="success",
        )

    async def save_slide_content(
        self, deck_id: UUID, slide_order: int, html_content: str
    ) -> SaveSlideContentResponse:
        """Save edited HTML content with versioning"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")

        deck = DeckDB.from_dict(deck_data)

        # Find the target slide
        target_slide = None
        for _i, slide in enumerate(deck.slides):
            if slide.order == slide_order:
                target_slide = slide
                break

        if not target_slide:
            raise ValueError(f"Slide {slide_order} not found")

        current_time = datetime.now()
        current_content = target_slide.content.html_content

        # Only create new version if content actually changed
        if current_content != html_content:
            # Initialize versions list if it doesn't exist
            if target_slide.versions is None:
                target_slide.versions = []

            # Mark all existing versions as not current
            for version in target_slide.versions:
                version.is_current = False

            # Create new version
            from app.models.database.deck import SlideVersionDB

            new_version = SlideVersionDB(
                version_id=f"v{len(target_slide.versions) + 1}_{int(current_time.timestamp())}",
                content=html_content,
                timestamp=current_time,
                is_current=True,
                created_by="user",
            )

            # Add new version to versions list
            target_slide.versions.append(new_version)

            # Keep only last 10 versions
            if len(target_slide.versions) > 10:
                target_slide.versions = target_slide.versions[-10:]

            # Update current content
            target_slide.content.html_content = html_content
            target_slide.content.current_version_id = new_version.version_id
            target_slide.content.updated_at = current_time

        # Update deck timestamp
        deck.updated_at = current_time

        # Save to database
        await self.repo.save_deck(deck_id, deck.to_dict())

        return SaveSlideContentResponse(
            status="success",
            message="편집 내용이 저장되었습니다",
            version_id=target_slide.content.current_version_id,
            version_count=len(target_slide.versions) if target_slide.versions else 0,
        )

    async def delete_deck(self, deck_id: UUID) -> dict:
        """Delete a deck"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")

        await self.repo.delete_deck(deck_id)

        return {
            "status": "success",
            "message": "Deck deleted successfully",
            "deck_id": str(deck_id),
        }

    async def _generate_deck(
        self,
        prompt: str,
        llm,
        repo,
        progress_callback=None,
        deck_id=None,
        files=None,
        config: DeckGenerationConfig = None,
    ) -> str:
        """Private method: Main orchestrator for deck generation"""
        import asyncio
        import time

        from app.core.config import settings
        from app.logging import get_logger
        from app.metrics import (
            active_deck_generations,
            deck_generation_duration_seconds,
            deck_generation_total,
            slide_generation_total,
        )
        from app.services.deck_planning import plan_deck

        logger = get_logger(__name__)

        # Use provided config or create default
        if config is None:
            config = DeckGenerationConfig()

        # Initialize concurrency control
        deck_semaphore = asyncio.Semaphore(max(1, settings.max_decks))

        # Enhance prompt with file content if provided
        enhanced_prompt = self._enhance_prompt_with_files(
            prompt, files, deck_id, logger
        )

        # Initialize progress tracking
        async def update_progress(step: str, progress: int, slide_data: dict = None):
            if progress_callback:
                if asyncio.iscoroutinefunction(progress_callback):
                    await progress_callback(step, progress, slide_data)
                else:
                    progress_callback(step, progress)

        # Start generation process
        start_time = time.time()
        active_deck_generations.inc()

        logger.info("🎯 [GENERATE_DECK] Starting deck generation", deck_id=str(deck_id))

        try:
            async with deck_semaphore:
                # Check for cancellation
                deck = await repo.get_deck(deck_id)
                if deck and deck.get("status") == "cancelled":
                    raise Exception("Deck generation was cancelled")

                # Step 1: Plan deck
                await update_progress("Planning presentation structure...", 30)
                deck_plan = await plan_deck(enhanced_prompt, llm, config)

                # Step 2: Initialize deck data
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
                }
                await repo.save_deck(deck_id, deck_data)

                # Step 3: Generate slides
                slides = await self._generate_all_slides(
                    deck_plan, llm, update_progress, repo, deck_id, config
                )

                # Step 4: Finalize deck
                await self._finalize_deck(
                    deck_data, slides, repo, deck_id, update_progress
                )

                # Record metrics
                duration = time.time() - start_time
                deck_generation_duration_seconds.observe(duration)
                deck_generation_total.labels(status="completed").inc()
                slide_generation_total.inc(len(slides))

                logger.info(
                    "🎉 [GENERATE_DECK] Generation completed", deck_id=str(deck_id)
                )
                return str(deck_id)

        except Exception as e:
            # Handle errors
            deck_generation_total.labels(status="failed").inc()
            await repo.update_deck_status(deck_id, "failed")
            logger.error(
                "❌ [GENERATE_DECK] Generation failed",
                deck_id=str(deck_id),
                error=str(e),
            )
            raise e
        finally:
            active_deck_generations.dec()

    def _enhance_prompt_with_files(self, prompt: str, files, deck_id, logger) -> str:
        """Enhance prompt with file contents if provided"""
        if not files:
            logger.info(
                "📝 [GENERATE_DECK] Basic prompt generation", deck_id=str(deck_id)
            )
            return prompt

        logger.info(
            "📎 [GENERATE_DECK] File-based generation",
            deck_id=str(deck_id),
            file_count=len(files),
        )

        file_contents = []
        for file_info in files:
            file_content = f"""
=== File: {file_info.filename} ===
File type: {file_info.content_type}
Content: {file_info.extracted_text}
=== End of File ==="""
            file_contents.append(file_content)

        return f"""{prompt}

Please generate a presentation based on the content of the following uploaded files:
{''.join(file_contents)}

Please create a detailed presentation based on these files."""

    async def _generate_all_slides(
        self, deck_plan, llm, update_progress, repo, deck_id, config
    ):
        """Generate content for all slides in parallel"""
        import asyncio

        from app.core.config import settings
        from app.services.content_creation import write_content
        from app.services.models import Slide

        # Get preferences from config.style_preferences with defaults
        style_prefs = config.style_preferences if config else {}
        
        deck_context = {
            "deck_title": deck_plan.deck_title,
            "audience": deck_plan.audience,
            "core_message": deck_plan.core_message,
            "goal": deck_plan.goal.value,
            "color_theme": deck_plan.color_theme.value,
            "layout_preference": style_prefs.get("layout_preference", "professional"),
            "color_preference": style_prefs.get("color_preference", "professional_blue"),
            "persona_preference": style_prefs.get("persona_preference", "balanced"),
        }

        total_slides = len(deck_plan.slides)
        completed_count = 0
        progress_lock = asyncio.Lock()
        slide_semaphore = asyncio.Semaphore(max(1, settings.max_slide_concurrency))

        async def generate_single_slide(i: int, slide_plan) -> Slide:
            nonlocal completed_count

            slide_info = slide_plan.model_dump()
            slide_title = slide_info.get("slide_title", "Untitled")

            # Check for cancellation
            deck = await repo.get_deck(deck_id)
            if deck and deck.get("status") == "cancelled":
                raise Exception("Generation cancelled")

            # Generate content
            async with slide_semaphore:
                content = await write_content(slide_info, deck_context, llm)

            slide = Slide(order=i + 1, content=content, plan=slide_info)

            # Update progress
            async with progress_lock:
                completed_count += 1
                progress = 60 + (completed_count * 25 // total_slides)
                await update_progress(
                    f"Completed slide {i+1}/{total_slides}: {slide_title}", progress
                )

            return slide

        # Generate all slides in parallel
        await update_progress("Starting slide generation...", 50)
        slide_tasks = [
            generate_single_slide(i, slide_plan)
            for i, slide_plan in enumerate(deck_plan.slides)
        ]
        return await asyncio.gather(*slide_tasks)

    async def _finalize_deck(self, deck_data, slides, repo, deck_id, update_progress):
        """Finalize deck with version history"""
        await update_progress("Finalizing presentation...", 95)
        current_time = datetime.now()

        # Add version history to slides
        slides_data = []
        for slide in slides:
            slide_dict = slide.model_dump()

            # Initialize version history
            initial_version = {
                "version_id": f"v1_{int(current_time.timestamp())}",
                "content": slide_dict["content"]["html_content"],
                "timestamp": current_time.isoformat(),
                "is_current": True,
                "created_by": "system",
            }

            slide_dict["content"]["current_version_id"] = initial_version["version_id"]
            slide_dict["content"]["updated_at"] = current_time.isoformat()
            slide_dict["versions"] = [initial_version]
            slides_data.append(slide_dict)

        # Save completed deck
        deck_data["slides"] = slides_data
        deck_data["status"] = "completed"
        deck_data["completed_at"] = current_time
        await repo.save_deck(deck_id, deck_data)
