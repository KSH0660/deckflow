import json

from app.logging import get_logger
from .models import SlideContent

logger = get_logger(__name__)


RENDER_PROMPT = """You are a presentation HTML layout assistant.
Produce a complete, self-contained HTML slide based on the provided context and data.
You MUST use Tailwind CSS via CDN (<script src="https://cdn.tailwindcss.com"></script>) and apply utility classes for all styling.
Your output should be only the HTML code. No Markdown or other text.

## Deck Context (for tone and consistency)
- Topic: {topic}
- Audience: {audience}
- Core Message: {theme}
- Color Preference: {color_preference}

## Slide JSON (Data to Render)
```json
{slide_json}
```

{modification_context}

## Guidelines
1.  **Output Format**: Your response MUST be a single, complete HTML document starting with `<!DOCTYPE html>`.
2.  **Tailwind CSS**: You MUST insert `<script src="https://cdn.tailwindcss.com"></script>` in the `<head>`.
3.  **Self-Contained**: The HTML must be self-contained. Do not use any external CSS or JS other than the Tailwind CDN.
4.  **Container Setup**: CRITICAL - Use this exact structure:
    - Body: `class="w-full h-screen flex items-center justify-center bg-gray-100 p-0 m-0 overflow-hidden"`
    - Main container: `class="w-full max-w-4xl h-full max-h-screen mx-auto bg-white shadow-lg rounded-lg overflow-hidden flex flex-col"`
    - Content area: `class="flex-1 p-6 overflow-hidden flex flex-col justify-center"`
5.  **HEIGHT CONSTRAINTS - MANDATORY**:
    - NEVER use fixed heights that exceed screen height
    - Use `h-screen`, `max-h-screen`, `h-full` for containers
    - Content must use `flex-1`, `space-y-2` (not space-y-4 or larger)
    - Text sizes: `text-sm` to `text-2xl` maximum (NO text-3xl or larger)
    - Padding: `p-2` to `p-6` maximum (NO p-8 or larger)
6.  **CONTENT FITTING STRATEGY**:
    - Limit bullet points to 3-4 maximum
    - Use compact text (`text-sm`, `text-base`)
    - Minimal spacing between elements (`space-y-1`, `space-y-2`)
    - If content is too much, summarize or truncate
7.  **Semantic HTML**: Use semantic elements like `<main>`, `<section>`, `<h1>`, `<p>`, `<ul>` for structure.
8.  **Styling**: Use Tailwind CSS utility classes extensively for ALL styling, including layout, spacing, typography, and colors.
9.  **Design**: The visual design must be professional, clean, and modern. It should clearly present all information from the Slide JSON.
10. **Visual Hierarchy**: Create a strong visual hierarchy. The `slide_title` should be prominent but not larger than `text-2xl`.
11. **Data Representation**: If the JSON contains lists (`key_points`, `data_points`, etc.), display them as clean, readable lists or grids with COMPACT spacing.
12. **Color**: The design should reflect the specified `color_preference` in the choice of Tailwind CSS classes (e.g., `bg-blue-700`, `text-gray-800`).
13. **No Placeholders**: The final HTML should contain the actual data from the JSON, not placeholders like `[[TITLE]]`.
14. **ABSOLUTE REQUIREMENT - NO VERTICAL OVERFLOW**:
    - ALL content MUST fit within screen height without scrolling
    - Use `overflow-hidden` on all containers
    - Test with shorter content if needed
    - Content that doesn't fit should be omitted, not overflowed
"""


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

    # Check for overflow prevention
    overflow_checks = [
        ("overflow-hidden 클래스", "overflow-hidden" in html),
        (
            "h-screen 또는 max-h-screen",
            any(h in html for h in ["h-screen", "max-h-screen", "h-full"]),
        ),
        ("적절한 flex 레이아웃", "flex" in html),
        (
            "너무 큰 텍스트 피하기",
            not any(
                large in html
                for large in ["text-3xl", "text-4xl", "text-5xl", "text-6xl"]
            ),
        ),
        (
            "과도한 패딩/마진 피하기",
            not any(
                large in html
                for large in ["p-8", "p-10", "p-12", "m-8", "m-10", "m-12"]
            ),
        ),
    ]

    failed_checks = [check for check, passed in overflow_checks if not passed]
    if failed_checks:
        logger.warning(
            "세로 오버플로우 방지 체크 실패",
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