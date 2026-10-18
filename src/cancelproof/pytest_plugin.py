"""Fixtures change no loop policy and cancel no pytest tasks."""
import pytest


@pytest.fixture
def cancelproof():
    from .runner import run_scenario
    return run_scenario


@pytest.fixture
def cancelproof_async():
    from .runner import arun_scenario
    return arun_scenario
