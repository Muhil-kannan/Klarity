"""
API v1 router — aggregates all route modules.
"""

from fastapi import APIRouter

from app.api.v1.routes import dashboard, health, webhook

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(webhook.router, tags=["webhook"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
