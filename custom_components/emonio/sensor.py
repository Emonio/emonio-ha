import asyncio
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    POWER_VOLT_AMPERE_REACTIVE,
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
)
from pymodbus.client import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# (name_suffix, uid_suffix, register_offset, unit, device_class, state_class)
SENSOR_TYPES = [
    ("Voltage", "voltage", 0, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    ("Current", "current", 2, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    ("Power", "power", 4, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    ("Apparent Power Reactive", "apparent_power_reactive", 6, POWER_VOLT_AMPERE_REACTIVE, SensorDeviceClass.REACTIVE_POWER, SensorStateClass.MEASUREMENT),
    ("Apparent Power", "apparent_power", 8, UnitOfApparentPower.VOLT_AMPERE, SensorDeviceClass.APPARENT_POWER, SensorStateClass.MEASUREMENT),
    ("Frequency", "frequency", 10, UnitOfFrequency.HERTZ, SensorDeviceClass.FREQUENCY, SensorStateClass.MEASUREMENT),
    ("Energy", "energy", 12, UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL),
    ("Power Factor", "power_factor", 14, "%", SensorDeviceClass.POWER_FACTOR, SensorStateClass.MEASUREMENT),
]

PHASES = [
    ("Phase A", "phase_a", 0),
    ("Phase B", "phase_b", 100),
    ("Phase C", "phase_c", 200),
    ("Total", "total", 300),
]


async def _get_mac_address(ip_addr):
    """Get the MAC address of a device by IP using ARP."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "arp", "-n", ip_addr,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return None
        for line in stdout.decode().split("\n"):
            if ip_addr in line:
                return line.split()[2]
        return None
    except Exception as e:
        _LOGGER.error("Error getting MAC address for %s: %s", ip_addr, e)
        return None


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Emonio Modbus sensor platform."""
    host = config_entry.data["host"]
    port = config_entry.data.get("port", 502)

    mac_address = await _get_mac_address(host)
    if not mac_address:
        _LOGGER.error("Could not get MAC address for %s", host)
        return
    mac_suffix = mac_address.replace(":", "")[-6:].upper()

    device_info = {
        "identifiers": {(DOMAIN, mac_suffix)},
        "name": f"Emonio P3 {mac_suffix}",
        "model": "Emonio P3",
        "manufacturer": "Berliner Energie Institut",
    }

    modbus_client = ModbusTcpClient(host=host, port=port)
    modbus_lock = asyncio.Lock()

    sensors = []
    for phase_name, phase_uid, phase_offset in PHASES:
        for sensor_name, sensor_uid, addr_offset, unit, device_class, state_class in SENSOR_TYPES:
            sensors.append(
                EmonioModbusSensor(
                    hass=hass,
                    name=f"Emonio {mac_suffix} {phase_name} {sensor_name}",
                    unit_of_measurement=unit,
                    address=phase_offset + addr_offset,
                    device_class=device_class,
                    state_class=state_class,
                    modbus_client=modbus_client,
                    modbus_lock=modbus_lock,
                    unique_id=f"{mac_suffix}_emonio_{phase_uid}_{sensor_uid}",
                    device_info=device_info,
                )
            )

    hass.data[DOMAIN][config_entry.entry_id]["entities"] = sensors
    async_add_entities(sensors, True)


class EmonioModbusSensor(SensorEntity):
    def __init__(self, hass, name, unit_of_measurement, address, device_class,
                 state_class, modbus_client, modbus_lock, unique_id, device_info):
        self.hass = hass
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info
        self._address = address
        self._modbus_client = modbus_client
        self._modbus_lock = modbus_lock

    def _read_register(self):
        """Read a float32 value from Modbus registers (runs in executor)."""
        if not self._modbus_client.connected:
            self._modbus_client.connect()

        result = self._modbus_client.read_holding_registers(self._address, 2, slave=1)
        if result.isError():
            raise ValueError(f"Modbus error at address {self._address}")

        registers = list(result.registers)
        registers.reverse()

        decoder = BinaryPayloadDecoder.fromRegisters(
            registers,
            byteorder=Endian.BIG,
            wordorder=Endian.BIG,
        )
        return round(decoder.decode_32bit_float(), 2)

    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            async with self._modbus_lock:
                value = await self.hass.async_add_executor_job(self._read_register)
            self._attr_native_value = value
        except Exception as e:
            _LOGGER.error("Error updating %s: %s", self._attr_name, e)

    def close_connection(self):
        """Close the Modbus client connection."""
        if self._modbus_client:
            self._modbus_client.close()
