# DIGIsens Troubleshooting Guide

## No Response from MUX - Complete Diagnostic Guide

If you're getting "No response from sensor" errors, this guide will help you identify and fix the issue.

---

## Quick Diagnostic Commands

### Test 1: Try Different Baudrates
```bash
python test_baudrates.py /dev/ttyUSB0 000
```

### Test 2: Listen for Any Data
```bash
python test_hardware.py /dev/ttyUSB0 listen
```

### Test 3: Raw Serial Terminal
```bash
# Install minicom if not available
sudo apt install minicom

# Open serial terminal
minicom -D /dev/ttyUSB0 -b 9600

# Type some characters and see if anything comes back
# Press Ctrl+A then X to exit
```

---

## Hardware Checklist

### ✅ Power Supply

**Check these items:**

- [ ] 12V DC adapter plugged in and turned ON
- [ ] Power LED on MUX unit is lit (green or red)
- [ ] Voltage at MUX input is at least 7V (use multimeter)
- [ ] Power supply rated for sufficient current (check MUX specs)

**RJ-45 Power Pins:**
- Pin 7-8: +12V
- Pin 5-6: GND (Ground)

**Test:**
```bash
# Use multimeter to measure voltage
# Between pins 7-8 and pins 5-6 on the RJ-45 connector
# Should read approximately 12V DC
```

**Common Issues:**
- Power adapter unplugged or failed
- Repeater not powered
- Voltage drop in long cables (should be >7V at MUX)
- Wrong polarity

---

### ✅ MUX Connection

**Check these items:**

- [ ] RJ-45 cable firmly connected to MUX unit
- [ ] RJ-45 cable firmly connected to repeater/converter
- [ ] Cable is not damaged (no cuts, crimps, or breaks)
- [ ] Using correct cable type (Cat5e or better)
- [ ] Cable length within limits (typically <100m per segment)

**Test:**
```bash
# Unplug and replug both ends of cable
# Try a different RJ-45 cable if available
# Check for damaged connectors or bent pins
```

---

### ✅ RS485 Wiring

**RJ-45 Pin Layout:**
```
Pin 1: RS485 A (or +)
Pin 2: RS485 B (or -)
Pin 3: Not used
Pin 4: Not used
Pin 5: GND
Pin 6: GND
Pin 7: +12V
Pin 8: +12V
```

**Check these items:**

- [ ] RS485 A (pin 1) properly connected
- [ ] RS485 B (pin 2) properly connected
- [ ] A and B are not reversed
- [ ] Ground connected (pins 5-6)
- [ ] Power connected (pins 7-8)

**Common Issues:**
- RS485 A and B reversed (swap them)
- Poor connection at RJ-45 connector
- Wrong wire colors used during crimping
- Cable wired as "crossover" instead of straight-through

**Test:**
```bash
# Check continuity with multimeter
# Pin 1 on one end should connect to Pin 1 on other end
# Pin 2 to Pin 2, etc.
```

---

### ✅ RS485 Converter

**Check these items:**

- [ ] Converter set to RS485 mode (not RS232)
- [ ] Half-duplex configuration (2-wire RS485)
- [ ] Termination resistor installed if needed (120Ω)
- [ ] USB connection to computer is solid
- [ ] Correct drivers installed (FTDI, CH340, etc.)

**Converter Types:**

**FTDI-based (USB VID:PID=0403:6001):**
- Usually auto-configure correctly
- May need 120Ω termination resistor

**CH340-based:**
- Requires driver installation
- Check mode switch if present

**Generic USB-to-RS485:**
- May have physical switch for RS485/RS232
- Check polarity markings (A/B or +/-)

**Test:**
```bash
# Hardware loopback test
python test_hardware.py /dev/ttyUSB0 loopback

# Follow instructions to short A and B pins
# This tests if converter is working
```

---

### ✅ MUX Configuration

**Check these items:**

- [ ] Know the correct MUX ID (check label on MUX unit)
- [ ] Know the configured baudrate (default: 9600)
- [ ] MUX firmware is operational
- [ ] No conflicting MUX IDs on the bus

**Finding MUX ID:**

The MUX has a label with:
- **Standard ID:** 3 digits (e.g., "123")
- **Extended ID:** 16 characters (e.g., "0120220429103142")

**Using Protocol Broadcast:**
```bash
# Use broadcast address as per LOWA protocol specification
python diagnostic.py /dev/ttyUSB0

# The diagnostic will automatically use broadcast '000'
# If broadcast fails, this indicates a hardware/configuration issue,
# not an ID problem. Check power, wiring, and baudrate.
```

**If broadcast fails:**
1. Check the physical label on the MUX device for the correct ID
2. Run baudrate test: `python test_baudrates.py /dev/ttyUSB0 000`
3. Verify 12V power supply is connected and working
4. Check RS485 wiring (pins 1-2 on RJ-45)

**For standard 3-digit MUX ID:**
```bash
# Use the ID from the MUX label
python diagnostic.py /dev/ttyUSB0 <YOUR_MUX_ID>
```

