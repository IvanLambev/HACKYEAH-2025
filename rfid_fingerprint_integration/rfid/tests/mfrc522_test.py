#!/usr/bin/env python3

"""
MFRC522 RFID Reader Test Script for Raspberry Pi

Wiring for MFRC522:
MFRC522    Raspberry Pi
VCC   -->  3.3V (Pin 1)
RST   -->  GPIO25 (Pin 22) 
GND   -->  GND (Pin 6)
MISO  -->  GPIO9/MISO (Pin 21)
MOSI  -->  GPIO10/MOSI (Pin 19)
SCK   -->  GPIO11/SCLK (Pin 23)
SDA   -->  GPIO8/CE0 (Pin 24)

Note: If you have PN532 wired to CE0, you may need to use CE1 for MFRC522
"""

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

print("=== MFRC522 RFID Test ===")
print("Make sure your MFRC522 is wired correctly:")
print("VCC->3.3V, GND->GND, RST->GPIO25, SDA->CE0")
print("MISO->MISO, MOSI->MOSI, SCK->SCLK")
print()

# Initialize the MFRC522 reader
try:
    reader = SimpleMFRC522()
    print("✅ MFRC522 initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize MFRC522: {e}")
    print("Check wiring and try again")
    exit(1)

def test_card_detection():
    """Test basic card detection"""
    print("\n=== Card Detection Test ===")
    print("Place a card on the reader...")
    
    try:
        # Try to read card with timeout
        print("Waiting for card (10 second timeout)...")
        start_time = time.time()
        
        while time.time() - start_time < 10:
            try:
                # Try non-blocking read
                id, text = reader.read_no_block()
                if id:
                    print(f"✅ Card detected!")
                    print(f"   ID: {id}")
                    print(f"   Data: '{text.strip()}'")
                    return True
            except:
                pass
            time.sleep(0.1)
        
        print("❌ No card detected in 10 seconds")
        return False
        
    except Exception as e:
        print(f"❌ Error during detection: {e}")
        return False

def test_read_write():
    """Test reading and writing data"""
    print("\n=== Read/Write Test ===")
    print("Place card on reader for read/write test...")
    
    try:
        # Read existing data
        print("Reading current data...")
        id, text = reader.read()
        print(f"✅ Read successful!")
        print(f"   Card ID: {id}")
        print(f"   Current text: '{text.strip()}'")
        
        # Write test data
        test_message = f"Test write at {time.strftime('%H:%M:%S')}"
        print(f"\nWriting test message: '{test_message}'")
        print("Keep card on reader...")
        
        reader.write(test_message)
        print("✅ Write successful!")
        
        # Verify write
        print("\nVerifying write... (place card again)")
        id2, text2 = reader.read()
        
        if test_message in text2:
            print("✅ Write verification successful!")
            print(f"   Verified text: '{text2.strip()}'")
            return True
        else:
            print(f"❌ Write verification failed")
            print(f"   Expected: '{test_message}'")
            print(f"   Got: '{text2.strip()}'")
            return False
            
    except Exception as e:
        print(f"❌ Read/write error: {e}")
        return False

def main():
    print("Starting MFRC522 tests...")
    
    # Test 1: Card detection
    if test_card_detection():
        print("\n🎉 Card detection works!")
        
        # Test 2: Read/write functionality  
        print("\nProceed to read/write test? (y/n): ", end="")
        if input().lower().startswith('y'):
            if test_read_write():
                print("\n🎉 ALL TESTS PASSED!")
                print("Your MFRC522 setup is working perfectly!")
            else:
                print("\n⚠️ Detection works but read/write has issues")
        else:
            print("Skipping read/write test")
    else:
        print("\n❌ Card detection failed")
        print("Check:")
        print("1. Wiring connections")
        print("2. Card placement on reader") 
        print("3. Power supply (3.3V)")
        print("4. SPI conflicts with other devices")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    finally:
        GPIO.cleanup()
        print("GPIO cleaned up")