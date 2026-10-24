"""Test local fetch.ai agent to agent communication"""

from uagents import Agent, Bureau, Context
from backend.fetch_agent import(
    create_agent,
    InvestigationRequest,
    InvestigationResponse,
)

# reuse the receiver
receiver = create_agent()

# separate sender identity - for local testing only
sender = Agent(
    name="vigiloforge_test_sender",
    seed="vigiloforge-local-test-sender-only-26",
)
sent = False

@sender.on_interval(period=3.0)
async def send_investigation(ctx: Context):
    global sent 
    if sent:
        return
    sent = True

    request = InvestigationRequest(
        task="investigate_visible_discoloration",
        crop_category="Tomato",
        features={
            "yellow_fraction": 0.3775,
            "brown_fraction": 0.2065,
            "mean_hue": 36.86,
            "texture_variance": 0.032078,
            "edge_density": 0.135861,
        },
        anomaly_score = 0.4649        
    )

    ctx.logger.info("Sending synthetic tomato investigation.")
    status = await ctx.send(receiver.address, request)
    ctx.logger.info(f"Send status: {status}")


@sender.on_message(model=InvestigationResponse)
async def receive_response(
    ctx: Context,
    source: str,
    msg: InvestigationResponse,
):
    ctx.logger.info("FETCH AGENT RESPONSE RECEIVED")
    ctx.logger.info(f"Summary: {msg.summary}")
    ctx.logger.info(f"Evidence count: {len(msg.citations)}")

    for citation in msg.citations:
        ctx.logger.info(f"Source: {citation.title} - {citation.url}")

    ctx.logger.info(
        f"Next observations: {msg.next_observations}"
    )


bureau = Bureau(
    port=8001,
    endpoint="http://127.0.0.1:8001/submit",
)

bureau.add(receiver)
bureau.add(sender)


if __name__ == "__main__":
    bureau.run()