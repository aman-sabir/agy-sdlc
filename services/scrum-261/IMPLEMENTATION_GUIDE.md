# SCRUM-261: Active Weather Alerts API & Caching Layer — Implementation Guide

## 1. Architectural Alignment (`SCRUM-248` & `SCRUM-247`)
This Pull Request implements the backend microservice component specified in:
- **Parent Architecture Story**: [`SCRUM-248`](https://google-asabir.atlassian.net/browse/SCRUM-248) (*In-App Display of Active Severe Weather Alerts*)
- **Epic / PRD**: [`SCRUM-247`](https://google-asabir.atlassian.net/browse/SCRUM-247) (*Weather App - Severe Weather Alerts & Push Notification System*)
- **Technical Task**: [`SCRUM-261`](https://google-asabir.atlassian.net/browse/SCRUM-261) (*[Backend] Develop Active Weather Alerts API & Caching Layer*)

### Key Architectural Patterns Implemented
1. **Cache-Aside Pattern (`RedisMemorystoreCache` / `AlertCacheBackend`)**:
   - Queries Cloud Memorystore (`weather:alerts:loc:{location_id}`) per saved user location first.
   - On cache miss, fetches active alerts for missing locations from the backing repository (`WeatherAlertRepository`) and populates the cache with a configurable TTL (`120s`).
2. **Domain & Preference Filtering (`ActiveWeatherAlertsService`)**:
   - Filters out expired CAP alerts (`expires_at <= now`), alerts below the user's `min_severity` threshold, and categories in `muted_categories`.
   - Sorts active alerts deterministically by `AlertSeverity.rank` descending (`EXTREME > SEVERE > MODERATE > MINOR`), then by `issued_at` descending so the most critical alert drives the dashboard banner.
3. **Clean Layered Architecture (SOLID)**:
   - `src/weather_alerts/models.py`: Pydantic v2 schemas (`WeatherAlert`, `AlertSeverity`, `UserAlertPreferences`, `ActiveAlertsResponse`).
   - `src/weather_alerts/repositories.py`: Abstract repository & cache interfaces (`UserPreferencesRepository`, `WeatherAlertRepository`, `AlertCacheBackend`) and concrete implementations.
   - `src/weather_alerts/service.py`: Pure domain service (`ActiveWeatherAlertsService`).
   - `src/weather_alerts/api.py`: FastAPI router exposing `GET /api/v1/users/{user_id}/alerts/active`.
   - `tests/test_weather_alerts_api.py`: Automated `pytest` unit and FastAPI `TestClient` integration tests.

---
## 🧪 Automated Pytest Verification (✅ PASSED)

```text
============================= test session starts ==============================
platform linux -- Python 3.13.15, pytest-9.1.1, pluggy-1.6.0 -- /usr/local/google/home/amansabir/.gemini/jetski/scratch/jira-agent/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /tmp/coder-pytest-c_u5me3m
plugins: mock-3.15.1, asyncio-1.4.0, respx-0.23.1, anyio-4.15.1
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 3 items

tests/test_weather_alerts_api.py::test_cache_aside_miss_then_hit PASSED  [ 33%]
tests/test_weather_alerts_api.py::test_muted_category_and_severity_filtering PASSED [ 66%]
tests/test_weather_alerts_api.py::test_fastapi_endpoint_success_and_404 PASSED [100%]

=============================== warnings summary ===============================
../../usr/local/google/home/amansabir/.gemini/jetski/scratch/jira-agent/.venv/lib/python3.13/site-packages/starlette/testclient.py:53
  /usr/local/google/home/amansabir/.gemini/jetski/scratch/jira-agent/.venv/lib/python3.13/site-packages/starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
========================= 3 passed, 1 warning in 0.50s =========================
```
