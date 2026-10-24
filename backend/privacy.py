
"""Backend-enforced privacy policy for VigiloForge Secured Crop Detective.

The collaborative-training switch defaults to OFF and is NOT permission for
Fetch.ai, CREAO, or Snowflake requests. Those requests need their own explicit
approval and must pass a restrictive outbound-data validator.

This module does not send network requests. Integrations must call
authorize_external_payload() immediately before sending anything.
"""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from copy import deepcopy
from urllib.parse import urlsplit

from backend import databases as database


class PrivacyViolation(PermissionError):
    """A security decision denied an operation."""

    def __init__(self, reason: str, blocked_fields: list[str] | None = None):
        self.reason = reason
        self.blocked_fields = blocked_fields or []
        super().__init__(reason)


EXTERNAL_PROVIDERS = frozenset({"creao", "fetch", "snowflake"})

ALLOWED_TOP_LEVEL = frozenset(
    {"task", "features", "anomaly_score", "crop_category", "public_references"}
)

ALLOWED_TASKS = frozenset(
    {"investigate_visible_discoloration", "summarize_public_references"}
)

LEAF_FEATURE_RANGES = {
    "yellow_fraction": (0.0, 1.0),
    "brown_fraction": (0.0, 1.0),
    "mean_hue": (0.0, 179.0),
    "texture_variance": (0.0, 1.0),
    "edge_density": (0.0, 1.0),
}

BLOCKED_NAMES = frozenset(
    {
        "image", "image_bytes", "raw_image", "image_data", "heatmap_data_url",
        "base64", "gps", "gps_coordinates", "latitude", "longitude", "lat",
        "lon", "lng", "coordinates", "precise_location", "address",
        "customer_id", "farmer_id", "farm_id", "farm_records",
        "proprietary_records", "filename", "file", "photo", "soil_telemetry",
    }
)


def get_settings() -> dict:
    return database.get_privacy_settings()


def update_settings(*, collaborative_training_enabled: bool) -> dict:
    """Change only federated-training preference, NOT LLM permissions."""
    return database.set_collaborative_training(collaborative_training_enabled)


def require_collaborative_training(*, action: str = "train") -> None:
    """Call before customer-data training and each federated update send.

    In-flight work needs cancellation and synchronization in federated.py.
    Switching OFF cannot undo contributions already aggregated.
    """
    if action not in {"train", "transmit_update"}:
        raise ValueError("Unsupported collaborative training action.")

    if not get_settings()["collaborative_training_enabled"]:
        database.record_security_event(
            event_type="collaborative_training",
            decision="blocked",
            destination="local" if action == "train" else "federated_server",
            reason="collaborative_training_disabled",
        )
        raise PrivacyViolation("collaborative_training_disabled")


def _field_names(payload: object) -> list[str]:
    if not isinstance(payload, Mapping):
        return []
    return [str(key) for key in payload.keys()]


def _reject(
    reason: str,
    *,
    provider: str,
    payload: object,
    blocked_fields: list[str] | None = None,
) -> None:
    database.record_security_event(
        event_type="external_data_request",
        decision="blocked",
        destination=provider,
        reason=reason,
        field_names=_field_names(payload),
    )
    raise PrivacyViolation(reason, blocked_fields)


def _all_nested_keys(value: object) -> set[str]:
    if isinstance(value, Mapping):
        result = {str(key).strip().lower() for key in value}
        for child in value.values():
            result.update(_all_nested_keys(child))
        return result

    if isinstance(value, (list, tuple)):
        result: set[str] = set()
        for child in value:
            result.update(_all_nested_keys(child))
        return result

    return set()


def _numeric(value: object, low: float, high: float) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (float, int))
        and math.isfinite(value)
        and low <= value <= high
    )


