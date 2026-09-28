from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.app.agents.query_agent import (
    parse_policy_query,
)
from backend.app.agents.summary_agent import (
    generate_policy_summary,
)
from backend.app.core.llm_config import (
    DEFAULT_END_YEAR,
    DEFAULT_START_YEAR,
)
from backend.app.services.scenario_simulator import (
    run_policy_scenario,
)


class EconomicAgentState(TypedDict, total=False):
    user_query: str
    parsed_query: dict[str, Any]
    simulation_result: dict[str, Any]
    summary: str


def understand_query(
    state: EconomicAgentState,
):
    parsed = parse_policy_query(
        state["user_query"]
    )

    return {
        "parsed_query": parsed.model_dump()
    }


def run_simulation(
    state: EconomicAgentState,
):
    query = state["parsed_query"]

    result = run_policy_scenario(
        country=query["country"],
        policy_variable=query["policy_variable"],
        change_percent=query["change_percent"],
        start_year=DEFAULT_START_YEAR,
        end_year=DEFAULT_END_YEAR,
        horizon=query["horizon"],
    )

    return {
        "simulation_result": result
    }


def explain_results(
    state: EconomicAgentState,
):
    language = state[
        "parsed_query"
    ]["language"]

    summary = generate_policy_summary(
        simulation_result=state[
            "simulation_result"
        ],
        language=language,
    )

    return {
        "summary": summary
    }


builder = StateGraph(
    EconomicAgentState
)

builder.add_node(
    "understand_query",
    understand_query,
)

builder.add_node(
    "run_simulation",
    run_simulation,
)

builder.add_node(
    "explain_results",
    explain_results,
)

builder.add_edge(
    START,
    "understand_query",
)

builder.add_edge(
    "understand_query",
    "run_simulation",
)

builder.add_edge(
    "run_simulation",
    "explain_results",
)

builder.add_edge(
    "explain_results",
    END,
)


economic_policy_graph = builder.compile()


def run_agent(
    user_query: str,
):
    return economic_policy_graph.invoke({
        "user_query": user_query
    })
