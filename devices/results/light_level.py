from enum import Enum, auto


class LightLevel(Enum):
    """
    Classifications of light as detected by the sensor.
    """

    UNKNOWN = auto()
    DARK = auto()
    DIM = auto()
    BRIGHT = auto()