def _valid_public_references(value: object) -> bool:
    """References must originate from the curated PUBLIC RAG index.

    Shape checks cannot prove provenance: agent_bridge.py must supply only
    passages already verified as public during RAG ingestion.
    """
    if not isinstance(value, list) or len(value) > 5:
        return False

    for reference in value:
        if not isinstance(reference, Mapping):
            return False

        if set(reference) != {"title", "url", "excerpt"}:
            return False

        title = reference["title"]
        excerpt = reference["excerpt"]
        url = reference["url"]

        if not (
            isinstance(title, str) and 0 < len(title) <= 160
            and isinstance(excerpt, str) and 0 < len(excerpt) <= 800
            and isinstance(url, str) and 0 < len(url) <= 500
        ):
            return False

        try:
            parsed = urlsplit(url)
        except ValueError:
            return False

        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False

        if parsed.username or parsed.password:
            return False

    return True


def authorize_external_payload(
    *,
    provider: str,
    payload: Mapping,
    explicit_authorization: bool = False,
) -> dict:
    """Return a validated payload copy or raise PrivacyViolation.

    Restricts transfers to five numerical image features, an optional
    discoloration score, a broad crop category, a fixed task, and curated
    public reference passages. This is a guard, not a general DLP scanner.

    No HTTP call happens here. Caller must enforce this check immediately
    before each request to a provider.
    """
    if provider not in EXTERNAL_PROVIDERS:
        _reject("unapproved_destination", provider=str(provider), payload=payload)

    if not explicit_authorization:
        _reject("external_request_not_authorized", provider=provider, payload=payload)

    if not isinstance(payload, Mapping):
        _reject("invalid_payload", provider=provider, payload=payload)

    fields = _all_nested_keys(payload)
    restricted = sorted(fields.intersection(BLOCKED_NAMES))

    if restricted:
        _reject(
            "restricted_data_fields",
            provider=provider,
            payload=payload,
            blocked_fields=restricted,
        )

    if not set(payload).issubset(ALLOWED_TOP_LEVEL):
        _reject("unexpected_payload_fields", provider=provider, payload=payload)

    if payload.get("task") not in ALLOWED_TASKS:
        _reject("invalid_task", provider=provider, payload=payload)

    if "features" in payload:
        features = payload["features"]

        if not isinstance(features, Mapping) or set(features) != set(LEAF_FEATURE_RANGES):
            _reject("invalid_leaf_features", provider=provider, payload=payload)

        if any(
            not _numeric(features[name], *bounds)
            for name, bounds in LEAF_FEATURE_RANGES.items()
        ):
            _reject("invalid_leaf_features", provider=provider, payload=payload)

    if "anomaly_score" in payload and not _numeric(payload["anomaly_score"], 0, 1):
        _reject("invalid_anomaly_score", provider=provider, payload=payload)

    if "crop_category" in payload:
        crop = payload["crop_category"]

        if not isinstance(crop, str) or not re.fullmatch(r"[A-Za-z][A-Za-z -]{0,39}", crop):
            _reject("invalid_crop_category", provider=provider, payload=payload)

    if "public_references" in payload and not _valid_public_references(payload["public_references"]):
        _reject("invalid_public_references", provider=provider, payload=payload)

    if not ("features" in payload or "public_references" in payload):
        _reject("missing_observations_or_references", provider=provider, payload=payload)

    database.record_security_event(
        event_type="external_data_request",
        decision="allowed",
        destination=provider,
        reason="explicitly_authorized_minimized_payload",
        field_names=_field_names(payload),
    )

    return deepcopy(dict(payload))


def simulate_unauthorized_export() -> dict:
    """Demonstrate a blocked attempted export. Nothing is transmitted.

    Uses placeholder values; the audit stores only field names and labels.
    """
    attempted_payload = {
        "raw_image": "<local-test-only>",
        "gps_coordinates": "<local-test-only>",
    }

    try:
        authorize_external_payload(
            provider="creao",
            payload=attempted_payload,
            explicit_authorization=True,
        )
    except PrivacyViolation as exc:
        return {
            "blocked": True,
            "reason": exc.reason,
            "blocked_fields": exc.blocked_fields,
            "transmitted": False,
        }

    raise RuntimeError("Privacy simulation unexpectedly passed.")
