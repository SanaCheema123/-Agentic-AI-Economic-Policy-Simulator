import json

from backend.app.agents.query_agent import get_llm


SUMMARY_SYSTEM_PROMPT = """
You explain outputs from an economic policy scenario
simulation.

Strict rules:

1. Use only the numerical results supplied to you.
2. Never invent economic values.
3. Never claim that correlation proves causation.
4. Describe results as estimates, projections, or scenario
   differences.
5. Do not recommend whether a government should adopt or
   reject a policy.
6. Mention important weak validation results when present.
7. Keep the explanation concise and understandable.
8. If language is ar, respond in Arabic.
9. If language is en, respond in English.
"""


def generate_policy_summary(
    simulation_result: dict,
    language: str,
) -> str:

    llm = get_llm()

    payload = json.dumps(
        simulation_result,
        ensure_ascii=False,
    )

    prompt = f"""
Language: {language}

Explain the following model-generated scenario result.

Do not calculate new values.
Do not add external numbers.

SIMULATION RESULT:

{payload}
"""

    response = llm.invoke([
        (
            "system",
            SUMMARY_SYSTEM_PROMPT,
        ),
        (
            "human",
            prompt,
        ),
    ])

    return str(response.content).strip()
