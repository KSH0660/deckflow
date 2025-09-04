from langchain.prompts import PromptTemplate
 
PLANNER_SYSTEM = (
    "You are an expert presentation planner. "
    "Return a JSON object for a PPT plan following the provided schema. "
    "Include realistic numbers where relevant (can be estimates) and clear, concise slide bullets."
)
PLANNER_PROMPT = PromptTemplate.from_template(
    "{system}\n"
    "User request:\n{user_request}\n\n"
    "Rules:\n"
    "- 8~12 slides typical (adjust if user implies different).\n"
    "- Each slide must have: title, 3-6 key_points, numbers (if applicable), optional notes, optional section.\n"
    "- Audience-aware tone.\n"
    "- Output must be a JSON object that matches the target schema.\n"
)
