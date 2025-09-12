"""
Concise, manageable prompts for slide content generation.

This module provides layout-specific prompts that reference 
the dynamically injected CSS components.
"""

from typing import Dict, Union
from app.models.enums import (
    LayoutType, 
    LayoutPreference,
    PersonaPreference,
    validate_layout_type,
    validate_layout_preference,
    validate_persona_preference
)

# Layout-specific body generation prompts
LAYOUT_PROMPTS: Dict[LayoutType, str] = {
    LayoutType.TITLE_SLIDE: """Create a title slide using the title-hero CSS component.

STRUCTURE:
```html
<div class="slide-container {layout_preference}">
    <div class="title-hero">
        <h1>{{main_title}}</h1>
        <p>{{subtitle}}</p>
    </div>
</div>
```

CONTENT GUIDELINES:
- Main title: Powerful, concise (max 8 words)
- Subtitle: Compelling supporting message (max 15 words)
- Use the provided slide data for content

SLIDE DATA: {slide_data}""",

    LayoutType.CONTENT_SLIDE: """Create a content slide using the content-layout CSS components.

STRUCTURE:
```html
<div class="slide-container {layout_preference}">
    <div class="content-layout">
        <div class="content-header">
            <h1>{{title}}</h1>
            <p>{{subtitle}}</p>
        </div>
        <div class="content-body {persona_preference}-spacing">
            <div class="content-callout">
                <p>{{key_insight}}</p>
            </div>
            <ul class="content-list">
                <li class="content-list-item">
                    <div class="content-list-bullet"></div>
                    <span>{{point_1}}</span>
                </li>
                <!-- Add 2-4 more points -->
            </ul>
        </div>
    </div>
</div>
```

CONTENT GUIDELINES:
- Max 4 bullet points
- Include 1 key callout/insight
- Keep text concise and impactful

SLIDE DATA: {slide_data}""",

    LayoutType.COMPARISON: """Create a comparison slide using the comparison-grid CSS components.

STRUCTURE:
```html
<div class="slide-container {layout_preference}">
    <div class="comparison-layout">
        <div class="comparison-header">
            <h1>{{title}}</h1>
        </div>
        <div class="comparison-grid">
            <div class="comparison-card left">
                <h2>{{left_title}}</h2>
                <div class="content">{{left_content}}</div>
            </div>
            <div class="comparison-card right">
                <h2>{{right_title}}</h2>
                <div class="content">{{right_content}}</div>
            </div>
        </div>
    </div>
</div>
```

CONTENT GUIDELINES:
- Clear comparison titles
- Balanced content on both sides
- Focus on key differences

SLIDE DATA: {slide_data}""",

    LayoutType.FEATURE_SHOWCASE: """Create a feature showcase using the feature-grid CSS components.

STRUCTURE:
```html
<div class="slide-container {layout_preference}">
    <div class="feature-layout">
        <div class="feature-header">
            <h1>{{title}}</h1>
        </div>
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">{{icon_1}}</div>
                <h3>{{feature_1_title}}</h3>
                <p>{{feature_1_desc}}</p>
            </div>
            <!-- Repeat for 2 more features -->
        </div>
    </div>
</div>
```

CONTENT GUIDELINES:
- 3 features maximum
- Use emoji icons (🚀, ⚡, 🎯, etc.)
- Keep descriptions brief

SLIDE DATA: {slide_data}""",

    LayoutType.CALL_TO_ACTION: """Create a call-to-action slide using the cta-layout CSS components.

STRUCTURE:
```html
<div class="slide-container {layout_preference}">
    <div class="cta-layout">
        <div class="cta-content {persona_preference}-text">
            <h1>{{headline}}</h1>
            <p>{{supporting_message}}</p>
            <button class="cta-button">{{action_text}}</button>
        </div>
    </div>
</div>
```

CONTENT GUIDELINES:
- Compelling headline (max 6 words)
- Clear supporting message
- Action-oriented button text

SLIDE DATA: {slide_data}""",
}

# Default fallback prompt for unknown layout types
DEFAULT_LAYOUT_PROMPT = """Create slide content using Bootstrap and available CSS classes.

AVAILABLE COMPONENTS:
- slide-container: Main slide wrapper
- content-layout: Flexible content structure  
- content-header: Section headers
- content-list: Bulleted lists
- content-callout: Highlighted text boxes

GUIDELINES:
- Keep content concise (max 4 points)
- Use semantic HTML structure
- Apply {persona_preference} spacing classes

SLIDE DATA: {slide_data}"""


def get_layout_prompt(
    layout_type: Union[LayoutType, str],
    slide_data: dict,
    layout_preference: Union[LayoutPreference, str] = LayoutPreference.PROFESSIONAL,
    persona_preference: Union[PersonaPreference, str] = PersonaPreference.BALANCED
) -> str:
    """
    Get the appropriate prompt for a layout type
    
    Args:
        layout_type: The slide layout type
        slide_data: Slide information from deck planning
        layout_preference: User's layout preference
        persona_preference: User's persona preference
        
    Returns:
        Formatted prompt string ready for LLM
    """
    # Validate and convert to enums
    if isinstance(layout_type, str):
        layout_type = validate_layout_type(layout_type)
    if isinstance(layout_preference, str):
        layout_preference = validate_layout_preference(layout_preference)
    if isinstance(persona_preference, str):
        persona_preference = validate_persona_preference(persona_preference)
    
    # Get the appropriate prompt template
    prompt_template = LAYOUT_PROMPTS.get(layout_type, DEFAULT_LAYOUT_PROMPT)
    
    # Format with provided data
    return prompt_template.format(
        slide_data=slide_data,
        layout_preference=layout_preference.value,
        persona_preference=persona_preference.value
    )


def get_available_layouts() -> list[LayoutType]:
    """Get list of available layout prompt types"""
    return list(LAYOUT_PROMPTS.keys())