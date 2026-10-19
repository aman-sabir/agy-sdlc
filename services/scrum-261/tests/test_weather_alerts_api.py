"""Unit and integration tests for Active Weather Alerts API & Caching Layer (SCRUM-261)."""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from weather_alerts.api import create_weather_alerts_app
from weather_alerts.models import AlertSeverity, UserAlertPreferences, WeatherAlert
from weather_alerts.repositories import (
    InMemoryUserPreferencesRepository,
    InMemoryWeatherAlertRepository,
    RedisMemorystoreCache,
)
from weather_alerts.service import ActiveWeatherAlertsService


@pytest.fixture
def sample_now() -> datetime:
    return datetime(2026, 10, 19, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def sample_alerts(sample_now: datetime):
    return [
        WeatherAlert(
            alert_id="CAP-MEL-001",
            location_id="LOC-MEL",
            location_name="Melbourne, VIC",
            category="SEVERE_THUNDERSTORM",
            severity=AlertSeverity.SEVERE,
            headline="Severe Thunderstorm Warning for Melbourne Metro",
            description="Damaging wind gusts up to 110 km/h and large hail forecast.",
            recommended_action="Move vehicles under cover and stay indoors.",
            issued_at=sample_now - timedelta(minutes=30),
            expires_at=sample_now + timedelta(hours=2),
        ),
        WeatherAlert(
            alert_id="CAP-SYD-002",
            location_id="LOC-SYD",
            location_name="Sydney, NSW",
            category="BUSHFIRE",
            severity=AlertSeverity.EXTREME,
            headline="Emergency Bushfire Warning - Western Sydney",
            description="Fast-moving bushfire fanned by hot westerly winds.",
            recommended_action="Activate your bushfire survival plan immediately.",
            issued_at=sample_now - timedelta(minutes=15),
            expires_at=sample_now + timedelta(hours=4),
        ),
        WeatherAlert(
            alert_id="CAP-MEL-003",
            location_id="LOC-MEL",
            location_name="Melbourne, VIC",
            category="FROST",
            severity=AlertSeverity.MINOR,
            headline="Light Morning Frost Advisory",
            description="Temperatures dropping to 1C in outer suburbs.",
            recommended_action="Protect sensitive plants.",
            issued_at=sample_now - timedelta(hours=1),
            expires_at=sample_now + timedelta(hours=1),
        ),
        WeatherAlert(
            alert_id="CAP-MEL-EXPIRED",
            location_id="LOC-MEL",
            location_name="Melbourne, VIC",
            category="FLASH_FLOOD",
            severity=AlertSeverity.EXTREME,
            headline="Expired Flash Flood Warning",
            description="Floodwaters have receded.",
            recommended_action="Drive with caution.",
            issued_at=sample_now - timedelta(hours=5),
            expires_at=sample_now - timedelta(hours=1),
        ),
    ]


@pytest.mark.asyncio
async def test_cache_aside_miss_then_hit(sample_alerts, sample_now):
    user_repo = InMemoryUserPreferencesRepository({
        "user-101": UserAlertPreferences(
            user_id="user-101",
            saved_location_ids=["LOC-MEL", "LOC-SYD"],
            min_severity=AlertSeverity.MODERATE,
        )
    })
    alert_repo = InMemoryWeatherAlertRepository(sample_alerts)
    cache = RedisMemorystoreCache()
    service = ActiveWeatherAlertsService(user_repo, alert_repo, cache)

    # First call: cache miss -> queries repository and populates Redis cache
    res1 = await service.get_active_alerts_for_user("user-101", now=sample_now)
    assert res1.cache_hit is False
    assert res1.total_active == 2
    assert res1.highest_severity == AlertSeverity.EXTREME
    # Highest severity (EXTREME bushfire) sorted first
    assert res1.alerts[0].alert_id == "CAP-SYD-002"
    assert res1.alerts[1].alert_id == "CAP-MEL-001"
    assert alert_repo.query_count == 1

    # Second call: cache hit -> zero repository queries
    res2 = await service.get_active_alerts_for_user("user-101", now=sample_now)
    assert res2.cache_hit is True
    assert res2.total_active == 2
    assert alert_repo.query_count == 1
    assert cache.hits == 2


@pytest.mark.asyncio
async def test_muted_category_and_severity_filtering(sample_alerts, sample_now):
    user_repo = InMemoryUserPreferencesRepository({
        "user-102": UserAlertPreferences(
            user_id="user-102",
            saved_location_ids=["LOC-MEL", "LOC-SYD"],
            min_severity=AlertSeverity.SEVERE,
            muted_categories=["BUSHFIRE"],
        )
    })
    alert_repo = InMemoryWeatherAlertRepository(sample_alerts)
    cache = RedisMemorystoreCache()
    service = ActiveWeatherAlertsService(user_repo, alert_repo, cache)

    res = await service.get_active_alerts_for_user("user-102", now=sample_now)
    assert res.total_active == 1
    assert res.alerts[0].alert_id == "CAP-MEL-001"


def test_fastapi_endpoint_success_and_404(sample_alerts):
    # Ensure sample alerts are active/expired relative to current UTC time
    now = datetime.now(timezone.utc)
    for a in sample_alerts:
        if a.alert_id != "CAP-MEL-EXPIRED":
            a.issued_at = now - timedelta(minutes=10)
            a.expires_at = now + timedelta(hours=2)
        else:
            a.issued_at = now - timedelta(hours=5)
            a.expires_at = now - timedelta(hours=1)

    user_repo = InMemoryUserPreferencesRepository({
        "user-101": UserAlertPreferences(
            user_id="user-101",
            saved_location_ids=["LOC-MEL", "LOC-SYD"],
            min_severity=AlertSeverity.MODERATE,
        )
    })
    alert_repo = InMemoryWeatherAlertRepository(sample_alerts)
    cache = RedisMemorystoreCache()
    service = ActiveWeatherAlertsService(user_repo, alert_repo, cache)
    app = create_weather_alerts_app(service)
    client = TestClient(app)

    # 1. Valid user returns 200 OK with sorted active alerts
    resp = client.get("/api/v1/users/user-101/alerts/active")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user_id"] == "user-101"
    assert body["total_active"] == 2
    assert body["highest_severity"] == "EXTREME"
    assert body["cache_hit"] is False

    # 2. Subsequent call hits cache
    resp_cached = client.get("/api/v1/users/user-101/alerts/active")
    assert resp_cached.status_code == 200
    assert resp_cached.json()["cache_hit"] is True

    # 3. Unknown user returns 404 Not Found
    resp_404 = client.get("/api/v1/users/unknown-user/alerts/active")
    assert resp_404.status_code == 404
