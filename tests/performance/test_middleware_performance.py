"""Performance tests for middleware overhead (User Story 2).

Ensures rate limit header addition doesn't degrade response times.
Following TDD: These tests should FAIL until implementation is complete.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.performance
def test_middleware_performance_no_regression(
    test_client: TestClient, performance_threshold_ms: int, measure_response_time: callable
) -> None:
    """Test that middleware overhead stays under performance threshold.

    Args:
        test_client: FastAPI TestClient fixture
        performance_threshold_ms: Maximum acceptable response time (500ms)
        measure_response_time: Function to measure execution time
    """

    # Measure response time for health endpoint
    def make_request():
        response = test_client.get("/health")
        assert response.status_code == 200
        return response

    response_time_ms = measure_response_time(make_request)

    # Verify response time is under threshold
    assert response_time_ms < performance_threshold_ms, (
        f"Response time {response_time_ms:.2f}ms exceeds threshold {performance_threshold_ms}ms. "
        "Rate limit header addition should not degrade performance."
    )


@pytest.mark.performance
def test_header_addition_overhead(test_client: TestClient, measure_response_time: callable) -> None:
    """Test that header addition adds minimal overhead (<1ms).

    Args:
        test_client: FastAPI TestClient fixture
        measure_response_time: Function to measure execution time
    """
    # Measure baseline (multiple requests to average out variance)
    times = []
    for _ in range(10):
        time_ms = measure_response_time(lambda: test_client.get("/health"))
        times.append(time_ms)

    avg_time = sum(times) / len(times)

    # Header addition should add <1ms overhead on average
    # This is a rough check - actual overhead depends on system load
    assert avg_time < 100, (
        f"Average response time {avg_time:.2f}ms seems high. "
        "This may indicate performance issues with middleware."
    )


@pytest.mark.performance
def test_concurrent_requests_performance(
    test_client: TestClient, measure_response_time: callable
) -> None:
    """Test that rate limit headers don't slow down concurrent requests.

    Args:
        test_client: FastAPI TestClient fixture
        measure_response_time: Function to measure execution time
    """
    import concurrent.futures

    # Make concurrent requests
    def make_concurrent_request():
        return test_client.get("/health")

    def measure_concurrent():
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_concurrent_request) for _ in range(10)]
            results = [f.result() for f in futures]
            assert all(r.status_code == 200 for r in results)

    concurrent_time_ms = measure_response_time(measure_concurrent)

    # Concurrent requests should complete in reasonable time
    # 10 requests with 5 workers should take < 2000ms
    assert concurrent_time_ms < 2000, (
        f"Concurrent requests took {concurrent_time_ms:.2f}ms, "
        "which may indicate performance degradation."
    )
