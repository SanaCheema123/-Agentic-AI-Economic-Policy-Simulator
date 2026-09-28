import json
import re

from langchain_ollama import ChatOllama

from backend.app.core.llm_config import (
    LLM_TEMPERATURE,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from backend.app.schemas.agent import PolicyQuery


SYSTEM_PROMPT = """
You are the query-understanding component of an economic
policy simulation system.

Convert the user's English or Arabic request into structured
JSON.

Allowed policy_variable values are exactly:

investment
fdi
government_consumption
exports
imports
household_consumption

Rules:

1. country must be an ISO-3 country code.
Examples:
Saudi Arabia = SAU
Pakistan = PAK
United Arab Emirates = ARE
Qatar = QAT
United States = USA
United Kingdom = GBR

2. change_percent means a RELATIVE percentage change.

3. horizon must be an integer from 1 to 10 years.

4. language:
English = en
Arabic = ar

5. Do not invent a policy variable if the user did not
provide enough information.

6. Return JSON only.

Required structure:

{
  "country": "SAU",
  "policy_variable": "investment",
  "change_percent": 10,
  "horizon": 5,
  "language": "en"
}
"""


def get_llm():
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=LLM_TEMPERATURE,
    )


def _extract_json(text: str) -> dict:

    cleaned = text.strip()

    cleaned = re.sub(
        r"^```(?:json)?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"```$",
        "",
        cleaned,
    ).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(
        r"\{.*\}",
        cleaned,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError(
            "The local LLM did not return valid JSON."
        )

    return json.loads(match.group(0))


def parse_policy_query(
    user_query: str,
) -> PolicyQuery:

    if not user_query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    llm = get_llm()

    response = llm.invoke([
        (
            "system",
            SYSTEM_PROMPT,
        ),
        (
            "human",
            user_query,
        ),
    ])

    data = _extract_json(
        str(response.content)
    )

    return PolicyQuery.model_validate(data)
