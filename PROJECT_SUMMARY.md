# DIGIsens Project - Complete Summary

## Executive Summary

**DIGIsens** is an industrial-grade weight sensing system designed for retail shelf inventory management. This project provides a complete Python interface to interact with LOWA DIGI SENS protocol-based weight sensors via RS485 communication.

---

## What This System Does

### Primary Function
Automatically tracks inventory on retail shelves by continuously measuring product weight, eliminating manual stock counting.

### Key Capabilities
- **Real-time weight monitoring** with 1-gram precision
- **Multi-shelf deployment** supporting dozens of shelves simultaneously
- **Automatic change detection** when products are added or removed
- **Industrial reliability** using RS485 protocol and factory-calibrated sensors

### Use Cases
1. **Retail inventory management** - Track stock levels automatically
2. **Warehouse monitoring** - Monitor product quantities in real-time
3. **Smart vending machines** - Detect when items are dispensed
4. **Supply chain optimization** - Automated reorder triggers
5. **Loss prevention** - Detect unauthorized removals

---

## System Architecture

### Hardware Stack

```
┌──────────────────────────────────────────────────────┐
│                    Computer                          │
│              (Python Application)                    │
└────────────────────┬─────────────────────────────────┘
                     │ USB
┌────────────────────▼─────────────────────────────────┐
│              RS485-to-USB Converter                  │
│         (FTDI, CH340, or similar adapter)            │
└────────────────────┬─────────────────────────────────┘
                     │ RS485 (RJ-45)
┌────────────────────▼─────────────────────────────────┐
│                   Repeater                           │
│        (12V Power + RS485 Signal Amplifier)          │
└─────┬──────┬──────┬──────┬──────┬──────┬────────────┘
      │      │      │      │      │      │
   ┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐┌──▼──┐
   │Shelf││Shelf││Shelf││Shelf││Shelf││Shelf│
   │ 1  ││ 2  ││ 3  ││ 4  ││ 5  ││ ... │
   └──┬──┘└──┬──┘└──┬──┘└──┬──┘└──┬──┘└─────┘
      │      │      │      │      │
   8 sensors per shelf (MUX unit)
```

### Component Details

| Component | Description | Specifications |
|-----------|-------------|----------------|
| **Load Cells** | Frequency-based weight sensors | ~14,000 Hz, 1g resolution |
| **MUX** | Multiplexer unit (1 per shelf) | 8 sensors/channels, unique 16-char ID |
| **Repeater** | Power supply + signal repeater | 12V DC output, RS485 amplification |
| **Converter** | RS485-to-USB interface | 9600-115200 baud, standard USB |
| **Computer** | Data processing & storage | Any PC/server running Python 3.7+ |

### Communication Flow

```
1. Computer sends command → RS485 bus → MUX
2. MUX measures sensor frequency (200ms)
3. MUX converts frequency to weight (calibrated)
4. MUX sends response → RS485 bus → Computer
5. Computer processes data (inventory tracking)
```

---

## Protocol: LOWA DIGI SENS

### Message Structure

```
@ or # | Length | Command | Data | Checksum | CR
───┬───   ──┬──    ──┬───   ──┬──   ───┬───   ─┬─
   │        │         │        │        │       │
Prefix   2-digit   2-char   MUX+Ch   2-hex   0x0D
(@=std   length    code     address   XOR
#=ext)
```

### Example Commands

**Get single weight:**
```
Request:  @09gw12305<checksum><CR>
          @ = standard addressing
          09 = message length
          gw = get weight command
          123 = MUX ID
          05 = channel 5

Response: @13 0002.130 5C<CR>
          @13 = prefix + length
           0002.130 = 2.130 kg
                   (space) = OK status
          5C = checksum
```

**Get all weights:**
```
Request:  @08gl123<checksum><CR>
Response: @91 0001.234  0002.456  0000.023 ...<checksum><CR>
          (8 weight readings, 11 chars each)
```

### Status Flags

| Flag | Meaning | Action Required |
|------|---------|-----------------|
| ` ` (space) | OK - Valid measurement | Use the reading |
| `M` | Motion detected | Wait 1s, retry |
| `C` | Sensor not connected | Check cable |
| `E` | EEPROM error | Contact manufacturer |

