import logging
import subprocess

_LOGGER = logging.getLogger(__name__)


def get_mac_address(ip_addr: str) -> str | None:
    """Get the MAC address of a device by IP using ARP."""
    try:
        result = subprocess.run(
            ["arp", "-n", ip_addr],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return None
        for line in result.stdout.split("\n"):
            parts = line.split()
            if len(parts) >= 3 and parts[0] == ip_addr:
                return parts[2]
        return None
    except Exception as e:
        _LOGGER.error("Error getting MAC address for %s: %s", ip_addr, e)
        return None
