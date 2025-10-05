#!/usr/bin/env python3
import board
import busio
import digitalio
from adafruit_pn532.spi import PN532_SPI
import time
import binascii

print("=== Arduino-Style MIFARE Authentication ===")
print("Attempting to mimic Arduino MFRC522 behavior\n")

cs_pin = digitalio.DigitalInOut(board.D8)  # Use your working CE0
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
pn532 = PN532_SPI(spi, cs_pin, debug=False)

while not spi.try_lock():
    pass
spi.configure(baudrate=50000)
spi.unlock()

ic, ver, rev, support = pn532.firmware_version
print(f"PN532 firmware: {ver}.{rev}")

# Configure with different SAM settings (more like Arduino)
pn532.SAM_configuration()

def arduino_style_auth():
    """Try authentication with Arduino-like timing and approach"""
    
    print("Waiting for card...")
    
    # Step 1: Detect card with multiple attempts (Arduino style)
    uid = None
    for attempt in range(10):
        uid = pn532.read_passive_target(timeout=0.2)
        if uid:
            break
        time.sleep(0.1)
    
    if not uid:
        return False
    
    uid_bytes = bytes(uid)
    print(f"Card found: {binascii.hexlify(uid_bytes).decode().upper()}")
    
    # Step 2: Multiple re-selections (Arduino MFRC522 often does this)
    print("Re-selecting card for stability...")
    for i in range(3):
        uid2 = pn532.read_passive_target(timeout=0.1)
        if uid2 and bytes(uid2) == uid_bytes:
            print(f"  Re-selection {i+1}: ✅")
        else:
            print(f"  Re-selection {i+1}: ❌")
        time.sleep(0.05)
    
    # Step 3: Try different blocks with Arduino-typical approach
    key = bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF')
    
    # Arduino usually starts with sector trailer blocks or specific data blocks
    test_blocks = [4, 8, 12, 16, 1, 2, 5, 6]  # Different block order
    
    for block in test_blocks:
        if block > 63:  # Skip invalid blocks for 1K cards
            continue
            
        print(f"\nTesting block {block}:")
        
        # Try Key A first, then Key B (Arduino default order)
        for key_type in [0, 1]:  # 0=KeyA, 1=KeyB
            key_name = "A" if key_type == 0 else "B"
            print(f"  Key {key_name}...", end="")
            
            try:
                # Add extra delay (Arduino libraries are often slower)
                time.sleep(0.1)
                
                result = pn532.mifare_classic_authenticate_block(uid_bytes, block, key_type, key)
                
                if result:
                    print(" ✅ SUCCESS!")
                    
                    # Try to read the block
                    try:
                        data = pn532.mifare_classic_read_block(block)
                        if data:
                            print(f"    Data: {[hex(x) for x in data[:8]]}...")
                            return True
                        else:
                            print("    Read failed after auth")
                    except Exception as e:
                        print(f"    Read error: {e}")
                        
                else:
                    print(" ❌ (False)")
                    
            except Exception as e:
                print(f" ❌ ({e})")
            
            # Delay between attempts (Arduino style)
            time.sleep(0.1)
    
    return False

def try_alternative_approach():
    """Try with different PN532 configuration"""
    print("\n=== Trying Alternative Configuration ===")
    
    try:
        # Re-initialize with different settings
        pn532.SAM_configuration()
        
        # Wait longer for card stabilization
        print("Looking for card with extended timeout...")
        uid = pn532.read_passive_target(timeout=2.0)
        
        if uid:
            uid_bytes = bytes(uid)
            print(f"Card detected: {binascii.hexlify(uid_bytes).decode().upper()}")
            
            # Try block 0 with different approach
            print("Attempting block 0 read (manufacturer block)...")
            key = bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF')
            
            try:
                # Some cards allow reading block 0 without auth
                data = pn532.mifare_classic_read_block(0)
                if data:
                    print(f"✅ Block 0 (no auth): {[hex(x) for x in data]}")
                    return True
            except:
                pass
            
            # Try with authentication
            try:
                result = pn532.mifare_classic_authenticate_block(uid_bytes, 0, 0, key)
                if result:
                    print("✅ Block 0 auth successful!")
                    data = pn532.mifare_classic_read_block(0)
                    if data:
                        print(f"Block 0 data: {[hex(x) for x in data]}")
                        return True
            except Exception as e:
                print(f"Block 0 auth failed: {e}")
                
    except Exception as e:
        print(f"Alternative approach failed: {e}")
    
    return False

# Main test
try:
    print("Place card on reader...")
    time.sleep(2)
    
    if arduino_style_auth():
        print("\n🎉 SUCCESS! Found working authentication method!")
    elif try_alternative_approach():
        print("\n🎉 SUCCESS with alternative approach!")
    else:
        print("\n❌ All authentication methods failed")
        print("\nThis suggests a fundamental incompatibility between:")
        print("- Your specific cards")  
        print("- The PN532 chip/library")
        print("- The Raspberry Pi environment")
        print("\nConsider:")
        print("1. Different RFID module (MFRC522 for Pi)")
        print("2. Different card brand/type")
        print("3. Using Arduino as RFID bridge to Pi")

except KeyboardInterrupt:
    print("\nExiting.")