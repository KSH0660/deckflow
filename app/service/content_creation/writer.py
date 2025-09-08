import json

from app.logging import get_logger
from .models import SlideContent

logger = get_logger(__name__)


def _inject_tinymce_script(html: str) -> str:
    """Inject TinyMCE script before closing body tag"""
    tinymce_script = '''
<!-- TinyMCE Editor Scripts -->
<script src="https://cdn.jsdelivr.net/npm/tinymce@6.8.3/tinymce.min.js"></script>
<script>
  // 1) 편집 대상으로 삼을 요소(화이트리스트)
  const EDITABLE_SELECTOR = [
    'h1','h2','h3','h4','h5','h6',
    'p','li','blockquote','figcaption','small',
    'td','th','caption',
    // 필요 시 span에 .inline-edit 클래스로 opt-in
    'span.inline-edit'
  ].join(',');

  // 2) 텍스트가 실제로 있는 노드만 data-editable 부여
  function markEditable(root=document) {
    root.querySelectorAll(EDITABLE_SELECTOR).forEach(el => {
      const text = (el.textContent || '').trim();
      if (!text) return;
      if (el.closest('[data-noedit]')) return; // 상위에 noedit 달리면 제외
      el.setAttribute('data-editable', 'true');
      el.classList.add('editable'); // 스타일로 표시하고 싶으면 활용
    });
  }

  // 3) TinyMCE 인라인 에디터 초기화
  function initTiny() {
    tinymce.init({
      selector: '[data-editable]',
      inline: true,
      menubar: false,
      plugins: 'lists link quickbars',
      toolbar: 'bold italic underline | fontsize | forecolor | alignleft aligncenter alignright | bullist numlist | link removeformat',
      quickbars_selection_toolbar: 'bold italic underline | h2 h3 | forecolor',
      forced_root_block: false,
      // Tailwind/기존 클래스/속성 보존
      valid_elements: '*[*]',
      valid_styles: { '*': 'color,font-size,text-decoration' }
    });
  }

  // 4) 실행
  markEditable(document);
  initTiny();

  // 5) 저장(예: 페이지 전체 HTML 수집 → 서버 전송)
  async function saveEditedHtml() {
    // TinyMCE 편집 내용 적용(편집중 블러 처리 등)
    tinymce.editors.forEach(ed => ed.undoManager.add());
    // 페이지 전체 HTML 직렬화
    const html = '<!DOCTYPE html>\\n' + document.documentElement.outerHTML;
    await fetch('/api/save', {
      method: 'POST',
      headers: {'Content-Type': 'text/html;charset=utf-8'},
      body: html
    });
    alert('저장 완료!');
  }

  // 전역에서 호출할 수 있게
  window.__saveEditedHtml = saveEditedHtml;
</script>'''
    
    if '</body>' in html:
        return html.replace('</body>', f'{tinymce_script}\n</body>')
    else:
        return html + tinymce_script


