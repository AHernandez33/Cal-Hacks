r"""Real Fetch.ai uAgent for public-reference crop investigations.

Run independently in Python 3.12 (FastAPI may remain on Python 3.14):
    py -3.12 -m venv .venv-fetch
    .\.venv-fetch\Scripts\python.exe -m pip install 'uagents>=0.25.5'
    .\.venv-fetch\Scripts\python.exe -m backend.fetch_agent

This agent supports both a structured uAgent request/response protocol and
Agent Chat Protocol messages for discovery/chat in the Fetch.ai ecosystem.
It uses ONLY public SQLite RAG passages. It is not a plant disease classifier,
LLM, or substitute for privacy authorization at the sending side.
"""

from __future__ import annotations

import os
from typing import Literal

from pydantic import Field
from uagents import Agent, Context, Model, Protocol
from uagents_core.registration import AgentRegistrationPolicy
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

from backend.RAG.retrieve import RAGRetrievalError, search_documents


class InvestigationRequest(Model):
    task: Literal["investigate_visible_discoloration", "summarize_public_references"]
    features: dict[str, float] | None = None
    anomaly_score: float | None = None
    crop_category: str | None = None


class EvidenceSource(Model):
    title: str
    url: str
    excerpt: str


class InvestigationResponse(Model):
    summary: str
    next_observations: list[str]
    citations: list[EvidenceSource]
    disclaimer: str


def _select_public_query(features: dict[str, float] | None) -> str:
    """Feature-derived general terms; never a disease identification."""
    if not features:
        return "plant leaf discoloration irrigation nutrient stress"
    expected = {
        "yellow_fraction",
        "brown_fraction",
        "mean_hue",
        "texture_variance",
        "edge_density",
    }
    if set(features) != expected:
        raise ValueError("The five required image features were not supplied.")
    for field, value in features.items():
        import math

        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
        ):
            raise ValueError("Invalid numerical observation.")
        minimum, maximum = (0, 179) if field == "mean_hue" else (0, 1)
        if not minimum <= value <= maximum:
            raise ValueError("Numerical observation outside the expected range.")
    if features["brown_fraction"] >= 0.10:
        return "leaf brown spots browning irrigation stress"
    if features["yellow_fraction"] >= 0.10:
        return "leaf yellowing nutrient irrigation stress"
    return "leaf health discoloration irrigation stress"


def _public_search(query: str) -> list[EvidenceSource]:
    try:
        matches = search_documents(query, limit=3)
    except RAGRetrievalError:
        return []  # An empty index is an honest missing-evidence outcome.
    return [
        EvidenceSource(
            title=item["title"],
            url=item["source_url"],
            excerpt=item["passage"][:500],
        )
        for item in matches
    ]


def build_public_report(
    features: dict[str, float] | None = None,
) -> InvestigationResponse:
    """Deterministic, non-diagnostic evidence summary using the public RAG DB."""
    query = _select_public_query(features)
    sources = _public_search(query)
    if features:
        summary = (
            "Received five numeric leaf observations. The system has not "
            "determined a disease, cause, or treatment. Public references "
            "are provided for further investigation."
        )
    else:
        summary = "Public agricultural guidance only; no private crop observations were supplied."
    if not sources:
        summary += " No matching vetted public passages were found in the local index."
    return InvestigationResponse(
        summary=summary,
        next_observations=[
            "Check which leaves were affected first (older or younger).",
            "Check leaf undersides and look for insects or distinct lesions.",
            "Review recent irrigation and environmental conditions locally.",
        ],
        citations=sources,
        disclaimer=(
            "Heuristic image features and keyword retrieval are not a validated "
            "disease diagnosis. Verify each reference before relying on it."
        ),
    )


class LocalRegistrationPolicy(AgentRegistrationPolicy):
    """Direct local messaging does not require public registry publication."""

    async def register(
        self, agent_identifier, identity, protocols, endpoints, metadata=None
    ):
        return None


def agent_seed() -> str:
    seed = os.getenv("FETCH_AGENT_SEED", "vigiloforge-local-seed-2026").strip()
    if len(seed) < 16:
        seed = (seed + "vigiloforge-local-seed-2026").strip()[:32]

    return seed


def create_agent() -> Agent:
    seed = agent_seed()

    mailbox = os.getenv("FETCH_MAILBOX", "false").strip().lower() == "true"
    agent = Agent(
        name="vigilo_public_crop_investigator",
        seed=seed,
        port=8001,
        endpoint=["http://127.0.0.1:8001/submit"],
        mailbox=mailbox,
        publish_agent_details=mailbox,
        registration_policy=None if mailbox else LocalRegistrationPolicy(),
        enable_agent_inspector=mailbox,
        report_events=mailbox,
        mark_inactive_on_shutdown=mailbox,
    )

    @agent.on_event("startup")
    async def on_start(ctx: Context) -> None:
        ctx.logger.info(f"VigiloForge Fetch agent started: {agent.address}")
        ctx.logger.info("Only public curated RAG passages will be queried.")

    @agent.on_message(model=InvestigationRequest, replies=InvestigationResponse)
    async def investigate(ctx: Context, sender: str, msg: InvestigationRequest) -> None:
        # Never log sender-supplied raw message contents or private observations.
        try:
            report = build_public_report(msg.features)
        except ValueError:
            report = InvestigationResponse(
                summary="Invalid or incomplete numerical observations.",
                next_observations=["Provide all five valid OpenCV features."],
                citations=[],
                disclaimer="No agricultural diagnosis has been produced.",
            )
        await ctx.send(sender, report)

    chat = Protocol(spec=chat_protocol_spec)

    @chat.on_message(ChatMessage)
    async def handle_chat(ctx: Context, sender: str, msg: ChatMessage) -> None:
        await ctx.send(
            sender,
            ChatAcknowledgement(acknowledged_msg_id=msg.msg_id),
        )
        # For unstructured public chat, ignore message contents to avoid
        # inadvertently copying farm records into logs or other services.
        # The fixed public query still invokes the real local RAG tool.
        report = build_public_report()
        sources = "\n".join(f"- {x.title}: {x.url}" for x in report.citations)
        answer = (
            f"{report.summary}\nNext observations: "
            + "; ".join(report.next_observations)
            + (f"\nPublic references:\n{sources}" if sources else "")
            + f"\n{report.disclaimer}"
        )
        await ctx.send(
            sender, ChatMessage(content=[TextContent(type="text", text=answer)])
        )

    @chat.on_message(ChatAcknowledgement)
    async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement) -> None:
        pass  # Acknowledgement only; never create a reply loop.

    agent.include(chat, publish_manifest=mailbox)
    return agent


if __name__ == "__main__":
    create_agent().run()