**For extended 16-character manufacturer ID:**
```python
from digisens_interface import DigiSensInterface

with DigiSensInterface('/dev/ttyUSB0') as sensor:
    reading = sensor.get_weight('0120220429103142', 0, use_extended=True)
```

---

## Step-by-Step Diagnostic Procedure

### Step 1: Verify Serial Port Access

```bash
# Check port exists
ls -l /dev/ttyUSB0

# Check permissions
groups

# Should show 'dialout' group
# If not:
sudo usermod -a -G dialout $USER
newgrp dialout
```

**Expected:** Port opens successfully ✓

---

### Step 2: Test Baudrates

```bash
python test_baudrates.py /dev/ttyUSB0 000
```

**Possible Results:**

✓ **Response received at specific baudrate**
- MUX is working!
- Use that baudrate for all future connections
- Update code: `DigiSensInterface('/dev/ttyUSB0', baudrate=19200)`

✗ **No response at any baudrate**
- Power issue (most common)
- Wiring issue
- Wrong MUX ID
- Continue to Step 3

---

### Step 3: Listen for Any Data

```bash
python test_hardware.py /dev/ttyUSB0 listen
```

**Possible Results:**

✓ **Data received**
- MUX is powered and transmitting
- Baudrate or protocol issue
- Check MUX documentation for baudrate
- Verify command format

✗ **No data after 30 seconds**
- MUX not powered (check 12V)
- RS485 wiring incorrect
- MUX hardware failure
- Continue to Step 4

---

### Step 4: Hardware Loopback Test

```bash
python test_hardware.py /dev/ttyUSB0 loopback
```

**Preparation:**
1. Disconnect RS485 cable from MUX
2. Short RS485 A and B pins together (use wire or jumper)
3. Run the test

**Possible Results:**

✓ **Echo received**
- RS485 converter is working
- Problem is with MUX or wiring to MUX
- Check MUX power supply
- Verify cable to MUX

✗ **No echo**
- RS485 converter issue
- Not in RS485 mode (check switch)
- Converter hardware failure
- A/B pins not properly shorted

---

### Step 5: Check MUX Power

**Visual Check:**
- Look for LED on MUX unit
- Green or red LED should be lit
- If no LED, MUX has no power

**Multimeter Check:**
```
1. Set multimeter to DC voltage (20V range)
2. Measure between RJ-45 pins 7-8 (+) and pins 5-6 (-)
3. Should read approximately 12V DC
4. Minimum 7V required at MUX input
```

**If voltage is correct but MUX doesn't respond:**
- MUX hardware failure
- Contact manufacturer
- Check warranty/support

**If voltage is low or zero:**
- Check power supply (12V adapter)
- Check cable continuity
- Check repeater if using one
- Voltage drop over long cables

---

### Step 6: Check RS485 Polarity

**RS485 A and B might be reversed.**

**Try swapping:**
1. Disconnect from MUX
2. Note which wire goes to pin 1 (A) and pin 2 (B)
3. Swap them (A to B, B to A)
4. Test again

**Or use code to test both polarities:**
```bash
# Some converters have reversible polarity
# Check converter documentation for polarity switch
```

---

### Step 7: Try Specific MUX IDs

**If broadcast '000' doesn't work, try specific IDs:**

```bash
# Check label on MUX for ID
# Try that specific ID

python diagnstic.py /dev/ttyUSB0 <YOUR_MUX_ID>
```

**Example:** If MUX label says "ID: 0120220429103142"

```python
from digisens_interface import DigiSensInterface

with DigiSensInterface('/dev/ttyUSB0') as sensor:
    # Use extended addressing mode
    weights = sensor.get_all_weights('0120220429103142', use_extended=True)
    print(weights)
```

---

## Common Error Messages

### "Permission denied: /dev/ttyUSB0"

**Solution:**
```bash
sudo usermod -a -G dialout $USER
newgrp dialout
```

Then log out and back in.

---

### "No response from sensor"

**Most Common Causes:**

1. **MUX not powered** (90% of cases)
   - Check 12V power supply
   - Verify LED is lit on MUX

2. **Wrong baudrate** (5% of cases)
   - Run: `python test_baudrates.py /dev/ttyUSB0 000`

3. **RS485 wiring incorrect** (3% of cases)
   - Check A/B connections
   - Try swapping A and B

4. **Wrong MUX ID** (2% of cases)
   - Check label on MUX
   - Try broadcast '000'

---

### "TimeoutError"

Same as "No response from sensor" - see above.

---

### "Failed to connect to /dev/ttyUSB0"

**Causes:**
- Port doesn't exist (check `ls /dev/ttyUSB*`)
- Permission issue (see above)
- Another program using port (close minicom, screen, etc.)

**Solution:**
```bash
# Check what's using the port
sudo lsof /dev/ttyUSB0

# Kill the process if needed
sudo killall minicom
```

---

## Testing with Minicom

**Install:**
```bash
sudo apt install minicom
```

**Configure:**
```bash
minicom -s
```

Settings:
- Serial Device: /dev/ttyUSB0
- Baud Rate: 9600
- Data bits: 8
- Parity: None
- Stop bits: 1
- Hardware flow control: No
- Software flow control: No

