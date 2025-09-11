import json
import os
from pathlib import Path

from app.logging import get_logger

from .models import SlideContent

logger = get_logger(__name__)


def _load_compiled_css() -> str:
    """Load compiled CSS file with all styles"""
    try:
        css_path = Path(__file__).parent.parent.parent / "assets" / "css" / "compiled" / "output.css"
        if css_path.exists():
            return css_path.read_text(encoding='utf-8')
        else:
            logger.warning(f"Compiled CSS file not found: {css_path}")
            # Fallback to CDN if compiled CSS is not available
            return ""
    except Exception as e:
        logger.error(f"Error loading compiled CSS file: {e}")
        return ""


def _get_persona_prefix(persona: str) -> str:
    """Get CSS prefix for persona"""
    persona_mapping = {
        "compact": "compact",
        "spacious": "spacious", 
        "balanced": "balanced"
    }
    return persona_mapping.get(persona, "balanced")


def _build_html_head(layout_preference: str, color_preference: str, persona_preference: str) -> str:
    """Build HTML head section with compiled CSS"""
    # Load compiled CSS that includes all Tailwind styles and our custom classes
    compiled_css = _load_compiled_css()
    
    # If compiled CSS is not available, fallback to CDN
    css_content = ""
    if compiled_css:
        css_content = compiled_css
    else:
        logger.warning("Using Tailwind CDN fallback - @apply directives may not work")
        css_content = ""
    
    head_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {"<script src='https://cdn.tailwindcss.com'></script>" if not compiled_css else ""}
    <style>
        /* Base styles */
        body {{ margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }}
        .slide-container {{ width: 100vw; height: 100vh; aspect-ratio: 16/9; }}
        
        /* Compiled Tailwind + Custom CSS */
        {css_content}
    </style>
</head>"""
    
    return head_content


def _combine_html_parts(head_content: str, body_content: str) -> str:
    """Combine head and body content into complete HTML"""
    # Extract body content (remove <body> and </body> tags if present)
    if body_content.strip().startswith('<body'):
        body_start = body_content.find('>') + 1
        body_end = body_content.rfind('</body>')
        if body_end == -1:
            body_end = len(body_content)
        body_inner = body_content[body_start:body_end].strip()
    else:
        body_inner = body_content.strip()
    
    return f"""{head_content}
<body class="w-full h-screen flex items-center justify-center bg-gray-100 overflow-hidden">
    {body_inner}
