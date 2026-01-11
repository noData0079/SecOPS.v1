import pytest
from datetime import datetime, timedelta
from core.telemetry.anomaly_engine import AnomalyEngine

def test_anomaly_detection_logic():
    engine = AnomalyEngine()

    # Establish a baseline: Normal Tuesday at 2 PM
    # 10 data points of "normal" behavior
    base_time = datetime(2023, 10, 10, 14, 0, 0) # A Tuesday at 2 PM

    # Train normal traffic (~100 rps) and latency (~50ms)
    for i in range(20):
        t = base_time + timedelta(minutes=i)
        engine.ingest_metric("latency", 50.0 + (i % 2), t)
        engine.ingest_metric("traffic_rate", 100.0 + (i % 5), t)

    # Check stats
    lat_mean, _ = engine.baselines["latency"].get_stats(base_time)
    assert 50.0 <= lat_mean <= 52.0

    # Scenario: Latency spike (55ms -> 10% increase) without traffic increase (100 rps)
    current_time = base_time + timedelta(minutes=25)

    # Ingest current metrics
    # Traffic is normal
    engine.ingest_metric("traffic_rate", 100.0, current_time)
    # Latency is high
    engine.ingest_metric("latency", 56.0, current_time) # > 10% increase

    anomalies = engine.detect_inflammation()

    assert len(anomalies) == 1
    assert anomalies[0].metric == "latency"
    assert anomalies[0].context["type"] == "internal_inflammation"
    assert anomalies[0].deviation_percent > 5.0

def test_no_anomaly_when_traffic_spikes():
    engine = AnomalyEngine()
    base_time = datetime(2023, 10, 10, 14, 0, 0)

    # Train baseline
    for i in range(20):
        t = base_time + timedelta(minutes=i)
        engine.ingest_metric("latency", 50.0, t)
        engine.ingest_metric("traffic_rate", 100.0, t)

    current_time = base_time + timedelta(minutes=25)

    # Traffic spikes significantly (200 rps)
    engine.ingest_metric("traffic_rate", 200.0, current_time)
    # Latency spikes (60ms)
    engine.ingest_metric("latency", 60.0, current_time)

    # Should NOT be "internal inflammation" because traffic also increased
    # (The logic says "without a traffic increase")
    anomalies = engine.detect_inflammation()

    # Depending on implementation, strictness may vary.
    # Our implementation checks if traffic_increase <= 5%.
    # Here traffic increase is 100%. So it should NOT flag.
    assert len(anomalies) == 0
