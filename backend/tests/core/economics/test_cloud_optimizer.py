import pytest
from src.core.economics.cloud_optimizer import CloudOptimizer, CloudResource

def test_cloud_optimizer_shutdown():
    optimizer = CloudOptimizer()

    # Idle GPU instance
    gpu_res = CloudResource(
        resource_id="gpu-1",
        resource_type="gpu_instance",
        state="running",
        cpu_usage_pct=0.1,
        idle_time_hours=2.0, # > 1.0 threshold
        cost_per_hour=1.5,
        tags={}
    )
    optimizer.add_resource(gpu_res)

    # Active Instance
    active_res = CloudResource(
        resource_id="web-1",
        resource_type="ec2",
        state="running",
        cpu_usage_pct=50.0,
        idle_time_hours=0.0,
        cost_per_hour=0.1,
        tags={}
    )
    optimizer.add_resource(active_res)

    # Run scan
    actions = optimizer.scan_resources()

    assert len(actions) == 1
    assert "gpu-1" in actions[0]

    # Verify state change
    assert optimizer.resources["gpu-1"].state == "stopped"
    assert optimizer.resources["web-1"].state == "running"

def test_cloud_optimizer_report():
    optimizer = CloudOptimizer()
    res = CloudResource(
        resource_id="test-1",
        resource_type="ec2",
        state="running",
        cpu_usage_pct=0,
        idle_time_hours=5.0, # > 4.0 threshold
        cost_per_hour=0.2,
        tags={}
    )
    optimizer.add_resource(res)

    actions = optimizer.scan_resources()
    assert len(actions) == 1
    # We can't easily check the logger output here without capturing logs,
    # but the logic flow is verified by actions list.
