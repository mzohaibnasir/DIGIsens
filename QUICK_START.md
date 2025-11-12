# DIGIsens Quick Start Guide

## What is DIGIsens?

DIGIsens is a **retail shelf weight monitoring system** that tracks inventory automatically using load cells integrated into shelves. Perfect for smart retail, warehouses, and automated stock management.

## How It Works

```
Product placed/removed → Weight sensor detects change → System logs inventory change
```

**Key Components:**
- **Load cells** in shelves measure weight (1g precision)
- **MUX unit** controls 8 sensors per shelf
- **RS485** connects everything to your computer
- **Python script** reads data and tracks inventory

## 5-Minute Setup

### 1. Hardware Connection

```
Computer → USB-to-RS485 → Repeater → Shelf MUX → 8 Weight Sensors
                          (12V power)
```

### 2. Install Software

```bash
cd /home/zohaib/DIGIsens
pip install pyserial
```

### 3. Find Your Serial Port

**Linux:**
```bash
ls /dev/ttyUSB*    # Usually /dev/ttyUSB0
```

**Windows:**
Check Device Manager → Ports → COM3, COM4, etc.

### 4. Test Connection

```bash
python diagnostic.py
```

Follow the prompts to auto-detect your sensors.

### 5. Read Weights

```python
from digisens_interface import DigiSensInterface

with DigiSensInterface('/dev/ttyUSB0') as sensor:
    # Read all sensors on shelf
    weights = sensor.get_all_weights('123')  # MUX ID = 123

    for i, reading in enumerate(weights):
        print(f"Sensor {i}: {reading.weight:.3f} kg")
```

Run it:
```bash
python my_script.py
```

## Common Tasks

### Monitor Shelf for Changes

```python
from digisens_interface import DigiSensInterface, ShelfMonitor

with DigiSensInterface('/dev/ttyUSB0') as sensor:
    monitor = ShelfMonitor(sensor)
    monitor.add_shelf('123')
    monitor.calibrate_shelf('123')  # Measure empty shelf
    monitor.monitor_shelf('123', interval=1.0)  # Detect changes
```

### Continuous Polling

```python
with DigiSensInterface('/dev/ttyUSB0') as sensor:
    sensor.poll_continuous('123', 0, interval=1.0)  # Every 1 second
```

### Check Sensor Status

```python
reading = sensor.get_weight('123', 0)

if reading.is_valid:
    print(f"Weight: {reading.weight} kg")
else:
    print(f"Error: {reading.status.name}")
    # Status: MOTION, NOT_CONNECTED, or EEPROM_ERROR
```

## Understanding MUX IDs

Each shelf has a MUX (multiplexer) with an ID:

- **Standard ID:** 3 digits (e.g., `'123'`)
- **Extended ID:** 16 characters (e.g., `'0120220429103142'`)
- **Broadcast:** `'000'` talks to any MUX

**Find your MUX ID:**
```python
sensor.get_mux_address('000')  # Broadcast query
```

## Channel Numbers

Each MUX controls 8 sensors: channels 0-7

```
MUX 123
├── Channel 0 (sensor 1)
├── Channel 1 (sensor 2)
├── ...
└── Channel 7 (sensor 8)
```

## Important Notes

### ⚠️ NEVER Over-Use `zero_sensor()`

The `zero_sensor()` command writes to EEPROM (limited to 100,000 cycles).

**Only use for:**
- Initial installation
- Annual calibration

**For daily tare, use software:**
```python
empty_weight = sensor.get_weight('123', 0).weight  # Store this
current_weight = sensor.get_weight('123', 0).weight
net_weight = current_weight - empty_weight
```

### Minimum Polling Interval

- Sensors need **200ms** to measure
- Recommended: **1 second** per reading
- Reading faster won't give more frequent updates

### Multi-Sensor Items

If an item spans multiple sensors, read them all at once:

```python
weights = sensor.get_all_weights('123')  # Simultaneous read
total = weights[0].weight + weights[1].weight + weights[2].weight
```

Don't read individually with delays - item might shift!

## Troubleshooting

### "Permission denied" on /dev/ttyUSB0

```bash
sudo usermod -a -G dialout $USER
# Log out and back in
```

### "No response from sensor"

1. Check MUX ID (try `'000'`)
2. Check 12V power supply
3. Check RS485 wiring (pins 1-2 on RJ-45)
4. Run diagnostic: `python diagnostic.py`

### Sensor shows "NOT_CONNECTED"

- Cable disconnected
- Check sensor connection to MUX

### Sensor shows "MOTION"

- Weight is changing
- Vibration or unstable surface
- Wait 1 second and retry

### Slow readings

Increase baudrate:
```python
sensor.set_baudrate('123', 115200)
# Reconnect with baudrate=115200
```

## Example Scripts

### 1. Basic Reading
```bash
python examples.py 1
```

### 2. Inventory Monitoring
```bash
python examples.py 4
```

### 3. Product Tracking
```bash
python examples.py 12
```

### Full Test Program
```bash
python digisens_interface.py /dev/ttyUSB0 123
```

## Files Reference

| File | Purpose |
|------|---------|
| `digisens_interface.py` | Main library - import this |
| `examples.py` | 12 usage examples |
| `diagnostic.py` | Troubleshooting tool |
| `README.md` | Complete documentation |
| `requirements.txt` | Python dependencies |
| `K321e-06_lowa_protocol.pdf` | Protocol specification |

## Protocol Basics

### Commands

| Command | What it does | Example |
|---------|--------------|---------|
| `gw` | Get single weight | `@09gw12300` → Read MUX 123, channel 0 |
| `gl` | Get all weights | `@08gl123` → Read all sensors on MUX 123 |
| `ag` | Get MUX address | `@06ag000` → Query MUX ID |

### Response Format

```
@13 0002.130 5C
    ^^^^^^^^ weight in kg
            ^ status flag (space=OK, M=motion, C=disconnected)
```

## Performance Tips

1. **Use `get_all_weights()` instead of multiple `get_weight()` calls**
   - Faster for reading entire shelf

2. **Increase baudrate for large systems**
   ```python
   sensor.set_baudrate('123', 115200)
   ```

3. **Log changes, not continuous data**
   - Store only when weight changes > threshold
   - Reduces data volume

4. **Use multiple RS485 buses for many shelves**
   - Each bus can handle ~10-20 shelves
   - Parallel processing

## Next Steps

1. ✅ Run diagnostic: `python diagnostic.py`
2. ✅ Try examples: `python examples.py`
3. ✅ Read full docs: `README.md`
4. ✅ Review protocol: `K321e-06_lowa_protocol.pdf`
5. ✅ Build your application!

## Support

- Hardware questions → Contact manufacturer
- Software questions → Check `README.md` and examples
- Protocol questions → See `K321e-06_lowa_protocol.pdf`

---

**You're ready to go! 🚀**

Start with: `python diagnostic.py`
