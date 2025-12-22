# This is a dummy test to check pytest discovery in CI/CD pipelines.

from src.dummy import dummy_function


def test_dummy():
    value = dummy_function()
    assert value is True