</body>
</html>"""


def _inject_tinymce_script(html: str) -> str:
    """Inject TinyMCE script before closing body tag"""
    tinymce_script = """
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
      toolbar: 'undo redo | bold italic underline | fontsize | forecolor | alignleft aligncenter alignright | bullist numlist | link removeformat',
      quickbars_selection_toolbar: 'bold italic underline | h2 h3 | forecolor',
      forced_root_block: false,

      // Enhanced undo/redo configuration
      custom_undo_redo_levels: 50,  // Keep 50 undo levels (micro versions)

      // Keyboard shortcuts (TinyMCE handles these automatically)
      // Ctrl+Z = undo, Ctrl+Y or Ctrl+Shift+Z = redo

      // Auto-save undo levels more frequently for better granularity
      setup: function(editor) {
        let saveTimer;

        // Add undo level after each significant change
        editor.on('input', function() {
          clearTimeout(saveTimer);
          saveTimer = setTimeout(function() {
            if (editor.undoManager && editor.undoManager.add) {
              editor.undoManager.add();
            }
          }, 1000); // Save undo level every 1 second of inactivity
        });

        // Add undo level when focus is lost (switching between elements)
        editor.on('blur', function() {
          if (editor.undoManager && editor.undoManager.add) {
            editor.undoManager.add();
          }
        });

        // Global keyboard shortcuts for undo/redo even outside editor focus
        document.addEventListener('keydown', function(e) {
          // Only handle if we're in the slide editing context
          if (document.querySelector('[data-editable]')) {
            if (e.ctrlKey || e.metaKey) { // Ctrl on Windows/Linux, Cmd on Mac
              if (e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                editor.undoManager.undo();
              } else if ((e.key === 'z' && e.shiftKey) || e.key === 'y') {
                e.preventDefault();
                editor.undoManager.redo();
              }
            }
          }
        });
      },

      // Tailwind/기존 클래스/속성 보존
      valid_elements: '*[*]',
      valid_styles: { '*': 'color,font-size,text-decoration' }
    });
  }

  // 4) 실행
  markEditable(document);
  initTiny();

  // 5) 저장 함수 (수동 호출용)
  window.saveEditedHtml = async function() {
    try {
      console.log('Starting save process...');

      // TinyMCE 편집 내용 적용 (안전한 방식)
      if (window.tinymce && window.tinymce.editors) {
        console.log('TinyMCE editors found:', window.tinymce.editors.length);
        for (let i = 0; i < window.tinymce.editors.length; i++) {
          const ed = window.tinymce.editors[i];
          if (ed && ed.undoManager && ed.undoManager.add) {
            ed.undoManager.add();
          }
        }
      } else {
        console.log('TinyMCE not available or no editors found');
      }

      // 페이지 전체 HTML 직렬화
      let html;
      try {
        html = '<!DOCTYPE html>\\n' + document.documentElement.outerHTML;
      } catch (htmlError) {
        console.error('HTML serialization failed:', htmlError);
        html = document.body.innerHTML; // fallback
      }

      // Extract deck_id and slide_order from URL or passed parameters
      const deckId = window.location.pathname.split('/')[2]; // Extract from /decks/{id}/preview
      const slideOrder = window.__currentSlideOrder || 1; // Set by frontend

      console.log('Saving with deckId:', deckId, 'slideOrder:', slideOrder);

      const response = await fetch(`/api/save?deck_id=\\${deckId}&slide_order=\\${slideOrder}`, {
        method: 'POST',
        headers: {'Content-Type': 'text/html;charset=utf-8'},
        body: html
      });

      if (response.ok) {
        console.log('Save successful');
        return { success: true, message: '저장 완료!' };
      } else {
        console.error('Save failed with status:', response.status);
        throw new Error('서버 저장 실패');
      }
    } catch (error) {
      console.error('Save error:', error);
      throw error;
    }
  };

  // 전역에서 호출할 수 있게 (호환성을 위한 alias)
  window.__saveEditedHtml = window.saveEditedHtml;
</script>"""

    if "</body>" in html:
        return html.replace("</body>", f"{tinymce_script}\n</body>")
    else:
        return html + tinymce_script


BODY_RENDER_PROMPT = """CRITICAL: CREATE HIGH-QUALITY PRESENTATION SLIDE USING PREDEFINED CSS CLASSES

You are a professional presentation designer. Create ONLY the body content for a single slide using predefined CSS classes to achieve modern, professional slide design.

MANDATORY RULES:
1. OUTPUT ONLY BODY CONTENT: Start with <body> and end with </body> - NO <!DOCTYPE>, <html>, or <head>
2. USE PREDEFINED CSS CLASSES: Focus on the enhanced block classes and layout-specific classes
3. CREATE PROFESSIONAL DESIGN: Use proper hierarchy, spacing, and visual elements
4. CONTENT OPTIMIZATION: Maximum 4 key points OR 3 paragraphs, concise and impactful
5. LAYOUT VARIETY: Choose from multiple layout patterns based on content type

ENHANCED CSS CLASSES AVAILABLE:

Core Structure:
- block-header, block-title, block-subtitle, block-content
- block-text, block-text-lg, block-text-emphasis
- block-list, block-list-item, block-list-bullet
- block-section, block-divider, block-card
- block-heading-xl, block-heading-lg, block-heading-md

Visual Enhancement:
- block-highlight, block-callout, block-accent
- block-stats, block-stats-number, block-stats-label
- {layout_preference}-hero, {layout_preference}-two-column
- {layout_preference}-icon-list, {layout_preference}-feature-grid

