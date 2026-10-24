from backend.privacy import PrivacyViolation, get_settings


def require_sync(explicit_authorization: bool):
    if not explicit_authorization or not get_settings()["observation_sync_enabled"]:
        raise PrivacyViolation(
            "Observation synchronization requires a saved opt-in and explicit permission."
        )
