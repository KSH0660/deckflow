from app.logging import get_logger

from .models import DeckPlan
from .prompts import AVAILABLE_PROMPTS

logger = get_logger(__name__)


async def plan_deck(prompt: str, llm, config=None) -> DeckPlan:
    """덱 플랜 생성"""
    if not prompt.strip():
        raise ValueError("발표 요청은 필수입니다")

    # Import here to avoid circular imports
    from app.models.config import DeckGenerationConfig

    # Use provided config or create default
    if config is None:
        config = DeckGenerationConfig()

    persona = config.persona

    if persona not in AVAILABLE_PROMPTS:
        raise ValueError(
            f"Unknown persona: {persona}. Available personas are: {list(AVAILABLE_PROMPTS.keys())}"
        )

    logger.info(
        "덱 플랜 생성 시작",
        prompt=prompt[:100],
        persona=persona,
        max_slides=config.max_slides,
    )

    # Generate prompt using the new template system with full config
    from .prompts import generate_persona_prompt

    try:
        enhanced_prompt = generate_persona_prompt(persona, config, prompt)
        logger.debug("Generated prompt", length=len(enhanced_prompt))
    except Exception as e:
        logger.error("Failed to generate prompt", error=str(e), persona=persona)
        # Fallback to old method
        planning_prompt = AVAILABLE_PROMPTS[persona]
        enhanced_prompt = planning_prompt.format(prompt=prompt)

    logger.info("프롬프트 준비 완료", prompt_length=len(enhanced_prompt))

    try:
        logger.info("🤖 [PLAN_DECK] LLM 호출 시작", step="plan_generation")
        plan = await llm.generate_structured(enhanced_prompt, schema=DeckPlan)

        _validate_plan_quality(plan)

        logger.info(
            "덱 플랜 생성 완료",
            deck_title=plan.deck_title,
            slide_count=len(plan.slides),
            goal=plan.goal.value,
            step="plan_generation_complete",
        )

        for slide in plan.slides:
            logger.debug(
                f"슬라이드 {slide.slide_id}: {slide.slide_title}",
                message=slide.message,
                key_points_count=len(slide.key_points),
                data_points_count=len(slide.data_points),
                expert_insights_count=len(slide.expert_insights),
                supporting_facts_count=len(slide.supporting_facts),
                quantitative_details_count=len(slide.quantitative_details),
                layout_type=slide.layout_type.value,
            )

        return plan

    except Exception as e:
        logger.error("덱 플랜 생성 실패", error=str(e), prompt=prompt[:50])
        raise RuntimeError(f"덱 플랜 생성에 실패했습니다: {e}") from e