Layout Patterns:
- {layout_preference}-spacing, {layout_preference}-text
- {persona_prefix}-padding, {persona_prefix}-section
- {persona_prefix}-title, {persona_prefix}-body
- block-grid, block-grid-2, block-grid-3

Color & Theme:
- text-primary, text-secondary, bg-primary
- color-primary, color-secondary

SLIDE CONTENT CONTEXT:
Topic: {topic}
Audience: {audience} 
Theme: {theme}
Layout: {layout_preference}
Persona: {persona_preference}

{modification_context}

{editing_context}

LAYOUT PATTERN EXAMPLES:

1. HERO SLIDE (for introductions/key messages):
<body class="w-full h-screen flex items-center justify-center overflow-hidden">
    <div class="slide-container max-w-7xl mx-auto bg-white shadow-2xl flex items-center justify-center">
        <div class="block-content {persona_prefix}-padding">
            <div class="{layout_preference}-hero">
                <h1 class="block-heading-xl {persona_prefix}-title">Main Title</h1>
                <p class="block-text-lg text-secondary">Compelling subtitle or key message</p>
            </div>
        </div>
    </div>
</body>

2. CONTENT SLIDE (for detailed information):
<body class="w-full h-screen flex items-center justify-center overflow-hidden">
    <div class="slide-container max-w-7xl mx-auto bg-white shadow-2xl flex items-center justify-center">
        <div class="block-content {persona_prefix}-padding">
            <div class="block-header">
                <h1 class="block-title {persona_prefix}-title text-primary">Section Title</h1>
                <p class="block-subtitle text-secondary">Supporting subtitle</p>
            </div>
            <div class="block-section {persona_prefix}-section">
                <div class="block-callout">
                    <p class="block-text-emphasis">Key insight or important point</p>
                </div>
                <ul class="block-list">
                    <li class="block-list-item {persona_prefix}-body">
                        <div class="block-list-bullet"></div>
                        <span>First important point</span>
                    </li>
                    <li class="block-list-item {persona_prefix}-body">
                        <div class="block-list-bullet"></div>
                        <span>Second key insight</span>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</body>

3. TWO-COLUMN SLIDE (for comparisons/balanced content):
<body class="w-full h-screen flex items-center justify-center overflow-hidden">
    <div class="slide-container max-w-7xl mx-auto bg-white shadow-2xl flex items-center justify-center">
        <div class="block-content {persona_prefix}-padding">
            <div class="block-header">
                <h1 class="block-title {persona_prefix}-title text-primary">Comparison Title</h1>
            </div>
            <div class="{layout_preference}-two-column">
                <div class="block-card">
                    <h3 class="block-heading-md">Left Side</h3>
                    <p class="block-text">Content for left column</p>
                </div>
                <div class="block-card">
                    <h3 class="block-heading-md">Right Side</h3>
                    <p class="block-text">Content for right column</p>
                </div>
            </div>
        </div>
    </div>
</body>

4. STATS/METRICS SLIDE (for data presentation):
<body class="w-full h-screen flex items-center justify-center overflow-hidden">
    <div class="slide-container max-w-7xl mx-auto bg-white shadow-2xl flex items-center justify-center">
        <div class="block-content {persona_prefix}-padding">
            <div class="block-header">
                <h1 class="block-title {persona_prefix}-title text-primary">Key Metrics</h1>
            </div>
            <div class="block-grid block-grid-3">
                <div class="block-stats">
                    <div class="block-stats-number">95%</div>
                    <div class="block-stats-label">Success Rate</div>
                </div>
                <div class="block-stats">
                    <div class="block-stats-number">2.5x</div>
                    <div class="block-stats-label">Growth</div>
                </div>
                <div class="block-stats">
                    <div class="block-stats-number">500+</div>
                    <div class="block-stats-label">Customers</div>
                </div>
            </div>
        </div>
    </div>
</body>

INSTRUCTIONS:
1. Analyze the slide content and choose the most appropriate layout pattern
2. Use the enhanced CSS classes to create visually appealing, professional slides
3. Ensure content is concise, impactful, and well-structured
4. Apply proper typography hierarchy and spacing
5. Include visual elements like callouts, highlights, or stats when relevant

