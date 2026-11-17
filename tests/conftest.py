"""
Gemeinsame pytest-Konfiguration.

- `pytest`                      -> nur Unit-Tests (kein Dobot nötig)
- `pytest --dobot`              -> zusätzlich Hardware-Tests
- `pytest --dobot --port COM5`  -> Port explizit angeben (sonst DOBOT_PORT oder Auto-Erkennung)
- `pytest --dobot -m "hardware and not motion"` -> Hardware-Tests ohne Armbewegung
"""

import os
from pathlib import Path

import pytest

HARDWARE_DIR = Path(__file__).parent / "hardware"


def pytest_addoption(parser):
    parser.addoption(
        "--dobot",
        action="store_true",
        default=False,
        help="Hardware-Tests mit angeschlossenem Dobot ausführen",
    )
    parser.addoption(
        "--port",
        default=os.environ.get("DOBOT_PORT"),
        help="Serieller Port des Dobot (Default: Umgebungsvariable DOBOT_PORT, sonst Auto-Erkennung)",
    )


def pytest_configure(config):
    # Port an die Hardware-Basisklasse weitergeben (TestCase-Klassen können keine Fixtures nutzen)
    from tests.hardware import base

    base.PORT = config.getoption("--port")


def pytest_collection_modifyitems(config, items):
    run_hardware = config.getoption("--dobot")
    skip_hw = pytest.mark.skip(reason="Hardware-Test: mit --dobot ausführen")

    for item in items:
        # Alles unter tests/hardware/ ist automatisch ein Hardware-Test
        if HARDWARE_DIR in Path(item.fspath).parents:
            item.add_marker(pytest.mark.hardware)
        if "hardware" in item.keywords and not run_hardware:
            item.add_marker(skip_hw)


def pytest_sessionfinish(session, exitstatus):
    # Eine gemeinsame Verbindung für alle Hardware-Tests -> am Ende sauber schliessen
    from tests.hardware import base

    base.disconnect()
