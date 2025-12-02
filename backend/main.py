# backend/main.py
import io
import os
import logging
import asyncio
import json
import re
from typing import Optional, Dict, Any, List

import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# load .env if present
load_dotenv()

# project imports (adjust if module path differs)
from .crew_builder import build_business_analytics_crew

# Optional Google GenAI (Gemini) SDK import — handled gracefully if not installed
try:
    from google import genai  # type: ignore
except Exception:
    genai = None

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="AI Business Analyst API")

# CORS for frontend dev (restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to your frontend origin(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeResponse(BaseModel):
    summary: str
    data_issues: str
    trends: str
    answer_to_question: str


def _extract_section(keyword: str, text: str, max_len: int = 1200) -> str:
    keyword_lower = keyword.lower()
    text_lower = text.lower()
    idx = text_lower.find(keyword_lower)
    if idx == -1:
        return ""
    return text[idx: idx + max_len]


# ---------------------------
# Gemini (Google) helper (robust)
# ---------------------------
def call_gemini_sync(prompt: str, model: str = "gemini-2.5-flash") -> Optional[str]:
    """
    Synchronous Gemini call helper using google-genai SDK.
    Returns text (raw response) or None on failure.
    """
    if genai is None:
        logger.warning("google-genai SDK not installed; Gemini fallback unavailable.")
        return None

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set; Gemini fallback unavailable.")
        return None

    try:
        client = genai.Client(api_key=api_key)

        # Minimal widely-compatible call signature:
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        # Most SDKs expose resp.text
        if hasattr(resp, "text") and resp.text:
            return resp.text

        # Some SDKs provide candidates or structured content
        if hasattr(resp, "candidates") and resp.candidates:
            first = resp.candidates[0]
            for attr in ("content", "message", "text"):
                if hasattr(first, attr):
                    val = getattr(first, attr)
                    if isinstance(val, (list, tuple)):
                        return " ".join(getattr(x, "text", str(x)) for x in val)
                    return str(val)
            return str(first)

        return str(resp)
    except TypeError as te:
        logger.exception("Gemini TypeError (signature mismatch): %s", te)
        return None
    except Exception as e:
        logger.exception("Gemini call failed: %s", e)
        return None


async def call_gemini(prompt: str, model: str = "gemini-2.5-flash") -> Optional[str]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: call_gemini_sync(prompt, model))


# ---------------------------
# Parse JSON safely from LLM text
# ---------------------------
def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Try to extract JSON object from arbitrary text. Returns dict or None.
    """
    if not text:
        return None
    # fast path: full string is valid JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # try to find first {...} block that parses
    # greedy capture of JSON-like substrings
    json_like = re.findall(r"\{(?:[^{}]|(?R))*\}", text, flags=re.DOTALL)
    for j in json_like:
        try:
            return json.loads(j)
        except Exception:
            continue

    # try bracketed lists (top-level array)
    array_like = re.findall(r"\[(?:[^\[\]]|(?R))*\]", text, flags=re.DOTALL)
    for a in array_like:
        try:
            parsed = json.loads(a)
            # if array of objects, return wrapped object
            if isinstance(parsed, list):
                return {"items": parsed}
        except Exception:
            continue

    return None


# ---------------------------
# Analyze endpoint
# ---------------------------
@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_data(
    file: UploadFile = File(...),
    question: str = Form("What are the most important insights from this data?"),
):
    """
    Upload a CSV/Excel file + optional business question.
    Returns AI-generated insights + simple chart data.
    """
    contents = await file.read()

    # read file safely and return 400 on failure
    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception:
        try:
            df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            logger.exception("Failed to read uploaded file")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to read file as CSV or Excel: {e}",
            )

    # Build crew (non-blocking call)
    try:
        crew = build_business_analytics_crew(df, question)
    except Exception as e:
        logger.exception("Failed to build analysis crew")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build analysis crew: {e}",
        )

    # Run the potentially-blocking crew.kickoff() in executor with a retry
    loop = asyncio.get_event_loop()

    def run_crew():
        return crew.kickoff()

    result = None
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        try:
            result = await loop.run_in_executor(None, run_crew)
            break
        except Exception as e:
            msg = str(e).lower()
            is_quota = (
                "insufficient_quota" in msg
                or ("quota" in msg and "exceed" in msg)
                or "rate limit" in msg
                or "ratelimit" in msg
                or "429" in msg
            )
            logger.exception("Crew attempt %d failed: %s", attempt, e)
            if not is_quota and attempt < max_attempts:
                await asyncio.sleep(1.5 ** attempt)
                continue
            result = None
            break

    # If crew succeeded normally:
    if result is not None:
        full_text = str(result)
        data_issues = _extract_section("clean", full_text) or _extract_section("data issue", full_text)
        trends = _extract_section("trend", full_text)
        question_answer = _extract_section("answer", full_text) or full_text[-1200:]
        return AnalyzeResponse(
            summary=full_text[:1200],
            data_issues=data_issues or "No specific data issues section found.",
            trends=trends or "No specific trends section found.",
            answer_to_question=question_answer
        )

    # ---------------------------
    # Fallback: OpenAI quota or persistent failure -> call Gemini with dataset context
    # ---------------------------
    logger.info("Crew failed or OpenAI quota detected; attempting Gemini fallback with dataset context.")

    # Build dataset context (larger head size requested)
    try:
        head_json = df.head(500).to_json(orient="records")  # increased head size (500 rows)
    except Exception:
        head_json = "Could not serialize head."

    try:
        # include numeric & categorical stats
        desc_json = df.describe(include="all", datetime_is_numeric=True).to_json()
    except Exception:
        desc_json = "Could not serialize describe."

    columns_list: List[str] = list(df.columns)

    # Strict JSON schema requested from Gemini
    # Chart schema: { "type": "bar"|"line"|"pie", "labels": [...], "values":[...], "title": "..." }
    fallback_prompt = f"""
