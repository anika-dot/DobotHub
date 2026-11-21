# Changelog
All notable changes to DobotHub are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Test suite (pytest, `unittest.TestCase` style): unit tests in `tests/unit/` (no hardware) and hardware tests in `tests/hardware/` (run with `--dobot`).
- `tests/conftest.py`: options `--dobot` and `--port`, hardware tests are skipped by default.
- `tests/helpers.py`: `FakeSerial` and frame helpers to test the protocol without a Dobot.
- Pytest markers for hardware tests: `hardware`, `motion`, `gripper`, `suction`, `laser`, `conveyor`, `ir`, `color`.
- `CLAUDE.md` with project, code style, testing and documentation rules.
- `CHANGELOG.md` (this file).
- README: features, project structure, prerequisites, hardware setup and testing sections.
- `exceptions.py`: `DobotError` and `DobotConnectionError`.
- `types.py`: `Position`, `Joints`, `Pose`, `MODE_PTP` and sensor ports `GP1`-`GP5`.
- `dobot.py`: `find_port()` detects the Dobot by USB VID.
- `dobot.py`: high-level API for motion, speed, alarms, gripper, suction cup, laser, conveyor, IR sensor, color sensor, jog and `close()`.
- `client.py`: `close()`, `home()`, `wait_until_done()`, `set_conveyor_speed()` (mm/s to pulses), `get_ir_state()`.

### Changed
- `client.py`: `get_ir_switch()` takes `port` instead of `index` and sends it as payload.
- Code comments and docstrings translated to English.

### Removed
- `tests/test_protocol.py` (empty, replaced by `tests/unit/`).

### Known issues
Found by the test suite, marked as `xfail(strict=True)` until fixed:
- `parser.py`: struct format `'<B' * n` instead of `'<' + 'B' * n` for IDs 20, 130, 131, 133, 137, 153-156 and 243 -> `struct.error` (e.g. `get_alarms()`, `get_io_di()`, `get_color()`).
- `parser.py`: ID 60 packs 4 floats, `set_end_effector_params()` passes 3.
- `parser.py`: ID 89 expects 6 values, `set_point_to_point_sliding_rail_po_command()` passes 3.
- `client.py`: `send()` does not release the lock if parsing fails -> all further calls block.
- `client.py`: invalid or missing response raises `AttributeError` instead of a `DobotError`.
- `message.py`: response to a non-queued setter is parsed with the getter parser -> `IndexError` on empty response.
- `dobot.py`: default mode of `move_to()` (3 = `JUMP_ANGLE`) and `slide_to()` (4 = `MOVJ_ANGLE`) interpret x, y, z as joint angles (to check).
