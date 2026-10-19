"""Repository and Cache abstractions for Cloud SQL and Cloud Memorystore (SCRUM-261)."""

from abc import ABC, abstractmethod
import json
from typing import Dict, List, Optional, Tuple
from weather_alerts.models import WeatherAlert, UserAlertPreferences


class UserNotFoundError(Exception):
    """Raised when the requested userId does not exist in Cloud SQL."""
    pass


class UserPreferencesRepository(ABC):
    """Abstract interface for fetching user saved locations and alert preferences."""

    @abstractmethod
    async def get_user_preferences(self, user_id: str) -> UserAlertPreferences:
        """Retrieve user preferences or raise UserNotFoundError."""


class WeatherAlertRepository(ABC):
    """Abstract interface for fetching active weather alerts by location IDs."""

    @abstractmethod
    async def get_alerts_for_locations(self, location_ids: List[str]) -> List[WeatherAlert]:
        """Fetch raw alerts matching the given location IDs."""


class AlertCacheBackend(ABC):
    """Abstract cache interface representing Cloud Memorystore (Redis)."""

    @abstractmethod
    async def get_location_alerts(self, location_id: str) -> Optional[List[WeatherAlert]]:
        """Return cached alerts for a location, or None on cache miss."""

    @abstractmethod
    async def set_location_alerts(
        self, location_id: str, alerts: List[WeatherAlert], ttl_seconds: int = 120
    ) -> None:
        """Store alerts for a location in cache with TTL."""


class InMemoryUserPreferencesRepository(UserPreferencesRepository):
    """In-memory / test implementation of Cloud SQL UserPreferencesRepository."""

    def __init__(self, initial_users: Optional[Dict[str, UserAlertPreferences]] = None):
        self._users: Dict[str, UserAlertPreferences] = dict(initial_users or {})

    async def get_user_preferences(self, user_id: str) -> UserAlertPreferences:
        if user_id not in self._users:
            raise UserNotFoundError(f"User '{user_id}' not found")
        return self._users[user_id]


class InMemoryWeatherAlertRepository(WeatherAlertRepository):
    """In-memory / test implementation of Cloud SQL WeatherAlertRepository."""

    def __init__(self, alerts: Optional[List[WeatherAlert]] = None):
        self._alerts: List[WeatherAlert] = list(alerts or [])
        self.query_count: int = 0

    async def get_alerts_for_locations(self, location_ids: List[str]) -> List[WeatherAlert]:
        self.query_count += 1
        loc_set = set(location_ids)
        return [a for a in self._alerts if a.location_id in loc_set]


class RedisMemorystoreCache(AlertCacheBackend):
    """TTL-aware cache implementation modeling Cloud Memorystore (Redis) cache-aside behavior."""

    def __init__(self):
        self._store: Dict[str, str] = {}
        self.hits: int = 0
        self.misses: int = 0

    async def get_location_alerts(self, location_id: str) -> Optional[List[WeatherAlert]]:
        key = f"weather:alerts:loc:{location_id}"
        raw = self._store.get(key)
        if raw is None:
            self.misses += 1
            return None
        self.hits += 1
        data = json.loads(raw)
        return [WeatherAlert.model_validate(item) for item in data]

    async def set_location_alerts(
        self, location_id: str, alerts: List[WeatherAlert], ttl_seconds: int = 120
    ) -> None:
        key = f"weather:alerts:loc:{location_id}"
        payload = [a.model_dump(mode="json") for a in alerts]
        self._store[key] = json.dumps(payload)
