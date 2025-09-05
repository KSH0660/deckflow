from enum import Enum

from pydantic import BaseModel, Field

from app.logging import get_logger

logger = get_logger(__name__)


class PresentationGoal(str, Enum):
    PERSUADE = "persuade"
    INFORM = "inform"
    INSPIRE = "inspire"
    EDUCATE = "educate"


class LayoutType(str, Enum):
    TITLE_SLIDE = "title_slide"  # 제목/인트로 슬라이드
    CONTENT_SLIDE = "content_slide"  # 일반 내용 슬라이드
    COMPARISON = "comparison"  # 비교/대조 슬라이드
    DATA_VISUAL = "data_visual"  # 데이터/차트 슬라이드
    PROCESS_FLOW = "process_flow"  # 프로세스/플로우 슬라이드
    FEATURE_SHOWCASE = "feature_showcase"  # 기능/특징 소개 슬라이드
    TESTIMONIAL = "testimonial"  # 증언/후기 슬라이드
    CALL_TO_ACTION = "call_to_action"  # 행동 유도 슬라이드


class ColorTheme(str, Enum):
    PROFESSIONAL_BLUE = "professional_blue"  # 전문적인 블루 (신뢰성, 기업)
    CORPORATE_GRAY = "corporate_gray"  # 기업용 그레이 (세련됨, 미니멀)
    VIBRANT_PURPLE = "vibrant_purple"  # 활기찬 보라 (창의성, 혁신)
    MODERN_TEAL = "modern_teal"  # 모던 틸 (성장, 안정성)
    ENERGETIC_ORANGE = "energetic_orange"  # 활동적인 오렌지 (열정, 에너지)
    NATURE_GREEN = "nature_green"  # 자연 그린 (친환경, 성장)
    ELEGANT_BURGUNDY = "elegant_burgundy"  # 우아한 버건디 (고급, 전통)
    TECH_DARK = "tech_dark"  # 테크 다크 (혁신, IT)
    WARM_SUNSET = "warm_sunset"  # 따뜻한 석양 (온화함, 긍정)
    MINIMAL_MONOCHROME = "minimal_monochrome"  # 미니멀 모노크롬 (단순함, 집중)


MASTER_STRATEGIST_PROMPT = """
You are a master presentation strategist who has advised world-class speakers and Fortune 500 executives.

Create a clear and impactful presentation plan based on this request: {prompt}

Return a structured plan with:

**DeckPlan Structure:**
- deck_title: Presentation title (5-120 characters)
- audience: Target audience and their key concerns (be specific)
- core_message: Single most important message audience must remember
- goal: Presentation objective (persuade/inform/inspire/educate)
- color_theme: Visual theme for presentation (professional_blue/corporate_gray/vibrant_purple/modern_teal/energetic_orange/nature_green/elegant_burgundy/tech_dark/warm_sunset/minimal_monochrome)
- slides: List of slide plans (3-12 slides)

**Each SlidePlan Structure:**
- id: Slide sequence id (starting from 1)
- slide_title: Powerful slide title (3-80 characters)
- message: Core one-line message (minimum 10 characters)
- layout_type: Choose most suitable layout (title_slide/content_slide/comparison/data_visual/process_flow/feature_showcase/testimonial/call_to_action)
- key_points: List of key points (empty array or 2-5 items)
- data_points: Statistics/numerical data (empty array or max 3 items)

**Layout Type Selection Guide:**
• title_slide: Opening, section breaks, or conclusion slides
• content_slide: General information, explanations, single concepts
• comparison: Side-by-side comparisons, pros/cons, before/after
• data_visual: Charts, statistics, metrics, numerical insights
• process_flow: Step-by-step processes, workflows, timelines
• feature_showcase: Product features, capabilities, benefits
• testimonial: Customer quotes, case studies, social proof
• call_to_action: Next steps, signup prompts, closing actions

**Color Theme Selection Guide:**
• professional_blue: Corporate presentations, business reports, trustworthy content
• corporate_gray: Executive briefings, minimalist presentations, sophisticated topics
• vibrant_purple: Creative industries, innovation topics, tech startups
• modern_teal: Healthcare, sustainability, growth-focused presentations
• energetic_orange: Sales presentations, marketing pitches, motivational content
• nature_green: Environmental topics, wellness, organic/natural products
• elegant_burgundy: Luxury brands, traditional industries, premium services
• tech_dark: Technology demos, developer presentations, modern/cutting-edge topics
• warm_sunset: Community presentations, educational content, friendly/approachable topics
• minimal_monochrome: Data-heavy presentations, academic research, focus on content

**Strategic Guidelines:**
• Analyze request to identify audience and presentation duration
• Follow narrative arc: Hook → Problem → Evidence → Resolution
• Adjust slide count based on time (2-3 minutes per slide)
• Select appropriate layout_type based on slide content and purpose
• Choose color_theme that matches audience, industry, and presentation tone
• Prioritize clarity, memorability, and strategic flow
• Include key_points and data_points only when impactful

Focus on clarity, memorability, and strategic flow.
"""


