import hashlib
import os
import random
import time

from pydantic import BaseModel

from app.logging import get_logger

logger = get_logger(__name__)


# 색상 테마별 색상 매핑
COLOR_THEME_MAPPING = {
    "professional_blue": {
        "primary": "#1e40af",  # blue-800
        "secondary": "#3b82f6",  # blue-500
        "accent": "#60a5fa",  # blue-400
        "background": "#ffffff",  # white
        "surface": "#f8fafc",  # slate-50
        "text_primary": "#1e293b",  # slate-800
        "text_secondary": "#64748b",  # slate-500
    },
    "corporate_gray": {
        "primary": "#374151",  # gray-700
        "secondary": "#6b7280",  # gray-500
        "accent": "#9ca3af",  # gray-400
        "background": "#ffffff",  # white
        "surface": "#f9fafb",  # gray-50
        "text_primary": "#111827",  # gray-900
        "text_secondary": "#6b7280",  # gray-500
    },
    "vibrant_purple": {
        "primary": "#7c3aed",  # violet-600
        "secondary": "#a855f7",  # purple-500
        "accent": "#c084fc",  # purple-400
        "background": "#ffffff",  # white
        "surface": "#faf5ff",  # purple-50
        "text_primary": "#581c87",  # purple-900
        "text_secondary": "#7c3aed",  # violet-600
    },
    "modern_teal": {
        "primary": "#0d9488",  # teal-600
        "secondary": "#14b8a6",  # teal-500
        "accent": "#5eead4",  # teal-300
        "background": "#ffffff",  # white
        "surface": "#f0fdfa",  # teal-50
        "text_primary": "#134e4a",  # teal-900
        "text_secondary": "#0f766e",  # teal-700
    },
    "energetic_orange": {
        "primary": "#ea580c",  # orange-600
        "secondary": "#fb923c",  # orange-400
        "accent": "#fed7aa",  # orange-200
        "background": "#ffffff",  # white
        "surface": "#fff7ed",  # orange-50
        "text_primary": "#9a3412",  # orange-800
        "text_secondary": "#ea580c",  # orange-600
    },
    "nature_green": {
        "primary": "#059669",  # emerald-600
        "secondary": "#10b981",  # emerald-500
        "accent": "#6ee7b7",  # emerald-300
        "background": "#ffffff",  # white
        "surface": "#ecfdf5",  # emerald-50
        "text_primary": "#064e3b",  # emerald-900
        "text_secondary": "#047857",  # emerald-700
    },
    "elegant_burgundy": {
        "primary": "#991b1b",  # red-800
        "secondary": "#dc2626",  # red-600
        "accent": "#fca5a5",  # red-300
        "background": "#ffffff",  # white
        "surface": "#fef2f2",  # red-50
        "text_primary": "#7f1d1d",  # red-900
        "text_secondary": "#991b1b",  # red-800
    },
    "tech_dark": {
        "primary": "#111827",  # gray-900
        "secondary": "#374151",  # gray-700
        "accent": "#06b6d4",  # cyan-500
        "background": "#000000",  # black
        "surface": "#1f2937",  # gray-800
        "text_primary": "#f9fafb",  # gray-50
        "text_secondary": "#d1d5db",  # gray-300
    },
    "warm_sunset": {
        "primary": "#f97316",  # orange-500
        "secondary": "#eab308",  # yellow-500
        "accent": "#f472b6",  # pink-400
        "background": "#ffffff",  # white
        "surface": "#fffbeb",  # amber-50
        "text_primary": "#92400e",  # amber-800
        "text_secondary": "#d97706",  # amber-600
    },
    "minimal_monochrome": {
        "primary": "#000000",  # black
        "secondary": "#374151",  # gray-700
        "accent": "#6b7280",  # gray-500
        "background": "#ffffff",  # white
        "surface": "#f9fafb",  # gray-50
        "text_primary": "#111827",  # gray-900
        "text_secondary": "#6b7280",  # gray-500
    },
}

# 레이아웃 타입별 asset 폴더 매핑
LAYOUT_TYPE_ASSET_MAPPING = {
    "title_slide": "title_slide",
    "content_slide": "content_slide",
    "comparison": "comparison",
    "data_visual": "data_visual",
    "process_flow": "process_flow",
    "feature_showcase": "feature_showcase",
    "testimonial": "testimonial",
    "call_to_action": "call_to_action",
}


