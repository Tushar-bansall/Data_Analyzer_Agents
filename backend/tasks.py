# backend/tasks.py

from crewai import Task
from crewai import Agent


def create_cleaning_task(data_context: str, agent: Agent) -> Task:
    return Task(
        description=(
            "Analyze the provided data sample and description.\n\n"
            f"{data_context}\n\n"
            "Identify missing values, outliers, inconsistent types, or any other issues.\n"
            "Suggest how to clean or pre-process the data (but do NOT output code)."
        ),
        expected_output=(
            "A short text report listing data issues and recommended cleaning steps."
        ),
        agent=agent,
    )


def create_trend_task(data_context: str, agent: Agent) -> Task:
    return Task(
        description=(
            "Using the same data context, identify key business trends.\n\n"
            f"{data_context}\n\n"
            "If there is any date/time, look for trends over time. "
            "Otherwise, focus on top categories/products/regions."
        ),
        expected_output=(
            "A list of 3–7 important trends with short explanations for each."
        ),
        agent=agent,
    )


def create_insight_task(agent: Agent) -> Task:
    return Task(
        description=(
            "Combine the findings from the cleaning and trend tasks and translate them "
            "into simple language.\n\n"
            "Give:\n"
            "1) A short plain-English summary (4–8 bullet points)\n"
            "2) 3–5 actionable recommendations to improve the business."
        ),
        expected_output=(
            "Short, simple language insights and clear recommendations."
        ),
        agent=agent,
    )


def create_question_task(question: str, agent: Agent) -> Task:
    return Task(
        description=(
            f"Answer this user question about the data: '{question}'.\n\n"
            "Use the context of all previous tasks (cleaning, trends, insights) and the "
            "data sample. Be specific and practical."
        ),
        expected_output=(
            "A clear, direct answer to the user's question with supporting reasoning."
        ),
        agent=agent,
    )