Create a slide that looks professional and modern, not basic or naive.
"""


def _extract_body_content(html_content: str, slide_title: str) -> str:
    """Extract and clean body content from LLM-generated HTML"""
    if not html_content or not html_content.strip():
        raise ValueError("Generated HTML content is empty.")
    
    content = html_content.strip()
    
    # If LLM generated complete HTML, extract just the body inner content
    if '<!doctype' in content.lower() or '<html' in content.lower():
        logger.info("Complete HTML detected, extracting body content", slide_title=slide_title)
        
        # Find body content
        body_start_tag = '<body'
        body_end_tag = '</body>'
        
        body_start_index = content.lower().find(body_start_tag)
        body_end_index = content.lower().find(body_end_tag)
        
        if body_start_index != -1 and body_end_index != -1:
            # Find the end of the opening body tag
            body_content_start = content.find('>', body_start_index) + 1
            
            # Extract just the inner body content
            body_inner_content = content[body_content_start:body_end_index].strip()
            
            logger.info("Successfully extracted body inner content", 
                       slide_title=slide_title, 
                       original_length=len(content),
                       extracted_length=len(body_inner_content))
            
            return body_inner_content
        else:
            logger.warning("Could not find body tags in complete HTML", slide_title=slide_title)
    
    # If content already looks like body content, clean it up
    if content.startswith('<body'):
        # Extract inner content from body tags
        body_start = content.find('>') + 1
        body_end = content.rfind('</body>')
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
        '<!doctype',
        '<html',
        '<head',
        '</head>',
        '</html>',
        '<meta',
        '<title',
        '<script src="https://cdn.tailwindcss.com"'
    ]
    
    cleaned_content = inner_content
    for forbidden in forbidden_elements:
        if forbidden in cleaned_content.lower():
            logger.warning(
                f"Removing forbidden element: {forbidden}",
                slide_title=slide_title
            )
            # More aggressive removal
            import re
            pattern = re.escape(forbidden) + r'[^>]*>'
            cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE)
    
    return cleaned_content.strip()


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
        logger.warning(
            "콘텐츠가 화면을 초과할 수 있습니다",
            slide_title=slide_title,
            indicators=overflow_indicators,
        )

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
        logger.warning(
            "슬라이드 요구사항 체크 실패",
            slide_title=slide_title,
            failed_checks=failed_checks,
        )

    logger.debug("슬라이드 콘텐츠 기본 검증 통과.", slide_title=slide_title)


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
        persona_prefix = _get_persona_prefix(persona_preference)

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
            "layout_preference": layout_preference,
            "color_preference": color_preference,
            "persona_preference": persona_preference,
            "persona_prefix": persona_prefix,
            "slide_json": json.dumps(slide_info, indent=2, ensure_ascii=False),
            "modification_context": modification_context,
            "editing_context": editing_context,
        }
        formatted_prompt = BODY_RENDER_PROMPT.format(**prompt_vars)

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
        body_content_result = await llm.generate_structured(formatted_prompt, schema=SlideContent)
        
        # Validate and sanitize body content
        body_content = _validate_body_content(body_content_result.html_content, slide_title)
        
        # Build complete HTML with predefined CSS
        head_content = _build_html_head(layout_preference, color_preference, persona_preference)
        complete_html = _combine_html_parts(head_content, body_content)
        
        # Create final content object
        content = SlideContent(html_content=complete_html)

        # Inject TinyMCE script if editing is enabled
        if enable_editing:
            content.html_content = _inject_tinymce_script(content.html_content)
            logger.info("TinyMCE 편집 스크립트 주입 완료", slide_title=slide_title)

        _validate_slide_content(content, slide_title)

        logger.info(
            f"슬라이드 {mode_text.lower()} 완료",
            slide_title=slide_title,
            html_length=len(content.html_content),
            step="content_generation_complete",
            is_modification=is_modification,
            preferences=f"layout:{layout_preference}, color:{color_preference}, persona:{persona_preference}"
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
