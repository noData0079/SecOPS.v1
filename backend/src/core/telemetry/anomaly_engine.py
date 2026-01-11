from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import math
import statistics

@dataclass
class MetricPoint:
    value: float
    timestamp: datetime

class DynamicBaseline:
    """
    Maintains a dynamic baseline for a metric, potentially bucketed by time.
    For this implementation, we use a simplified Exponential Moving Average (EMA)
    and Standard Deviation to represent 'normal'.

    To support "Tuesday at 2 PM", we can bucket stats by (weekday, hour).
    """
    def __init__(self, history_size: int = 100):
        # bucket_key -> (count, mean, M2) for Welford's online algorithm
        # or just a list of recent values for simplicity in this MVP.
        # Let's use a list of recent values per bucket for simplicity and accuracy on small scale.
        self.buckets: Dict[Tuple[int, int], List[float]] = {}
        self.history_size = history_size

    def _get_bucket_key(self, timestamp: datetime) -> Tuple[int, int]:
        return (timestamp.weekday(), timestamp.hour)

    def update(self, value: float, timestamp: datetime):
        key = self._get_bucket_key(timestamp)
        if key not in self.buckets:
            self.buckets[key] = []

        self.buckets[key].append(value)
        if len(self.buckets[key]) > self.history_size:
            self.buckets[key].pop(0)

    def get_stats(self, timestamp: datetime) -> Tuple[float, float]:
        """Returns (mean, std_dev) for the given timestamp's bucket."""
        key = self._get_bucket_key(timestamp)
        values = self.buckets.get(key, [])

        if not values:
            return 0.0, 0.0

        if len(values) < 2:
            return values[0], 0.0

        return statistics.mean(values), statistics.stdev(values)

@dataclass
class AnomalyEvent:
    metric: str
    value: float
    expected_mean: float
    deviation_percent: float
    severity: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)

class AnomalyEngine:
    """
    Detects anomalies by comparing current metrics against dynamic baselines.
    """
    def __init__(self):
        self.baselines: Dict[str, DynamicBaseline] = {}
        self.recent_metrics: Dict[str, MetricPoint] = {}

    def ingest_metric(self, name: str, value: float, timestamp: Optional[datetime] = None):
        if timestamp is None:
            timestamp = datetime.now()

        if name not in self.baselines:
            self.baselines[name] = DynamicBaseline()

        self.baselines[name].update(value, timestamp)
        self.recent_metrics[name] = MetricPoint(value, timestamp)

    def detect_inflammation(self, latency_metric: str = "latency", traffic_metric: str = "traffic_rate") -> List[AnomalyEvent]:
        """
        Detects 'internal inflammation': Latency spikes > 5% without traffic increase.
        """
        anomalies = []

        if latency_metric not in self.recent_metrics or traffic_metric not in self.recent_metrics:
            return anomalies

        curr_latency = self.recent_metrics[latency_metric]
        curr_traffic = self.recent_metrics[traffic_metric]

        # Ensure metrics are somewhat fresh (e.g., within last minute)
        # For simulation/test, we assume they are fresh.

        # Get baselines for the current time
        lat_mean, lat_std = self.baselines[latency_metric].get_stats(curr_latency.timestamp)
        traf_mean, traf_std = self.baselines[traffic_metric].get_stats(curr_traffic.timestamp)

        if lat_mean == 0:
            return anomalies

        latency_increase_percent = (curr_latency.value - lat_mean) / lat_mean

        # Check if traffic is "normal" or lower (not significantly increased)
        # We consider traffic increased if it's > mean + 1 std_dev?
        # Or simply if current > mean?
        # The prompt says "without a traffic increase".
        # Let's say traffic increase is > 10% or > 1 std dev.

        traffic_increase_percent = 0.0
        if traf_mean > 0:
            traffic_increase_percent = (curr_traffic.value - traf_mean) / traf_mean

        # "If latency spikes by 5% without a traffic increase"
        is_latency_spike = latency_increase_percent > 0.05
        is_traffic_stable = traffic_increase_percent <= 0.05 # Traffic hasn't increased by much

        if is_latency_spike and is_traffic_stable:
            anomalies.append(AnomalyEvent(
                metric=latency_metric,
                value=curr_latency.value,
                expected_mean=lat_mean,
                deviation_percent=latency_increase_percent * 100,
                severity="high",
                timestamp=curr_latency.timestamp,
                context={
                    "type": "internal_inflammation",
                    "traffic_change_percent": traffic_increase_percent * 100,
                    "traffic_value": curr_traffic.value,
                    "traffic_baseline": traf_mean
                }
            ))

        return anomalies
