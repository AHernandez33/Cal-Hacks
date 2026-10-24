def local_report(context: dict) -> dict:
    return {
        "summary": "Local numerical observations and public keyword retrieval; no disease diagnosis was made.",
        "possible_explanations": [
            "Discoloration can have environmental, nutritional, pest, or disease causes; these measurements cannot distinguish them."
        ],
        "citations": context["citations"],
        "uncertainty": "Heuristic vision and keyword matching are not a validated diagnostic model. Sources require human review.",
        "next_observations": [
            "Compare older and younger leaves.",
            "Inspect leaf undersides and document changes.",
            "Review irrigation and recent temperature changes.",
        ],
        "minimum_intervention": [
            "Collect additional observations before selecting treatment.",
            "Consult a local agricultural extension specialist if symptoms spread.",
        ],
        "evidence_count": context["evidence_count"],
    }
