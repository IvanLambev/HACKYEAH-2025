#!/usr/bin/env python3

# Simple test to verify RFID CARD storage works correctly

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import base64

from rfid_manager import RFID_Manager

def test_rfid_crypto_storage():
    """Test storing and retrieving encrypted-like data on RFID card"""
    
    rfid = RFID_Manager()
    
    print("🧪 Testing RFID Card Storage for Encrypted Data")
    print("=" * 50)
    
    # Simulate encrypted data (just some fake binary data)
    fake_message = "Hello RFID world!"
    fake_encrypted = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10'
    
    print(f"Original message: '{fake_message}' ({len(fake_message)} chars)")
    print(f"Simulated encrypted data: {len(fake_encrypted)} bytes")
    
    # Convert to base64 format like the fingerprint system does
    encrypted_b64 = base64.b64encode(fake_encrypted).decode('ascii')
    card_string = f"ENCRYPTED:{encrypted_b64}:{len(fake_message)}"
    
    print(f"Card string: '{card_string}' ({len(card_string)} chars)")
    
    # Wait for card
    print("\nPlace MIFARE Classic card on reader...")
    if not rfid.wait_for_card(timeout=10):
        print("❌ No card detected")
        return False
        
    # Clear the test area first
    print("Clearing test area...")
    if not rfid.check_and_recover_connection():
        print("❌ Card connection failed")
        return False
        
    # Write the string
    start_block = 4
    print(f"\nWriting to block {start_block}...")
    
    if rfid.write_string(start_block, card_string):
        print("✅ Write successful!")
        
        # Read back
        print("Reading back...")
        rfid.refresh_cache()
        read_string = rfid.read_string(start_block)
        
        if read_string == card_string:
            print("✅ Perfect match!")
            
            # Parse and verify
            if read_string.startswith("ENCRYPTED:"):
                parts = read_string.split(":")
                if len(parts) == 3:
                    retrieved_b64 = parts[1]
                    original_length = int(parts[2])
                    retrieved_encrypted = base64.b64decode(retrieved_b64)
                    
                    print(f"\n📋 Verification:")
                    print(f"   Retrieved original length: {original_length}")
                    print(f"   Retrieved encrypted data: {len(retrieved_encrypted)} bytes")
                    print(f"   Data matches: {retrieved_encrypted == fake_encrypted}")
                    
                    if retrieved_encrypted == fake_encrypted and original_length == len(fake_message):
                        print("\n🎉 SUCCESS: RFID card storage working perfectly!")
                        return True
                    else:
                        print("\n❌ Data corruption during storage/retrieval")
                else:
                    print("\n❌ Invalid format after retrieval")
            else:
                print("\n❌ Wrong format prefix")
        else:
            print(f"❌ Mismatch!")
            print(f"  Expected: '{card_string}'")
            print(f"  Got:      '{read_string}'")
    else:
        print("❌ Write failed")
        
    return False

if __name__ == "__main__":
    test_rfid_crypto_storage()