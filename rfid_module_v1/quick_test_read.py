#!/usr/bin/env python3

"""Quick test to debug string reading"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rfid_manager import RFID_Manager

def quick_test():
    rfid = RFID_Manager()
    
    print("Testing string info for block 4...")
    info = rfid.get_string_info(4)
    print(f"String info: {info}")
    
    if "error" not in info:
        print("\nTesting string read with timeout...")
        try:
            result = rfid.read_string(4)
            print(f"Read result: '{result}'")
        except KeyboardInterrupt:
            print("Read interrupted by user")
        except Exception as e:
            print(f"Read failed with error: {e}")
    
    print("\nTesting simple block read...")
    block_data = rfid.read_block(4)
    if block_data:
        hex_data = ' '.join([f'{b:02x}' for b in block_data])
        ascii_data = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in block_data])
        print(f"Block 4: {hex_data} | {ascii_data}")
        
        # Manual decode test
        if block_data[0:4] == b'\x00\x00\x00\x0c':
            print("Found 4-byte length header: 12 characters")
            text_bytes = block_data[4:16]  # Rest of block
            try:
                decoded = text_bytes.decode('utf-8').rstrip('\x00')
                print(f"Manual decode: '{decoded}' (length: {len(decoded)})")
            except Exception as e:
                print(f"Manual decode failed: {e}")

if __name__ == "__main__":
    quick_test()