---

## Python Interface

### Core Classes

#### 1. **DigiSensInterface**
Low-level protocol implementation - direct sensor communication.

```python
from digisens_interface import DigiSensInterface

with DigiSensInterface('/dev/ttyUSB0', baudrate=9600) as sensor:
    # Single sensor read
    reading = sensor.get_weight('123', 0)
    print(f"{reading.weight} kg - {reading.status.name}")

    # All sensors on shelf
    weights = sensor.get_all_weights('123')

    # Configuration
    model = sensor.get_model_number('123')
    sensor.set_baudrate('123', 115200)
```

**Key Methods:**
- `get_weight(mux_id, channel)` - Read single sensor
- `get_all_weights(mux_id)` - Read entire shelf
- `zero_sensor(mux_id, channel)` - Hardware tare (EEPROM write!)
- `poll_continuous(mux_id, channel, interval, callback)` - Continuous monitoring
- `get_mux_address()`, `get_model_number()`, `get_software_revision()` - Info queries
- `set_baudrate()` - Change communication speed

#### 2. **ShelfMonitor**
High-level inventory tracking - manages tare, change detection.

```python
from digisens_interface import ShelfMonitor

monitor = ShelfMonitor(sensor)

# Setup
monitor.add_shelf('123', num_sensors=8)
tare_weights = monitor.calibrate_shelf('123')  # Measure empty

# Track inventory
net_weights = monitor.get_net_weights('123')  # Current - tare

# Auto-detect changes
monitor.monitor_shelf('123', interval=1.0, threshold=0.05)
```

**Key Methods:**
- `add_shelf()` - Register shelf
- `calibrate_shelf()` - Software tare (empty shelf measurement)
- `get_net_weights()` - Gross weight minus tare
- `monitor_shelf()` - Continuous change detection

#### 3. **WeightReading**
Data structure for sensor measurements.

```python
reading = sensor.get_weight('123', 0)

reading.weight        # float: Weight in kg
reading.status        # StatusFlag: OK, MOTION, NOT_CONNECTED, EEPROM_ERROR
reading.is_valid      # bool: True if status == OK
reading.raw_response  # str: Original protocol response
```

---

## File Structure & Usage

### Core Files

| File | Purpose | Usage |
|------|---------|-------|
| **digisens_interface.py** | Main library | `from digisens_interface import DigiSensInterface` |
| **examples.py** | 12 usage examples | `python examples.py <1-12>` |
| **diagnostic.py** | Troubleshooting tool | `python diagnostic.py` |
| **requirements.txt** | Python dependencies | `pip install -r requirements.txt` |

### Documentation Files

| File | Content |
|------|---------|
| **README.md** | Complete technical documentation (60+ sections) |
| **QUICK_START.md** | 5-minute setup guide |
| **PROJECT_SUMMARY.md** | This file - executive overview |
| **K321e-06_lowa_protocol.pdf** | Official protocol specification (31 pages) |
| **qna.txt** | Manufacturer Q&A |
| **unnamed.png** | System topology diagram |

---

## Installation & Setup

### 1. Hardware Installation

```bash
# Physical connections
1. Connect shelves to repeater via RJ-45 cables
2. Connect repeater to 12V power supply
3. Connect repeater to RS485-USB converter
4. Connect converter to computer USB port

# Linux: Find serial port
ls /dev/ttyUSB*   # Usually /dev/ttyUSB0

# Grant permissions
sudo usermod -a -G dialout $USER
# Log out and back in
```

### 2. Software Installation

```bash
cd /home/zohaib/DIGIsens
pip install -r requirements.txt
```

### 3. Test Connection

```bash
# Auto-detect and test
python diagnostic.py

# Or manual test
python digisens_interface.py /dev/ttyUSB0 123
```

---

## Usage Workflows

### Workflow 1: Initial Setup

