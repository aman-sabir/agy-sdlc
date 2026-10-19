"""FastAPI HTTP router for GET /api/v1/users/{userId}/alerts/active (SCRUM-261)."""

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from weather_alerts.models import ActiveAlertsResponse
from weather_alerts.repositories import UserNotFoundError
from weather_alerts.service import ActiveWeatherAlertsService


def create_weather_alerts_app(service: ActiveWeatherAlertsService) -> FastAPI:
    """Create FastAPI application wired with ActiveWeatherAlertsService."""
    app = FastAPI(
        title="Weather Alerts Backend Service",
        version="1.0.0",
        description="Cloud Run microservice for in-app active severe weather alerts (SCRUM-261)",
    )
    router = APIRouter(prefix="/api/v1")

    def get_service() -> ActiveWeatherAlertsService:
        return service

    @router.get(
        "/users/{user_id}/alerts/active",
        response_model=ActiveAlertsResponse,
        summary="Get active severe weather alerts for a user",
    )
    async def get_active_alerts(
        user_id: str,
        svc: ActiveWeatherAlertsService = Depends(get_service),
    ) -> ActiveAlertsResponse:
        try:
            return await svc.get_active_alerts_for_user(user_id=user_id)
        except UserNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    app.include_router(router)
    return app
