import time

from managers.relay_manager import RelayManager
from managers.sensors_manager import SensorsManager


class GasSafetyManager:
    """
    Handles readings from a gas sensor.
    Handles determining if alerts should be sent or cleared.
    Handles queuing the alerts.
    """

    def __init__(self, sensors: SensorsManager, relay: RelayManager, alert_callback):
        """
        Initialize the safety manager with the connections needed.

        Args:
            sensors (SensorsManager): The manager for all of the sensors. This enables the safety manager to get the current version.
            relay (RelayManager): The manager for the relay. This allows for the safety manager to turn off the relay.
            alert_callback (_type_): Function to call when an alert needs to be sent.
        """
        self.__sensors_ = sensors
        self.__relay__ = relay
        self.__alert_callback__ = alert_callback
        self.__is_gas_detected__ = False
        self.__last_alert_time__ = 0

    def update(self) -> bool:
        now = time.time()
        gas_sensor_reading = self.__sensors_.current_gas_sensor_reading
        is_relay_on: bool = self.__relay__.is_relay_on()

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
            relay_status: str = "ON" if is_relay_on else "OFF"
            alert_message: str = (
                f"WARNING: Gas is detected! Currently {gas_sensor_reading.current_value}. Relay is {relay_status}."
            )
            self.__alert_callback__(alert_message)
            self.__relay__.turn_off()
            self.__last_alert_time__ = now

        return self.__is_gas_detected__

    def is_gas_detected(self) -> bool:
        """
        Is gas currently detected?

        Returns:
            bool: Is gas currently detected?
        """
        return self.__is_gas_detected__

    def can_turn_on_relay(self):
        """
        Is it safe to turn the relay on?

        Returns:
            _type_: True if it is safe for the relay to be turned on.
        """
        return not self.__is_gas_detected__
