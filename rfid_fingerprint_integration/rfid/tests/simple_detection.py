#!/usr/bin/env python3

"""
Simple card detection test
"""

import subprocess
import time

def test_card_detection():
    print("=== Simple Card Detection Test ===")
    print("Place your card on the PN532 reader...")
    print()
    
    for attempt in range(10):
        print(f"Attempt {attempt + 1}/10: ", end="", flush=True)
        
        try:
            result = subprocess.run(['nfc-list'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=3)
            
            print(f"Exit code: {result.returncode}")
            
            if result.returncode == 0:
                print("✅ nfc-list succeeded!")
                if "ISO/IEC 14443A" in result.stdout:
                    print("🎉 CARD DETECTED!")
                    print("Output:", result.stdout)
                    return True
                else:
                    print("No card found in output")
                    print("Output:", result.stdout)
            else:
                print("❌ nfc-list failed")
                print("Error:", result.stderr.strip())
                
                # If it's an I/O error, wait longer
                if "Input / Output Error" in result.stderr:
                    print("   (I/O Error - waiting 3 seconds...)")
                    time.sleep(3)
                    
        except subprocess.TimeoutExpired:
            print("❌ Timeout")
        except Exception as e:
            print(f"❌ Exception: {e}")
            
        time.sleep(1)
    
    print("\n❌ No card detected in 10 attempts")
    return False

def test_card_reading():
    print("\n=== Card Reading Test ===")
    print("Attempting to read card data...")
    
    try:
        result = subprocess.run([
            'nfc-mfclassic', 'r', 'a', 'u', '/tmp/test_read.mfd'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("🎉 Card read successful!")
            print("Output:", result.stdout)
            return True
        else:
            print("❌ Card read failed")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Read error: {e}")
        return False

if __name__ == "__main__":
    if test_card_detection():
        test_card_reading()
    else:
        print("\nTroubleshooting tips:")
        print("1. Make sure card is properly placed on reader")
        print("2. Try moving the card around on the antenna")
        print("3. Check if PN532 wiring is still secure")
        print("4. Try restarting the Pi if errors persist")