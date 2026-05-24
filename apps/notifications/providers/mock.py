import uuid

from .base import PushProvider, PushResult


class MockPushProvider(PushProvider):
    """
    Fake push provider for local development and tests.
    Always succeeds without making any real network calls.
    """

    def send(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: dict,
    ) -> PushResult:
        return PushResult(
            success=True,
            message_id=f"mock_msg_{uuid.uuid4().hex[:12]}",
        )
