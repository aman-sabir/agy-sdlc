"""Business logic for Active Weather Alerts with Cache-Aside & Preference Filtering (SCRUM-261)."""

from datetime import datetime, timezone
import logging
from typing import List, Optional

from weather_alerts.models import ActiveAlertsResponse, AlertSeverity, WeatherAlert
from weather_alerts.repositories import (
    AlertCacheBackend,
    UserPreferencesRepository,
    WeatherAlertRepository,
)

logger = logging.getLogger("weather_alerts.service")


class ActiveWeatherAlertsService:
    """Orchestrates cache-aside lookup, preference filtering, and severity ranking."""

    def __init__(
        self,
        user_repo: UserPreferencesRepository,
        alert_repo: WeatherAlertRepository,
        cache: AlertCacheBackend,
        cache_ttl_seconds: int = 120,
    ):
        self._user_repo = user_repo
        self._alert_repo = alert_repo
        self._cache = cache
        self._cache_ttl = cache_ttl_seconds

    async def get_active_alerts_for_user(
        self,
        user_id: str,
        now: Optional[datetime] = None,
    ) -> ActiveAlertsResponse:
        """Fetch, cache, filter, and sort active severe weather alerts for a user."""
        current_time = now or datetime.now(timezone.utc)
        prefs = await self._user_repo.get_user_preferences(user_id)

        if not prefs.saved_location_ids:
            return ActiveAlertsResponse(
                user_id=user_id,
                total_active=0,
                highest_severity=None,
                cache_hit=True,
                alerts=[],
            )

        collected_alerts: List[WeatherAlert] = []
        missing_locations: List[str] = []

        # 1. Cache-aside lookup per saved location
        for loc_id in prefs.saved_location_ids:
            cached = await self._cache.get_location_alerts(loc_id)
            if cached is not None:
                collected_alerts.extend(cached)
            else:
                missing_locations.append(loc_id)

        all_from_cache = len(missing_locations) == 0

        # 2. On cache miss, query backing database and populate cache
        if missing_locations:
            db_alerts = await self._alert_repo.get_alerts_for_locations(missing_locations)
            by_loc = {loc_id: [] for loc_id in missing_locations}
            for alert in db_alerts:
                if alert.location_id in by_loc:
                    by_loc[alert.location_id].append(alert)
            for loc_id, loc_alerts in by_loc.items():
                await self._cache.set_location_alerts(
                    loc_id, loc_alerts, ttl_seconds=self._cache_ttl
                )
                collected_alerts.extend(loc_alerts)

        # 3. Filter out expired alerts, muted categories, and alerts below min_severity
        muted_upper = {c.upper() for c in prefs.muted_categories}
        filtered: List[WeatherAlert] = [
            alert
            for alert in collected_alerts
            if alert.is_active(current_time)
            and alert.severity.rank >= prefs.min_severity.rank
            and alert.category.upper() not in muted_upper
        ]

        # 4. Sort by severity descending, then issued_at descending
        filtered.sort(key=lambda a: (a.severity.rank, a.issued_at), reverse=True)

        highest: Optional[AlertSeverity] = filtered[0].severity if filtered else None

        return ActiveAlertsResponse(
            user_id=user_id,
            total_active=len(filtered),
            highest_severity=highest,
            cache_hit=all_from_cache,
            alerts=filtered,
        )
