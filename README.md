# DobotHub
DobotHub standardization of python library for usage of Dobot Magician and additional components.

## ✨ Features
- Serial communication with the Dobot Magician based on the Communication Protocol V1.1.5
- Automatic port detection (`find_port()`)
- Motion: homing, absolute and relative point-to-point moves, path following, jog, speed settings
- End effectors: gripper, suction cup, laser
- Peripherals: conveyor belt (speed in mm/s, move by distance), IR sensor (light barrier), color sensor
- Alarm handling
- Test suite with unit tests (no hardware) and hardware tests

## 🏗️ Project structure
```
DobotHub/
├── src/DobotHub/
│   ├── dobot.py        # user-facing API (Dobot class, find_port)
│   ├── client.py       # one method per protocol command
│   ├── message.py      # packet framing and checksum
│   ├── parser.py       # byte <-> Python conversion per message ID
│   ├── types.py        # Position, Joints, Pose, MODE_PTP, sensor ports
│   └── exceptions.py   # DobotError, DobotConnectionError
├── tests/
│   ├── unit/           # tests without hardware
│   └── hardware/       # tests with a connected Dobot (--dobot)
├── CHANGELOG.md        # documented changes
└── pyproject.toml
```

## 📦 Getting started
### 🚀 Prerequisites
- Python >= 3.10
- [pyserial](https://pypi.org/project/pyserial/) >= 3.5 (installed automatically)
- Dobot Magician with USB cable; on Windows the USB serial driver of the Dobot must be installed
- Optional for development: `pytest`, `ruff` (`pip install -e ".[dev]"`)

### 🔌 Hardware setup
- Connect the Dobot via USB. The port is detected automatically, or pass it explicitly, e.g. `Dobot("COM5")`.
- Default sensor ports used by the API (`types.py`):

| Accessory | Port / index |
|---|---|
| IR sensor (light barrier) | `GP4` |
| Color sensor | `GP2` |
| Conveyor belt | stepper 1 (`index=0`) |

## 📖 Usage
### 1. Install the repository
Install the package directly from GitHub using `pip`:

```bash
pip install git+https://github.com/anika-dot/DobotHub.git
```

### 2. Import the package
After installation, you can import the required modules in your Python script:

```python
import DobotHub
```

### 3. Use the package
You can now use the functions and classes provided by the repository:

```python
from DobotHub import dobot
```

### Without installation
If you don't want to install the package, you can also directly clone it:
```bash
git clone https://github.com/anika-dot/DobotHub.git
```

## 📡 Communication with the Dobot
### Communication protocol
The base of the communication with the Dobot is the Communication Protocol (https://www.alcom.no/wp-content/uploads/2019/11/Dobot-Communication-Protocol-V1.1.5-1.pdf). It contains a list of all commands the Dobot understands. 

### parser.py
The parser.py file translates between raw bytes to python values. It contains a dictionary with all the relevant translations. The dictionary is based on the communication protocol

### message.py
The message.py file builds a structure, that the Dobot can understand the command. It contains functions to send an receive messages from and to the Dobot. It is used by the client file and retreives the information from the parser file.

### client.py
In the client.py file the basic Dobot functions are defined in readable and understandable python language.

### dobot.py
In these files the functions we use in the final script are defined. A function can contain several different basic functions from client.py

## 💡 How to add a new function
New user-facing functions go into the `Dobot` class in `dobot.py`. They combine one or more
low-level methods from `client.py`.

**1. Check if the client method exists.** Search `client.py` for the protocol command you need
(see the communication protocol for the message ID). If it exists, go to step 3.

**2. If not, add the protocol command** (only needed for commands not yet implemented):
- `parser.py`: add an entry for the message ID. The list holds four parsers:
  `[getter response, setter response, queued setter response, setter request]` (use `None` if not needed).
- `client.py`: add a method that builds and sends the `Message`

**3. Add the function to `dobot.py`** in the matching section (e.g. `# ----- Laser -----`).
Give it a short English docstring. Commands that are queued on the Dobot should offer a
`wait=True` parameter and call `self.wait()`

**4. Write tests.**
- Unit test in `tests/unit/test_dobot.py` (mocked client, no hardware)
- If the function talks to the robot: hardware test in `tests/hardware/` with a matching marker.
- Run `pytest` – all tests must pass.

**5. Update the documentation.** Add the function to the *Features* list above (if user-facing)
and log the change in [CHANGELOG.md](CHANGELOG.md) under `## [Unreleased]`

## 🐛 Testing
Tests are written as `unittest.TestCase` classes and run with pytest.

```bash
pip install -e ".[dev]"        # or: uv pip install -e ".[dev]"
pytest                         # unit tests only, no Dobot needed
pytest --dobot                 # also run hardware tests (Dobot connected)
pytest --dobot --port COM5     # set the port (default: env DOBOT_PORT, else auto-detect)
pytest --dobot -m "hardware and not motion"   # hardware tests without arm movement
pytest --dobot -m gripper      # only tests for the mounted tool / accessory
```

| Folder | Content | Dobot needed |
|---|---|---|
| `tests/unit/` | parser, message, client (simulated serial port), Dobot API (mocked client) | no |
| `tests/hardware/` | 01 info (read only) → 02 params → 03 motion → 04 effectors → 05 peripherals | yes |

Markers: `hardware`, `motion`, `gripper`, `suction`, `laser`, `conveyor`, `ir`, `color`.
Safe positions for the motion tests are defined in `tests/hardware/base.py` (`SAFE_POINT`) – adapt them to your setup.
Known bugs are marked with `xfail(strict=True)`: once a bug is fixed, the test reports `XPASS` and the marker can be removed.
The list of known issues is kept in [CHANGELOG.md](CHANGELOG.md).

## 📜 License 
DobotHub based on [dobot-python](https://github.com/AlexGustafsson/dobot-python)
from Alex Gustafsson (MIT-License). DobotHub itself is also licensed under the MIT License; see [LICENSE](LICENSE).