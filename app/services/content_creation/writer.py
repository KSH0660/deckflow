from pathlib import Path

from app.logging import get_logger

from .models import SlideContent

logger = get_logger(__name__)


def _load_bootstrap_css() -> str:
    """Load Bootstrap-based styles"""
    try:
        css_path = (
            Path(__file__).parent.parent.parent
            / "assets"
            / "bootstrap-styles.css"
        )
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")
        else:
            logger.warning(f"Bootstrap styles not found: {css_path}")
            return ""
    except Exception as e:
        logger.error(f"Error loading Bootstrap CSS file: {e}")
        return ""


def _get_persona_prefix(persona: str) -> str:
    """Get CSS prefix for persona"""
    persona_mapping = {
        "compact": "compact",
        "spacious": "spacious",
        "balanced": "balanced",
    }
    return persona_mapping.get(persona, "balanced")


def _build_html_head(
    layout_type: str,
    layout_preference: str,
    color_preference: str,
    persona_preference: str,
) -> str:
    """Build HTML head section with dynamic CSS injection"""
    from .css_builder import build_slide_css

    # Generate layout-specific CSS
    custom_css = build_slide_css(
        layout_type=layout_type,
        layout_preference=layout_preference,
        color_preference=color_preference,
        persona_preference=persona_preference,
    )

    head_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeckFlow Slide</title>

    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

    <!-- TinyMCE Editor -->
    <script src="https://cdn.jsdelivr.net/npm/tinymce@6.8.3/tinymce.min.js"></script>

    <!-- Dynamic Layout-Specific CSS -->
    <style>
{custom_css}
    </style>
</head>"""

    return head_content


def _combine_html_parts(head_content: str, body_content: str) -> str:
    """Combine head and body content into complete HTML"""
    # Extract body content (remove <body> and </body> tags if present)
    if body_content.strip().startswith("<body"):
        body_start = body_content.find(">") + 1
        body_end = body_content.rfind("</body>")
        if body_end == -1:
            body_end = len(body_content)
        body_inner = body_content[body_start:body_end].strip()
    else:
        body_inner = body_content.strip()

    return f"""{head_content}
<body class="d-flex align-items-center justify-content-center min-vh-100 bg-light overflow-hidden">
    {body_inner}
</body>
</html>"""


def _inject_tinymce_script(html: str) -> str:
    """Inject external TinyMCE editor script"""
    tinymce_script = """
<!-- TinyMCE Editor Script -->
<script src="/static/js/tinymce-editor.js"></script>"""

    if "</body>" in html:
        return html.replace("</body>", f"{tinymce_script}\n</body>")
    else:
        return html + tinymce_script


# The massive prompt has been replaced with modular layout-specific prompts
# See prompts.py for the new manageable prompt system


def _extract_body_content(html_content: str, slide_title: str) -> str:
    """Extract and clean body content from LLM-generated HTML"""
    if not html_content or not html_content.strip():
        raise ValueError("Generated HTML content is empty.")

    content = html_content.strip()

    # If LLM generated complete HTML, extract just the body inner content
    if "<!doctype" in content.lower() or "<html" in content.lower():
        logger.info(
            "Complete HTML detected, extracting body content", slide_title=slide_title
        )

        # Find body content
        body_start_tag = "<body"
        body_end_tag = "</body>"

        body_start_index = content.lower().find(body_start_tag)
        body_end_index = content.lower().find(body_end_tag)

        if body_start_index != -1 and body_end_index != -1:
            # Find the end of the opening body tag
            body_content_start = content.find(">", body_start_index) + 1

            # Extract just the inner body content
            body_inner_content = content[body_content_start:body_end_index].strip()

            logger.info(
                "Successfully extracted body inner content",
                slide_title=slide_title,
                original_length=len(content),
                extracted_length=len(body_inner_content),
            )

            return body_inner_content
        else:
            logger.warning(
                "Could not find body tags in complete HTML", slide_title=slide_title
            )

    # If content already looks like body content, clean it up
    if content.startswith("<body"):
        # Extract inner content from body tags
        body_start = content.find(">") + 1
        body_end = content.rfind("</body>")
        if body_end == -1:
            body_end = len(content)
        return content[body_start:body_end].strip()

    # If it's just inner content, return as-is
    return content


def _validate_body_content(body_content: str, slide_title: str) -> str:
    """Validate and sanitize body content to ensure it's only body HTML"""
    if not body_content or not body_content.strip():
        raise ValueError("Generated body content is empty.")

    # First extract the actual body content
    inner_content = _extract_body_content(body_content, slide_title)

    # Remove any remaining forbidden elements
    forbidden_elements = [
        "<!doctype",
        "<html",
        "<head",
        "</head>",
        "</html>",
        "<meta",
        "<title",
        '<script src="https://cdn.tailwindcss.com"',
        "tailwind",
    ]

    cleaned_content = inner_content
    for forbidden in forbidden_elements:
        if forbidden in cleaned_content.lower():
            logger.warning(
                f"Removing forbidden element: {forbidden}", slide_title=slide_title
            )
            # More aggressive removal
            import re

            pattern = re.escape(forbidden) + r"[^>]*>"
            cleaned_content = re.sub(pattern, "", cleaned_content, flags=re.IGNORECASE)

    return cleaned_content.strip()


