from django.conf import settings

from .base import PushProvider, PushResult


class FCMProvider(PushProvider):
    """
    Firebase Cloud Messaging push provider.

    Requires FIREBASE_CREDENTIALS_PATH setting pointing to a service-account
    JSON file.  If the path is empty the SDK uses Application Default
    Credentials (ADC), which works inside GCP environments.
    """

    def __init__(self) -> None:
        import firebase_admin
        from firebase_admin import credentials

        if not firebase_admin._apps:
            cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", "")
            cred = (
                credentials.Certificate(cred_path)
                if cred_path
                else credentials.ApplicationDefault()
            )
            firebase_admin.initialize_app(cred)

    def send(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: dict,
    ) -> PushResult:
        from firebase_admin import messaging
        from firebase_admin.exceptions import FirebaseError

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            # FCM data payload values must be strings.
            data={k: str(v) for k, v in data.items()},
            token=fcm_token,
        )
        try:
            message_id = messaging.send(message)
            return PushResult(success=True, message_id=message_id)
        except FirebaseError as exc:
            return PushResult(success=False, error=str(exc))