class SlidePlan(BaseModel):
    slide_id: int = Field(ge=1, le=200, description="Slide sequence id")
    slide_title: str = Field(
        min_length=3, max_length=100, description="Powerful slide title"
    )
    message: str = Field(min_length=10, description="Core one-line message")
    layout_type: LayoutType = Field(
        description="Most suitable layout type for this slide"
    )
    key_points: list[str] = Field(
        default_factory=list, description="Key bullet points (3-5 recommended)"
    )
    data_points: list[str] = Field(
        default_factory=list, description="Statistics/numerical data"
    )


class DeckPlan(BaseModel):
    deck_title: str = Field(
        min_length=5, max_length=120, description="Presentation title"
    )
    audience: str = Field(
        min_length=5, description="Target audience and their concerns"
    )
    core_message: str = Field(
        min_length=10, description="Single most important message"
    )
    goal: PresentationGoal = Field(description="Presentation objective")
    color_theme: ColorTheme = Field(description="Visual theme for presentation")
    slides: list[SlidePlan]


async def plan_deck(prompt: str, llm) -> DeckPlan:
    """덱 플랜 생성"""
    if not prompt.strip():
        raise ValueError("발표 요청은 필수입니다")

    logger.info("덱 플랜 생성 시작", prompt=prompt[:100])

    enhanced_prompt = MASTER_STRATEGIST_PROMPT.format(prompt=prompt)

    logger.debug("프롬프트 준비 완료", prompt_length=len(enhanced_prompt))

    try:
        plan = await llm.generate_structured(enhanced_prompt, schema=DeckPlan)

        _validate_plan_quality(plan)

        logger.info(
            "덱 플랜 생성 완료",
            deck_title=plan.deck_title,
            slide_count=len(plan.slides),
            goal=plan.goal.value,
        )

        for slide in plan.slides:
            logger.debug(
                f"슬라이드 {slide.slide_id}: {slide.slide_title}",
                message=slide.message,
                key_points_count=len(slide.key_points),
                data_points_count=len(slide.data_points),
                layout_type=slide.layout_type.value,
            )

        return plan

    except Exception as e:
        logger.error("덱 플랜 생성 실패", error=str(e), prompt=prompt[:50])
        raise RuntimeError(f"덱 플랜 생성에 실패했습니다: {e}") from e


def _calculate_plan_score(plan: DeckPlan) -> dict:
    """덱 플랜의 품질을 정량적으로 평가"""
    score_details = {
        "total": 0,
        "structure": 0,  # 구조적 완성도 (0-30점)
        "content": 0,  # 내용 충실도 (0-40점)
        "clarity": 0,  # 명확성 (0-30점)
    }

    # 구조적 완성도 (30점 만점)
    slide_count = len(plan.slides)
    if 5 <= slide_count <= 8:  # 최적 슬라이드 수
        score_details["structure"] += 15
    elif 4 <= slide_count <= 10:  # 양호한 슬라이드 수
        score_details["structure"] += 10
    elif slide_count >= 3:  # 최소 요구사항
        score_details["structure"] += 5

    # 슬라이드 번호 연속성 (5점)
    ids = [s.slide_id for s in plan.slides]
    if ids == list(range(1, len(ids) + 1)):
        score_details["structure"] += 5

    # 핵심 필드 완성도 (10점)
    if len(plan.deck_title) >= 10 and len(plan.core_message) >= 20:
        score_details["structure"] += 10
    elif len(plan.deck_title) >= 5 and len(plan.core_message) >= 10:
        score_details["structure"] += 5

    # 내용 충실도 (40점 만점)
    slides_with_points = [s for s in plan.slides if s.key_points]
    content_ratio = len(slides_with_points) / slide_count if slide_count > 0 else 0
    score_details["content"] += int(content_ratio * 20)  # 최대 20점

    # 평균 키 포인트 개수 (3-5개가 최적)
    total_points = sum(len(s.key_points) for s in plan.slides)
    avg_points = total_points / slide_count if slide_count > 0 else 0
    if 3 <= avg_points <= 5:
        score_details["content"] += 15
    elif 2 <= avg_points <= 6:
        score_details["content"] += 10
    elif avg_points >= 1:
        score_details["content"] += 5

    # 데이터 포인트 활용도 (5점)
    slides_with_data = [s for s in plan.slides if s.data_points]
    if len(slides_with_data) > 0:
        score_details["content"] += 5

    # 명확성 (30점 만점)
    # 제목 길이 적정성 (10점)
    title_lengths = [len(s.slide_title) for s in plan.slides]
    optimal_titles = [t for t in title_lengths if 10 <= t <= 60]
    title_ratio = len(optimal_titles) / slide_count if slide_count > 0 else 0
    score_details["clarity"] += int(title_ratio * 10)

    # 메시지 충실도 (10점)
    message_lengths = [len(s.message) for s in plan.slides]
    good_messages = [m for m in message_lengths if m >= 15]
    message_ratio = len(good_messages) / slide_count if slide_count > 0 else 0
    score_details["clarity"] += int(message_ratio * 10)

    # 청중 명시성 (10점)
    if len(plan.audience) >= 20:
        score_details["clarity"] += 10
    elif len(plan.audience) >= 10:
        score_details["clarity"] += 5

    score_details["total"] = (
        score_details["structure"] + score_details["content"] + score_details["clarity"]
    )
    return score_details


