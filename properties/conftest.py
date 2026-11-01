"""Fixtures for the reliability property checks P1-P10 (#6).

Run against the live stack: `make up && make properties`. Every check starts and ends with a clean
stack (no toxics, all proxies enabled, no data, no Payment fault), even when it fails.
"""
import pytest

from helpers import reset_all, wait_healthy


@pytest.fixture(scope="session", autouse=True)
def healthy_stack():
    wait_healthy()


@pytest.fixture(autouse=True)
def stack(healthy_stack):
    reset_all()
    try:
        yield
    finally:
        # Faults must not leak into the next check, whatever happened in this one.
        reset_all()
