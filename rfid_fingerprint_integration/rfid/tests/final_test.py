#!/usr/bin/env python3
import board
import busio
import digitalio
from adafruit_pn532.spi import PN532_SPI
import time
import binascii

cs_pin = digitalio.DigitalInOut(board.D8)  # CE0
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
pn532 = PN532_SPI(spi, cs_pin, debug=False)

while not spi.try_lock():
    pass
spi.configure(baudrate=25000)  # Even slower - 25kHz
spi.unlock()

print("Testing with ultra-slow SPI (25kHz) and different approach...")

try:
    ic, ver, rev, support = pn532.firmware_version
    print(f"Found PN532 with firmware version: {ver}.{rev}")
except Exception as e:
    print("ERROR:", e)
    exit(1)

pn532.SAM_configuration()

def try_different_approach():
    """Try different card types and approaches"""
    print("\n=== Testing Different Card Types ===")
    
    # Test 1: Check if it's detected as ISO14443A
    print("Test 1: ISO14443A detection...")
    uid = pn532.read_passive_target(timeout=1.0)
    if uid:
        uid_bytes = bytes(uid)
        print(f"✅ ISO14443A card detected: {binascii.hexlify(uid_bytes).decode().upper()}")
        
        # Test 2: Check card type details
        print(f"Card UID length: {len(uid_bytes)} bytes")
        if len(uid_bytes) == 4:
            print("This suggests MIFARE Classic 1K or Mini")
        elif len(uid_bytes) == 7:
            print("This suggests MIFARE Classic 4K")
        else:
            print("This might not be MIFARE Classic")
        
        # Test 3: Try reading without authentication (some cards allow this)
        print("\nTest 2: Attempting read without authentication...")
        try:
            for block in [0, 1, 2, 4, 5]:
                try:
                    data = pn532.mifare_classic_read_block(block)
                    if data:
                        print(f"✅ Block {block} (no auth): {[hex(x) for x in data]}")
                    else:
                        print(f"❌ Block {block}: No data returned")
                except Exception as e:
                    print(f"❌ Block {block}: {e}")
        except Exception as e:
            print(f"Read test failed: {e}")
            
        # Test 4: Try authentication with different parameters
        print("\nTest 3: Authentication with different timing...")
        key = bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF')
        
        for block in [1, 4]:
            print(f"\nTrying block {block}:")
            for delay in [0.1, 0.5, 1.0]:
                try:
                    print(f"  Delay {delay}s...")
                    time.sleep(delay)
                    result = pn532.mifare_classic_authenticate_block(uid_bytes, block, 0, key)
                    if result:
                        print(f"✅ Success with {delay}s delay!")
                        return True
                    else:
                        print(f"❌ Auth failed (False)")
                except Exception as e:
                    print(f"❌ Exception: {e}")
                    
        return False
    else:
        print("❌ No card detected")
        return False

try:
    print("Place your card on the reader...")
    time.sleep(2)
    
    if try_different_approach():
        print("\n🎉 Found working configuration!")
    else:
        print("\n⚠️  This card appears incompatible with standard MIFARE Classic authentication")
        print("\nPossible reasons:")
        print("1. Card uses non-standard access conditions")
        print("2. Card has been configured with custom security")
        print("3. Card is damaged or partially corrupted")
        print("4. Card is not actually MIFARE Classic (despite 4-byte UID)")
        print("\nSuggestions:")
        print("- Try a different MIFARE Classic card")
        print("- Check if this card requires special software/keys")
        print("- Use an NFC app on phone to verify card type")

except KeyboardInterrupt:
    print("\nExiting.")