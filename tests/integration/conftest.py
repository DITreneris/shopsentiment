import pytest
from pytest_mock import MockerFixture

@pytest.fixture
def mocker(pytestconfig) -> MockerFixture:
    """Return the MockerFixture for patching."""
    return MockerFixture(pytestconfig) 