import logging
import struct
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.client import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

PHASE_OFFSETS = [0, 100, 200, 300]
REGISTERS_PER_PHASE = 16


def _decode_float32_le(regs: list[int]) -> float:
    """Decode two 16-bit registers as a little-endian word order float32."""
    packed = struct.pack("<HH", regs[0], regs[1])
    return struct.unpack("<f", packed)[0]


class EmonioCoordinator(DataUpdateCoordinator[dict[int, float]]):
    """Coordinator to manage fetching Emonio Modbus data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Emonio Modbus",
            update_interval=SCAN_INTERVAL,
        )
        self._host = entry.data["host"]
        self._port = entry.data.get("port", 502)
        self._client = ModbusTcpClient(self._host, port=self._port)

    def _read_all_registers(self) -> dict[int, float]:
        """Read all phase registers from the Modbus device."""
        if not self._client.connected:
            if not self._client.connect():
                raise UpdateFailed(f"Cannot connect to {self._host}:{self._port}")

        data: dict[int, float] = {}
        for phase_offset in PHASE_OFFSETS:
            result = self._client.read_holding_registers(
                phase_offset, count=REGISTERS_PER_PHASE
            )
            if result.isError():
                raise UpdateFailed(
                    f"Modbus error reading registers at offset {phase_offset}"
                )
            for i in range(0, REGISTERS_PER_PHASE, 2):
                address = phase_offset + i
                data[address] = round(
                    _decode_float32_le(result.registers[i : i + 2]), 2
                )
        return data

    async def _async_update_data(self) -> dict[int, float]:
        """Fetch data from the Modbus device."""
        try:
            return await self.hass.async_add_executor_job(self._read_all_registers)
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Emonio: {err}") from err

    def close(self) -> None:
        """Close the Modbus client connection."""
        self._client.close()
