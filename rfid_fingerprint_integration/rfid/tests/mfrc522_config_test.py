#!/usr/bin/env python3

"""
MFRC522 Configuration Tester
Tests different SPI configurations to find what works
"""

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import sys

print("=== MFRC522 Configuration Tester ===")
print()

def test_configuration(spi_device=0, reset_pin=25):
    """Test MFRC522 with specific configuration"""
    
    print(f"Testing SPI device {spi_device}, RST pin {reset_pin}")
    
    try:
        # Clean up any existing GPIO setup
        GPIO.cleanup()
        
        # Try to initialize with specific pins
        reader = SimpleMFRC522(spi=spi_device, rst=reset_pin)
        print(f"✅ MFRC522 initialized on SPI{spi_device}")
        
        # Quick detection test
        print("Quick card test (3 seconds)...")
        start_time = time.time()
        
        while time.time() - start_time < 3:
            try:
                id, text = reader.read_no_block()
                if id:
                    print(f"🎉 CARD DETECTED!")
                    print(f"   ID: {id}")
                    print(f"   Data: '{text.strip()}'")
                    return True
            except Exception as e:
                if "timeout" not in str(e).lower():
                    print(f"   Read error: {e}")
                pass
            time.sleep(0.1)
        
        print("   No card in 3 seconds")
        return False
        
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False
    finally:
        try:
            GPIO.cleanup()
        except:
            pass

def main():
    print("Testing different MFRC522 configurations...")
    print("Place a card on your MFRC522 reader")
    print()
    
    # Test different SPI devices and reset pins
    configurations = [
        (0, 25),  # Standard: SPI0, RST=GPIO25
        (1, 25),  # Alternative: SPI1, RST=GPIO25  
        (0, 24),  # Alternative: SPI0, RST=GPIO24
        (1, 24),  # Alternative: SPI1, RST=GPIO24
    ]
    
    for spi_dev, rst_pin in configurations:
        print(f"\n--- Configuration {spi_dev},{rst_pin} ---")
        
        if test_configuration(spi_dev, rst_pin):
            print(f"\n🎉 SUCCESS! Working configuration found:")
            print(f"   SPI Device: {spi_dev}")
            print(f"   Reset Pin: GPIO{rst_pin}")
            print(f"\nUse this in your code:")
            print(f"   reader = SimpleMFRC522(spi={spi_dev}, rst={rst_pin})")
            return
        
        time.sleep(1)
    
    print(f"\n❌ No working configuration found")
    print(f"\nTroubleshooting:")
    print(f"1. Check if you have MFRC522 (not PN532) connected")
    print(f"2. Verify wiring:")
    print(f"   MFRC522 VCC  -> Pi 3.3V")
    print(f"   MFRC522 GND  -> Pi GND") 
    print(f"   MFRC522 RST  -> Pi GPIO25")
    print(f"   MFRC522 SDA  -> Pi CE0 (GPIO8)")
    print(f"   MFRC522 SCK  -> Pi SCLK (GPIO11)")
    print(f"   MFRC522 MOSI -> Pi MOSI (GPIO10)")
    print(f"   MFRC522 MISO -> Pi MISO (GPIO9)")
    print(f"3. Disconnect PN532 if still connected")
    print(f"4. Enable SPI: sudo raspi-config -> Interface -> SPI -> Enable")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    finally:
        GPIO.cleanup()
        print("GPIO cleaned up")