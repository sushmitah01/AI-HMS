from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Keyed by remote address by default. In-memory storage is fine for a single
# dev/demo process; for multi-worker production deployments, point
# storage_uri at Redis (e.g. "redis://localhost:6379") instead.
limiter = Limiter(key_func=get_remote_address)
