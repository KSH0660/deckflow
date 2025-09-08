from pydantic import BaseModel


class SlideContent(BaseModel):
    html_content: str


# Color theme mapping for content generation
COLOR_THEME_MAPPING = {
    "professional_blue": {
        "primary": "#1e40af",
        "secondary": "#3b82f6",
        "accent": "#60a5fa",
        "background": "#ffffff",
        "surface": "#f8fafc",
        "text_primary": "#1e293b",
        "text_secondary": "#64748b",
    },
    "corporate_gray": {
        "primary": "#374151",
        "secondary": "#6b7280",
        "accent": "#9ca3af",
        "background": "#ffffff",
        "surface": "#f9fafb",
        "text_primary": "#111827",
        "text_secondary": "#6b7280",
    },
    "vibrant_purple": {
        "primary": "#7c3aed",
        "secondary": "#a855f7",
        "accent": "#c084fc",
        "background": "#ffffff",
        "surface": "#faf5ff",
        "text_primary": "#581c87",
        "text_secondary": "#7c3aed",
    },
    "modern_teal": {
        "primary": "#0d9488",
        "secondary": "#14b8a6",
        "accent": "#5eead4",
        "background": "#ffffff",
        "surface": "#f0fdfa",
        "text_primary": "#134e4a",
        "text_secondary": "#0f766e",
    },
    "energetic_orange": {
        "primary": "#ea580c",
        "secondary": "#fb923c",
        "accent": "#fed7aa",
        "background": "#ffffff",
        "surface": "#fff7ed",
        "text_primary": "#9a3412",
        "text_secondary": "#ea580c",
    },
    "nature_green": {
        "primary": "#059669",
        "secondary": "#10b981",
        "accent": "#6ee7b7",
        "background": "#ffffff",
        "surface": "#ecfdf5",
        "text_primary": "#064e3b",
        "text_secondary": "#047857",
    },
    "elegant_burgundy": {
        "primary": "#991b1b",
        "secondary": "#dc2626",
        "accent": "#fca5a5",
        "background": "#ffffff",
        "surface": "#fef2f2",
        "text_primary": "#7f1d1d",
        "text_secondary": "#991b1b",
    },
    "tech_dark": {
        "primary": "#111827",
        "secondary": "#374151",
        "accent": "#06b6d4",
        "background": "#000000",
        "surface": "#1f2937",
        "text_primary": "#f9fafb",
        "text_secondary": "#d1d5db",
    },
    "warm_sunset": {
        "primary": "#f97316",
        "secondary": "#eab308",
        "accent": "#f472b6",
        "background": "#ffffff",
        "surface": "#fffbeb",
        "text_primary": "#92400e",
        "text_secondary": "#d97706",
    },
    "minimal_monochrome": {
        "primary": "#000000",
        "secondary": "#374151",
        "accent": "#6b7280",
        "background": "#ffffff",
        "surface": "#f9fafb",
        "text_primary": "#111827",
        "text_secondary": "#6b7280",
    },
}

# Layout type asset mapping
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