"""
Joint pytest configuration.

- `pytest`                      -> only unit tests (no Dobot required)
- `pytest --dobot`              -> additionally run hardware tests
- `pytest --dobot --port COM5`  -> explicitly specify the port (otherwise use DOBOT_PORT or auto-detection)
- `pytest --dobot -m "hardware and not motion"` -> hardware tests without arm movement
"""

import os
from pathlib import Path

import pytest
from tests.hardware import base

HARDWARE_DIR = Path(__file__).parent / "hardware"


def pytest_addoption(parser):
    """
    Adds command line options for pytest.
    """
    parser.addoption(
        "--dobot",
        action="store_true",
        default=False,
        help="Run hardware tests with the Dobot connected",
    )
    parser.addoption(
        "--port",
        default=os.environ.get("DOBOT_PORT"),
        help="Serial port of the Dobot (Default: Environment variable DOBOT_PORT, otherwise auto-detection)",
    )


def pytest_configure(config):
    """
    Pass the --port option to the hardware base class (TestCase classes cannot use fixtures).
    """
    base.PORT = config.getoption("--port")


def pytest_collection_modifyitems(config, items):
    """
    Mark tests under tests/hardware/ as hardware tests. Skip them if --dobot is not specified.
    """
    run_hardware = config.getoption("--dobot")
    skip_hw = pytest.mark.skip(reason="Hardware-Test: run with --dobot")

    for item in items:
        # Everything under tests/hardware/ is automatically a hardware test
        if HARDWARE_DIR in Path(item.fspath).parents:
            item.add_marker(pytest.mark.hardware)
        if "hardware" in item.keywords and not run_hardware:
            item.add_marker(skip_hw)


def pytest_sessionfinish(session, exitstatus):
    """
    Joint connection for all hardware tests -> close it cleanly at the end.
    """
    base.disconnect()
