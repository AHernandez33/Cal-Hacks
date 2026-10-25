"""Hosted agent roles. Credentials stay exclusively on the backend."""
import os

ROLES = (
    "coordinator", "crop_investigator", "leaf_analyst", "reference_retriever",
    "response_advisor", "trend_analyst", "privacy_reviewer", "telemetry_analyst", "visitor_guide",
)

def credentials(role="coordinator"):
    if role not in ROLES:
        raise ValueError("Unknown CREAO role.")
    prefix = "CREAO_" + role.upper()
    key = os.getenv(prefix + "_API_KEY", "").strip()
    app = os.getenv(prefix + "_APP_ID", "").strip()
    if os.getenv("CREAO_API_VERSION", "v1").strip() != "v1":
        from backend.creao_api import CreaoConfigurationError
        raise CreaoConfigurationError("CREAO_API_VERSION must be v1 for this adapter.")
    if role == "coordinator" and not key and not app:
        key = key or os.getenv("creao_api_key", "").strip()
        app = app or os.getenv("creao_app_id", "").strip()
    if not key or not app:
        from backend.creao_api import CreaoConfigurationError
        raise CreaoConfigurationError(f"Set {prefix}_API_KEY and {prefix}_APP_ID securely on the server.")
    if key.lower().startswith("bearer "):
        from backend.creao_api import CreaoConfigurationError
        raise CreaoConfigurationError("Store the CREAO key without the Bearer prefix.")
    return key, app

def configured_roles():
    result = []
    for role in ROLES:
        try:
            credentials(role)
            configured = True
        except RuntimeError:
            configured = False
        result.append({"role": role, "name": role.replace("_", " ").title(), "configured": configured})
    return result
