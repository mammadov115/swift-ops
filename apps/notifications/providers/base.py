from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class PushResult:
    success: bool
    message_id: str | None = None
    error: str | None = None


class PushProvider(ABC):
    """Abstract base for push notification delivery backends."""

    @abstractmethod
    def send(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: dict,
    ) -> PushResult: ...
