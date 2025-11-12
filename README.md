# DIGIsens Weight Sensing System

A Python interface for LOWA DIGI SENS protocol-based weight sensing systems used in retail shelf monitoring and inventory management.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Hardware Setup](#hardware-setup)
- [Software Installation](#software-installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Protocol Details](#protocol-details)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

DIGIsens is a professional weight sensing system for retail environments that enables:

- **Real-time inventory tracking** - Monitor product levels automatically
- **Multi-shelf deployments** - Scale to dozens of shelves
- **Accurate measurements** - 1-gram resolution with frequency-based load cells
- **Reliable operation** - Industrial-grade RS485 communication

### Key Features

- Frequency-based load cells (~14,000 Hz)
- RS485 multi-drop bus architecture
- 8 sensors per MUX unit
- Factory-calibrated sensors with unique IDs
- 200ms measurement integration time
- ASCII text-based protocol

## System Architecture

```
┌─────────────┐
│  Computer   │
│  (Python)   │
└──────┬──────┘
       │ USB
┌──────▼──────┐
│  RS485-USB  │
│  Converter  │
└──────┬──────┘
       │ RS485
┌──────▼──────┐
│  Repeater   │ (Power + Signal Distribution)
└──────┬──────┘
       │
       ├─────────────┬─────────────┬─────────────┐
       ▼             ▼             ▼             ▼
   ┌───────┐     ┌───────┐     ┌───────┐     ┌───────┐
   │ Shelf │     │ Shelf │     │ Shelf │     │ Shelf │
   │  MUX  │     │  MUX  │     │  MUX  │     │  MUX  │
   └───┬───┘     └───┬───┘     └───┬───┘     └───┬───┘
       │             │             │             │
   8 sensors    8 sensors     8 sensors     8 sensors
```

### Components

1. **Load Cells** - Frequency-based weight sensors (integrated in shelves)
2. **MUX Unit** - Multiplexer controlling 8 sensors per shelf
3. **Repeater** - Power supply and RS485 signal repeater
4. **RS485-USB Converter** - Interface to computer
5. **Computer** - Runs monitoring software (Python)

## Hardware Setup

### Physical Connections

1. **Power Supply**
   - 12V DC minimum (7V at MUX entry)
   - Connect via repeater to MUX units
   - RJ-45 pins 7-8: +12V
   - RJ-45 pins 5-6: GND

2. **RS485 Bus**
   - RJ-45 pins 1-2: RS485 A/B
   - Use shielded twisted pair cable
   - Daisy-chain topology supported
   - Maximum bus length depends on cable quality

3. **Termination**
   - RS485 bus may require 120Ω termination resistors
   - Consult converter documentation

### RS485-USB Converter

You'll need an RS485-to-USB converter. Common options:

- **USB-to-RS485 adapter** (e.g., FTDI-based)
- **USB-to-Serial + Serial-to-RS485 adapter**

**Settings:**
- Baud rate: 9600 (default) or up to 115200
- Data bits: 8
- Parity: None
- Stop bits: 1
- Flow control: None

### Linux Setup

1. **Check Serial Port**
   ```bash
   ls /dev/ttyUSB* /dev/ttyACM*
   ```
   Common ports: `/dev/ttyUSB0`, `/dev/ttyUSB1`

2. **User Permissions**
   Add user to dialout group:
   ```bash
   sudo usermod -a -G dialout $USER
   # Log out and back in for changes to take effect
   ```

3. **Test Connection**
   ```bash
   # Install minicom
   sudo apt install minicom

   # Test serial port
   minicom -D /dev/ttyUSB0 -b 9600
   ```

### Windows Setup

1. **Check Serial Port**
   - Open Device Manager
   - Look under "Ports (COM & LPT)"
   - Note COM port number (e.g., COM3)

2. **Install Drivers**
   - Install manufacturer drivers for your RS485 converter
   - Common: FTDI, CH340, Prolific drivers

## Software Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager

### Install Dependencies

```bash
# Navigate to project directory
cd /home/zohaib/DIGIsens

# Install required packages
pip install -r requirements.txt

# Or install directly
pip install pyserial
```

### Verify Installation

```bash
python -c "import serial; print(serial.VERSION)"
```

## Quick Start

### 1. Basic Weight Reading

```python
from digisens_interface import DigiSensInterface

# Connect to sensor
with DigiSensInterface('/dev/ttyUSB0') as sensor:
    # Read weight from MUX 123, channel 0
    reading = sensor.get_weight('123', 0)
    print(f"Weight: {reading.weight:.3f} kg")
```

### 2. Read All Sensors on Shelf

```python
with DigiSensInterface('/dev/ttyUSB0') as sensor:
    weights = sensor.get_all_weights('123')
    for i, reading in enumerate(weights):
        print(f"Channel {i}: {reading.weight:.3f} kg")
```

### 3. Continuous Monitoring

```python
with DigiSensInterface('/dev/ttyUSB0') as sensor:
    # Poll every second
    sensor.poll_continuous('123', 0, interval=1.0)
```

### 4. Inventory Tracking

```python
from digisens_interface import DigiSensInterface, ShelfMonitor

with DigiSensInterface('/dev/ttyUSB0') as sensor:
    monitor = ShelfMonitor(sensor)

    # Register and calibrate shelf
    monitor.add_shelf('123')
    monitor.calibrate_shelf('123')

    # Monitor for changes
    monitor.monitor_shelf('123', interval=1.0, threshold=0.05)
```

### 5. Run Test Program

```bash
# Basic test
python digisens_interface.py /dev/ttyUSB0 123

# View examples
python examples.py

# Run specific example
python examples.py 1
```

## Usage Examples

See `examples.py` for 12 comprehensive examples:

1. **Basic Reading** - Single sensor weight
2. **All Sensors** - Read entire shelf
3. **Continuous Monitoring** - Real-time polling
4. **Inventory Monitoring** - Track changes
5. **Extended Addressing** - 16-char IDs
6. **Multi-Sensor Items** - Items spanning multiple sensors
7. **Error Handling** - Proper exception handling
8. **Configuration** - MUX settings
9. **Zeroing** - EEPROM tare (use sparingly!)
10. **Software Tare** - Daily tare operations
11. **Parallel Shelves** - Multiple shelf monitoring
12. **Product Tracking** - Real-world scenario

## API Reference

### DigiSensInterface

Main interface for communicating with sensors.

#### Constructor

```python
DigiSensInterface(port, baudrate=9600, timeout=1.0)
```

- `port`: Serial port (e.g., '/dev/ttyUSB0', 'COM3')
- `baudrate`: Communication speed (default: 9600)
- `timeout`: Read timeout in seconds

#### Methods

##### get_weight(mux_id, channel, use_extended=False)

Read weight from single sensor.

**Returns:** `WeightReading` object

```python
reading = sensor.get_weight('123', 0)
print(reading.weight)    # 2.350 kg
print(reading.status)    # StatusFlag.OK
print(reading.is_valid)  # True
```

##### get_all_weights(mux_id, use_extended=False)

Read all sensors on a shelf.

**Returns:** List of `WeightReading` objects

```python
weights = sensor.get_all_weights('123')
for i, w in enumerate(weights):
    print(f"Sensor {i}: {w.weight:.3f} kg")
```

##### zero_sensor(mux_id, channel, use_extended=False)

Zero/tare sensor (EEPROM write - use sparingly!).

**⚠️ WARNING:** Writes to EEPROM (100,000 cycle limit). Only use during installation/annual calibration.

```python
sensor.zero_sensor('123', 0)
```

##### poll_continuous(mux_id, channel, interval=1.0, callback=None)

Continuously poll sensor.

```python
def my_callback(reading):
    print(f"Weight: {reading.weight} kg")

sensor.poll_continuous('123', 0, interval=1.0, callback=my_callback)
```

##### Configuration Methods

```python
# Get MUX info
address = sensor.get_mux_address('123')
model = sensor.get_model_number('123')
revision = sensor.get_software_revision('123')

# Change baudrate
sensor.set_baudrate('123', 115200)
```

### ShelfMonitor

High-level interface for managing multiple shelves.

```python
monitor = ShelfMonitor(interface)
monitor.add_shelf('123', num_sensors=8)
monitor.calibrate_shelf('123')
net_weights = monitor.get_net_weights('123')
monitor.monitor_shelf('123', interval=1.0, threshold=0.05)
```

### WeightReading

Data class representing a weight measurement.

```python
reading.weight      # Weight in kg (float)
reading.status      # StatusFlag enum
reading.is_valid    # True if status is OK
reading.raw_response  # Original response string
```

### StatusFlag

Measurement status enumeration.

- `StatusFlag.OK` - Normal measurement
- `StatusFlag.MOTION` - Motion detected (unreliable)
- `StatusFlag.NOT_CONNECTED` - Sensor disconnected
- `StatusFlag.EEPROM_ERROR` - Calibration data error

## Protocol Details

### LOWA DIGI SENS Protocol

**Format:** `@ or # | Length | Command | Data | Checksum | CR`

### Addressing Modes

**Standard (@):**
- 3-digit user ID (000-999)
- Example: `@09gw12305` - Get weight from MUX 123, channel 5

**Extended (#):**
- 16-character manufacturer ID
- Example: `#22gw012022042910314200`

### Key Commands

| Command | Description | Example |
|---------|-------------|---------|
| `gw` | Get single weight | `@09gw12300` |
| `gl` | Get all weights | `@08gl123` |
| `sz` | Zero sensor | `@09sz12300` |
| `ag` | Get address | `@06ag123` |
| `gm` | Get model | `@06gm123` |
| `gr` | Get revision | `@06gr123` |
| `br` | Set baudrate | `@07br1230` |

### Checksum Calculation

XOR of all bytes in message, formatted as 2-digit hex:

```python
def calculate_checksum(message):
    checksum = 0
    for char in message:
        checksum ^= ord(char)
    return f"{checksum:02X}"
```

### Response Format

**Single weight:**
```
@13 0002.130 5C
│  │ │      │ └─ Checksum
│  │ │      └─── Status flag
│  │ └────────── Weight (8 chars)
│  └──────────── Length
└─────────────── Prefix
```

**Status flags:**
- ` ` (space) - OK
- `M` - Motion
- `C` - Not connected
- `E` - EEPROM error

## Troubleshooting

### Connection Issues

**Problem:** `Failed to connect to /dev/ttyUSB0`

**Solutions:**
1. Check port name: `ls /dev/ttyUSB*`
2. Check permissions: `sudo usermod -a -G dialout $USER`
3. Check cable connection
4. Try different port: `/dev/ttyUSB1`

### No Response from Sensor

**Problem:** `TimeoutError: No response from sensor`

**Solutions:**
1. Verify MUX ID is correct
2. Check power supply (12V)
3. Verify RS485 wiring (pins 1-2)
4. Test with broadcast ID: `000`
5. Check baudrate matches MUX setting
6. Verify RS485 A/B polarity

### Invalid Readings

**Problem:** Status flag shows `M` (motion) or `C` (not connected)

**Solutions:**
- **Motion (`M`):** Wait for stabilization, retry after 1 second
- **Not Connected (`C`):** Check sensor cable, verify connection
- **EEPROM Error (`E`):** Contact manufacturer, sensor needs recalibration

### Slow Performance

**Problem:** Readings take too long

**Solutions:**
1. Increase baudrate to 115200:
   ```python
   sensor.set_baudrate('123', 115200)
   # Reconnect at new baudrate
   ```
2. Use `get_all_weights()` instead of multiple `get_weight()` calls
3. Respect 200ms measurement interval
4. For multiple shelves, use parallel RS485 buses

## Best Practices

### 1. EEPROM Write Limits

**NEVER use `zero_sensor()` for daily operations!**

- EEPROM has 100,000 write cycle limit
- Only use during:
  - Initial installation
  - Annual calibration
  - Sensor replacement

For daily tare operations, use **software tare**:

```python
# Read empty weight once
empty = sensor.get_weight('123', 0).weight

# Calculate net weight
current = sensor.get_weight('123', 0).weight
net = current - empty
```

### 2. Polling Intervals

- **Minimum:** 200ms (sensor integration time)
- **Recommended:** 1 second for most applications
- **Multi-sensor items:** Poll all sensors simultaneously

```python
# GOOD: Read all at once
weights = sensor.get_all_weights('123')
total = weights[0].weight + weights[1].weight

# BAD: Sequential reads (time skew)
w1 = sensor.get_weight('123', 0)
time.sleep(0.5)  # Item might move during this time!
w2 = sensor.get_weight('123', 1)
```

### 3. Error Handling

Always check `is_valid` before using measurements:

```python
reading = sensor.get_weight('123', 0)
if reading.is_valid:
    process_weight(reading.weight)
else:
    print(f"Error: {reading.status.name}")
    # Implement retry logic or alert
```

### 4. Multi-Shelf Systems

For large deployments:

1. Use unique MUX IDs for each shelf
2. Consider multiple RS485 buses for higher throughput
3. Implement parallel polling:
   ```python
   for mux_id in ['123', '124', '125']:
       weights = sensor.get_all_weights(mux_id)
       process_shelf(mux_id, weights)
   ```

### 5. Calibration Schedule

- **Installation:** Zero all sensors when empty
- **Annual:** Re-zero to compensate for drift
- **After sensor replacement:** Zero new sensor
- **Daily:** Use software tare only

### 6. Power Considerations

- Ensure stable 12V supply (minimum 7V at MUX)
- Use repeaters for long cable runs
- Calculate power budget for multi-shelf systems

### 7. Data Logging

For inventory tracking, log changes not continuous readings:

```python
previous = current_weights
while True:
    current = sensor.get_all_weights('123')
    for i, (prev, curr) in enumerate(zip(previous, current)):
        if abs(curr.weight - prev.weight) > 0.05:  # 50g threshold
            log_change(shelf_id, sensor_id, prev.weight, curr.weight)
    previous = current
    time.sleep(1.0)
```

## Technical Specifications

| Parameter | Value |
|-----------|-------|
| Protocol | LOWA DIGI SENS (RS485) |
| Baudrate | 9600-115200 (default: 9600) |
| Measurement time | 200ms per sensor |
| Resolution | 0.001 kg (1 gram) |
| Sensors per MUX | 8 |
| Frequency range | ~14,000 Hz typical |
| Power | 12V DC (min 7V at MUX) |
| Connector | RJ-45 |
| EEPROM cycles | 100,000 writes |

## File Structure

```
DIGIsens/
├── digisens_interface.py   # Main interface library
├── examples.py              # Usage examples
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── K321e-06_lowa_protocol.pdf  # Protocol specification
├── qna.txt                 # Manufacturer Q&A
└── unnamed.png             # System diagram
```

## References

- **Protocol Specification:** K321e-06_lowa_protocol.pdf
- **Manufacturer Q&A:** qna.txt
- **System Diagram:** unnamed.png

## License

This software is provided as-is for use with DIGIsens hardware.

## Support

For hardware issues, contact the manufacturer (Romain).

For software issues:
1. Check this README
2. Review examples.py
3. Consult protocol specification PDF
4. Test with provided test program

---

**Last Updated:** 2025-11-12
