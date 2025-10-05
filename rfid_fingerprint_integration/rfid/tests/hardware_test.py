#!/usr/bin/env python3
import board
import busio
import digitalio
from adafruit_pn532.spi import PN532_SPI
import time
import binascii

print("=== PN532 Hardware Diagnostic Tool ===")
print("This will test your PN532 setup systematically\n")

# Test different CS pins
for use_ce1 in [False, True]:
    pin_name = "D7 (CE1)" if use_ce1 else "D8 (CE0)"
    print(f"\n--- Testing CS pin: {pin_name} ---")
    
    try:
        # Setup
        cs_pin = digitalio.DigitalInOut(board.D7 if use_ce1 else board.D8)
        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        
        # Test multiple SPI speeds
        for speed in [25000, 50000, 100000]:
            print(f"\nTesting SPI speed: {speed} Hz")
            
            try:
                pn532 = PN532_SPI(spi, cs_pin, debug=False)
                
                while not spi.try_lock():
                    pass
                spi.configure(baudrate=speed)
                spi.unlock()
                
                # Test firmware detection
                ic, ver, rev, support = pn532.firmware_version
                print(f"✅ PN532 detected: v{ver}.{rev}")
                
                # Configure SAM
                pn532.SAM_configuration()
                print("✅ SAM configuration successful")
                
                # Test card detection (quick test)
                print("Testing card detection (5 second timeout)...")
                start_time = time.time()
                card_detected = False
                
                while time.time() - start_time < 5:
                    uid = pn532.read_passive_target(timeout=0.1)
                    if uid:
                        print(f"✅ Card detected: {binascii.hexlify(bytes(uid)).decode().upper()}")
                        card_detected = True
                        
                        # Quick auth test
                        uid_bytes = bytes(uid)
                        key = bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF')
                        
                        try:
                            result = pn532.mifare_classic_authenticate_block(uid_bytes, 1, 0, key)
                            if result:
                                print("🎉 AUTHENTICATION SUCCESS!")
                                print(f"Working configuration:")
                                print(f"  - CS Pin: {pin_name}")
                                print(f"  - SPI Speed: {speed} Hz")
                                exit(0)  # Found working config!
                            else:
                                print("❌ Auth failed (returned False)")
                        except Exception as e:
                            print(f"❌ Auth exception: {e}")
                        break
                
                if not card_detected:
                    print("⚠️ No card detected in 5 seconds")
                    
            except Exception as e:
                print(f"❌ Failed at {speed} Hz: {e}")
                continue
                
        # Clean up
        try:
            spi.deinit()
        except:
            pass
            
    except Exception as e:
        print(f"❌ CS pin {pin_name} failed: {e}")

print("\n=== Hardware Check Complete ===")
print("If no working configuration was found, check:")
print("1. Power supply - use external 3.3V if possible")
print("2. Wiring - ensure solid connections")
print("3. PN532 jumpers - confirm SPI mode")
print("4. Card positioning - try different angles/distances")