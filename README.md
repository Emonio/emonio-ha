# Emonio Modbus Integration for Home Assistant

This repository contains the code for integrating the Emonio P3 three-phase power measuring device with Home Assistant using the Modbus protocol. The Emonio P3 is designed to determine the power consumption of house connection points, main and sub distribution points, devices, and systems. It is particularly suitable for mobile and temporary measurement of 1-phase and 3-phase AC power, providing quick and precise measuring results and easy connection to any distribution cabinet.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview

This project provides a custom component for Home Assistant that integrates Emonio P3 devices using the Modbus protocol. The integration is managed through Home Assistant Community Store (HACS) to facilitate easy installation and updates.

## Installation

### Prerequisites

- Home Assistant installed and running.
- HACS (Home Assistant Community Store) installed.

### Steps

1. **Clone the repository:**

    ```sh
    git clone https://github.com/andsk8/emonio-test.git
    ```

2. **Add the custom component to Home Assistant:**

    Copy the `emonio_modbus` directory to your Home Assistant `custom_components` directory:

    ```sh
    cp -r emonio-test/emonio_modbus /path/to/your/home-assistant/config/custom_components/
    ```

3. **Restart Home Assistant:**

    Restart Home Assistant to recognize the new custom component.

## Configuration

### Setup in Home Assistant

1. **Add Emonio Modbus integration:**

    In your `configuration.yaml` file, add the following configuration:

    ```yaml
    modbus:
      - name: emonio
        type: tcp
        host: YOUR_EMONIO_IP_ADDRESS
        port: 502
        sensors:
          - name: Emonio Voltage Phase 1
            unit_of_measurement: "V"
            address: 0
            input_type: input
            data_type: int16
          - name: Emonio Voltage Phase 2
            unit_of_measurement: "V"
            address: 1
            input_type: input
            data_type: int16
          - name: Emonio Voltage Phase 3
            unit_of_measurement: "V"
            address: 2
            input_type: input
            data_type: int16
          - name: Emonio Current Phase 1
            unit_of_measurement: "A"
            address: 3
            input_type: input
            data_type: int16
          - name: Emonio Current Phase 2
            unit_of_measurement: "A"
            address: 4
            input_type: input
            data_type: int16
          - name: Emonio Current Phase 3
            unit_of_measurement: "A"
            address: 5
            input_type: input
            data_type: int16
          - name: Emonio Power Consumption
            unit_of_measurement: "W"
            address: 6
            input_type: input
            data_type: int32
    ```

    Adjust the addresses and data types according to your specific Modbus register map for the Emonio P3 device.

2. **Reload configuration:**

    Reload your Home Assistant configuration to apply the new settings.

## Usage

### Viewing Sensors

After configuring the integration, your Emonio sensors should be available in Home Assistant. You can view them in the Home Assistant dashboard under the `Entities` section.

### Automations and Scripts

You can create automations and scripts in Home Assistant to react to the data from your Emonio sensors. For example, you can create an automation to turn off a device if the power consumption exceeds a certain threshold.

Example automation:

```yaml
automation:
  - alias: Turn off device on high power consumption
    trigger:
      platform: numeric_state
      entity_id: sensor.emonio_power_consumption
      above: 5000
    action:
      service: switch.turn_off
      target:
        entity_id: switch.your_device