RENDER_PROMPT = """CRITICAL: STATIC PRINT SLIDE - CONTENT MUST FIT ON ONE SCREEN

You are an HTML layout assistant. Create a single HTML slide using Tailwind CSS for {slide_json}. 

MANDATORY RULES - NEVER BREAK THESE:
1. CONTENT LENGTH: Maximum 4 bullet points OR 3 short paragraphs - IF MORE CONTENT EXISTS, SUMMARIZE OR CUT IT
2. NO VERTICAL OVERFLOW: Content must fit in 100vh - use h-screen, max-h-screen, overflow-hidden
3. NO LARGE SPACING: Only p-1 to p-6, m-1 to m-6, gap-1 to gap-6 - NEVER p-8+ or m-8+
4. NO FIXED HEIGHTS: Never use h-16, h-20, h-24+ etc - only h-screen, h-full, max-h-screen
5. TEXT SIZE LIMIT: Maximum text-2xl - NEVER text-3xl or larger
6. NO JAVASCRIPT: Only Tailwind CDN script allowed - NO onclick, addEventListener, custom scripts (TinyMCE editor scripts are allowed when editing mode is enabled)
7. NO ANIMATIONS: NO @keyframes, animation:, transition:, transform: - completely static
8. 16:9 ASPECT RATIO: Use aspect-ratio: 16/9 in CSS
9. IF CONTENT TOO LONG: Cut content, don't try to fit everything - slide must be readable

Topic: {topic} | Audience: {audience} | Theme: {theme} | Colors: {color_preference}

{modification_context}

{editing_context}

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

FINAL CHECK: Does content fit in one screen? If not, remove content until it does."""


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
    
    # Check for content that might cause overflow
    content_body = html[html.lower().find('<body'):html.lower().rfind('</body>') + 7] if '<body' in html.lower() else html
    
    # Count potential overflow indicators
    overflow_indicators = []
    
    # Count bullet points/list items
    list_items = content_body.count('<li') + content_body.count('•') + content_body.count('-')
    if list_items > 6:
        overflow_indicators.append(f"too many list items ({list_items})")
    
    # Count paragraphs
    paragraphs = content_body.count('<p>')
    if paragraphs > 4:
        overflow_indicators.append(f"too many paragraphs ({paragraphs})")
    
    # Check for very long text content (rough estimate)
    text_content = len([c for c in content_body if c.isalnum() or c.isspace()])
    if text_content > 800:  # Rough character limit for fitting on screen
        overflow_indicators.append(f"content too long (~{text_content} chars)")
    
    if overflow_indicators:
        logger.warning(
            "콘텐츠가 화면을 초과할 수 있습니다",
            slide_title=slide_title,
            indicators=overflow_indicators,
        )

    # Check for key requirements from simplified prompt
    requirement_checks = [
        ("16:9 aspect ratio", "aspect-ratio: 16/9" in html or "aspect-ratio:16/9" in html),
        ("overflow prevention", "overflow-hidden" in html),
        ("responsive height", any(h in html for h in ["h-screen", "max-h-screen", "h-full"])),
        ("text size limits", not any(large in html for large in ["text-3xl", "text-4xl", "text-5xl", "text-6xl"])),
        ("no animations", not any(anim in html.lower() for anim in ["@keyframes", "animation:", "transition:", "transform:"])),
        ("no custom scripts", html.count("<script") <= 3),  # Tailwind CDN + TinyMCE (2 scripts) allowed
    ]
    
    # Additional strict checks for vertical overflow prevention
    overflow_prevention_checks = [
        ("no fixed heights", not any(h in html for h in ["h-96", "h-80", "h-72", "h-64", "h-60", "h-56", "h-52", "h-48", "h-44", "h-40", "h-36", "h-32", "h-28", "h-24", "h-20", "h-16"])),
        ("no large padding", not any(p in html for p in ["p-12", "p-16", "p-20", "py-12", "py-16", "py-20", "pt-12", "pt-16", "pt-20", "pb-12", "pb-16", "pb-20"])),
        ("no large margins", not any(m in html for m in ["m-12", "m-16", "m-20", "my-12", "my-16", "my-20", "mt-12", "mt-16", "mt-20", "mb-12", "mb-16", "mb-20"])),
        ("no large gaps", not any(g in html for g in ["gap-12", "gap-16", "gap-20", "space-y-12", "space-y-16", "space-y-20"])),
    ]
    
    # Check for custom JavaScript content (beyond just script tags)
    script_content_checks = [
        ("no onclick handlers", "onclick=" not in html.lower()),
        ("no event listeners", not any(event in html.lower() for event in ["addeventlistener", "onload=", "onmouseover=", "onmouseout=", "onchange="])),
        ("no javascript urls", "javascript:" not in html.lower()),
    ]

    # Combine all checks
    all_checks = requirement_checks + overflow_prevention_checks + script_content_checks
    failed_checks = [check for check, passed in all_checks if not passed]
    
    if failed_checks:
        logger.warning(
            "슬라이드 요구사항 체크 실패",
            slide_title=slide_title,
            failed_checks=failed_checks,
        )

    logger.debug("슬라이드 콘텐츠 기본 검증 통과.", slide_title=slide_title)


async def write_content(slide_info: dict, deck_context: dict, llm, is_modification: bool = False, modification_prompt: str = "", enable_editing: bool = True) -> SlideContent:
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

        # 편집 컨텍스트 준비
        editing_context = ""
        if enable_editing:
            editing_context = """
## EDITOR MODE ENABLED
This slide will have TinyMCE inline editor injected after generation.
Editor scripts will be automatically added - focus on creating clean, semantic HTML structure.
"""

        prompt_vars = {
            "topic": deck_context.get("deck_title", ""),
            "audience": deck_context.get("audience", ""),
            "theme": deck_context.get("core_message", ""),
            "color_preference": deck_context.get("color_theme", "professional_blue"),
            "slide_json": json.dumps(slide_info, indent=2, ensure_ascii=False),
            "modification_context": modification_context,
            "editing_context": editing_context,
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

        # Inject TinyMCE script if editing is enabled
        if enable_editing:
            content.html_content = _inject_tinymce_script(content.html_content)
            logger.info(f"TinyMCE 편집 스크립트 주입 완료", slide_title=slide_title)

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