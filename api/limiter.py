from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared limiter instance to avoid duplication and circular imports
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
