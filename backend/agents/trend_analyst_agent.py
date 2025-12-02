# backend/agents/trend_analyst_agent.py

from crewai import Agent
from ..config import DEFAULT_MODEL


def create_trend_analyst_agent() -> Agent:
    return Agent(
        role="Trend Analyst",
        goal="Find key patterns, trends, and seasonality in business metrics.",
        backstory=(
            "You are a senior business analyst. You look at time-series or tabular business "
            "data and quickly find trends in sales, profit, regions, and products."
        ),
        llm=DEFAULT_MODEL,
        verbose=True,
    )
