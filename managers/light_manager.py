from datetime import datetime, timezone

from devices.results.light_sensor_result import LightLevel
from managers.sensors_manager import SensorsManager


class LightManager:
    def __init__(self, sensors: SensorsManager, alert_callback):
        self.__sensors_ = sensors
        self.__alert_callback__ = alert_callback
        self.__last_brightness__: LightLevel = LightLevel.UNKNOWN

    def update(self) -> None:
        light_sensor_reading = self.__sensors_.current_light_sensor_reading

        if light_sensor_reading is None:
            return

        new_light_level: LightLevel = light_sensor_reading.get_light_level()

        if self.__last_brightness__ == LightLevel.UNKNOWN:
            self.__last_brightness__ = new_light_level
            return

        if new_light_level == self.__last_brightness__:
            return

        # Triggering state
        alert_message: str = (
            f"WARNING: {datetime.now(timezone.utc)} The hangar is now {new_light_level.name}, was {self.__last_brightness__.name}."
        )
        self.__last_brightness__ = new_light_level
        self.__alert_callback__(alert_message)
