# Project description
DobotHub: Python library to control the Dobot Magician and its accessories
(gripper, suction cup, laser, conveyor belt, IR sensor, color sensor) via USB/serial.
Based on dobot-python by Alex Gustafsson (MIT). Python >= 3.10, dependency: pyserial.
Protocol reference: Dobot Communication Protocol V1.1.5 (link in README).

## Architecture
- parser.py: byte <-> Python conversion per message ID 
- message.py: packet framing (header, length, control byte, checksum).
- client.py: one method per protocol command (low level).
- dobot.py: user-facing API, combines client methods.
- New command: parser entry -> client method -> (optional) dobot.py function -> tests.
- Changes to code taken over from dobot-python are marked with "Added." in the docstring.

# Commands
- Setup: `uv pip install -e ".[dev]"`
- Unit tests (no hardware): `pytest`
- Hardware tests: `pytest --dobot [--port COMx] [-m <marker>]`

# Code style
- Functions and classes need a docstring (english, short, 1-2 lines per description).
- Docstrings, comments, test messages, README and CHANGELOG always in English.

# Testing
- Framework: pytest, tests written as `unittest.TestCase` classes.
- Every new or changed function gets a unit test in tests/unit/ (FakeSerial / mocked Client).
- Functions that talk to the robot also get a hardware test in tests/hardware/ (with a matching marker).
- Known bugs: test with `@pytest.mark.xfail(strict=True, reason=...)`; remove the marker once fixed.
- Run `pytest` before finishing a task; all tests must pass or xfail.
- NEVER run `pytest --dobot` yourself: the arm moves. Ask the user to run it.

# Documentation
- README must stay in sync with the library. Update when relevant:
  - Features: new user-facing function in dobot.py
  - Usage: example for new or changed dobot.py functions
  - Hardware setup / Prerequisites: new accessory, port or dependency
  - Project structure: new file or folder
  - Testing: new markers, options or test folders
- Log every change in CHANGELOG.md under `## [Unreleased]`
  (categories: Added / Changed / Fixed / Removed), one line per change:
  `- dobot.py: conveyor_distance() moves belt by mm (host-side timing)`
  Mention the reason when it is not obvious (e.g. "Fixed: ... struct.error on get_alarms()").
- Open bugs are listed under `### Known issues` in CHANGELOG.md. When fixing one: move it to
  `### Fixed` and remove the matching xfail marker in the tests.

# Git
- Main branch: main. Work branches: testing, 
- Do not commit or push without being asked.