# backend/agents/question_expert_agent.py

from crewai import Agent
from ..config import DEFAULT_MODEL


def create_question_expert_agent() -> Agent:
    return Agent(
        role="Business Question Expert",
        goal="Answer the user's specific business question using the uploaded data context.",
        backstory=(
            "You are a consultant who answers targeted business questions using analysis "
            "of provided data and trends."
        ),
        llm=DEFAULT_MODEL,
        verbose=True,
    )
