import json
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.schemas.insight import InsightAnalysis
from app.schemas.agent import AgentAnswer

SYSTEM_INSTRUCTION = """You are a competitive intelligence analyst interpreting verified scraped changes.
Use ONLY the supplied evidence. Clearly distinguish observed facts from interpretation.
Never invent prices, products, dates, competitors, URLs, features, statistics, customer behavior,
motives, or business facts. Do not use web browsing, search, or external knowledge. Describe motives
only as uncertainty (for example, 'may indicate'). If evidence is insufficient, say so explicitly.
Every major conclusion must be supported by the supplied diff and source URL."""

AGENT_SYSTEM_INSTRUCTION = """You answer competitive intelligence questions using ONLY the supplied
stored competitor context. The context is the source of truth. Do not browse, search, use tools, or
use external knowledge. Do not invent products, prices, dates, URLs, statistics, competitors, actions,
or customer information. If context is insufficient, state that clearly. Distinguish observed facts from
reasonable interpretation. Every factual claim should be supported by evidence, and every evidence URL
must be one of the source URLs in the supplied context."""


class LLMError(Exception):
    """Gemini could not produce a usable analysis."""


class LLMTimeoutError(LLMError):
    """Gemini did not answer within the configured transport timeout."""


class LLMClient:
    """Gemini-specific implementation behind a small injectable analysis interface."""

    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self.client = genai.Client(api_key=config.gemini_api_key) if config.gemini_api_key else None

    def analyze_change(self, evidence: dict[str, Any]) -> InsightAnalysis:
        return self._generate(evidence, SYSTEM_INSTRUCTION, InsightAnalysis)

    def answer_question(self, context: dict[str, Any], question: str) -> AgentAnswer:
        return self._generate({"question": question, "context": context}, AGENT_SYSTEM_INSTRUCTION, AgentAnswer)

    def _generate(self, contents: dict[str, Any], instruction: str, response_schema: type[Any]) -> Any:
        if self.client is None:
            raise LLMError("GEMINI_API_KEY is not configured")
        try:
            response = self.client.models.generate_content(
                model=self.config.gemini_model,
                contents=json.dumps(contents, ensure_ascii=False),
                config=types.GenerateContentConfig(
                    system_instruction=instruction,
                    temperature=0,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                ),
            )
        except TimeoutError as exc:
            raise LLMTimeoutError("Gemini analysis timed out") from exc
        except Exception as exc:
            raise LLMError("Gemini analysis request failed") from exc

        try:
            parsed = response.parsed
            if parsed is None:
                raise ValueError("Gemini returned no structured response")
            return response_schema.model_validate(parsed)
        except (ValidationError, ValueError, TypeError) as exc:
            raise LLMError("Gemini returned invalid structured insight output") from exc


def get_llm_client() -> LLMClient:
    return LLMClient()
