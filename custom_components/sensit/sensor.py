import logging
import json

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_SENSORS
import homeassistant.helpers.config_validation as cv
from . import DOMAIN

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.components.text import TextEntity

from homeassistant.const import TEMP_CELSIUS
from homeassistant.const import UnitOfElectricPotential

from homeassistant import config_entries, core


_LOGGER = logging.getLogger(__name__)

#CONF_NAME = "name"
CONF_DEVICE_ID = "device_id"
CONF_VERSION = "version"
CONF_MODE = "mode"

DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEVICE_ID): cv.string,
        vol.Required(CONF_VERSION): cv.positive_int,
        vol.Optional(CONF_MODE, default="local"): cv.string,
    }
)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_SENSORS): vol.Schema({cv.string: DEVICE_SCHEMA}),
    }
)

# Load configuration from file
def setup_platform(hass, config, add_entities, discovery_info=None):
    # Obtain configuration
    sensors = config.get(CONF_SENSORS)
    devices = []
    # Create Device (Sensors + Sensit object)
    for dev_name, properties in sensors.items():
        # Device ID should be added as attr to the sensors
        # Other fields expect name could be removed
        temp_sensor = SensitTemperature(
            properties.get(CONF_NAME, dev_name),
            properties.get(CONF_DEVICE_ID),
            properties.get(CONF_VERSION),
            properties.get(CONF_MODE),
        )
        battery_sensor = SensitBattery(
            properties.get(CONF_NAME, dev_name),
            properties.get(CONF_DEVICE_ID),
        )
        sensit = SensitDevice(
                properties.get(CONF_NAME, dev_name),
                properties.get(CONF_DEVICE_ID),
                properties.get(CONF_VERSION),
                properties.get(CONF_MODE),
                temp_sensor,
                battery_sensor)
        # Register a callback to update value on new data reception
        hass.helpers.event.async_track_state_change_event("sensor."+sensit.device_id, sensit.handle_event)
        devices.append(temp_sensor)
        devices.append( battery_sensor)
    # Add entities to Home Assistant
    add_entities(devices)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    # Update our config to include new repos and remove those that have been removed.
    if config_entry.options:
        config.update(config_entry.options)
    # sensors = config.get(CONF_SENSORS)
    # logging.info(f"Adding sensors {sensors}")
    devices = []
    # Create Device (Sensors + Sensit object)
    # for dev in sensors:
    # Device ID should be added as attr to the sensors
    # Other fields expect name could be removed
    temp_sensor = SensitTemperature(
        config.get(CONF_NAME, config.get(CONF_DEVICE_ID)),
        config.get(CONF_DEVICE_ID),
        config.get(CONF_VERSION),
        config.get(CONF_MODE),
    )
    battery_sensor = SensitBattery(
        config.get(CONF_NAME, config.get(CONF_DEVICE_ID)),
        config.get(CONF_DEVICE_ID),
    )
    sensit = SensitDevice(
            config.get(CONF_NAME, config.get(CONF_DEVICE_ID)),
            config.get(CONF_DEVICE_ID),
            config.get(CONF_VERSION),
            config.get(CONF_MODE),
            temp_sensor,
            battery_sensor)
    # Register a callback to update value on new data reception
    hass.helpers.event.async_track_state_change_event("sensor."+sensit.device_id, sensit.handle_event)
    devices.append(temp_sensor)
    devices.append( battery_sensor)
    # Add entities to Home Assistant
    async_add_entities(devices)



