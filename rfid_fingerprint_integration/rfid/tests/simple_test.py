#!/usr/bin/env python3
import board
import busio
import digitalio
from adafruit_pn532.spi import PN532_SPI
import time
import binascii

# ---- CONFIG ----
USE_CE1 = False   # set True if your PN532 CS is wired to CE1 (GPIO7 / board.D7)
DEBUG_PN532 = False  # set True to enable lower-level PN532 debug from driver
# ----------------

# choose CS pin based on config
cs_pin = digitalio.DigitalInOut(board.D7 if USE_CE1 else board.D8)

# SPI setup
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

# Create PN532 object
pn532 = PN532_SPI(spi, cs_pin, debug=DEBUG_PN532)
while not spi.try_lock():
    pass
spi.configure(baudrate=50000)  # 50kHz for stability
spi.unlock()
print(f"Using CS pin: {'D7 (CE1)' if USE_CE1 else 'D8 (CE0)'}")

# check firmware
try:
    ic, ver, rev, support = pn532.firmware_version
    print(f"Found PN532 with firmware version: {ver}.{rev}")
except Exception as e:
    print("ERROR: Failed to detect PN532. Check wiring, SPI mode jumpers, and CS pin.")
    print("Driver exception:", e)
    raise

pn532.SAM_configuration()
print("Waiting for a card...\n")

def test_simple_read():
    """Try to read block 0 (manufacturer block) which doesn't need authentication"""
    try:
        # Block 0 is usually readable without authentication
        # But let's try with default key first
        key_default = bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF')
        print("Attempting to authenticate block 0 with default key...")
        
        # Get card UID first
        uid = pn532.read_passive_target(timeout=0.5)
        if uid is None:
            print("No card found")
            return False
            
        uid_bytes = bytes(uid)
        print("Found card UID:", [hex(x) for x in uid_bytes])
        
        # Try authentication with longer timeout and multiple attempts
        for attempt in range(3):
            print(f"  Authentication attempt {attempt + 1}/3...")
            try:
                # Try Key A first
                result = pn532.mifare_classic_authenticate_block(uid_bytes, 0, 0, key_default)
                if result:
                    print("  ✅ Authenticated with Key A!")
                    # Try to read block 0
                    block0 = pn532.mifare_classic_read_block(0)
                    if block0:
                        print("  Block 0 data:", [hex(x) for x in block0])
                        return True
                    else:
                        print("  ❌ Read failed after authentication")
                else:
                    print("  ❌ Authentication returned False")
                    
                # Small delay between attempts
                time.sleep(0.3)
                    
            except Exception as e:
                print(f"  ❌ Exception on attempt {attempt + 1}: {e}")
                time.sleep(0.5)
                
        return False
        
    except Exception as e:
        print(f"Test failed with exception: {e}")
        return False

try:
    while True:
        if test_simple_read():
            print("\n✅ SUCCESS! Card authentication and reading works.")
            break
        else:
            print("\n❌ Failed. Remove and reposition card, then try again...")
            time.sleep(2)

except KeyboardInterrupt:
    print("\nExiting.")