```python
from digisens_interface import DigiSensInterface

# 1. Connect and discover MUX ID
with DigiSensInterface('/dev/ttyUSB0') as sensor:
    mux_id = sensor.get_mux_address('000')  # Broadcast
    print(f"Found MUX: {mux_id}")

    # 2. Get MUX info
    model = sensor.get_model_number(mux_id)
    revision = sensor.get_software_revision(mux_id)
    print(f"Model: {model}, Software: {revision}")

    # 3. Test all sensors
    weights = sensor.get_all_weights(mux_id)
    for i, w in enumerate(weights):
        status = "OK" if w.is_valid else w.status.name
        print(f"Sensor {i}: {w.weight:.3f} kg [{status}]")
```

### Workflow 2: Daily Monitoring

```python
from digisens_interface import DigiSensInterface, ShelfMonitor

with DigiSensInterface('/dev/ttyUSB0') as sensor:
    monitor = ShelfMonitor(sensor)

    # One-time calibration (empty shelf)
    monitor.add_shelf('123')
    monitor.calibrate_shelf('123')

    # Continuous monitoring
    monitor.monitor_shelf('123', interval=1.0, threshold=0.05)
    # Prints: "Sensor 3: REMOVED 0.500 kg"
```

### Workflow 3: Product Tracking

```python
PRODUCTS = {
    'Milk 1L': 1.050,      # kg
    'Bread': 0.450,
    'Orange Juice': 1.100
}

previous = monitor.get_net_weights('123')

while True:
    time.sleep(1)
    current = monitor.get_net_weights('123')

    for i, (prev, curr) in enumerate(zip(previous, current)):
        change = curr - prev
        if abs(change) > 0.05:  # 50g threshold
            # Match to product
            product = None
            for name, weight in PRODUCTS.items():
                if abs(abs(change) - weight) < 0.05:
                    product = name
                    break

            if change < 0:  # Removed
                print(f"SOLD: {product} from sensor {i}")
            else:  # Added
                print(f"RESTOCKED: {product} on sensor {i}")

    previous = current
```

---

## Critical Best Practices

### 🚨 EEPROM Write Limit

The `zero_sensor()` command writes to EEPROM (100,000 cycle limit).

**ONLY use for:**
- Initial installation
- Annual calibration
- Sensor replacement

**For daily tare, use software tare:**
```python
# Store empty weight in memory/database
empty = sensor.get_weight('123', 0).weight

# Calculate net weight
current = sensor.get_weight('123', 0).weight
net = current - empty
```

### ⏱️ Timing Constraints

- **Sensor integration time:** 200ms (fixed by hardware)
- **Minimum polling interval:** 200ms
- **Recommended polling:** 1 second (allows stabilization)
- **Response time:** 5-50ms typical (varies with baudrate)

**Don't poll faster than necessary** - won't get more frequent data!

### 🔗 Multi-Sensor Items

Items spanning multiple sensors must be read simultaneously:

```python
# CORRECT: Single command reads all sensors at once
weights = sensor.get_all_weights('123')
total = weights[0].weight + weights[1].weight + weights[2].weight

# WRONG: Sequential reads have time skew
w1 = sensor.get_weight('123', 0)
time.sleep(0.5)  # Item might shift during this delay!
w2 = sensor.get_weight('123', 1)
total = w1.weight + w2.weight  # Unreliable!
```

### 🛡️ Error Handling

Always check validity before using measurements:

```python
reading = sensor.get_weight('123', 0)

if reading.status.name == 'NOT_CONNECTED':
    alert_maintenance("Sensor 0 cable disconnected")
elif reading.status.name == 'MOTION':
    time.sleep(1)
    reading = sensor.get_weight('123', 0)  # Retry
elif reading.status.name == 'EEPROM_ERROR':
    alert_critical("Sensor 0 needs recalibration")
elif reading.is_valid:
    process_weight(reading.weight)
```

### ⚡ Performance Optimization

**For large systems:**

1. **Increase baudrate:**
   ```python
   sensor.set_baudrate('123', 115200)
   ```

2. **Use `get_all_weights()` instead of multiple `get_weight()` calls:**
   ```python
   # Fast: Single command
   weights = sensor.get_all_weights('123')

   # Slow: 8 separate commands
   for i in range(8):
       w = sensor.get_weight('123', i)
   ```

3. **Parallel RS485 buses for >20 shelves**

4. **Log changes, not continuous data** (reduces storage)

---

## Troubleshooting Guide

### Connection Issues