**Test Manually:**

Type command (you won't see what you type):
```
@06ag00046<Enter>
```

Expected response:
```
@...some response...
```

If you see a response, MUX is working!

---

## Testing with Python Interactive Mode

```bash
python3
```

```python
import serial
import time

# Open port
ser = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=1)

# Build command
message = "@06ag000"
checksum = 0
for c in message:
    checksum ^= ord(c)
command = f"{message}{checksum:02X}\r"

print(f"Sending: {repr(command)}")

# Send
ser.write(command.encode('ascii'))
time.sleep(0.5)

# Read response
response = ser.read(100)
print(f"Received: {repr(response)}")

if response:
    print("SUCCESS - MUX is responding!")
else:
    print("NO RESPONSE - Check power and wiring")

ser.close()
```

---

## Advanced Diagnostics

### Check USB Device
```bash
lsusb
```

Look for FTDI device:
```
Bus 001 Device 005: ID 0403:6001 Future Technology Devices International, Ltd FT232 Serial (UART) IC
```

### Check Kernel Messages
```bash
dmesg | grep tty | tail -20
```

Should show:
```
[ 1234.567890] usb 1-1: FTDI USB Serial Device converter now attached to ttyUSB0
```

### Check Serial Port Info
```bash
python3 -c "import serial.tools.list_ports; [print(f'{p.device}: {p.description}') for p in serial.tools.list_ports.comports()]"
```

### Test Different Timeout Values
```python
from digisens_interface import DigiSensInterface

# Try longer timeout
with DigiSensInterface('/dev/ttyUSB0', timeout=5.0) as sensor:
    reading = sensor.get_weight('000', 0)
```

---

## Contact Manufacturer

If all else fails, contact the manufacturer (Romain) with this information:

**Hardware Details:**
- MUX model number: (check label)
- MUX ID: (from physical label on device)
- Power supply voltage: (measure with multimeter)
- LED status: (on/off, color)

**Software Details:**
- Baudrates tested: 9600, 19200, 38400, 57600, 115200
- Broadcast response: (success/timeout)
- Response to loopback test: (pass/fail)

**Diagnostic Results:**
```bash
# Run and save output
python test_baudrates.py /dev/ttyUSB0 000 > test_results.txt
python test_hardware.py /dev/ttyUSB0 listen >> test_results.txt
```

Send `test_results.txt` to manufacturer.

---

## Summary Flowchart

```
No Response from MUX?
│
├─ Port won't open?
│  └─ Fix permissions: sudo usermod -a -G dialout $USER
│
├─ Port opens but no response?
│  │
│  ├─ Is MUX powered? (Check LED)
│  │  ├─ NO → Check 12V power supply
│  │  └─ YES → Continue
│  │
│  ├─ Test baudrates: python test_baudrates.py /dev/ttyUSB0 000
│  │  ├─ Response? → Use that baudrate
│  │  └─ No response? → Continue
│  │
│  ├─ Listen for data: python test_hardware.py /dev/ttyUSB0 listen
│  │  ├─ Data received? → Check protocol/baudrate
│  │  └─ No data? → Continue
│  │
│  ├─ Hardware loopback: python test_hardware.py /dev/ttyUSB0 loopback
│  │  ├─ Echo works? → MUX or wiring issue
│  │  └─ No echo? → RS485 converter issue
│  │
│  └─ Check:
│     ├─ RS485 A/B polarity (try swapping)
│     ├─ Correct MUX ID (check label)
│     ├─ Cable continuity (test with multimeter)
│     └─ Contact manufacturer if all else fails
```

---

## Prevention / Best Practices

### Before Connecting Software

1. ✅ Verify 12V power at MUX (multimeter)
2. ✅ Check LED is lit on MUX
3. ✅ Verify cable connections are secure
4. ✅ Note MUX ID from label
5. ✅ Test with loopback first
6. ✅ Start with broadcast ID '000'

### During Operation

1. ✅ Monitor power supply stability
2. ✅ Check for loose connections regularly
3. ✅ Log all errors for pattern analysis
4. ✅ Keep backup cables and power supplies
5. ✅ Document working configuration

### Maintenance Schedule

- **Daily:** Visual LED check
- **Weekly:** Test connection with diagnostic script
- **Monthly:** Clean connectors, check cables
- **Annually:** Replace preventively worn cables

---

## Quick Reference Commands

```bash
# Find serial ports
ls /dev/ttyUSB*

# Fix permissions
sudo usermod -a -G dialout $USER
newgrp dialout

# Test baudrates
python test_baudrates.py /dev/ttyUSB0 000

# Listen for data
python test_hardware.py /dev/ttyUSB0 listen

# Hardware loopback
python test_hardware.py /dev/ttyUSB0 loopback

# Full diagnostic
python diagnstic.py

# Quick test with specific MUX
python diagnstic.py /dev/ttyUSB0 123

# Manual serial terminal
minicom -D /dev/ttyUSB0 -b 9600
```

---

**Last Updated:** 2025-11-12
**Project:** DIGIsens Weight Sensing System
