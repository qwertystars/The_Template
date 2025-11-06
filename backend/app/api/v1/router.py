"""API v1 router combining all endpoints."""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, items


api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(items.router)