def _calculate_plan_score(plan: DeckPlan) -> dict:
    """데이터 풍부한 덱 플랜의 품질을 정량적으로 평가"""
    score_details = {
        "total": 0,
        "structure": 0,  # 구조적 완성도 (0-25점)
        "content": 0,  # 내용 충실도 (0-35점)
        "data_richness": 0,  # 데이터 풍부도 (0-25점)
        "clarity": 0,  # 명확성 (0-15점)
    }

    slide_count = len(plan.slides)

    # 구조적 완성도 (25점 만점)
    if 5 <= slide_count <= 8:  # 최적 슬라이드 수
        score_details["structure"] += 12
    elif 4 <= slide_count <= 10:  # 양호한 슬라이드 수
        score_details["structure"] += 8
    elif slide_count >= 3:  # 최소 요구사항
        score_details["structure"] += 4

    # 슬라이드 번호 연속성 (5점)
    ids = [s.slide_id for s in plan.slides]
    if ids == list(range(1, len(ids) + 1)):
        score_details["structure"] += 5

    # 핵심 필드 완성도 (8점)
    if len(plan.deck_title) >= 10 and len(plan.core_message) >= 20:
        score_details["structure"] += 8
    elif len(plan.deck_title) >= 5 and len(plan.core_message) >= 10:
        score_details["structure"] += 4

    # 내용 충실도 (35점 만점)
    slides_with_points = [s for s in plan.slides if s.key_points]
    content_ratio = len(slides_with_points) / slide_count if slide_count > 0 else 0
    score_details["content"] += int(content_ratio * 15)  # 최대 15점

    # 평균 키 포인트 개수 (3-5개가 최적)
    total_points = sum(len(s.key_points) for s in plan.slides)
    avg_points = total_points / slide_count if slide_count > 0 else 0
    if 3 <= avg_points <= 5:
        score_details["content"] += 12
    elif 2 <= avg_points <= 6:
        score_details["content"] += 8
    elif avg_points >= 1:
        score_details["content"] += 4

    # 전문가 인사이트 활용도 (8점)
    slides_with_insights = [s for s in plan.slides if s.expert_insights]
    insight_ratio = len(slides_with_insights) / slide_count if slide_count > 0 else 0
    score_details["content"] += int(insight_ratio * 8)

    # 데이터 풍부도 (25점 만점) - 새로운 평가 기준
    # 기본 데이터 포인트 (8점)
    slides_with_data = [s for s in plan.slides if s.data_points]
    data_ratio = len(slides_with_data) / slide_count if slide_count > 0 else 0
    score_details["data_richness"] += int(data_ratio * 8)

    # 지원 팩트 (6점)
    slides_with_facts = [s for s in plan.slides if s.supporting_facts]
    facts_ratio = len(slides_with_facts) / slide_count if slide_count > 0 else 0
    score_details["data_richness"] += int(facts_ratio * 6)

    # 정량적 세부사항 (8점)
    slides_with_quant = [s for s in plan.slides if s.quantitative_details]
    quant_ratio = len(slides_with_quant) / slide_count if slide_count > 0 else 0
    score_details["data_richness"] += int(quant_ratio * 8)

    # 데이터 밀도 보너스 (3점) - 모든 필드가 채워진 슬라이드 비율
    fully_loaded_slides = [
        s
        for s in plan.slides
        if s.data_points
        and s.expert_insights
        and s.supporting_facts
        and s.quantitative_details
    ]
    if len(fully_loaded_slides) > slide_count * 0.5:  # 50% 이상이 풀로 채워짐
        score_details["data_richness"] += 3

    # 명확성 (15점 만점)
    # 제목 길이 적정성 (6점)
    title_lengths = [len(s.slide_title) for s in plan.slides]
    optimal_titles = [t for t in title_lengths if 10 <= t <= 60]
    title_ratio = len(optimal_titles) / slide_count if slide_count > 0 else 0
    score_details["clarity"] += int(title_ratio * 6)

    # 메시지 충실도 (5점)
    message_lengths = [len(s.message) for s in plan.slides]
    good_messages = [m for m in message_lengths if m >= 15]
    message_ratio = len(good_messages) / slide_count if slide_count > 0 else 0
    score_details["clarity"] += int(message_ratio * 5)

    # 청중 명시성 (4점)
    if len(plan.audience) >= 20:
        score_details["clarity"] += 4
    elif len(plan.audience) >= 10:
        score_details["clarity"] += 2

    score_details["total"] = (
        score_details["structure"]
        + score_details["content"]
        + score_details["data_richness"]
        + score_details["clarity"]
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
    """데이터 풍부한 플랜의 품질 검증 및 점수 평가"""
    # 기존 검증 로직
    if len(plan.slides) < 3:
        logger.warning("슬라이드 수가 너무 적음", actual=len(plan.slides))

    if len(plan.slides) > 12:
        logger.warning("슬라이드 수가 너무 많음", actual=len(plan.slides))

    # 데이터 풍부도 검증 - 새로운 기준들
    slides_without_data = [s for s in plan.slides if not s.data_points]
    if len(slides_without_data) > len(plan.slides) * 0.3:  # 30% 이상이 데이터 없음
        logger.warning(
            "데이터 포인트가 부족한 슬라이드가 많음", count=len(slides_without_data)
        )

    slides_without_insights = [s for s in plan.slides if not s.expert_insights]
    if (
        len(slides_without_insights) > len(plan.slides) * 0.4
    ):  # 40% 이상이 인사이트 없음
        logger.warning(
            "전문가 인사이트가 부족한 슬라이드가 많음",
            count=len(slides_without_insights),
        )

    slides_without_quant = [s for s in plan.slides if not s.quantitative_details]
    if (
        len(slides_without_quant) > len(plan.slides) * 0.5
    ):  # 50% 이상이 정량 데이터 없음
        logger.warning(
            "정량적 세부사항이 부족한 슬라이드가 많음", count=len(slides_without_quant)
        )

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

    # 데이터 풍부도 통계
    total_data_points = sum(len(s.data_points) for s in plan.slides)
    total_insights = sum(len(s.expert_insights) for s in plan.slides)
    total_facts = sum(len(s.supporting_facts) for s in plan.slides)
    total_quant = sum(len(s.quantitative_details) for s in plan.slides)

    # 품질 점수 계산 및 로깅
    score_info = _calculate_plan_score(plan)
    grade = _get_grade(score_info["total"])

    logger.info(
        "데이터 풍부한 덱 플랜 품질 평가 완료",
        총점=f"{score_info['total']}/100",
        등급=grade,
        구조점수=f"{score_info['structure']}/25",
        내용점수=f"{score_info['content']}/35",
        데이터풍부도=f"{score_info['data_richness']}/25",
        명확성점수=f"{score_info['clarity']}/15",
        총데이터포인트=total_data_points,
        총인사이트=total_insights,
        총팩트=total_facts,
        총정량데이터=total_quant,
    )
