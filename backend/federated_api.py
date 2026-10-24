"""Local-only FastAPI router for an explicitly consented synthetic FL demo."""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from .federated import CLIENT_NAMES, run_demo

router = APIRouter(prefix="/federated", tags=["federated demo"])


class DemoRequest(BaseModel):
    # These switches ONLY authorize synthetic demo participants for this request.
    # They do not change the production privacy settings in backend/privacy.py.
    consent: dict[str, bool] = Field(default_factory=dict)
    rounds: int = Field(default=10, ge=1, le=20)
    local_epochs: int = Field(default=2, ge=1, le=3)
    samples_per_client: int = Field(default=120, ge=20, le=400)


@router.get("/status")
def status():
    return {
        "mode": "synthetic local simulation",
        "consent_default": False,
        "clients": list(CLIENT_NAMES),
        "privacy_integration": "This demo is isolated from real-user privacy settings",
    }


@router.post("/demo")
def demo(request: Request, payload: DemoRequest):
    # Do NOT expose a compute-intensive training demo as a public unauthenticated endpoint.
    # Reverse proxies can invalidate this assumption; do not deploy this router publicly.
    if request.client is None or request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(status_code=403, detail="Local demonstration only")
    if set(payload.consent) - set(CLIENT_NAMES):
        raise HTTPException(status_code=422, detail="Unknown demo client")
    try:
        return run_demo(
            consent=payload.consent,
            rounds=payload.rounds,
            local_epochs=payload.local_epochs,
            samples_per_client=payload.samples_per_client,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
