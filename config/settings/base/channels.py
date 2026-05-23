from .general import env

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

# Django Channels – Redis channel layer
# https://channels.readthedocs.io/en/latest/topics/channel_layers.html
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    }
}