def _get_template_examples(layout_type: str, max_templates: int = 3) -> list[str]:
    """레이아웃 타입에 맞는 템플릿 예제들을 가져옵니다"""
    asset_folder = LAYOUT_TYPE_ASSET_MAPPING.get(layout_type)
    if not asset_folder:
        logger.warning("알 수 없는 레이아웃 타입", layout_type=layout_type)
        return []

    # asset 폴더 경로 (프로젝트 루트에서)
    templates_path = os.path.join("asset", asset_folder)

    try:
        if not os.path.exists(templates_path):
            logger.warning("템플릿 폴더가 존재하지 않음", path=templates_path)
            return []

        # HTML 파일들 찾기
        html_files = [f for f in os.listdir(templates_path) if f.endswith(".html")]

        if not html_files:
            logger.warning("템플릿 HTML 파일을 찾을 수 없음", path=templates_path)
            return []

        # 최대 max_templates개까지 랜덤 선택
        selected_files = random.sample(html_files, min(len(html_files), max_templates))

        templates = []
        for file_name in selected_files:
            file_path = os.path.join(templates_path, file_name)
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                    templates.append(f"=== {file_name} ===\n{content}\n")
                    logger.debug(
                        "템플릿 로드 성공",
                        file_name=file_name,
                        content_length=len(content),
                    )
            except Exception as e:
                logger.warning(
                    "템플릿 파일 읽기 실패", file_name=file_name, error=str(e)
                )
                continue

        logger.info(
            "템플릿 예제 로드 완료",
            layout_type=layout_type,
            loaded_count=len(templates),
            available_count=len(html_files),
        )

        return templates

    except Exception as e:
        logger.error("템플릿 예제 로드 실패", layout_type=layout_type, error=str(e))
        return []


MASTER_WRITER_PROMPT = """
You are an expert presentation designer who creates stunning HTML slides using Tailwind CSS.

Create a complete HTML slide based on the provided information that matches the presentation theme and maintains visual consistency.

**Slide Information:**
- Slide Title: {slide_title}
- Message: {message}
- Layout Type: {layout_type}
- Key Points: {key_points}
- Data Points: {data_points}

**Presentation Context:**
- Deck Title: {deck_title}
- Audience: {audience}
- Core Message: {core_message}
- Goal: {goal}
- Color Theme: {color_theme}

**Color Theme: {color_theme}**
Create a cohesive color scheme that embodies the "{color_theme}" aesthetic. Choose colors that work harmoniously together and fit the theme's personality. Use your expertise to select appropriate colors for backgrounds, text, accents, and UI elements.

**Template Examples for {layout_type} Layout:**
{template_examples}

**HTML Requirements:**
1. Must include: <script src="https://cdn.tailwindcss.com"></script>
2. Must be 16:9 aspect ratio (use w-screen h-screen)
3. Prevent vertical overflow (use overflow-hidden)
4. Apply the specified color theme consistently (replace template colors with the provided palette)
5. Make content visually engaging and professional
6. Use the template examples as inspiration but create original content
7. Include placeholder variables like {{variable_name}} for dynamic content
8. Ensure responsive design within the 16:9 constraint

**Instructions:**
- Study the provided template examples to understand the layout structure and design patterns
- Create a new slide that follows similar layout principles but with your own creative interpretation
- Replace template placeholder content with the actual slide information provided
- Apply the specified color palette throughout the design
- Ensure the final result is polished, professional, and fits the presentation context
- Make it better than the templates while maintaining their structural excellence

Create a complete, ready-to-use HTML slide that surpasses the template quality.
"""


class SlideContent(BaseModel):
    html_content: str


