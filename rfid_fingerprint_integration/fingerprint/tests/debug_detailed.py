#!/usr/bin/env python3

# Debug the exact string reading issue

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rfid_manager import RFID_Manager

def debug_detailed_read():
    """Debug what's happening byte by byte"""
    
    rfid = RFID_Manager()
    
    print("🔍 Detailed RFID String Debug")
    print("=" * 40)
    
    # Wait for card
    if not rfid.wait_for_card(timeout=5):
        print("❌ No card detected")
        return
        
    print("Reading raw blocks used by the string...")
    
    # Read the exact blocks that should contain our string
    blocks_to_check = [4, 5, 6, 7, 8]  # Check a range around where data should be
    
    for block in blocks_to_check:
        data = rfid.read_block(block)
        if data:
            hex_data = ' '.join([f'{b:02x}' for b in data])
            ascii_data = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
            print(f"Block {block}: {hex_data}")
            print(f"           {ascii_data}")
            
            # Also show as raw bytes for debugging
            non_zero_bytes = [b for b in data if b != 0]
            if non_zero_bytes:
                print(f"           Non-zero: {non_zero_bytes}")
            print()
    
    # Now manually reconstruct what the string should be
    print("Manual reconstruction from raw blocks:")
    
    # Read blocks 4, 5, 6, 8 and manually piece together
    block4 = rfid.read_block(4)
    block5 = rfid.read_block(5) 
    block6 = rfid.read_block(6)
    block8 = rfid.read_block(8)
    
    if block4:
        # Skip the 4-byte header, get the string data
        header = block4[:4]
        char_count = (header[0] << 24) | (header[1] << 16) | (header[2] << 8) | header[3]
        print(f"Header indicates {char_count} characters expected")
        
        # Collect all bytes after header
        all_bytes = bytearray()
        all_bytes.extend(block4[4:])  # Rest of block 4
        if block5: all_bytes.extend(block5)  # All of block 5
        if block6: all_bytes.extend(block6)  # All of block 6  
        if block8: all_bytes.extend(block8)  # All of block 8
        
        print(f"Collected {len(all_bytes)} raw bytes total")
        
        # Try different decoding approaches
        print("\nDecoding attempts:")
        
        # Method 1: Direct decode with ignore
        try:
            decode1 = all_bytes.decode('utf-8', errors='ignore')
            print(f"1. Direct decode (ignore): '{decode1}' ({len(decode1)} chars)")
        except Exception as e:
            print(f"1. Direct decode failed: {e}")
        
        # Method 2: Remove nulls first, then decode
        try:
            no_nulls = bytes([b for b in all_bytes if b != 0])
            decode2 = no_nulls.decode('utf-8', errors='ignore')
            print(f"2. Remove nulls first: '{decode2}' ({len(decode2)} chars)")
        except Exception as e:
            print(f"2. Remove nulls failed: {e}")
        
        # Method 3: Trim to expected length, then remove nulls
        try:
            trimmed = all_bytes[:char_count]  # Take only expected number of bytes
            decode3 = trimmed.decode('utf-8', errors='replace')
            print(f"3. Trim then decode: '{decode3}' ({len(decode3)} chars)")
        except Exception as e:
            print(f"3. Trim decode failed: {e}")

if __name__ == "__main__":
    debug_detailed_read()