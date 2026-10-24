"""VigiloForge SCD agent bridge - local evidence and optional CREAO runs.

NO RAW IMAGES OR HEATMAPS ARE ACCEPTED. No external data is sent unnless the caller
explicitly/consents to opt in. Fetch.ai is a separately running uAgent; this module
does not pretend that importing its Python code sends an agent message.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from backend.RAG.pipeline import build_context
from backend.privacy import authorize_external_payload


class AgentBridgeError(ValueError):
    """Invalid investigation input or unsupported agent mode."""


def investigate(
    *,
    features: Mapping[str, Any] | None = None,
    anomaly_score: float | None = None,
    crop_category: str | None = None,
    provider: Literal["local", "creao"] = "local",
    authorize_external: bool = False,
) -> dict[str, Any]:
    """Prepare local evidence, optionally initiate a real CREAO run.

    Input is *only* the five numeric observations returned by vision.py;
    never pass its complete response, image bytes, or heatmap_data_url.

    'local' works without credentials or the Fetch.ai SDK. 'creao' initiates
    an asynchronous remote run and returns its ID; poll via get_creao_result.
    """
    if provider not in {"local", "creao"}:
        raise AgentBridgeError("provider must be 'local' or 'creao'.")
    if provider == "local" and authorize_external:
        raise AgentBridgeError("authorize_external is only for external requests.")

    context = build_context(
        features=features,
        anomaly_score=anomaly_score,
        crop_category=crop_category,
    )
    if provider == "local":
        return {
            "provider": "local",
            "status": "evidence_ready",
            "search_query": context["search_query"],
            "evidence_count": context["evidence_count"],
            "citations": context["citations"],
            "disclaimer": context["disclaimer"],
            "external_request_sent": False,
        }

    if not authorize_external:
        # Enforce and audit an explicitly denied external request.
        authorize_external_payload(
            provider="creao",
            payload=context["agent_payload"],
            explicit_authorization=False,
        )

    # Import only when CREAO is actually requested, so local RAG requires no
    # httpx installation and doesn't depend on any external service.
    from backend.creao_api import start_investigation

    run = start_investigation(
        context["agent_payload"],
        explicit_authorization=authorize_external,
    )
    return {
        **run,
        "citations": context["citations"],
        "evidence_count": context["evidence_count"],
        "external_request_sent": True,
        "disclaimer": context["disclaimer"],
    }


def get_creao_result(run_id: str) -> dict:
    """Poll CREAO only after the API route has checked run ownership.

    This helper does not implement authentication/ownership itself and must
    not be exposed as a public endpoint without access controls.
    """
    from backend.creao_api import get_investigation
    return get_investigation(run_id)
