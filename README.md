# Emonio P3 Integration for Home Assistant

Custom [Home Assistant](https://www.home-assistant.io/) integration for the [Emonio P3](https://www.emonio.de/) three-phase power measuring device using Modbus TCP.

## Features

- Automatic device discovery via config flow (UI-based setup)
- 32 sensors: 4 phases (A, B, C, Total) x 8 measurements each:
  - Voltage, Current, Power, Reactive Power, Apparent Power, Frequency, Energy, Power Factor
- Efficient batched Modbus polling via `DataUpdateCoordinator`

## Installation

### Via HACS (recommended)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** and click the three-dot menu.
3. Select **Custom repositories** and add this repository URL with category **Integration**.
4. Search for "Emonio P3" and install it.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/emonio` directory into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**.
2. Search for "Emonio P3".
3. Enter the IP address of your Emonio device and the Modbus port (default: 502).
4. The integration will test the connection and set up all sensors automatically.

## Usage

After setup, 32 sensor entities are created under a single Emonio P3 device. You can add them to dashboards or use them in automations:

```yaml
automation:
  - alias: Alert on high power consumption
    trigger:
      platform: numeric_state
      entity_id: sensor.emonio_xxxxxx_total_power
      above: 5000
    action:
      service: notify.notify
      data:
        message: "Power consumption exceeded 5000W"
```

## Requirements

- Home Assistant 2024.1 or later
- Emonio P3 device with Modbus TCP enabled
- Network connectivity between Home Assistant and Emonio device
