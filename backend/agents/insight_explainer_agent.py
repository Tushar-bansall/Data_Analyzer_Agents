# backend/agents/insight_explainer_agent.py

from crewai import Agent
from ..config import DEFAULT_MODEL


def create_insight_explainer_agent() -> Agent:
    return Agent(
        role="Insight Explainer",
        goal=(
            "Explain insights in very simple language, and suggest 3–5 actionable steps "
            "for the business."
        ),
        backstory=(
            "You specialize in translating complex analysis into clear, simple language "
            "for non-technical business stakeholders."
        ),
        llm=DEFAULT_MODEL,
        verbose=True,
    )
