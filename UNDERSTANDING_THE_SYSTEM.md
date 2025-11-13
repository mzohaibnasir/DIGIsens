# Understanding the DIGIsens System - Complete Explanation

## Table of Contents
1. [What is This System?](#what-is-this-system)
2. [How Does It Work?](#how-does-it-work)
3. [Understanding Each Script](#understanding-each-script)
4. [Communication Flow](#communication-flow)
5. [Protocol Explained Simply](#protocol-explained-simply)
6. [What We're Testing](#what-were-testing)

---

## What is This System?

### The Big Picture

Imagine a **smart shelf in a store** that automatically knows when products are added or removed. That's DIGIsens!

```
┌─────────────────────────────────────────┐
│  RETAIL SHELF                           │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐           │
│  │ 🥛 │ │ 🍞 │ │ 🧃 │ │ 🥫 │           │
│  └─┬──┘ └─┬──┘ └─┬──┘ └─┬──┘           │
│    │      │      │      │               │
│   [Scale][Scale][Scale][Scale]          │ ← 8 weight sensors per shelf
│    └──────┴──────┴──────┘               │
│            MUX Unit                      │ ← Controller (brain of the shelf)
│              │                           │
└──────────────┼───────────────────────────┘
               │ RS485 cable
               │
         ┌─────▼──────┐
         │  Repeater  │                     ← Power supply + signal booster
         │    12V     │
         └─────┬──────┘
               │ USB
         ┌─────▼──────┐
         │  Computer  │                     ← Your Python scripts run here
         └────────────┘
```

**What happens:**
1. Product placed on shelf → Weight increases → Computer knows item was added
2. Product removed → Weight decreases → Computer knows item was sold

**Result:** Automatic inventory tracking without scanning barcodes or manual counting!

---

## How Does It Work?

### The Components

#### 1. **Weight Sensors (Load Cells)**
- **What:** Small electronic scales built into the shelf
- **How they work:** Use a vibrating wire that changes frequency based on weight
- **Frequency:** Vibrates at ~14,000 Hz when empty
- **Heavier weight:** Frequency changes (higher or lower depending on design)
- **Precision:** Can detect 1 gram (0.001 kg) changes

**Think of it like:** A guitar string - add weight, the pitch changes!

#### 2. **MUX (Multiplexer)**
- **What:** The "brain" of one shelf
- **Job:** Controls 8 weight sensors (channels 0-7)
- **What it does:**
  1. Measures frequency from each sensor (takes 200ms per sensor)
  2. Converts frequency to weight using calibration data
  3. Stores calibration in EEPROM (permanent memory)
  4. Responds to computer commands via RS485

**Think of it like:** A traffic controller managing 8 roads (sensors)

#### 3. **RS485 Communication**
- **What:** Industrial serial communication protocol
- **Why RS485:** Can go long distances (100+ meters), reliable, multiple devices on one cable
- **Wires:** Just 2 wires (A and B) + power + ground
- **Speed:** 9600 to 115200 baud (characters per second)

**Think of it like:** A telephone line, but for industrial equipment

#### 4. **The Protocol (LOWA DIGI SENS)**
- **What:** The "language" the computer and MUX use to talk
- **Format:** ASCII text (human-readable)
- **Type:** Master-slave (computer asks, MUX answers)

**Think of it like:** Speaking a specific language with grammar rules

---

## Understanding Each Script

### 1. **digisens_interface.py** - The Main Library

**What it does:** This is the "universal translator" between Python and the MUX.

**Key classes:**

#### **DigiSensInterface Class**

```python
with DigiSensInterface('/dev/ttyUSB0') as sensor:
    reading = sensor.get_weight('123', 0)
```

**What happens under the hood:**

1. **Opens serial port** (`/dev/ttyUSB0`)
   - Configures: 9600 baud, 8 data bits, no parity, 1 stop bit

2. **Builds command** (`get_weight('123', 0)`)
   ```
   Input:  MUX ID = '123', Channel = 0

   Step 1: Build message
           "@09gw12300"
           @ = standard addressing
           09 = length (9 characters)
           gw = "get weight" command
           123 = MUX ID
           00 = channel 0

   Step 2: Calculate checksum (XOR of all bytes)
           @ XOR 0 XOR 9 XOR g XOR w XOR 1 XOR 2 XOR 3 XOR 0 XOR 0
           = 0x42 (hex) = "42"

   Step 3: Add checksum and carriage return
           "@09gw1230042\r"
   ```

3. **Sends over RS485**
   - Converts to bytes: `b'@09gw1230042\r'`
   - Writes to serial port

4. **Waits for response** (timeout: 1 second)
   - MUX measures sensor (200ms)
   - MUX sends back: `@13 0002.130 5C\r`

5. **Parses response**
   ```
   "@13 0002.130 5C"

   @ = prefix
   13 = length
   (space) = sign (positive)
   0002.130 = weight (2.130 kg)
   (space) = status (OK)
   5C = checksum
   ```

6. **Returns WeightReading object**
   ```python
   reading.weight = 2.130  # kg
   reading.status = StatusFlag.OK
   reading.is_valid = True
   ```

**Why it's important:** You don't have to deal with checksums, serial ports, or protocols. Just call `get_weight()` and get the result!

---

#### **ShelfMonitor Class**

```python
monitor = ShelfMonitor(sensor)
monitor.add_shelf('123')
monitor.calibrate_shelf('123')  # Measure empty shelf
net_weights = monitor.get_net_weights('123')
```

**What it does:**

1. **Software Tare (calibration)**
   ```
   Step 1: Read all sensors when shelf is empty
           [0.123, 0.050, 0.089, 0.145, ...]  # Small offsets

   Step 2: Store as "tare weights" in memory
           tare_weights = [0.123, 0.050, 0.089, ...]

   Step 3: Later, subtract tare from measurements
           Current: [2.123, 0.050, 1.589, 0.145]
           Tare:    [0.123, 0.050, 0.089, 0.145]
           Net:     [2.000, 0.000, 1.500, 0.000]
   ```

2. **Change Detection**
   ```
   Previous: [2.000, 0.000, 1.500, 0.000]
   Current:  [2.000, 0.500, 1.500, 0.000]
                     ↑ Changed!

   Difference = 0.500 kg
   Threshold = 0.05 kg

   0.500 > 0.05 → Alert: "Sensor 1: ADDED 0.500 kg"
   ```

**Why it's important:** Handles the business logic of inventory tracking. You just get "item added" or "item removed" notifications.

---

### 2. **examples.py** - Learn By Doing

**What it does:** Shows 12 real-world scenarios with working code.

**Examples breakdown:**

#### **Example 1: Basic Reading**
```python
reading = sensor.get_weight('123', 0)
print(f"Weight: {reading.weight} kg")
```
**Teaches:** How to read a single sensor

#### **Example 4: Inventory Monitoring**
```python
monitor = ShelfMonitor(sensor)
monitor.calibrate_shelf('123')  # Empty shelf
monitor.monitor_shelf('123')    # Detect changes
```
**Teaches:** How to track when items are added/removed

#### **Example 12: Product Tracking**
```python
PRODUCTS = {'Milk': 1.050, 'Bread': 0.450}
# Detects which product based on weight change
```
**Teaches:** How to identify specific products by weight

**Why it's important:** Copy and modify these examples for your own application!

---

### 3. **diagnostic.py** - The Doctor

**What it does:** Automatically tests your hardware and finds problems.

**Tests performed:**

#### **Test 1: Serial Port Detection**
```python
ports = serial.tools.list_ports.comports()
```
**Checks:** Can Python find the RS485 converter?
**Output:** List of available serial ports

#### **Test 2: Opening Serial Port**
```python
ser = serial.Serial(port='/dev/ttyUSB0', baudrate=9600)
```
**Checks:** Can Python open the port?
**Catches:** Permission errors, port in use, driver issues

#### **Test 3: Communication Test**
```python
command = "@06ag00046\r"  # Get address command
ser.write(command.encode())
response = ser.read(100)
```
**Checks:** Does MUX respond to commands?
**Detects:** Power issues, wiring problems, wrong baudrate

#### **Test 4: MUX Discovery**
```python
for mux_id in ['000', '001', '123', '100']:
    try:
        response = sensor.get_mux_address(mux_id)
    except TimeoutError:
        continue
```
**Checks:** What is the MUX ID?
**Tries:** Common IDs and broadcast

#### **Test 5: MUX Information**
```python
model = sensor.get_model_number(mux_id)
revision = sensor.get_software_revision(mux_id)
```
**Checks:** Can we read MUX details?
**Gets:** Model number (e.g., "H1103"), firmware version

#### **Test 6: Read Sensors**
```python
weights = sensor.get_all_weights(mux_id)
for i, w in enumerate(weights):
    print(f"Channel {i}: {w.weight} kg - {w.status.name}")
```
**Checks:** Are all 8 sensors working?
**Detects:** Disconnected sensors, motion, errors

#### **Test 7: Stability Test**
```python
readings = []
for _ in range(20):  # 10 seconds
    readings.append(sensor.get_weight(mux_id, 0).weight)

range = max(readings) - min(readings)
if range < 0.005:  # 5 grams
    print("Excellent stability")
```
**Checks:** Is the sensor stable or noisy?
**Measures:** Variation over time

#### **Test 8: Response Time**
```python
start = time.time()
sensor.get_weight(mux_id, 0)
elapsed = time.time() - start
```
**Checks:** How fast does MUX respond?
**Measures:** Milliseconds per reading

**Why it's important:** Automatically finds 90% of problems without guessing!

---

### 4. **test_baudrates.py** - Speed Tester

**What it does:** Tests if MUX is set to a different communication speed.

**The problem:**
- Computer: "Hello at 9600 baud"
- MUX: *listening at 19200 baud* (hears gibberish)
- Computer: "No response!"

**The solution:**
```python
baudrates = [9600, 19200, 38400, 57600, 115200]

for baud in baudrates:
    ser = serial.Serial('/dev/ttyUSB0', baudrate=baud)
    ser.write(b'@06ag00046\r')
    response = ser.read(100)

    if response:
        print(f"MUX responds at {baud} baud!")
        break
```

**What happens:**
1. Try 9600 baud → Send command → Wait → No response
2. Try 19200 baud → Send command → Wait → Response! ✓
3. Found it! Use 19200 baud from now on

**Why it's important:** Baudrate mismatch is a common issue. This finds it automatically.

---

### 5. **test_hardware.py** - Hardware Tester

**What it does:** Tests if your RS485 converter is working (separate from MUX).

#### **Mode 1: Loopback Test**
```python
# Short RS485 A and B pins together
ser.write(b"HELLO123")
response = ser.read(100)

if response == b"HELLO123":
    print("Converter works!")
```

**What this proves:**
- USB connection works ✓
- Serial port works ✓
- RS485 converter transmits ✓
- RS485 converter receives ✓

**If it fails:**
- Converter is broken
- Not in RS485 mode
- Driver issue

#### **Mode 2: Listen**
```python
for 30 seconds:
    data = ser.read(100)
    if data:
        print(f"Received: {data}")
```

**What this proves:**
- Is MUX sending anything?
- Even garbage data means MUX is powered

**If nothing received:**
- MUX has no power
- RS485 A/B not connected

**Why it's important:** Separates converter problems from MUX problems.

---

## Communication Flow

### Example: Reading Weight from Sensor

Let's trace what happens when you run:
```python
reading = sensor.get_weight('123', 0)
```

**Step-by-step:**

```
┌──────────────┐
│ Your Program │
└──────┬───────┘
       │ sensor.get_weight('123', 0)
       ▼
┌────────────────────────┐
│ digisens_interface.py  │
│                        │
│ 1. Build command:      │
│    "@09gw12300"        │
│                        │
│ 2. Calculate checksum: │
│    XOR all bytes = 42  │
│                        │
│ 3. Final command:      │
│    "@09gw1230042\r"    │
└──────┬─────────────────┘
       │ serial.write()
       ▼
┌────────────────┐
│  Serial Port   │
│  /dev/ttyUSB0  │
└──────┬─────────┘
       │ USB cable
       ▼
┌──────────────────┐
│ RS485 Converter  │
│ (FTDI chip)      │
└──────┬───────────┘
       │ RS485 A/B wires
       ▼
┌────────────────────┐
│   MUX Unit         │
│   (ID: 123)        │
│                    │
│ 1. Receives: "@09gw1230042\r"
│ 2. Validates checksum: ✓
│ 3. Parses: Get weight, channel 0
│ 4. Measures sensor: 200ms
│ 5. Reads frequency: 14,523 Hz
│ 6. Converts to weight: 2.130 kg
│ 7. Builds response: "@13 0002.130 "
│ 8. Calculates checksum: 5C
│ 9. Sends: "@13 0002.130 5C\r"
└──────┬─────────────────┘
       │ RS485 A/B wires
       ▼
┌──────────────────┐
│ RS485 Converter  │
└──────┬───────────┘
       │ USB cable
       ▼
┌────────────────┐
│  Serial Port   │
└──────┬─────────┘
       │ serial.read()
       ▼
┌────────────────────────┐
│ digisens_interface.py  │
│                        │
│ 1. Receives: "@13 0002.130 5C\r"
│ 2. Validates checksum: ✓
│ 3. Parses:             │
│    weight = 2.130      │
│    status = OK         │
│ 4. Creates object:     │
│    WeightReading(...)  │
└──────┬─────────────────┘
       │ return
       ▼
┌──────────────┐
│ Your Program │
│              │
│ reading.weight = 2.130
│ reading.status = OK
│ reading.is_valid = True
└──────────────┘
```

**Total time:** ~250ms (200ms MUX measurement + 50ms communication)

---

## Protocol Explained Simply

### The LOWA DIGI SENS Protocol

Think of it like sending a letter:

```
┌─────────────────────────────────────┐
│ @ | 09 | gw | 12300 | 42 | CR      │ ← The "letter"
└─────────────────────────────────────┘
  │    │    │     │      │    └─ End (carriage return = seal envelope)
  │    │    │     │      └────── Checksum (verify letter wasn't corrupted)
  │    │    │     └───────────── Data (address: MUX 123, channel 0)
  │    │    └─────────────────── Command (gw = get weight)
  │    └──────────────────────── Length (9 characters in message)
  └───────────────────────────── Prefix (@ = standard addressing)
```

### Commands (The Vocabulary)

| Command | English | What It Does | Example |
|---------|---------|--------------|---------|
| `gw` | Get Weight | Read one sensor | `@09gw12300` → "Read MUX 123, channel 0" |
| `gl` | Get List | Read all sensors | `@08gl123` → "Read all sensors on MUX 123" |
| `sz` | Set Zero | Tare sensor | `@09sz12300` → "Zero MUX 123, channel 0" |
| `ag` | Address Get | Get MUX ID | `@06ag000` → "What's your ID?" |
| `gm` | Get Model | Get model number | `@06gm123` → "What model are you?" |
| `gr` | Get Revision | Get firmware | `@06gr123` → "What firmware version?" |
| `br` | Baudrate | Change speed | `@07br1231` → "Switch to 19200 baud" |

### Responses (The Reply)

```
@13 0002.130 5C
│   │        └─ Checksum (verify reply)
│   └────────── Weight + status
│               [ ][0002.130][ ]
│                │      │      └─ Status flag
│                │      └──────── Weight (2.130 kg)
│                └─────────────── Sign (space = positive, - = negative)
└─────────────── Prefix + length
```

**Status Flags:**
- ` ` (space) = OK, measurement is good
- `M` = Motion detected, wait and retry
- `C` = Cable not connected, check wiring
- `E` = EEPROM error, sensor needs repair

---

## What We're Testing

### Your Current Situation

You ran `diagnostic.py` and got "No response from sensor". Here's what we're checking:

#### **Is the port accessible?**
✓ **YES** - Port opened successfully

#### **Is the MUX powered?**
❓ **CHECKING** - Need to verify:
- Is LED lit on MUX?
- Is 12V power connected?

#### **Is the baudrate correct?**
❓ **CHECKING** - Run `test_baudrates.py`
- Tests: 9600, 19200, 38400, 57600, 115200
- If any responds → that's the right speed

#### **Is the MUX sending anything?**
❓ **CHECKING** - Run `test_hardware.py /dev/ttyUSB0 listen`
- Waits 30 seconds
- Any data = MUX is alive
- No data = power or wiring issue

#### **Is the RS485 converter working?**
❓ **CHECKING** - Run `test_hardware.py /dev/ttyUSB0 loopback`
- Short A and B pins together
- Echo test
- If works → converter OK, problem is MUX side

#### **Is the wiring correct?**
❓ **CHECKING** - Physical inspection:
- Pin 1-2: RS485 A/B
- Pin 5-6: Ground
- Pin 7-8: +12V
- Try swapping A and B if nothing else works

---

## The Big Picture: Why Each Script Exists

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR APPLICATION                         │
│  "I want to track inventory on my retail shelves"           │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ examples.py │  │   Your Own  │  │ Custom App  │
│             │  │   Script    │  │             │
│ "Learn how  │  │             │  │             │
│  to use it" │  │ "Modified   │  │ "Production │
│             │  │  example"   │  │  system"    │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
         ▼              ▼              ▼
┌──────────────────────────────────────────────┐
│      digisens_interface.py                   │
│                                              │
│  "The universal translator"                 │
│  • Handles protocol                         │
│  • Calculates checksums                     │
│  • Manages serial port                      │
│  • Parses responses                         │
│  • Error handling                           │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  Hardware (MUX + Sensors)                    │
└──────────────────────────────────────────────┘

Meanwhile, when things don't work:

┌──────────────────────────────────────────────┐
│           diagnostic.py                      │
│  "The doctor - finds what's wrong"           │
├──────────────────────────────────────────────┤
│  • Test 1: Find serial ports                 │
│  • Test 2: Open port                         │
│  • Test 3: Talk to MUX                       │
│  • Test 4: Find MUX ID                       │
│  • Test 5: Get MUX info                      │
│  • Test 6: Read sensors                      │
│  • Test 7: Stability test                    │
│  • Test 8: Speed test                        │
└──────────────┬───────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌──────┐  ┌──────┐  ┌──────────┐
│ test_│  │ test_│  │minicom   │
│ baud │  │ hard │  │          │
│ rates│  │ ware │  │"Manual   │
│      │  │      │  │ testing" │
│"Find │  │"Test │  └──────────┘
│ the  │  │ conv │
│ speed│  │ erter│
└──────┘  └──────┘
```

---

## Summary

### What Each Script Does:

1. **digisens_interface.py**
   - The core library
   - Speaks the LOWA protocol
   - You import this in your code

2. **examples.py**
   - 12 working examples
   - Copy and modify for your needs
   - Shows best practices

3. **diagnostic.py**
   - Automatic problem finder
   - 8 comprehensive tests
   - Run when something doesn't work

4. **test_baudrates.py**
   - Tests all communication speeds
   - Finds baudrate mismatches
   - Quick focused test

5. **test_hardware.py**
   - Tests RS485 converter separately
   - Loopback mode + listen mode
   - Isolates hardware vs software issues

### What You Should Do Now:

1. **Check hardware:**
   - Is MUX LED lit?
   - Is 12V power connected?

2. **Run tests:**
   ```bash
   python test_baudrates.py /dev/ttyUSB0 000
   python test_hardware.py /dev/ttyUSB0 listen
   ```

3. **Once working:**
   - Run examples: `python examples.py 1`
   - Build your app using `digisens_interface.py`

---

**Remember:** The scripts are tools to help you. The MUX does the actual work of measuring weight. We're just trying to talk to it!

