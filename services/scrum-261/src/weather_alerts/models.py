"""Pydantic v2 domain models and DTOs for Active Severe Weather Alerts (SCRUM-261)."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class AlertSeverity(str, Enum):
    """Standardized NWS/CAP alert severity levels ordered by criticality."""
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    EXTREME = "EXTREME"

    @property
    def rank(self) -> int:
        ranks = {
            AlertSeverity.MINOR: 1,
            AlertSeverity.MODERATE: 2,
            AlertSeverity.SEVERE: 3,
            AlertSeverity.EXTREME: 4,
        }
        return ranks[self]


class WeatherAlert(BaseModel):
    """Represents a severe weather alert for a specific geographic zone/location."""
    alert_id: str = Field(..., description="Unique CAP alert identifier")
    location_id: str = Field(..., description="Target location or zone ID")
    location_name: str = Field(..., description="Human-readable city/region name")
    category: str = Field(..., description="Alert category (e.g. TORNADO, FLASH_FLOOD, BUSHFIRE)")
    severity: AlertSeverity = Field(..., description="Severity level")
    headline: str = Field(..., description="Short banner headline for in-app dashboard display")
    description: str = Field(..., description="Full meteorological advisory details")
    recommended_action: str = Field(..., description="Safety instructions for the user")
    issued_at: datetime = Field(..., description="UTC timestamp when alert was issued")
    expires_at: datetime = Field(..., description="UTC timestamp when alert expires")

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Return True if the alert has not yet expired."""
        current = now or datetime.now(timezone.utc)
        return self.expires_at > current


class UserAlertPreferences(BaseModel):
    """User-specific saved locations and alert filtering settings from Cloud SQL."""
    user_id: str
    saved_location_ids: List[str] = Field(default_factory=list)
    min_severity: AlertSeverity = Field(default=AlertSeverity.MODERATE)
    muted_categories: List[str] = Field(default_factory=list)
    notifications_enabled: bool = Field(default=True)


class ActiveAlertsResponse(BaseModel):
    """API response schema for GET /api/v1/users/{userId}/alerts/active."""
    user_id: str
    total_active: int
    highest_severity: Optional[AlertSeverity] = None
    cache_hit: bool = False
    alerts: List[WeatherAlert] = Field(default_factory=list)
