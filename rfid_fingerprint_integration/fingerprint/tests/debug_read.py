#!/usr/bin/env python3

# Debug the string reading issue

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rfid_manager import RFID_Manager

def debug_string_read():
    """Debug what's happening during string read"""
    
    rfid = RFID_Manager()
    
    print("🔍 Debugging RFID String Read")
    print("=" * 30)
    
    # Wait for card
    if not rfid.wait_for_card(timeout=5):
        print("❌ No card detected")
        return
        
    print("Reading raw blocks 4, 5, 6...")
    
    for block in [4, 5, 6]:
        data = rfid.read_block(block)
        if data:
            hex_data = ' '.join([f'{b:02x}' for b in data])
            ascii_data = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
            print(f"Block {block}: {hex_data}")
            print(f"           {ascii_data}")
            print()
    
    print("Now testing string read from block 4...")
    string_result = rfid.read_string(4)
    print(f"String result: '{string_result}'")
    print(f"Length: {len(string_result) if string_result else 0}")

if __name__ == "__main__":
    debug_string_read()