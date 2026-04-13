"""PII guardrails — before_model_callback and before_tool_callback for redaction."""

import re

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext

# Patterns ordered: SSN & CC before generic digits to avoid false positives
_PII_PATTERNS: list[tuple[str, str]] = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]"),
    (r"\b(?:4\d{12}(?:\d{3})?|5[1-5]\d{14}|3[47]\d{13})\b", "[CC_REDACTED]"),
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE_REDACTED]"),
]


def _redact_pii(text: str) -> str:
    for pattern, replacement in _PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def _has_pii(text: str) -> bool:
    return any(re.search(p, text) for p, _ in _PII_PATTERNS)


# ── Callbacks ───────────────────────────────────────────────────

def pii_before_model(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> LlmResponse | None:
    """Redact PII in the latest user message before it reaches the LLM."""
    if llm_request.contents:
        last_content = llm_request.contents[-1]
        if last_content.parts:
            for part in last_content.parts:
                if hasattr(part, "text") and part.text and _has_pii(part.text):
                    part.text = _redact_pii(part.text)
    return None  # proceed with (possibly redacted) request


def pii_before_tool(
    tool: BaseTool, args: dict, tool_context: ToolContext
) -> dict | None:
    """Redact PII from tool arguments before execution."""
    for key, value in args.items():
        if isinstance(value, str) and _has_pii(value):
            args[key] = _redact_pii(value)
    return None  # proceed with (possibly redacted) args
