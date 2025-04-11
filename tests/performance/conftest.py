import pytest


def pytest_configure(config):
    """Add custom markers for performance tests."""
    config.addinivalue_line(
        "markers", "slow_network: mark tests that simulate slow network conditions"
    )
    config.addinivalue_line(
        "markers", "memory: mark tests that check memory usage"
    ) 