async def write_content(slide_info: dict, deck_context: dict, llm) -> SlideContent:
    """HTML 슬라이드 콘텐츠 생성 - 장인정신으로 완벽한 슬라이드를 만들어냅니다"""
    if not slide_info or not deck_context:
        raise ValueError("슬라이드 정보와 덱 컨텍스트는 필수입니다")

    slide_number = slide_info.get("number", -1)
    slide_title = slide_info.get("slide_title", "Untitled Slide")
    layout_type = slide_info.get("layout_type", "content_slide")
    color_theme = deck_context.get("color_theme", "professional_blue")
    mapped_color_theme = COLOR_THEME_MAPPING.get(
        color_theme, COLOR_THEME_MAPPING["professional_blue"]
    )

    logger.info(
        "슬라이드 콘텐츠 생성 시작",
        number=slide_number,
        slide_title=slide_title,
        color_theme=color_theme,
        layout_type=layout_type,
        deck_title=deck_context.get("deck_title", "N/A")[:30],
    )

    try:
        # 템플릿 예제 가져오기 - 고퀄리티 참고자료로
        template_examples = _get_template_examples(layout_type, max_templates=3)
        template_examples_text = (
            "\n".join(template_examples)
            if template_examples
            else "No template examples available for this layout type."
        )

        prompt_vars = {
            **slide_info,  # 슬라이드 기본 정보
            **deck_context,  # 덱 컨텍스트
            "color_theme": mapped_color_theme,  # 색상 테마
            "template_examples": template_examples_text,  # 템플릿 예제
        }

        # 프롬프트 포맷팅 - 한 줄로 끝!
        formatted_prompt = MASTER_WRITER_PROMPT.format(**prompt_vars)

        # 프롬프트 해시 생성 (캐싱 디버깅용)
        prompt_hash = hashlib.md5(formatted_prompt.encode()).hexdigest()[:8]

        logger.debug(
            "프롬프트 준비 완료",
            prompt_length=len(formatted_prompt),
            prompt_hash=prompt_hash,
            variables_count=len(prompt_vars),
            template_count=len(template_examples),
            templates_total_length=len(template_examples_text),
            key_points_count=len(slide_info.get("key_points", [])),
            data_points_count=len(slide_info.get("data_points", [])),
        )

        # AI를 통한 HTML 생성 - 혼을 담아서 (캐싱 성능 측정)
        llm_start = time.time()
        content = await llm.generate_structured(formatted_prompt, schema=SlideContent)
        llm_end = time.time()
        llm_time = llm_end - llm_start

        # 캐싱 여부 추정 (0.5초 미만이면 캐시 히트로 추정)
        cache_hit_likely = llm_time < 0.5
        cache_status = "🚀 캐시 히트" if cache_hit_likely else "🐌 캐시 미스"

        # 품질 검증
        _validate_slide_content(content, slide_info, deck_context)

        logger.info(
            "슬라이드 콘텐츠 생성 완료",
            slide_number=slide_number,
            slide_title=slide_title,
            html_length=len(content.html_content),
            layout_type=layout_type,
            color_theme=color_theme,
            llm_time=f"{llm_time:.2f}초",
            cache_status=cache_status,
            prompt_hash=prompt_hash,
        )

        return content

    except Exception as e:
        logger.error(
            "슬라이드 콘텐츠 생성 실패",
            error=str(e),
            slide_title=slide_title,
            layout_type=layout_type,
        )
        raise RuntimeError(f"슬라이드 콘텐츠 생성에 실패했습니다: {e}") from e


def _validate_slide_content(
    content: SlideContent, slide_info: dict, deck_context: dict
) -> None:
    """생성된 슬라이드 콘텐츠의 품질을 검증합니다 - 장인의 눈으로"""
    html = content.html_content
    slide_title = slide_info.get("slide_title", "Unknown")

    # 필수 요소 검증
    required_elements = [
        '<script src="https://cdn.tailwindcss.com"></script>',
        "w-screen h-screen",
        "overflow-hidden",
    ]

    missing_elements = []
    for element in required_elements:
        if element not in html:
            missing_elements.append(element)

    if missing_elements:
        logger.warning(
            "슬라이드에 필수 요소 누락 발견",
            slide_title=slide_title,
            missing_elements=missing_elements,
        )

    # HTML 길이 검증
    if len(html) < 500:
        logger.warning(
            "슬라이드 HTML이 너무 짧음", slide_title=slide_title, html_length=len(html)
        )
    elif len(html) > 10000:
        logger.warning(
            "슬라이드 HTML이 너무 긺", slide_title=slide_title, html_length=len(html)
        )

    # 색상 테마 간단 검증 - LLM이 알아서 잘 했을 것 같지만 체크
    color_theme = deck_context.get("color_theme", "professional_blue")

    # 기본적인 색상 스타일링이 있는지만 확인
    has_colors = any(
        indicator in html
        for indicator in [
            "bg-",
            "text-",
            "border-",
            "from-",
            "to-",
            "#",
            "rgb",
            "gradient",
        ]
    )

    if not has_colors:
        logger.warning("색상 스타일링이 감지되지 않음", slide_title=slide_title)
    else:
        logger.debug(
            "색상 스타일링 확인됨", slide_title=slide_title, color_theme=color_theme
        )

    logger.debug(
        "슬라이드 콘텐츠 검증 완료",
        slide_title=slide_title,
        html_length=len(html),
        required_elements_present=len(required_elements) - len(missing_elements),
        total_required=len(required_elements),
    )


