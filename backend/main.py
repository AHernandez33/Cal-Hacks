"""VigiloForge API with pseudonymous workspace preferences and local demonstrations."""

from __future__ import annotations
import asyncio
import os
from typing import Literal
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, StrictBool
from backend import __version__, databases, privacy
from backend.access import require_access
from backend.vision import MAX_IMAGE_BYTES, VisionAnalysisError, analyze_image
from backend.RAG.retrieve import RAGRetrievalError, search_documents
from backend.creao_api import CreaoAPIError, CreaoConfigurationError, get_investigation
from backend.fetch_service import request_fetch_evidence
from backend.federated_api import router as federated_router
from backend.orchestration.coordinator import coordinate
from backend.orchestration.permissions import require_sync
from backend.orchestration.schemas import InvestigationRequest
from backend.tigerdata import TelemetryUnavailable, history

app = FastAPI(
    title="VigiloForge Secured Crop Detector",
    version=__version__,
    dependencies=[Depends(require_access)],
)
from backend.accounts import router as account_router

app.include_router(federated_router)
app.include_router(account_router)
from backend.report_email import router as report_email_router
app.include_router(report_email_router)
from backend.verified_report import router as verified_report_router
app.include_router(verified_report_router)
origins = [
    x.strip()
    for x in os.getenv(
        "FRONTEND_ORIGIN", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if x.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "vigiloforge-vision", "version": __version__}


async def read_analysis(file: UploadFile):
    try:
        if file.content_type not in {
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/webp",
        }:
            raise HTTPException(415, "Upload JPEG, PNG, or WebP.")
        image_bytes = await file.read(MAX_IMAGE_BYTES + 1)
        if len(image_bytes) > MAX_IMAGE_BYTES:
            raise HTTPException(413, "Image exceeds the 8 MiB limit.")
        return await asyncio.to_thread(analyze_image, image_bytes)
    except VisionAnalysisError as exc:
        raise HTTPException(422, str(exc)) from exc
    finally:
        await file.close()


@app.post("/vision/analyze")
async def vision_analyze(file: UploadFile = File(...)):
    return await read_analysis(file)


@app.post("/observations/sync")
async def sync_observation(
    file: UploadFile = File(...), authorize_sync: bool = Query(False)
):
    try:
        require_sync(authorize_sync)
    except PermissionError as exc:
        await file.close()
        raise HTTPException(403, str(exc)) from exc
    # Process and return; do not persist the private image on the server.
    return {
        "status": "analyzed",
        "stored_on_server": False,
        "analysis": await read_analysis(file),
    }


class PrivacySettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    collaborative_training_enabled: StrictBool | None = None
    external_services_enabled: StrictBool | None = None
    observation_sync_enabled: StrictBool | None = None
    local_retention_enabled: StrictBool | None = None


@app.get("/privacy/settings")
def get_privacy_settings():
    return privacy.get_settings()


@app.put("/privacy/settings")
def update_privacy_settings(settings: PrivacySettingsUpdate):
    values = settings.model_dump(exclude_none=True)
    training = values.pop("collaborative_training_enabled", None)
    if training is not None:
        privacy.update_settings(collaborative_training_enabled=training)
    if values:
        databases.set_preferences(values)
    return privacy.get_settings()


@app.post("/security/simulate")
def simulate_security_export():
    return privacy.simulate_unauthorized_export()


@app.get("/security/events")
def get_security_events(limit: int = Query(25, ge=1, le=100)):
    return {"events": databases.list_security_events(limit)}


@app.get("/knowledge/search")
def knowledge_search(
    query: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(5, ge=1, le=10),
):
    try:
        results = search_documents(query, limit)
        return {"query": query, "count": len(results), "results": results}
    except RAGRetrievalError as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/agents/analyze")
def analyze_agent(request: InvestigationRequest):
    try:
        return coordinate(request)
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except CreaoConfigurationError as exc:
        raise HTTPException(503, str(exc)) from exc
    except CreaoAPIError as exc:
        raise HTTPException(502, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


class FetchInvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: dict[str, float] | None = None
    anomaly_score: float | None = None
    crop_category: str | None = None
    authorize_external: StrictBool = False


@app.post("/agents/fetch")
async def fetch_investigation(request: FetchInvestigationRequest):
    try:
        result = await request_fetch_evidence(
            features=request.features,
            anomaly_score=request.anomaly_score,
            crop_category=request.crop_category,
            explicit_authorization=request.authorize_external,
        )
        return {"provider": "fetch", "status": "completed", "result": result}
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(502, str(exc)) from exc
    except OSError as exc:
        raise HTTPException(
            502,
            "Fetch interpreter could not start. Clear FETCH_PYTHON or point it to the installed virtual environment.",
        ) from exc
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            504,
            "Fetch receiver timed out. Wait for startup and verify the configured agent address.",
        ) from exc


@app.get("/agents/creao/{run_id}")
def creao_result(run_id: str):
    if not databases.has_creao_run(run_id):
        raise HTTPException(404, "Run not found for this installation.")
    if not privacy.get_settings()["external_services_enabled"]:
        raise HTTPException(403, "External services are disabled.")
    try:
        return get_investigation(run_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    except CreaoConfigurationError as exc:
        raise HTTPException(503, str(exc)) from exc
    except CreaoAPIError as exc:
        raise HTTPException(502, str(exc)) from exc


@app.get("/telemetry/history")
def telemetry_history(
    source: Literal["live", "demo"] = "live", limit: int = Query(24, ge=1, le=200)
):
    if source == "demo":
        from backend.telemetry import history as demo_history

        return {**demo_history(), "synthetic": True}
    try:
        return history(limit)
    except TelemetryUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc


class SupportQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    topic: Literal["analysis", "privacy", "offline", "pilot"]


@app.post("/support/answer")
def support_answer(request: SupportQuestion):
    answers = {
        "analysis": "Upload one well-lit leaf or capture a photo. Results are heuristic observations, not disease diagnoses. Request local evidence before choosing any external provider.",
        "privacy": "Privacy settings are saved for your workspace (or the shared local demo when not signed in). External transfers require both the saved switch and consent for that request. Raw photos are not sent to agents.",
        "offline": "Field Mode stores photos in this browser. Queue analysis and explicitly synchronize after reconnecting. OpenCV and cloud agents require the backend; they do not run offline.",
        "pilot": "Pilot enrollment is not configured. No contact information is collected by this prototype.",
    }
    return {"provider": "local FAQ", "answer": answers[request.topic]}


@app.get("/integrations/status")
async def integrations_status():
    from backend.integrations import integration_status

    return await integration_status()


@app.get("/knowledge/status")
def knowledge_status():
    from urllib.parse import urlsplit

    databases.init_db()
    with databases.connection() as db:
        exists = db.execute(
            "SELECT 1 FROM sqlite_master WHERE name='rag_passages_fts'"
        ).fetchone()
        rows = (
            db.execute(
                "SELECT title, source_url, passage FROM rag_passages_fts"
            ).fetchall()
            if exists
            else []
        )
    usable = [
        row
        for row in rows
        if urlsplit(row["source_url"]).hostname
        not in {"example.org", "example.com", "example.net"}
    ]
    sources = {row["source_url"]: row["title"] for row in usable}
    return {
        "engine": "SQLite FTS5 keyword retrieval",
        "llm_used": False,
        "indexed": bool(exists),
        "passages": len(usable),
        "sources": [{"url": url, "title": title} for url, title in sources.items()],
        "notice": "No reviewed scientific passages are indexed."
        if not usable
        else "Passages are marked as public by the corpus curator. Review provenance before relying on them.",
    }


@app.get("/billing/status")
def billing_status():
    return {
        "plan": "free",
        "status": "active",
        "billing_enabled": False,
        "payment_collected": False,
        "message": "Hackathon features are free. Paid subscriptions and checkout are not configured.",
    }


@app.middleware("http")
async def private_api_responses(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response
