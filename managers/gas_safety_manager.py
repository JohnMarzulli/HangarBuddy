import time

from managers.relay_manager import RelayManager
from managers.sensors_manager import SensorsManager


class GasSafetyManager:
    def __init__(self, sensors: SensorsManager, relay: RelayManager, alert_callback):
        self.__sensors_ = sensors
        self.__relay__ = relay
        self.__alert_callback__ = alert_callback
        self.__is_gas_detected__ = False
        self.__last_alert_time__ = 0

    def update(self) -> bool:
        now = time.time()
        gas_sensor_reading = self.__sensors_.current_gas_sensor_reading

        if gas_sensor_reading is None:
            self.__is_gas_detected__ = False
            return False

        # Triggering state
        if gas_sensor_reading.is_gas_detected and not self.__is_gas_detected__:
            self.__is_gas_detected__ = True
            self.__relay__.turn_off()
        # Relaxing state
        elif not gas_sensor_reading.is_gas_detected and self.__is_gas_detected__:
            self.__is_gas_detected__ = False
            self.__last_alert_time__ = 0
            self.__alert_callback__("Gas has cleared.")

        if self.__is_gas_detected__ and (
            now - self.__last_alert_time__ > 1800
        ):  # 30 minutes
            self.__alert_callback__("WARNING: Gas detected! Heater is OFF.")
            self.__last_alert_time__ = now

        return self.__is_gas_detected__

    def is_gas_detected(self) -> bool:
        return self.__is_gas_detected__

    def can_turn_on_heater(self):
        return not self.__is_gas_detected__
