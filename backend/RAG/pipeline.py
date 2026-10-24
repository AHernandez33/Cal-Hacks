
"""Assemble local crop observations and retrieved PUBLIC reference passages.

This is evidence preparation, not LLM generation or a disease diagnosis.
It does not send data to CREAO, Fetch.ai, Snowflake, or any other network.
The agent bridge must require explicit authorization and invoke
`privacy.authorize_external_payload` before each outbound request.

Run a basic local test from the project root:
    python -m backend.RAG.pipeline
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections.abc import Mapping

from backend.privacy import LEAF_FEATURE_RANGES
from backend.RAG.retrieve import search_documents

MAX_REFERENCES = 5  # Matches privacy.py's public_references maximum.


class RAGPipelineError(ValueError):
    """Raised for invalid local observation inputs."""


def _validate_features(features: Mapping | None) -> dict[str, float] | None:
    if features is None:
        return None
    if not isinstance(features, Mapping) or set(features) != set(LEAF_FEATURE_RANGES):
        raise RAGPipelineError(
            "features must contain exactly yellow_fraction, brown_fraction, "
            "mean_hue, texture_variance, and edge_density."
        )

    cleaned = {}
    for name, (lower, upper) in LEAF_FEATURE_RANGES.items():
        value = features[name]
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or not lower <= value <= upper):
            raise RAGPipelineError(f"Invalid feature value: {name}")
        cleaned[name] = float(value)
    return cleaned


def _search_terms(features: dict[str, float] | None) -> str:
    """Generate broad search keywords; thresholds are heuristic, not diagnostic."""
    if features is None:
        return "plant leaf discoloration irrigation nutrient stress"

    if features["brown_fraction"] >= 0.10:
        return "leaf brown spots browning necrosis irrigation stress"
    if features["yellow_fraction"] >= 0.10:
        return "leaf yellowing chlorosis nutrient irrigation stress"
    return "plant leaf health discoloration irrigation stress"


def build_context(
    *,
    features: Mapping | None = None,
    anomaly_score: float | None = None,
    crop_category: str | None = None,
    query: str | None = None,
    limit: int = 5,
) -> dict:
    """Build cited public context and a minimized, NOT-YET-AUTHORIZED payload.

    Inputs:
      features: five numerical outputs from vision.analyze_image()['features'].
      anomaly_score: optional local heuristic index (0 to 1).
      crop_category: optional broad crop label, never a farm identifier.
      query: optional local search override; never included in agent_payload.
      limit: 1 to 5 retrieved references.

    Outputs include 'citations' for the frontend and 'agent_payload' for a
    future agent bridge. The payload is NOT permission to transmit anything.
    """
    clean_features = _validate_features(features)

    if anomaly_score is not None:
        if (isinstance(anomaly_score, bool)
                or not isinstance(anomaly_score, (int, float))
                or not math.isfinite(anomaly_score)
                or not 0 <= anomaly_score <= 1):
            raise RAGPipelineError("anomaly_score must be a number from 0 to 1.")

    if crop_category is not None:
        if (not isinstance(crop_category, str)
                or not re.fullmatch(r"[A-Za-z][A-Za-z -]{0,39}", crop_category)):
            raise RAGPipelineError("crop_category must be a broad alphabetic label.")

    if type(limit) is not int or not 1 <= limit <= MAX_REFERENCES:
        raise RAGPipelineError("limit must be an integer from 1 to 5.")

    search_query = query if query is not None else _search_terms(clean_features)
    matches = search_documents(search_query, limit=limit)

    citations = [
        {
            "document_id": match["document_id"],
            "title": match["title"],
            "url": match["source_url"],
            "excerpt": match["passage"],
            "chunk_index": match["chunk_index"],
        }
        for match in matches
    ]

    # The shape matches privacy.py's strict external-data allowlist.
    agent_payload: dict = {
        "task": (
            "investigate_visible_discoloration" if clean_features is not None
            else "summarize_public_references"
        ),
    }
    if clean_features is not None:
        agent_payload["features"] = clean_features
    if anomaly_score is not None:
        agent_payload["anomaly_score"] = float(anomaly_score)
    if crop_category is not None:
        agent_payload["crop_category"] = crop_category
    if citations:
        agent_payload["public_references"] = [
            {"title": item["title"], "url": item["url"], "excerpt": item["excerpt"]}
            for item in citations
        ]

    return {
        "search_query": search_query,
        "evidence_count": len(citations),
        "citations": citations,
        "agent_payload": agent_payload,
        "ready_for_authorization": bool(clean_features is not None or citations),
        "disclaimer": (
            "Public references are manually curated; source accuracy and usage "
            "rights must be checked. Image features and search keywords are "
            "not a validated plant disease diagnosis. No external request was made."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble local RAG evidence.")
    parser.add_argument("--query", default="leaf discoloration")
    args = parser.parse_args()
    result = build_context(query=args.query)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
