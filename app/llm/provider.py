"""Chat model abstraction.

get_chat_model() returns a LangChain BaseChatModel. Which concrete class
comes back depends entirely on app.config.settings -- callers (the agent
graph, the routers) never branch on demo-vs-real themselves, they just
call .invoke(...) or .with_structured_output(...) like any LangChain
model. That is the whole point: swapping demo mode for a real key is a
config change, not a code change.
"""

from __future__ import annotations

import re
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from app.config import settings

_TIER_LINE = re.compile(r"\btier[:=]\s*(\w+)", re.IGNORECASE)


class MockChatModel(BaseChatModel):
    """A deterministic, zero-cost stand-in for a real chat LLM.

    It implements just enough of BaseChatModel to be a drop-in replacement
    for ChatOpenAI / ChatAnthropic anywhere in the graph, including
    .with_structured_output(...) (see RouteDecision usage in
    app/agent/router.py, which we bypass in demo mode with a keyword
    heuristic instead of relying on this).

    Rather than trying to "reason", it does something more honest for a
    demo: it looks at the structured tool findings already computed
    upstream (SQL rows, Mongo documents, Oracle loyalty numbers, RAG
    passages) and phrases them into a readable sentence. All of the actual
    lookup logic lives in the deterministic tools -- exactly the
    plan-then-execute split used in the Insight project, applied here to
    an agent instead of a chart spec.
    """

    @property
    def _llm_type(self) -> str:
        return "mock-chat-model"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = "\n".join(str(m.content) for m in messages)
        text = _synthesize_from_prompt(prompt)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])


def _synthesize_from_prompt(prompt: str) -> str:
    """Turn the synthesize-node prompt (question + labelled tool findings)
    into a short natural-language answer, without any real language model.
    """
    findings = re.findall(r"\[(\w+)\]\s*(.+?)(?=\n\[\w+\]|\Z)", prompt, re.DOTALL)
    if not findings:
        return (
            "I could not find any relevant information for this question in the "
            "connected data sources. Could you rephrase it or provide an order or "
            "customer id?"
        )

    parts: list[str] = []
    for _source, content in findings:
        content = content.strip()
        if not content or content.lower().startswith("no result") or content.lower().startswith("error"):
            continue
        parts.append(content)

    if not parts:
        return (
            "I looked into this but did not find matching data. Could you double-check "
            "the order id or customer id you gave me?"
        )

    return " ".join(parts)


def get_chat_model() -> BaseChatModel:
    if settings.llm_provider == "openai" and settings.openai_api_key:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=settings.anthropic_model, api_key=settings.anthropic_api_key, temperature=0)
    return MockChatModel()
