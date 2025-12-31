"""API FastAPI per backend asincrono"""

from actproof.api.main import app
from actproof.api.routes import router

__all__ = ["app", "router"]
