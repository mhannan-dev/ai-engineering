"""Aggregated API router combining all v1 endpoints."""

from fastapi import APIRouter

from meeting_intelligence.api.v1.endpoints import auth, health, meetings, users

api_router = APIRouter()

# Core diagnostic and health routes
api_router.include_router(health.router, tags=["health"])

# Authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# User management routes
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Meeting minutes & audio processing routes
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
