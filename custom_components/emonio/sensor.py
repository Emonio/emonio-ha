import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfReactivePower,
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EmonioCoordinator
from .helpers import get_mac_address

_LOGGER = logging.getLogger(__name__)

# (name_suffix, uid_suffix, register_offset, unit, device_class, state_class)
SENSOR_TYPES = [
    ("Voltage", "voltage", 0, UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    ("Current", "current", 2, UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    ("Power", "power", 4, UnitOfPower.WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
    ("Apparent Power Reactive", "apparent_power_reactive", 6, UnitOfReactivePower.VOLT_AMPERE_REACTIVE, SensorDeviceClass.REACTIVE_POWER, SensorStateClass.MEASUREMENT),
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


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Emonio Modbus sensor platform."""
    coordinator: EmonioCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    host = config_entry.data["host"]

    mac_address = await hass.async_add_executor_job(get_mac_address, host)
    if not mac_address:
        raise ConfigEntryNotReady(
            f"Could not determine MAC address for {host}. "
            "Ensure the device is reachable and the arp command is available."
        )
    mac_suffix = mac_address.replace(":", "")[-6:].upper()

    device_info = DeviceInfo(
        identifiers={(DOMAIN, mac_suffix)},
        name=f"Emonio P3 {mac_suffix}",
        model="Emonio P3",
        manufacturer="Emonio GmbH",
    )

    sensors = []
    for phase_name, phase_uid, phase_offset in PHASES:
        for sensor_name, sensor_uid, addr_offset, unit, device_class, state_class in SENSOR_TYPES:
            sensors.append(
                EmonioModbusSensor(
                    coordinator=coordinator,
                    name=f"Emonio {mac_suffix} {phase_name} {sensor_name}",
                    unit_of_measurement=unit,
                    address=phase_offset + addr_offset,
                    device_class=device_class,
                    state_class=state_class,
                    unique_id=f"{mac_suffix}_emonio_{phase_uid}_{sensor_uid}",
                    device_info=device_info,
                )
            )

    async_add_entities(sensors)


class EmonioModbusSensor(CoordinatorEntity[EmonioCoordinator], SensorEntity):
    """Representation of an Emonio Modbus sensor."""

    def __init__(
        self,
        coordinator: EmonioCoordinator,
        name: str,
        unit_of_measurement: str,
        address: int,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass,
        unique_id: str,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_unique_id = unique_id
        self._attr_device_info = device_info
        self._address = address

    @property
    def native_value(self) -> float | None:
        """Return the sensor value from coordinator data."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._address)
