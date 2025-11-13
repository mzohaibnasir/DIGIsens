#!/usr/bin/env python3
"""
Capture raw hex data from MUX to diagnose baudrate/protocol issues.
"""
import serial
import time

def test_raw_response(port, baudrate):
    """Send broadcast command and capture raw response."""
    print(f"\n{'='*60}")
    print(f"Testing baudrate: {baudrate}")
    print('='*60)

    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0
        )

        # Build extended mode broadcast: #05ag
        message = "#05ag"
        checksum = 0
        for char in message:
            checksum ^= ord(char)
        command = f"{message}{checksum:02X}\r"

        print(f"Sending: {repr(command)}")
        print(f"Hex:     {command.encode('ascii').hex()}")

        # Send command
        ser.write(command.encode('ascii'))
        ser.flush()
        time.sleep(0.5)

        # Read raw bytes
        raw_response = ser.read(100)

        if raw_response:
            print(f"\n✓ Received {len(raw_response)} bytes")
            print(f"Raw hex: {raw_response.hex()}")
            print(f"Raw bytes: {list(raw_response)}")

            # Try to show ASCII where possible
            ascii_attempt = ""
            for byte in raw_response:
                if 32 <= byte <= 126:  # Printable ASCII
                    ascii_attempt += chr(byte)
                else:
                    ascii_attempt += f"<{byte:02X}>"
            print(f"ASCII interpretation: {ascii_attempt}")

            # Check if it looks like valid response
            if raw_response[0:1] in [b'@', b'#']:
                print("\n✓ Response starts with @ or # (good!)")
                if raw_response[-1:] == b'\r':
                    print("✓ Response ends with CR (good!)")
                else:
                    print("✗ Response doesn't end with CR")
            else:
                print("\n✗ Response doesn't start with @ or # (wrong baudrate or noise)")

            ser.close()
            return True
        else:
            print("✗ No response")
            ser.close()
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_raw_response.py /dev/ttyUSB0")
        sys.exit(1)

    port = sys.argv[1]
    baudrates = [9600, 19200, 38400, 57600, 115200]

    print("RAW DATA CAPTURE TEST")
    print("="*60)
    print("This will show the actual bytes received from the MUX")
    print("to diagnose baudrate and protocol issues.")
    print("="*60)

    for baud in baudrates:
        if test_raw_response(port, baud):
            print(f"\n*** MUX responded at {baud} baud ***")
            print("Review the hex data above to verify protocol format")
            break
        time.sleep(0.5)
    else:
        print("\n" + "="*60)
        print("No response at any baudrate")
        print("\nCheck:")
        print("  1. MUX power (12V, LED lit)")
        print("  2. RS485 wiring (pins 1-2)")
        print("  3. Only ONE MUX connected")
