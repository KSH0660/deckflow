"""Custom metrics for DeckFlow monitoring."""

from prometheus_client import Counter, Gauge, Histogram

# Deck generation metrics
deck_generation_total = Counter(
    "deckflow_deck_generation_total",
    "Total number of deck generation requests",
    ["status"]
)

deck_generation_duration_seconds = Histogram(
    "deckflow_deck_generation_duration_seconds",
    "Time spent generating decks",
    buckets=[10, 30, 60, 120, 300, 600, 1200]  # 10s to 20min
)

active_deck_generations = Gauge(
    "deckflow_active_deck_generations",
    "Number of currently active deck generations"
)

slide_generation_total = Counter(
    "deckflow_slide_generation_total",
    "Total number of slides generated"
)

llm_requests_total = Counter(
    "deckflow_llm_requests_total",
    "Total LLM API requests",
    ["model", "status"]
)

llm_request_duration_seconds = Histogram(
    "deckflow_llm_request_duration_seconds",
    "LLM request duration",
    ["model"]
)
