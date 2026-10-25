from backend.RAG.pipeline import build_context
from backend.orchestration.agent_registry import AGENTS
from backend.orchestration.reports import local_report
from backend.orchestration.schemas import InvestigationRequest
from backend import databases


def coordinate(request: InvestigationRequest) -> dict:
    context = build_context(
        features=request.features,
        anomaly_score=request.anomaly_score,
        crop_category=request.crop_category,
    )
    report = local_report(context)
    result = {
        **report,
        "provider": "local",
        "status": "completed",
        "external_request_sent": False,
        "stages": [{**agent, "status": "completed"} for agent in AGENTS],
    }
    if request.provider == "creao":
        from backend.creao_api import start_investigation

        run = start_investigation(
            context["agent_payload"], explicit_authorization=request.authorize_external, role=request.creao_role
        )
        databases.remember_creao_run(run["run_id"])
        databases.remember_creao_role(run["run_id"], request.creao_role)
        result.update(
            provider="creao",
            status=run["status"],
            run_id=run["run_id"],
            role=request.creao_role,
            result=run.get("result"),
            notice=run.get("notice"),
            error=run.get("error"),
            external_request_sent=True,
        )
        result["stages"].append(
            {
                "id": "creao",
                "name": "Configured CREAO hosted agent",
                "execution": "remote API",
                "status": run["status"],
            }
        )
    return result