def _get_grade(score: int) -> str:
    """점수를 등급으로 변환"""
    if score >= 90:
        return "A+ (최우수)"
    elif score >= 80:
        return "A (우수)"
    elif score >= 70:
        return "B+ (양호)"
    elif score >= 60:
        return "B (보통)"
    elif score >= 50:
        return "C+ (미흡)"
    else:
        return "C (개선 필요)"


def _validate_plan_quality(plan: DeckPlan) -> None:
    """생성된 플랜의 품질 검증 및 점수 평가"""
    # 기존 검증 로직
    if len(plan.slides) < 3:
        logger.warning("슬라이드 수가 너무 적음", actual=len(plan.slides))

    if len(plan.slides) > 12:
        logger.warning("슬라이드 수가 너무 많음", actual=len(plan.slides))

    empty_slides = [s for s in plan.slides if not s.key_points]
    if empty_slides:
        logger.warning("키 포인트가 비어있는 슬라이드 발견", count=len(empty_slides))

    duplicate_ids = []
    seen_ids = set()
    for slide in plan.slides:
        if slide.slide_id in seen_ids:
            duplicate_ids.append(slide.slide_id)
        seen_ids.add(slide.slide_id)

    if duplicate_ids:
        logger.warning("중복된 슬라이드 번호 발견", duplicates=duplicate_ids)

    # 품질 점수 계산 및 로깅
    score_info = _calculate_plan_score(plan)
    grade = _get_grade(score_info["total"])

    logger.info(
        "덱 플랜 품질 평가 완료",
        총점=f"{score_info['total']}/100",
        등급=grade,
        구조점수=f"{score_info['structure']}/30",
        내용점수=f"{score_info['content']}/40",
        명확성점수=f"{score_info['clarity']}/30",
    )


if __name__ == "__main__":
    import asyncio
    import time

    from app.adapter.llm.langchain_client import LangchainLLM
    from app.logging import configure_logging

    configure_logging(level="DEBUG")

    async def main():
        """덱 플랜 생성 데모 - 장인정신으로 시간도 측정하자"""
        llm = LangchainLLM()

        try:
            logger.info("=== 덱 플랜 생성 데모 시작 ===")
            start_time = time.time()

            # 덱 플랜 생성
            plan = await plan_deck(
                prompt="Samsung vs Hynix 메모리 반도체 기술 비교 분석 프레젠테이션",
                llm=llm,
            )

            end_time = time.time()
            execution_time = end_time - start_time

            logger.info("🎉 덱 플랜 생성 성공!")
            logger.info(f"⏱️  총 실행시간: {execution_time:.2f}초")
            logger.info(f"📋 제목: {plan.deck_title}")
            logger.info(f"🎯 목표: {plan.goal.value}")
            logger.info(f"🎨 색 테마: {plan.color_theme.value}")
            logger.info(f"📊 슬라이드 수: {len(plan.slides)}")
            logger.info(
                f"⚡ 슬라이드당 평균 시간: {execution_time/len(plan.slides):.2f}초"
            )

            # 슬라이드별 상세 정보
            logger.info("=== 생성된 슬라이드 목록 ===")
            for slide in plan.slides:
                logger.info(
                    f"  {slide.slide_id}. {slide.slide_title} ({slide.layout_type})"
                )

        except Exception as e:
            logger.error("데모 실행 실패", error=str(e))
            raise

    asyncio.run(main())
