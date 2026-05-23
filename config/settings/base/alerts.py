# Inactivity thresholds in minutes, keyed by Vehicle.Type value.
# "default" is the fallback for any type not explicitly listed.
VEHICLE_INACTIVITY_THRESHOLDS: dict = {
    "default": 30,
    "scooter": 15,
    "bicycle": 20,
    "moped": 30,
}

# How often (in minutes) the inactivity-check Beat task is scheduled.
INACTIVITY_CHECK_INTERVAL_MINUTES: int = 5
