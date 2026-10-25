"""python 3.12 with fetch ai messaging client for VigiloForge"""

import asyncio
import json
import os
import sys

from backend.integrations import fetch_endpoint
from uagents_core.identity import Identity
from uagents.communication import send_sync_message
from uagents.resolver import RulesBasedResolver
from backend.fetch_agent import (
    agent_seed,
    InvestigationRequest,
    InvestigationResponse,
)

default_address = "agent1qw9yp4u3waeymzkf6gnm9ta5stsqu547mh37xg2setuq568t69vkcl0d5j7"


async def investigate(payload: dict) -> dict:
    address = (
        os.getenv("fetch_agent_address") or Identity.from_seed(agent_seed(), 0).address
    )

    # local endpoint for the running agent
    resolver = RulesBasedResolver(rules={address: fetch_endpoint()})

    request = InvestigationRequest(
        task="investigate_visible_discoloration",
        features=payload.get("features"),
        anomaly_score=payload.get("anomaly_score"),
        crop_category=payload.get("crop_category"),
    )

    response = await send_sync_message(
        destination=address,
        message=request,
        response_type=InvestigationResponse,
        resolver=resolver,
        timeout=10,
    )

    if not isinstance(response, InvestigationResponse):
        raise RuntimeError("Fetch.ai did not return an investigation response.")

    return response.model_dump()


if __name__ == "__main__":
    try:
        payload = json.loads(sys.stdin.read())
        result = asyncio.run(investigate(payload))
        print(json.dumps(result), flush=True)
    except Exception as exc:
        print(
            f"Fetch.ai request failed: {exc}",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(1)