You are a senior data analyst. You MUST analyze only the provided DATA CONTEXT and USER QUESTION.
Return ONLY a single valid JSON object (no markdown, no explanation) that exactly matches this schema:

{{
  "summary": "<short paragraph (string)>",
  "data_issues": ["<issue 1>", "<issue 2>", ...],         // list of strings
  "trends": ["<trend 1>", "<trend 2>", ...],              // list of strings
  "answer": "<direct answer to the user's question (string)>",
  
}}

Do NOT include any other keys. Do NOT include markdown, bullet characters, asterisks, or additional commentary.


### DATA CONTEXT (JSON)
DATA_HEAD (first 500 rows):
{head_json}

SUMMARY_STATS:
{desc_json}

COLUMNS:
{columns_list}

USER QUESTION:
{question}

TASK (be precise):
1) Using ONLY the DATA CONTEXT above, produce a concise "summary".
2) Identify specific "data_issues" (missing values, constant columns, anomalous zeros, type problems).
3) State concrete "trends" observed in the data (use numbers where applicable).
4) Answer the USER QUESTION directly.
5) Optionally include a small "chart" (type, labels, values) that best illustrates a key trend.

Return EXACTLY one JSON object. If you cannot compute some field, return null or empty list for that field.
"""

    gemini_text = await call_gemini(fallback_prompt)

    # Try parse JSON strictly, with some robustness
    parsed: Optional[Dict[str, Any]] = None
    if gemini_text:
        parsed = extract_json_from_text(gemini_text)

    if parsed:
        # Map parsed fields to AnalyzeResponse
        summary = parsed.get("summary", "") or ""
        data_issues_list = parsed.get("data_issues", []) or []
        trends_list = parsed.get("trends", []) or []
        answer_to_question = parsed.get("answer", "") or ""

        # Convert lists to readable strings for response fields
        data_issues_str = "\n".join(f"- {i}" for i in data_issues_list) if data_issues_list else "No specific data issues found."
        trends_str = "\n".join(f"- {t}" for t in trends_list) if trends_list else "No trends found."

        # If chart_obj is None, fallback to basic chart extraction from data
       
        return AnalyzeResponse(
            summary=summary,
            data_issues=data_issues_str,
            trends=trends_str,
            answer_to_question=answer_to_question
        )

    # If Gemini returned text but not JSON, attempt heuristic parsing:
    if gemini_text:
        # remove markdown bullets/stars and convert to clean text
        cleaned = re.sub(r"[*\u2022\-]+", "-", gemini_text)  # normalize bullets
        # attempt to extract headings (lenient)
        def get_block(h):
            m = re.search(rf"{h}[:\n]\s*(.+?)(?=\n[A-Z_]+[:\n]|$)", cleaned, flags=re.I | re.S)
            return m.group(1).strip() if m else ""

        summary = get_block("SUMMARY") or cleaned[:1200]
        data_issues = get_block("DATA_ISSUES") or "No specific data issues found."
        trends = get_block("TRENDS") or "No specific trends found."
        answer_to_question = get_block("ANSWER") or cleaned[-1200:]
        # fallback chart from dataframe
        return AnalyzeResponse(
            summary=summary,
            data_issues=data_issues,
            trends=trends,
            answer_to_question=answer_to_question
        )

    # If Gemini failed entirely, return 503
    logger.error("Both OpenAI and Gemini failed or returned no usable content.")
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="LLM providers unavailable (OpenAI quota + Gemini failed). Try again later.",
    )


@app.get("/")
def root():
    return {"message": "AI Business Analyst API is running"}

