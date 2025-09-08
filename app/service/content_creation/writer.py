import json

from app.logging import get_logger
from .models import SlideContent

logger = get_logger(__name__)


RENDER_PROMPT = """IMPORTANT: You are creating a STATIC PRINT SLIDE. No scrolling, animations, or JavaScript allowed.

You are an HTML layout assistant. Create a single HTML slide that accurately reflects the slide content. Use 16:9 aspect ratio and ensure elements don't overlap. Use Tailwind CSS via CDN and avoid common, monotonous layouts.

Topic: {topic}
Audience: {audience} 
Theme: {theme}
Color preference: {color_preference}

{slide_json}

{modification_context}

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }}
        .slide-container {{ width: 100vw; height: 100vh; aspect-ratio: 16/9; }}
    </style>
</head>
<body class="w-full h-screen flex items-center justify-center bg-gray-100 overflow-hidden">
    <div class="slide-container max-w-7xl mx-auto bg-white shadow-2xl flex items-center justify-center">
        <!-- Your slide content here -->
    </div>
</body>
</html>

CRITICAL REQUIREMENTS:
- Output only complete HTML (no markdown, no explanations)
- 16:9 aspect ratio enforced
- NO element overlapping
- NO scrolling, NO animations, NO JavaScript
- NO VERTICAL OVERFLOW - use max-h-screen and h-screen
- text-2xl maximum
- Static print slide only
- Professional creative design"""


def _validate_slide_content(content: SlideContent, slide_title: str) -> None:
    """슬라이드 콘텐츠의 기본 품질을 검증합니다."""
    html = content.html_content

    if not html or not html.strip():
        logger.error("생성된 HTML 콘텐츠가 비어 있습니다.", slide_title=slide_title)
        raise ValueError("Generated HTML content is empty.")

    if '<script src="https://cdn.tailwindcss.com"></script>' not in html:
        logger.warning(
            "Tailwind CSS CDN 스크립트가 누락되었습니다.", slide_title=slide_title
        )

    if "</html>" not in html.lower():
        logger.warning(
            "완전한 HTML 문서가 아닙니다. `</html>` 태그가 없습니다.",
            slide_title=slide_title,
        )

    if len(html) < 200:
        logger.warning(
            "생성된 HTML이 너무 짧습니다.", slide_title=slide_title, length=len(html)
        )

    # Check for key requirements from simplified prompt
    requirement_checks = [
        ("16:9 aspect ratio", "aspect-ratio: 16/9" in html or "aspect-ratio:16/9" in html),
        ("overflow prevention", "overflow-hidden" in html),
        ("responsive height", any(h in html for h in ["h-screen", "max-h-screen", "h-full"])),
        ("text size limits", not any(large in html for large in ["text-3xl", "text-4xl", "text-5xl", "text-6xl"])),
        ("no animations", not any(anim in html.lower() for anim in ["@keyframes", "animation:", "transition:", "transform:"])),
        ("no custom scripts", html.count("<script") <= 1),  # Only Tailwind CDN allowed
    ]

    failed_checks = [check for check, passed in requirement_checks if not passed]
    if failed_checks:
        logger.warning(
            "슬라이드 요구사항 체크 실패",
            slide_title=slide_title,
            failed_checks=failed_checks,
        )

    logger.debug("슬라이드 콘텐츠 기본 검증 통과.", slide_title=slide_title)


async def write_content(slide_info: dict, deck_context: dict, llm, is_modification: bool = False, modification_prompt: str = "") -> SlideContent:
    """HTML 슬라이드 콘텐츠 생성 - 프롬프트 기반의 'from-scratch' 방식"""
    if not slide_info or not deck_context:
        raise ValueError("슬라이드 정보와 덱 컨텍스트는 필수입니다")

    slide_title = slide_info.get("slide_title", "Untitled Slide")
    mode_text = "Modification" if is_modification else "From-Scratch"
    logger.info(
        f"슬라이드 콘텐츠 생성 시작 ({mode_text})",
        slide_title=slide_title,
        layout_type=slide_info.get("layout_type", "content_slide"),
        is_modification=is_modification,
    )

    try:
        # 수정 컨텍스트 준비
        modification_context = ""
        if is_modification and modification_prompt:
            modification_context = f"""
## MODIFICATION REQUEST
The user wants to modify this existing slide with the following request:
"{modification_prompt}"

Please incorporate these changes while maintaining the overall structure and design consistency with the deck theme.
Focus on addressing the specific modification request while keeping the professional appearance.
"""

        prompt_vars = {
            "topic": deck_context.get("deck_title", ""),
            "audience": deck_context.get("audience", ""),
            "theme": deck_context.get("core_message", ""),
            "color_preference": deck_context.get("color_theme", "professional_blue"),
            "slide_json": json.dumps(slide_info, indent=2, ensure_ascii=False),
            "modification_context": modification_context,
        }
        formatted_prompt = RENDER_PROMPT.format(**prompt_vars)

        logger.debug(
            f"{mode_text} 프롬프트 준비 완료", prompt_length=len(formatted_prompt)
        )

        logger.info(
            "🤖 [WRITE_CONTENT] LLM 호출 시작",
            slide_title=slide_title,
            step="content_generation",
            prompt_length=len(formatted_prompt),
            is_modification=is_modification
        )
        content = await llm.generate_structured(formatted_prompt, schema=SlideContent)

        _validate_slide_content(content, slide_title)

        logger.info(
            f"슬라이드 {mode_text.lower()} 완료",
            slide_title=slide_title,
            html_length=len(content.html_content),
            step="content_generation_complete",
            is_modification=is_modification,
        )

        return content

    except Exception as e:
        logger.error(
            f"슬라이드 콘텐츠 {mode_text.lower()} 실패",
            error=str(e),
            slide_title=slide_title,
            is_modification=is_modification,
        )
        raise RuntimeError(f"슬라이드 콘텐츠 {'수정' if is_modification else '생성'}에 실패했습니다: {e}") from e