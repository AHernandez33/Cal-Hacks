from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: dict[str, float] | None = None
    anomaly_score: float | None = Field(default=None, ge=0, le=1)
    crop_category: str | None = Field(default=None, max_length=40)
    provider: Literal["local", "creao"] = "local"
    creao_role: Literal["coordinator", "crop_investigator", "leaf_analyst", "reference_retriever", "response_advisor", "trend_analyst", "privacy_reviewer", "telemetry_analyst", "visitor_guide"] = "coordinator"
    authorize_external: StrictBool = False
