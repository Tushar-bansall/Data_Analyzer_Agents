# backend/crew_builder.py

import pandas as pd
from crewai import Crew, Process

from .agents import (
    create_data_cleaner_agent,
    create_trend_analyst_agent,
    create_insight_explainer_agent,
    create_question_expert_agent,
)
from .tasks import (
    create_cleaning_task,
    create_trend_task,
    create_insight_task,
    create_question_task,
)


def build_data_context(df: pd.DataFrame) -> str:
    """
    Build a compact text representation of the uploaded data
    to pass into agents/tasks.
    """
    # Convert dataframe to a compact text form (only top rows + description)
    try:
        head_str = df.head(10).to_markdown()
    except Exception:
        # fallback: plain text table
        head_str = df.head(10).to_string()
    try:
        desc_str = df.describe(include="all", datetime_is_numeric=True).to_markdown()
    except TypeError:
        # pandas < 2.0 compatibility (no datetime_is_numeric)
        desc_str = df.describe(include="all").to_markdown()

    data_context = f"""
    Here is a sample of the uploaded business data (first 10 rows):

    {head_str}

    And here is a statistical/summary description:

    {desc_str}
    """
    return data_context


def build_business_analytics_crew(
    df: pd.DataFrame,
    question: str | None = None,
) -> Crew:
    """
    Build and return a CrewAI multi-agent system for business analytics.
    """

    if not question:
        question = (
            "Give overall important business insights from this data. "
            "Focus on sales, revenue, or performance trends if possible."
        )

    data_context = build_data_context(df)

    # ---------- Agents ----------
    data_cleaner_agent = create_data_cleaner_agent()
    trend_analyst_agent = create_trend_analyst_agent()
    insight_explainer_agent = create_insight_explainer_agent()
    question_expert_agent = create_question_expert_agent()

    # ---------- Tasks ----------
    cleaning_task = create_cleaning_task(data_context, data_cleaner_agent)
    trend_task = create_trend_task(data_context, trend_analyst_agent)
    insight_task = create_insight_task(insight_explainer_agent)
    question_task = create_question_task(question, question_expert_agent)

    crew = Crew(
        agents=[
            data_cleaner_agent,
            trend_analyst_agent,
            insight_explainer_agent,
            question_expert_agent,
        ],
        tasks=[cleaning_task, trend_task, insight_task, question_task],
        process=Process.sequential,
        verbose=True,
    )

    return crew