def _validate_slide_content(content: SlideContent, slide_title: str) -> list[str]:
    """슬라이드 콘텐츠의 기본 품질을 검증하고 경고 목록을 반환합니다."""
    warnings = []
    html = content.html_content

    if not html or not html.strip():
        logger.error("생성된 HTML 콘텐츠가 비어 있습니다.", slide_title=slide_title)
        raise ValueError("Generated HTML content is empty.")

    if "bootstrap" not in html.lower():
        warnings.append("Bootstrap CSS가 누락되었습니다.")

    if "</html>" not in html.lower():
        warnings.append("완전한 HTML 문서가 아닙니다. `</html>` 태그가 없습니다.")

    if len(html) < 200:
        warnings.append(f"생성된 HTML이 너무 짧습니다. length={len(html)}")

    # Check for content that might cause overflow
    content_body = (
        html[html.lower().find("<body") : html.lower().rfind("</body>") + 7]
        if "<body" in html.lower()
        else html
    )

    # Count potential overflow indicators
    overflow_indicators = []

    # Count bullet points/list items
    list_items = (
        content_body.count("<li") + content_body.count("•") + content_body.count("-")
    )
    if list_items > 6:
        overflow_indicators.append(f"too many list items ({list_items})")

    # Count paragraphs
    paragraphs = content_body.count("<p>")
    if paragraphs > 4:
        overflow_indicators.append(f"too many paragraphs ({paragraphs})")

    # Check for very long text content (rough estimate)
    text_content = len([c for c in content_body if c.isalnum() or c.isspace()])
    if text_content > 800:  # Rough character limit for fitting on screen
        overflow_indicators.append(f"content too long (~{text_content} chars)")

    if overflow_indicators:
        warnings.append(f"콘텐츠가 화면을 초과할 수 있습니다: {overflow_indicators}")

    # Check for key requirements from simplified prompt
    requirement_checks = [
        (
            "16:9 aspect ratio",
            "aspect-ratio: 16/9" in html or "aspect-ratio:16/9" in html,
        ),
        ("overflow prevention", "overflow-hidden" in html),
        (
            "responsive height",
            any(h in html for h in ["h-screen", "max-h-screen", "h-full"]),
        ),
        (
            "text size limits",
            not any(
                large in html
                for large in ["text-3xl", "text-4xl", "text-5xl", "text-6xl"]
            ),
        ),
        (
            "no animations",
            not any(
                anim in html.lower()
                for anim in ["@keyframes", "animation:", "transition:", "transform:"]
            ),
        ),
        (
            "no custom scripts",
            html.count("<script") <= 3,
        ),  # Tailwind CDN + TinyMCE (2 scripts) allowed
    ]

    # Additional strict checks for vertical overflow prevention
    overflow_prevention_checks = [
        (
            "no fixed heights",
            not any(
                h in html
                for h in [
                    "h-96",
                    "h-80",
                    "h-72",
                    "h-64",
                    "h-60",
                    "h-56",
                    "h-52",
                    "h-48",
                    "h-44",
                    "h-40",
                    "h-36",
                    "h-32",
                    "h-28",
                    "h-24",
                    "h-20",
                    "h-16",
                ]
            ),
        ),
        (
            "no large padding",
            not any(
                p in html
                for p in [
                    "p-12",
                    "p-16",
                    "p-20",
                    "py-12",
                    "py-16",
                    "py-20",
                    "pt-12",
                    "pt-16",
                    "pt-20",
                    "pb-12",
                    "pb-16",
                    "pb-20",
                ]
            ),
        ),
        (
            "no large margins",
            not any(
                m in html
                for m in [
                    "m-12",
                    "m-16",
                    "m-20",
                    "my-12",
                    "my-16",
                    "my-20",
                    "mt-12",
                    "mt-16",
                    "mt-20",
                    "mb-12",
                    "mb-16",
                    "mb-20",
                ]
            ),
        ),
        (
            "no large gaps",
            not any(
                g in html
                for g in [
                    "gap-12",
                    "gap-16",
                    "gap-20",
                    "space-y-12",
                    "space-y-16",
                    "space-y-20",
                ]
            ),
        ),
    ]

    # Check for custom JavaScript content (beyond just script tags)
    script_content_checks = [
        ("no onclick handlers", "onclick=" not in html.lower()),
        (
            "no event listeners",
            not any(
                event in html.lower()
                for event in [
                    "addeventlistener",
                    "onload=",
                    "onmouseover=",
                    "onmouseout=",
                    "onchange=",
                ]
            ),
        ),
        ("no javascript urls", "javascript:" not in html.lower()),
    ]

    # Combine all checks
    all_checks = requirement_checks + overflow_prevention_checks + script_content_checks
    failed_checks = [check for check, passed in all_checks if not passed]

    if failed_checks:
        warnings.append(f"슬라이드 요구사항 체크 실패: {failed_checks}")

    for warning in warnings:
        logger.warning(warning, slide_title=slide_title)

    return warnings


