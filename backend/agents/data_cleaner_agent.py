# backend/agents/data_cleaner_agent.py

from crewai import Agent
from ..config import DEFAULT_MODEL


def create_data_cleaner_agent() -> Agent:
    return Agent(
        role="Data Cleaner",
        goal="Identify data quality issues and suggest how the data could be cleaned or pre-processed.",
        backstory=(
            "You are a data analyst expert in cleaning and preparing tabular business data "
            "for analysis, reporting, and dashboards."
        ),
        llm=DEFAULT_MODEL,
        verbose=True,
    )