if __name__ == "__main__":
    import asyncio
    import time

    from app.adapter.llm.langchain import LangchainLLM
    from app.logging import configure_logging
    from app.service.module.plan_deck import ColorTheme, LayoutType

    configure_logging(level="DEBUG")

    async def main():
        """슬라이드 콘텐츠 생성 데모 - 장인의 혼을 담아서"""
        llm = LangchainLLM()

        # 테스트용 슬라이드 정보
        slide_info = {
            "slide_title": "혁신적인 AI 솔루션",
            "message": "AI가 만들어가는 새로운 미래를 경험해보세요",
            "layout_type": LayoutType.FEATURE_SHOWCASE.value,
            "key_points": [
                "자동화된 워크플로우로 생산성 300% 향상",
                "머신러닝 기반 예측으로 리스크 95% 감소",
                "직관적인 UI로 누구나 쉽게 사용 가능",
            ],
            "data_points": ["사용자 만족도 98%", "평균 도입 기간 2주", "ROI 450%"],
        }

        # 테스트용 덱 컨텍스트
        deck_context = {
            "deck_title": "AI 혁신 솔루션 발표",
            "audience": "기술 임원진 및 의사결정권자",
            "core_message": "AI로 비즈니스 혁신을 이루고 경쟁우위를 확보하세요",
            "goal": "persuade",
            "color_theme": ColorTheme.TECH_DARK.value,
        }

        try:
            logger.info("=== 슬라이드 콘텐츠 생성 데모 시작 ===")
            start_time = time.time()

            # 슬라이드 콘텐츠 생성 - 장인정신으로!
            content_start = time.time()
            content = await write_content(slide_info, deck_context, llm)
            content_end = time.time()
            content_generation_time = content_end - content_start

            logger.info("🎉 슬라이드 콘텐츠 생성 성공!")
            logger.info(f"⏱️  콘텐츠 생성 시간: {content_generation_time:.2f}초")
            logger.info(f"📏 생성된 HTML 길이: {len(content.html_content):,}자")
            logger.info(
                f"🚀 생성 속도: {len(content.html_content)/content_generation_time:.0f}자/초"
            )

            # 캐싱 정보 확인 (LLM이 빠르게 응답했다면 캐시 히트 가능성)
            cache_performance = (
                "🚀 캐시 히트 가능성 높음"
                if content_generation_time < 1.0
                else "🐌 새로운 생성으로 추정"
            )
            logger.info(f"🔄 캐시 상태: {cache_performance}")

            # 템플릿 로드 테스트
            template_start = time.time()
            test_templates = _get_template_examples(
                LayoutType.FEATURE_SHOWCASE.value, max_templates=2
            )
            template_end = time.time()
            template_load_time = template_end - template_start

            logger.info(
                f"📂 템플릿 로드: {len(test_templates)}개, 시간: {template_load_time:.3f}초"
            )

            # HTML이 필수 요소들을 포함하는지 확인
            validation_start = time.time()
            required_checks = [
                ("Tailwind CDN", "cdn.tailwindcss.com" in content.html_content),
                ("16:9 화면", "w-screen h-screen" in content.html_content),
                ("Overflow 방지", "overflow-hidden" in content.html_content),
                (
                    "색상 스타일링",
                    any(
                        indicator in content.html_content
                        for indicator in ["bg-", "text-", "#"]
                    ),
                ),
                (
                    "다크 테마",
                    any(
                        dark in content.html_content
                        for dark in ["bg-gray-900", "bg-black", "text-white"]
                    ),
                ),
            ]
            validation_end = time.time()
            validation_time = validation_end - validation_start

            logger.info("🔍 품질 체크 결과:")
            passed_count = 0
            for check_name, passed in required_checks:
                status = "✅ 통과" if passed else "❌ 실패"
                logger.info(f"  {check_name}: {status}")
                if passed:
                    passed_count += 1

            logger.info(
                f"📊 품질 점수: {passed_count}/{len(required_checks)} ({passed_count/len(required_checks)*100:.1f}%)"
            )
            logger.info(f"⏱️  검증 시간: {validation_time:.3f}초")

            # 생성된 HTML의 미리보기
            preview = (
                content.html_content[:300] + "..."
                if len(content.html_content) > 300
                else content.html_content
            )
            logger.info("📝 HTML 미리보기:")
            logger.info(preview)

            # 파일 저장
            file_start = time.time()
            output_file = "/tmp/generated_slide.html"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(content.html_content)
            file_end = time.time()
            file_save_time = file_end - file_start

            total_time = time.time() - start_time
            logger.info(f"💾 파일 저장: {output_file} ({file_save_time:.3f}초)")
            logger.info(f"🏁 총 실행시간: {total_time:.2f}초")

            # 시간 분석
            logger.info("=== 시간 분석 ===")
            logger.info(
                f"  콘텐츠 생성: {content_generation_time:.2f}초 ({content_generation_time/total_time*100:.1f}%)"
            )
            logger.info(
                f"  템플릿 로드: {template_load_time:.3f}초 ({template_load_time/total_time*100:.1f}%)"
            )
            logger.info(
                f"  품질 검증: {validation_time:.3f}초 ({validation_time/total_time*100:.1f}%)"
            )
            logger.info(
                f"  파일 저장: {file_save_time:.3f}초 ({file_save_time/total_time*100:.1f}%)"
            )

        except Exception as e:
            logger.error("데모 실행 실패", error=str(e))
            raise

    # 장인의 마음으로 실행
    asyncio.run(main())
