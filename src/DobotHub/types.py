from enum import IntEnum
from typing import NamedTuple

# Sensor ports on the Dobot Magician base
GP1, GP2, GP4, GP5 = 0, 1, 2, 3 # TODO: A: Check if this is needed? 

class MODE_PTP(IntEnum):
    JUMP_XYZ = 0; MOVJ_XYZ = 1; MOVL_XYZ = 2
    JUMP_ANGLE = 3; MOVJ_ANGLE = 4; MOVL_ANGLE = 5
    MOVJ_INC = 6; MOVL_INC = 7; MOVJ_XYZ_INC = 8; JUMP_MOVL_XYZ = 9

class Position(NamedTuple):
    x: float; y: float; z: float; r: float

class Joints(NamedTuple):
    j1: float; j2: float; j3: float; j4: float

class Pose(NamedTuple):
    position: Position
    joints: Joints