| Problem | Solution |
|---------|----------|
| Permission denied | `sudo usermod -a -G dialout $USER` |
| Port not found | Check `ls /dev/ttyUSB*`, verify converter connected |
| No response | Check 12V power, RS485 wiring, MUX ID |
| Timeout | Try broadcast ID `'000'`, check baudrate |

### Sensor Issues

| Problem | Solution |
|---------|----------|
| NOT_CONNECTED status | Check sensor cable, verify connection to MUX |
| MOTION status | Ensure stable surface, wait 1s, retry |
| EEPROM_ERROR | Contact manufacturer for recalibration |
| Unstable readings | Check for vibration, electrical noise |
| Slow response | Increase baudrate, check cable quality |

### Run Diagnostic Tool

```bash
python diagnostic.py
```

Auto-detects issues and provides specific solutions.

---

## Technical Specifications

| Parameter | Specification |
|-----------|---------------|
| **Communication** | RS485, LOWA DIGI SENS protocol |
| **Baudrate** | 9600-115200 (default: 9600) |
| **Connector** | RJ-45 (pins 1-2: RS485, 5-6: GND, 7-8: +12V) |
| **Power** | 12V DC (min 7V at MUX) |
| **Sensors/MUX** | 8 (channels 0-7) |
| **Integration time** | 200ms per sensor |
| **Resolution** | 0.001 kg (1 gram) |
| **Sensor type** | Frequency-based load cell (~14kHz) |
| **Calibration** | Factory calibrated, stored in EEPROM |
| **EEPROM endurance** | 100,000 write cycles |
| **Topology** | Multi-drop bus (unlimited MUX units) |

---

## Example Applications

### 1. Retail Shelf Monitoring
Monitor product levels, trigger restock alerts when weight drops below threshold.

### 2. Warehouse Inventory
Track pallet weights, detect unauthorized removals, automate stock counts.

### 3. Smart Vending Machine
Detect product dispensing, track sales in real-time, manage inventory.

### 4. Laboratory Sample Tracking
Monitor sample weights, detect unauthorized access, maintain chain of custody.

### 5. Manufacturing Quality Control
Verify packaging weights, detect missing components, ensure quality compliance.

---

## Next Steps

### Getting Started (First Time Users)

1. **Run diagnostic:**
   ```bash
   python diagnostic.py
   ```

2. **Try examples:**
   ```bash
   python examples.py 1   # Basic reading
   python examples.py 4   # Inventory monitoring
   ```

3. **Read documentation:**
   - Start: `QUICK_START.md`
   - Complete: `README.md`
   - Protocol: `K321e-06_lowa_protocol.pdf`

### Development

1. **Import library:**
   ```python
   from digisens_interface import DigiSensInterface, ShelfMonitor
   ```

2. **Build your application** using the examples as templates

3. **Consult API reference** in `README.md`

### Production Deployment

1. **Hardware installation** (repeater, shelves, power)
2. **Calibration** (zero all sensors when empty)
3. **Software setup** (install dependencies, configure ports)
4. **Testing** (diagnostic tool, verify all sensors)
5. **Monitoring** (deploy application, set up logging/alerts)

---

## Support Resources

| Resource | Location |
|----------|----------|
| Quick start | `QUICK_START.md` |
| Full documentation | `README.md` |
| Code examples | `examples.py` (12 examples) |
| Troubleshooting | `diagnostic.py` |
| Protocol spec | `K321e-06_lowa_protocol.pdf` |
| Manufacturer Q&A | `qna.txt` |
| System diagram | `unnamed.png` |

For hardware support, contact the manufacturer (Romain).

---

## Project Status

✅ **Complete and production-ready**

All components delivered:
- ✅ Python interface library (`digisens_interface.py`)
- ✅ 12 comprehensive examples (`examples.py`)
- ✅ Diagnostic tool (`diagnostic.py`)
- ✅ Complete documentation (`README.md`, `QUICK_START.md`, this summary)
- ✅ Dependencies specified (`requirements.txt`)

**Ready for immediate deployment!**

---

*Last Updated: 2025-11-12*
*Project: DIGIsens Weight Sensing System*
*Location: /home/zohaib/DIGIsens*
