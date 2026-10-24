from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    features: dict[str, float] | None = None
    anomaly_score: float | None = Field(default=None, ge=0, le=1)
    crop_category: str | None = Field(default=None, max_length=40)
    provider: Literal["local", "creao"] = "local"
    authorize_external: StrictBool = False