async def write_content(
    slide_info: dict,
    deck_context: dict,
    llm,
    is_modification: bool = False,
    modification_prompt: str = "",
    enable_editing: bool = True,
) -> SlideContent:
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
        # Get preferences from deck context
        layout_preference = deck_context.get("layout_preference", "professional")
        color_preference = deck_context.get("color_preference", "professional_blue")
        persona_preference = deck_context.get("persona_preference", "balanced")
        _get_persona_prefix(persona_preference)

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

        # 편집 컨텍스트 준비
        editing_context = ""
        if enable_editing:
            editing_context = """
## EDITOR MODE ENABLED
This slide will have TinyMCE inline editor injected after generation.
Editor scripts will be automatically added - focus on creating clean, semantic HTML structure.
"""

        # Use the new modular prompt system
        from .prompts import get_layout_prompt

        layout_type = slide_info.get("layout_type", "content_slide")

        # Get layout-specific prompt
        formatted_prompt = get_layout_prompt(
            layout_type=layout_type,
            slide_data=slide_info,
            layout_preference=layout_preference,
            persona_preference=persona_preference,
        )

        # Add modification context if needed
        if modification_context:
            formatted_prompt += f"\n\nMODIFICATION REQUEST:\n{modification_context}"

        # Add editing context if needed
        if editing_context:
            formatted_prompt += f"\n\nEDITOR NOTES:\n{editing_context}"

        logger.debug(
            f"{mode_text} 프롬프트 준비 완료", prompt_length=len(formatted_prompt)
        )

        logger.info(
            "🤖 [WRITE_CONTENT] LLM 호출 시작 (Body-only generation)",
            slide_title=slide_title,
            step="content_generation",
            prompt_length=len(formatted_prompt),
            is_modification=is_modification,
        )

        # Generate body content only
        body_content_result = await llm.generate_structured(
            formatted_prompt, schema=SlideContent
        )

        # Validate and sanitize body content
        body_content = _validate_body_content(
            body_content_result.html_content, slide_title
        )

        # Build complete HTML with dynamic CSS
        head_content = _build_html_head(
            layout_type=layout_type,
            layout_preference=layout_preference,
            color_preference=color_preference,
            persona_preference=persona_preference,
        )
        complete_html = _combine_html_parts(head_content, body_content)

        # Create final content object
        content = SlideContent(html_content=complete_html)

        # Inject TinyMCE script if editing is enabled
        if enable_editing:
            content.html_content = _inject_tinymce_script(content.html_content)
            logger.info("TinyMCE 편집 스크립트 주입 완료", slide_title=slide_title)

        warnings = _validate_slide_content(content, slide_title)
        if warnings:
            logger.warning("Slide content validation warnings", warnings=warnings)

        logger.info(
            f"슬라이드 {mode_text.lower()} 완료",
            slide_title=slide_title,
            html_length=len(content.html_content),
            step="content_generation_complete",
            is_modification=is_modification,
            preferences=f"layout:{layout_preference}, color:{color_preference}, persona:{persona_preference}",
        )

        return content

    except Exception as e:
        logger.error(
            f"슬라이드 콘텐츠 {mode_text.lower()} 실패",
            error=str(e),
            slide_title=slide_title,
            is_modification=is_modification,
        )
        raise RuntimeError(
            f"슬라이드 콘텐츠 {'수정' if is_modification else '생성'}에 실패했습니다: {e}"
        ) from e
