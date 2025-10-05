#!/usr/bin/env python3
import board
import busio
import digitalio
from adafruit_pn532.spi import PN532_SPI
import time
import binascii

# ---- CONFIG ----
USE_CE1 = False
DEBUG_PN532 = False
# ----------------

cs_pin = digitalio.DigitalInOut(board.D7 if USE_CE1 else board.D8)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
pn532 = PN532_SPI(spi, cs_pin, debug=DEBUG_PN532)

while not spi.try_lock():
    pass
spi.configure(baudrate=50000)
spi.unlock()

print(f"Using CS pin: {'D7 (CE1)' if USE_CE1 else 'D8 (CE0)'}")

# check firmware
try:
    ic, ver, rev, support = pn532.firmware_version
    print(f"Found PN532 with firmware version: {ver}.{rev}")
except Exception as e:
    print("ERROR: Failed to detect PN532:", e)
    raise

# Configure with different settings for better card handling
pn532.SAM_configuration()

print("Testing RF field and card power...")
print("Place card on reader and hold steady...\n")

def enhanced_card_test():
    try:
        # First, detect card with longer timeout
        print("Step 1: Detecting card...")
        uid = pn532.read_passive_target(timeout=2.0)
        if uid is None:
            return False
            
        uid_bytes = bytes(uid)
        print(f"✅ Card detected: UID = {binascii.hexlify(uid_bytes).decode().upper()}")
        
        # Give card more time to stabilize
        print("Step 2: Waiting for card to stabilize...")
        time.sleep(0.5)
        
        # Re-detect to ensure stable connection
        print("Step 3: Re-detecting for stability...")
        uid2 = pn532.read_passive_target(timeout=1.0)
        if uid2 is None:
            print("❌ Card lost during re-detection")
            return False
            
        if bytes(uid2) != uid_bytes:
            print("❌ UID changed during re-detection")
            return False
            
        print("✅ Card connection stable")
        
        # Now try authentication with maximum delays
        print("Step 4: Attempting authentication...")
        key_default = bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF')
        
        # Try with extra delay before auth
        time.sleep(0.2)
        
        try:
            # Try block 1 instead of 0 (block 0 has special properties)
            result = pn532.mifare_classic_authenticate_block(uid_bytes, 1, 0, key_default)
            if result:
                print("✅ Authentication successful!")
                
                # Try to read the block
                block_data = pn532.mifare_classic_read_block(1)
                if block_data:
                    print(f"✅ Block 1 data: {[hex(x) for x in block_data]}")
                    return True
                else:
                    print("❌ Read failed after successful auth")
            else:
                print("❌ Authentication returned False")
                
        except Exception as e:
            print(f"❌ Authentication exception: {e}")
            
            # Try one more time with block 4
            print("Trying block 4 as fallback...")
            time.sleep(0.3)
            try:
                result = pn532.mifare_classic_authenticate_block(uid_bytes, 4, 0, key_default)
                if result:
                    print("✅ Block 4 authentication successful!")
                    block_data = pn532.mifare_classic_read_block(4)
                    if block_data:
                        print(f"✅ Block 4 data: {[hex(x) for x in block_data]}")
                        return True
                else:
                    print("❌ Block 4 authentication also failed")
            except Exception as e2:
                print(f"❌ Block 4 also failed: {e2}")
        
        return False
        
    except Exception as e:
        print(f"Test failed with exception: {e}")
        return False

try:
    test_count = 0
    while test_count < 5:  # Try 5 times max
        test_count += 1
        print(f"\n=== Test attempt {test_count}/5 ===")
        
        if enhanced_card_test():
            print(f"\n🎉 SUCCESS after {test_count} attempts!")
            print("The card authentication is working!")
            break
        else:
            print(f"\n❌ Test {test_count} failed.")
            if test_count < 5:
                print("Remove card completely, wait 2 seconds, then place it back...")
                time.sleep(3)
    
    if test_count == 5:
        print("\n⚠️  All 5 attempts failed.")
        print("Possible issues:")
        print("1. Card might not be MIFARE Classic 1K")
        print("2. Power supply issues (try different power source)")
        print("3. Wiring issues (double-check all connections)")
        print("4. Card damage or unusual access control")
        print("5. SPI speed still too fast (try even slower)")

except KeyboardInterrupt:
    print("\nExiting.")