from __future__ import annotations
import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware 
from backend import __version__
from backend.vision import MAX_IMAGE_BYTES, VisionAnalysisError, analyze_image
from typing import Any, Literal 
from pydantic import BaseModel, StrictBool
from fastapi import Query
from backend.RAG.retrieve import search_documents, RAGRetrievalError
from backend.fetch_service import request_fetch_evidence
from backend import databases, privacy
from backend.bridge import investigate
from backend.federated_api import router as federated_router

app = FastAPI(
    title="VigiloForge Secured Crop Detective",
    description="Smarter Farming - Private By Design",
    version=__version__,
)

app.include_router(federated_router)


# this restricts browser access to the development frontend or to origins you allow 
origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGIN", "http://localhost:3000,http://127.0.0.1:3000"

    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)

@app.get("/health")
def health() -> dict[str, str]:
    """Check the API itself, not future third-party integrations."""
    return {"status": "ok", "service": "farmvault-vision", "version": __version__}

@app.post("/vision/analyze")
async def vision_analyze(file: UploadFile = File(...)) -> dict:
    """Accept a JPEG, PNG, or WebP and return purely local leaf observations.

    Input: multipart/form-data with an upload field named `file`.
    Output: the five numerical features, a heuristic discoloration score,
    warnings, and a base64 PNG heatmap overlay for the original user.
    """
    accepted_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    try:
        if file.content_type not in accepted_types:
            raise HTTPException(
                status_code=415,
                detail="Unsupported file type. Upload JPEG, PNG, or WebP.",
            )

        # Read just one byte beyond the limit to detect oversized inputs.
        image_bytes = await file.read(MAX_IMAGE_BYTES + 1)
        if len(image_bytes) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="Image exceeds the 8 MiB limit.")

        try:
            return analyze_image(image_bytes)
        except VisionAnalysisError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()



# Privacy and security API endpoints

class PrivacySettingsUpdate(BaseModel):
    collaborative_training_enabled: StrictBool


@app.get("/privacy/settings")
def get_privacy_settings():
    """Retrieve the persistent collaborative-training preference."""
    return privacy.get_settings()


@app.put("/privacy/settings")
def update_privacy_settings(settings: PrivacySettingsUpdate):
    """Enable or disable collaborative training."""
    return privacy.update_settings(
        collaborative_training_enabled=settings.collaborative_training_enabled
    )


@app.post("/security/simulate")
def simulate_security_export():
    """Demonstrate the blocking of unauthorized sensitive-data exports."""
    return privacy.simulate_unauthorized_export()


@app.get("/security/events")
def get_security_events(limit: int = Query(default=25, ge=1, le=100)):
    """Retrieve sanitized security audit events."""
    return {"events": databases.list_security_events(limit)}

# Search public agricultural references
@app.get("/knowledge/search")
def knowledge_search(
    query: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(default=5, ge=1, le=10)
):
    try:
        results = search_documents(query=query, limit=limit)

        return {
            "query": query,
            "count": len(results),
            "results": results
        }

    except RAGRetrievalError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error


# Agent investigation request
class AgentAnalyzeRequest(BaseModel):
    features: dict[str, float] | None = None
    anomaly_score: float | None = None
    crop_category: str | None = None
    provider: Literal["local", "creao"] = "local"
    authorize_external: bool = False


# Agent investigation endpoint
@app.post("/agents/analyze")
def analyze_agent(request: AgentAnalyzeRequest):
    try:
        result = investigate(
            features=request.features,
            anomaly_score=request.anomaly_score,
            crop_category=request.crop_category,
            provider=request.provider,
            authorize_external=request.authorize_external,
        )
        return result

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc)
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )




from fastapi import HTTPException
from pydantic import BaseModel
from typing import Literal


class FetchInvestigationRequest(BaseModel):
    features: dict[str, float] | None = None
    anomaly_score: float | None = None
    crop_category: str | None = None


@app.post("/agents/fetch")
async def fetch_investigation(request: FetchInvestigationRequest):
    try:
        # This endpoint accepts public or synthetic demo observations.
        # Production requests must additionally enforce authenticated
        # user authorization and backend privacy allowlist checks.
        result = await request_fetch_evidence(
            features=request.features,
            anomaly_score=request.anomaly_score,
            crop_category=request.crop_category,
        )

        return {
            "provider": "fetch",
            "status": "completed",
            "result": result,
        }

    except RuntimeError as exc:
        print(
        f"[FETCH API ERROR] {type(exc).__name__}: {exc}",
        flush=True,
    )
    raise HTTPException(
        status_code=502,
        detail="Fetch.ai investigation unavailable",
    )
