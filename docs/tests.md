# Testing Strategy

## Backend Unit Tests
- Located in `backend/app/tests`.
- Use async SQLite in-memory database to exercise service logic.
- Coverage:
  - Sensor ingestion persists data (`test_sensor_ingestion_creates_row`).
  - Alarm thresholding creates alarms (`test_alarm_created_on_high_value`).
  - Prediction workflow persists AI output with monkeypatched service (`test_prediction_workflow_persists_result`).

Run via:
```bash
cd backend
pytest --asyncio-mode=auto
```

## Integration Testing (Future)
- Compose-based smoke test to publish MQTT payload and assert DB rows.
- API journey test to create machine → sensor → ingest reading → check frontend.

## CI
- `.github/workflows/ci.yml` (to be added) should run:
  - `backend` unit tests + coverage
  - `frontend` lint/build
  - Docker build validation (`docker-compose build`)

