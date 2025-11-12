#!/usr/bin/env python3
"""
Test multiple baudrates to find the correct one
"""
import serial
import time

def test_baudrate(port, baudrate, mux_id='000'):
    """Test a specific baudrate."""
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.5
        )

        # Build command: @06ag000<checksum>\r
        message = f"@06ag{mux_id}"
        checksum = 0
        for char in message:
            checksum ^= ord(char)
        command = f"{message}{checksum:02X}\r"

        # Send command
        ser.write(command.encode('ascii'))
        time.sleep(0.3)

        # Read response
        response = ser.read(100).decode('ascii', errors='ignore').strip()

        ser.close()

        return response

    except Exception as e:
        return None

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_baudrates.py /dev/ttyUSB0 [mux_id]")
        sys.exit(1)

    port = sys.argv[1]
    mux_id = sys.argv[2] if len(sys.argv) > 2 else '000'

    baudrates = [9600, 19200, 38400, 57600, 115200]

    print("Testing baudrates on", port)
    print("=" * 60)

    for baud in baudrates:
        print(f"\nTesting {baud:6d} baud...", end=' ')
        response = test_baudrate(port, baud, mux_id)

        if response:
            print(f"✓ RESPONSE: {repr(response)}")
            print(f"\n*** SUCCESS! MUX responds at {baud} baud ***")
            break
        else:
            print("✗ No response")
    else:
        print("\n" + "=" * 60)
        print("No response at any baudrate.")
        print("\nPossible issues:")
        print("  1. MUX not powered (check 12V supply)")
        print("  2. RS485 wiring incorrect")
        print("  3. Wrong MUX ID (check label on MUX)")
        print("  4. RS485 converter polarity reversed")
