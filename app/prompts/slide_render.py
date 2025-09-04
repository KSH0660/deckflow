from langchain.prompts import PromptTemplate

RENDER_SYSTEM = (
    "You are a presentation HTML layout assistant. "
    "Choose the best template among the given candidates and produce a complete HTML for the slide. "
    'Use Tailwind CSS via CDN (<script src="https://cdn.tailwindcss.com"></script>) and apply utility classes appropriately. '
    "Replace any placeholders/comments from the chosen template with real content. No Markdown."
)
RENDER_PROMPT = PromptTemplate.from_template(
    "{system}\n"
    "Deck context (for tone/consistency): topic='{topic}', audience='{audience}', theme='{theme}', color_preference='{color_preference}'.\n\n"
    "Candidate Templates (ONLY these):\n{candidate_templates}\n\n"
    "Slide JSON:\n{slide_json}\n\n"
    "Guidelines:\n"
    '- Insert <script src="https://cdn.tailwindcss.com"></script> in <head>.\n'
    "- Keep it self-contained (no external CSS/JS besides Tailwind CDN).\n"
    "- Use semantic elements and Tailwind utility classes for spacing/typography/layout.\n"
    "- Replace placeholders like [[TITLE]] and commented sections (e.g., <!-- POINTS -->) with actual content.\n"
    "- If 'numbers' exist, render a neat key-value list or small metric grid.\n"
    "- The design should reflect the specified theme and color preferences in the choice of Tailwind CSS classes (e.g., colors, fonts, spacing).\n"
)
