"""The camera both profile images share.

YAW is how far the scene is turned away from facing the reader:
45 is the classic isometric view, 0 would be flat on. PITCH is how
far the camera looks down.
"""
import math

YAW = 25.0
PITCH = 35.264  # the isometric pitch; sin = 0.577

COS_YAW, SIN_YAW = math.cos(math.radians(YAW)), math.sin(math.radians(YAW))
COS_PITCH, SIN_PITCH = math.cos(math.radians(PITCH)), math.sin(math.radians(PITCH))


def ground(u, v, size=1.0):
    """A point on the floor, u along the long side and v toward the reader."""
    return ((u * COS_YAW - v * SIN_YAW) * size, (u * SIN_YAW + v * COS_YAW) * SIN_PITCH * size)
