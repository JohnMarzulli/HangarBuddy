from devices.results.light_sensor_result import LightLevel
from lib.time_correction import TIME_CORRECTION
from managers.sensors_manager import SensorsManager


class LightManager:
    """
    Manages the light sensor. Causes readings to be taken, saves the latest measurements.
    """

    def __init__(self, location_name: str, sensors: SensorsManager, alert_callback):
        """
        Initialize the sensor manager.

        Args:
            location_name (str): A friendly name of where the sensor is.
            sensors (SensorsManager): The manager for all of the sensors.
            alert_callback (_type_): A function to call if the light status changes.
        """
        self.__sensors__ = sensors
        self.__location_name__ = location_name.strip().lower()
        self.__alert_callback__ = alert_callback
        self.__last_brightness__: LightLevel = LightLevel.UNKNOWN

    def update(self) -> None:
        """
        Services the manager so it is working with the latest measurements.
        Will cause an alert to be changed if the lighting changes.
        """
        light_sensor_reading = self.__sensors__.current_light_sensor_reading

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
            f"LIGHTS: {TIME_CORRECTION.get_time()} The {self.__location_name__} is now {new_light_level.name}, was {self.__last_brightness__.name}."
        )
        self.__last_brightness__ = new_light_level
        self.__alert_callback__(alert_message)
