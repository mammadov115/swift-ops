import environ

env = environ.Env()

# Push provider: "mock" (default) or "fcm"
PUSH_PROVIDER = env("PUSH_PROVIDER", default="mock")

# Path to Firebase service-account JSON key file.
# If empty, Firebase Application Default Credentials are used.
FIREBASE_CREDENTIALS_PATH = env("FIREBASE_CREDENTIALS_PATH", default="")

# Battery percentage below which a LOW_BATTERY alert is triggered.
BATTERY_ALERT_THRESHOLD = env.int("BATTERY_ALERT_THRESHOLD", default=20)