class SensitDevice:
    # TODO Change SensitDevice to a Registered Device
    def __init__(self, name, device_id, version, mode, temperature_sensor, battery_sensor):
        # Different attributes of the device
        self._name = name
        self.device_id = device_id
        self.version = version
        self.mode = mode
        self.delay_limit = 5
        # Sensors linked to the device
        # Mostly data parsed from the raw Data
        self.temperature_sensor = temperature_sensor
        self.battery_sensor = battery_sensor

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.device_id


    @property
    def state(self) -> str | None:
        return self._state

    def handle_event(self, event):
        """ Callback function called when a the state of sensor.device_id is changed
        """
        #print(f"handle_event " + str(self.device_id) + " : " + str(event.data))
        logging.info(f"handle_event {str(self.device_id)} : {str(event.data.get('new_state'))}")
        # TODO Filter new events based on message age ? 
        # New metric is include in the new_state key as state
        raw_data = event.data.get("new_state").state
        if raw_data:
            if self.version == 1:
                parsed_data = self.parse_v1(raw_data)
                logging.info(parsed_data)
        # self.parse_data(data=event.data.get('new_state').state)
        #self.temperature_sensor.update(int(event.data.get('new_state').state))

    def parse_data(self, data, data_time=None):
        """ Parse new data received
        """
        logging.info("Device {self.name} - Parsing data {data}")

    def convert_battery(self, data):
        ret = 0
        if len(data) <= 2:
            ret = int(data, 16) * 0.02
        return ret

    def convert_temperature(self, data):
        ret = 0
        if len(data) <= 2:
            ret = int(data, 16)
            if ret > 128:
                ret = ret - 256
            ret = (ret + 46) /2
        return ret

    def parse_v1(self, data):
        """ Parser for sensit v1
        b0-b2: Mode (0: off, 1: temperature, 2: movement, 3: full)
        b3-b5: Period (0: 24h, 1: 12h, 2: 6h, 3: 2h, 4: 1h, 5: 30m, 6: 15m, 7: 10m)
        b6: Forced message
        b7: Button message
        B1: Battery (voltage = 0.02 * value)
        B2: Sent battery (voltage during previous frame)
        B3: Temperature = (value + 46)/2
        0-6 bytes: DATA, depend on the mode
            - Temperature: 6 values, each on 1 byte
            - Movement: 1 byte for value, 3 bytes for config
            - Full: 1 byte min temp, 1 byte max temp, 1 byte movement value
        """
        out_data = {}
        try:
            logging.debug(f"Sensit {self.name} v1 data parsing {data}")
            # First byte must be split in bits
            b = "{:08b}".format(int(data[:2], base=16))
            # print("First byte: " + str(b))
            out_data.update({"mode":  int(b[2:])})
            out_data.update({"period": int(b[len(b)-5:len(b)-3], 2)})
            out_data.update({"forced": int(b[1])})
            out_data.update({"button": int(b[0])})
            # Following bytes are battery levels and temperature
            out_data.update({"battery": self.convert_battery(data[2:4])})
            self.battery_sensor.update(out_data.get("battery"))

            # Push battery update to sensor
            out_data.update({"sent_battery": self.convert_battery(data[4:6])})
            out_data.update({"temperature": self.convert_temperature(data[6:8])})
            # Push temperature update to sensor
            self.temperature_sensor.update(out_data.get("temperature"))
            # Next bytes depends on mode
            mode = out_data.get("mode")
            out_data.update({"values": []})
            if mode == 1:
                logging.info(f"Sensit {self.name} mode temperature")
                for i in range(8, len(data), 2):
                    out_data["values"].append(self.convert_temperature(data[i:i+2]))
                logging.info("-- Data parsed: {str(out_data)}")
                return {"body": {"message": "Temperature message stored " + str(out_data.get("values"))}, "statusCode": 200}
            elif mode == 2:
                logging.info(f"Sensit {self.name} mode movement")
                return {"body": {"message": "Mouvement message not implemented yet"}, "statusCode": 500}
            elif mode == 3:
                logging.info(f"Sensit {self.name}  mode full")
                return {"body": {"message": "Full message not implemented yet"}, "statusCode": 500}
            else:
                logging.info(f"Sensit {self.name} OFF")
                return {"body": {"message": "OFF notification not implemented yet"}, "statusCode": 500}
        except Exception as e:
            logging.error(f"Sensit {self.name} Error during data parsing {str(data)}. Error: {str(e.args)}")
            return {"body": {"message": "Error " + str(e.args)}, "statusCode": 500}
        return {"body": {"message": "Nothing was processed"}, "statusCode": 500}


class SensitTemperature(SensorEntity):
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, name, device_id, version, mode):
        self._name = name + "_temperature"
        self.device_id = device_id + "_temperature"
        self._version = version
        self._mode = mode
        #self.update(20)

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.device_id

    def update(self, temperature) -> None:
        # logging(f"Device {self._device_id} state: {self.state()}, value: {self.native_value()}")
        #logging(f"Device {self._device_id}, value: {self.native_value()}")
        logging.info(f"Update temperature for device {self.device_id}, sensor {self._name} - {str(temperature)}")
        #self._attr_native_value = float(temperature)
        self._attr_native_value = float(temperature)
        self.schedule_update_ha_state()

    @property
    def should_poll(self):
        return False


"""
    def turn_on(self, **kwargs):
        if self._send_code(self._code_on, self._protocol, self._length):
            self._state = True
            self.schedule_update_ha_state()

    def turn_off(self, **kwargs):
        if self._send_code(self._code_off, self._protocol, self._length):
            self._state = False
            self.schedule_update_ha_state()
"""
class SensitBattery(SensorEntity):
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, name, device_id):
        self._name = name + "_battery"
        self.device_id = device_id + "_battery"


    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the sensor."""
        return self.device_id


    def update(self, battery) -> None:
        logging.info(f"Update battery for device {self.device_id}, sensor {self._name} - {str(battery)}")
        self._attr_native_value = float(battery)
        self.schedule_update_ha_state()

    @property
    def should_poll(self):
        return False

