from fastapi import APIRouter

api_router = APIRouter()

from .routes import router as _router  # noqa: E402

api_router.include_router(_router)
