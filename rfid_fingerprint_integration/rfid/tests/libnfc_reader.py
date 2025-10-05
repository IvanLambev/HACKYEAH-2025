#!/usr/bin/env python3

"""
PN532 MIFARE Classic Reader using libnfc
This works with your existing PN532 hardware setup!
"""

import subprocess
import os
import time
import binascii

class LibNFC_MIFARE:
    def __init__(self):
        self.temp_file = "/tmp/card_dump.mfd"
        self.last_error_time = 0
    
    def reset_pn532(self):
        """Try to reset PN532 if it gets into bad state"""
        print("Attempting to reset PN532...")
        try:
            # Kill any hanging processes
            subprocess.run(['pkill', '-f', 'nfc-'], capture_output=True)
            time.sleep(1)
            
            # Try to re-initialize
            result = subprocess.run(['nfc-list'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                print("PN532 reset successful")
                return True
            else:
                print(f"Reset failed: {result.stderr}")
                return False
        except Exception as e:
            print(f"Reset error: {e}")
            return False
    
    def is_card_present(self):
        """Check if a card is present"""
        try:
            result = subprocess.run(['nfc-list'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=3)
            
            if result.returncode == 0:
                # Look for card presence indicators
                return "ISO14443A passive target(s) found:" in result.stdout
            else:
                # If nfc-list fails frequently, try reset
                current_time = time.time()
                if current_time - self.last_error_time > 10:  # Reset every 10 seconds max
                    self.last_error_time = current_time
                    if "Input / Output Error" in result.stderr or "Unable to open" in result.stderr:
                        self.reset_pn532()
                return False
        except subprocess.TimeoutExpired:
            return False
        except Exception as e:
            return False
    
    def get_card_uid(self):
        """Get the UID of the present card"""
        try:
            result = subprocess.run(['nfc-list'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=2)
            
            for line in result.stdout.split('\n'):
                if 'UID (NFCID1):' in line:
                    # Extract UID after the colon and remove spaces
                    uid_part = line.split(':', 1)[1].strip()
                    uid_str = uid_part.replace(' ', '')
                    return uid_str.upper()
            return "Unknown"
        except Exception as e:
            print(f"UID extraction error: {e}")
            return "Error"
    
    def read_card(self):
        """Read entire card and return data"""
        try:
            # Remove old dump file
            if os.path.exists(self.temp_file):
                os.remove(self.temp_file)
            
            # Read card using nfc-mfclassic with error tolerance
            result = subprocess.run([
                'nfc-mfclassic', 'r', 'a', 'u', self.temp_file
            ], capture_output=True, text=True, timeout=10)
            
            # Even if there's an authentication error on some blocks, we might have partial data
            if os.path.exists(self.temp_file):
                with open(self.temp_file, 'rb') as f:
                    data = f.read()
                if len(data) > 0:  # We got some data
                    if result.returncode != 0:
                        print(f"Partial read (some blocks failed): {result.stderr.strip()}")
                    return data
            
            print("Read completely failed:", result.stderr)
            return None
                
        except Exception as e:
            print(f"Read error: {e}")
            return None
    
    def read_block(self, block_num):
        """Read a specific block"""
        data = self.read_card()
        if data and len(data) >= (block_num + 1) * 16:
            start = block_num * 16
            return data[start:start + 16]
        return None
    
    def write_block(self, block_num, data):
        """Write data to a specific block"""
        if len(data) != 16:
            print("Block data must be exactly 16 bytes")
            return False
            
        try:
            # First read the entire card
            card_data = self.read_card()
            if not card_data:
                print("Failed to read card for write operation")
                return False
            
            # Modify the specific block
            card_data = bytearray(card_data)
            start = block_num * 16
            card_data[start:start + 16] = data
            
            # Write modified data to temp file
            write_file = "/tmp/card_write.mfd"
            with open(write_file, 'wb') as f:
                f.write(card_data)
            
            # Write back to card
            result = subprocess.run([
                'nfc-mfclassic', 'w', 'a', 'u', write_file
            ], capture_output=True, text=True, timeout=10)
            
            os.remove(write_file)
            return result.returncode == 0
            
        except Exception as e:
            print(f"Write error: {e}")
            return False
    
    def read_long_string(self, start_block):
        """Read a long string starting from the given block (your original function)"""
        try:
            block_data = self.read_block(start_block)
            if not block_data:
                return None
            
            # Get length from first 2 bytes
            length = (block_data[0] << 8) | block_data[1]
            if length == 0:
                return ""
            if length > 900:  # Sanity check
                return None
            
            # Start collecting data from byte 2 of first block
            data = bytearray()
            data.extend(block_data[2:2 + min(14, length)])
            copied = len(data)
            
            # Read additional blocks if needed
            block_num = start_block + 1
            while copied < length and block_num < 64:
                # Skip trailer blocks (every 4th block starting from 3)
                if (block_num % 4) == 3:
                    block_num += 1
                    continue
                
                block_data = self.read_block(block_num)
                if not block_data:
                    break
                
                need = length - copied
                copy_now = min(16, need)
                data.extend(block_data[:copy_now])
                copied += copy_now
                block_num += 1
            
            return data.decode("utf-8", errors="ignore")
            
        except Exception as e:
            print(f"Error reading long string: {e}")
            return None

def main():
    print("=== PN532 MIFARE Classic Reader (libnfc) ===")
    print("Using libnfc library - this should work with your setup!")
    print()
    
    reader = LibNFC_MIFARE()
    
    print("Waiting for a card...")
    
    while True:
        try:
            if reader.is_card_present():
                uid = reader.get_card_uid()
                print(f"\n🎉 Card detected: UID = {uid}")
                
                # Test reading some blocks
                print("\nReading blocks...")
                for block in [0, 1, 4, 5]:
                    data = reader.read_block(block)
                    if data:
                        hex_data = ' '.join([f'{b:02x}' for b in data])
                        print(f"Block {block:2d}: {hex_data}")
                    else:
                        print(f"Block {block:2d}: Read failed")
                
                # Test your long string function
                print(f"\nTrying to read long string from block 4...")
                try:
                    long_str = reader.read_long_string(4)
                    if long_str is not None and long_str != "":
                        print(f"Long string: '{long_str}'")
                    else:
                        print("No long string found (empty or null)")
                except Exception as e:
                    print(f"Long string read error: {e}")
                
                print(f"\nRemove card and place another, or Ctrl+C to exit...")
                
                # Wait for card to be removed
                while reader.is_card_present():
                    time.sleep(0.2)
                
                print("Card removed. Waiting for next card...")
                
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()