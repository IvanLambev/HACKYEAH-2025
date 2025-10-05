#!/usr/bin/env python3

"""
Simple RFID Examples - Basic usage of the RFID_Manager library
"""

import sys
import os
import time

# Add the current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rfid_manager import RFID_Manager

def example_1_basic_card_info():
    """Example 1: Basic card detection and information"""
    print("=" * 50)
    print("EXAMPLE 1: Basic Card Information")
    print("=" * 50)
    
    rfid = RFID_Manager()
    
    print("Place a card on the reader...")
    if rfid.wait_for_card(timeout=15):
        info = rfid.get_card_info()
        
        print(f"✅ Card detected!")
        print(f"   UID: {info.get('uid', 'Unknown')}")
        print(f"   Type: {info.get('type', 'Unknown')}")
        print(f"   Size: {info.get('size', 'Unknown')} bytes")
        print(f"   ATQA: {info.get('atqa', 'Unknown')}")
        print(f"   SAK: {info.get('sak', 'Unknown')}")
        return True
    else:
        print("❌ No card detected within timeout")
        return False

def example_2_read_blocks():
    """Example 2: Reading card blocks"""
    print("\n" + "=" * 50)
    print("EXAMPLE 2: Reading Card Blocks")
    print("=" * 50)
    
    rfid = RFID_Manager()
    
    if not rfid.is_card_present():
        print("❌ No card present")
        return False
    
    print("Reading first 8 blocks:")
    for block in range(8):
        data = rfid.read_block(block)
        if data:
            # Convert to hex string
            hex_str = ' '.join([f'{b:02x}' for b in data])
            # Convert to ASCII (printable chars only)
            ascii_str = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
            
            block_type = ""
            if block == 0:
                block_type = " (UID)"
            elif (block + 1) % 4 == 0:
                block_type = " (Keys)"
            
            print(f"Block {block}: {hex_str} | {ascii_str}{block_type}")
        else:
            print(f"Block {block}: ❌ Read failed")
    
    return True

def example_3_write_and_read_string():
    """Example 3: Writing and reading strings"""
    print("\n" + "=" * 50)
    print("EXAMPLE 3: String Operations")
    print("=" * 50)
    
    rfid = RFID_Manager()
    
    if not rfid.is_card_present():
        print("❌ No card present")
        return False
    
    # Test string
    test_string = f"Hello RFID! Time: {time.strftime('%H:%M:%S')}"
    start_block = 4  # Safe block for writing
    
    print(f"Writing string to block {start_block}: '{test_string}'")
    
    if rfid.write_string(start_block, test_string):
        print("✅ String write successful!")
        
        # Read it back
        print("Reading string back...")
        read_string = rfid.read_string(start_block)
        
        if read_string:
            print(f"✅ Read back: '{read_string}'")
            
            if read_string == test_string:
                print("🎉 Perfect match!")
                return True
            else:
                print("⚠️ Strings don't match exactly")
                return False
        else:
            print("❌ Failed to read string back")
            return False
    else:
        print("❌ String write failed")
        return False

def example_4_interactive_demo():
    """Example 4: Interactive demonstration"""
    print("\n" + "=" * 50)
    print("EXAMPLE 4: Interactive Demo")
    print("=" * 50)
    
    rfid = RFID_Manager()
    
    print("This demo will continuously monitor for cards...")
    print("Place and remove cards to see real-time detection")
    print("Press Ctrl+C to stop")
    
    card_present = False
    
    try:
        while True:
            current_present = rfid.is_card_present()
            
            if current_present and not card_present:
                # Card just placed
                print("\n🎉 Card placed!")
                info = rfid.get_card_info()
                print(f"   UID: {info.get('uid', 'Unknown')}")
                
                # Show a preview of the card
                result = rfid.quick_read_card()
                if result['strings']:
                    print("   Found strings:")
                    for block, text in result['strings'].items():
                        print(f"     Block {block}: '{text[:40]}...'")
                
                card_present = True
                
            elif not current_present and card_present:
                # Card just removed
                print("👋 Card removed")
                card_present = False
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n\nDemo stopped by user")

def example_5_data_storage():
    """Example 5: Simple data storage system"""
    print("\n" + "=" * 50)
    print("EXAMPLE 5: Data Storage System")
    print("=" * 50)
    
    rfid = RFID_Manager()
    
    if not rfid.is_card_present():
        print("❌ No card present")
        return False
    
    print("Simple card data storage system")
    print("This will store some sample data on your card")
    
    # Sample data to store
    data_items = [
        ("Name", "John Doe"),
        ("Department", "Engineering"),
        ("Access Level", "2"),
        ("Issued", time.strftime('%Y-%m-%d'))
    ]
    
    start_block = 4
    current_block = start_block
    
    print(f"\nStoring data starting at block {start_block}:")
    
    for label, value in data_items:
        data_string = f"{label}: {value}"
        print(f"  Writing '{data_string}' to block {current_block}")
        
        if rfid.write_string(current_block, data_string):
            print(f"    ✅ Success")
        else:
            print(f"    ❌ Failed")
            return False
        
        current_block += 2  # Skip a block to avoid overlap
    
    print(f"\nReading back stored data:")
    current_block = start_block
    
    for label, _ in data_items:
        stored_data = rfid.read_string(current_block)
        if stored_data:
            print(f"  Block {current_block}: '{stored_data}'")
        else:
            print(f"  Block {current_block}: ❌ No data")
        
        current_block += 2
    
    return True

def main():
    """Main function to run all examples"""
    print("RFID Manager - Example Programs")
    print("Make sure your card is ready and PN532 is connected")
    print()
    
    # Check if libnfc is working
    try:
        import subprocess
        result = subprocess.run(['nfc-list'], capture_output=True, text=True, timeout=3)
        if result.returncode != 0:
            print("❌ Error: nfc-list failed")
            print("Make sure libnfc is installed and PN532 is connected")
            return
    except Exception as e:
        print(f"❌ Error running nfc-list: {e}")
        return
    
    print("✅ libnfc is working")
    
    # Run examples
    examples = [
        example_1_basic_card_info,
        example_2_read_blocks,
    ]
    
    # Run read-only examples first
    for i, example in enumerate(examples, 1):
        try:
            success = example()
            if not success and i == 1:
                print("❌ Cannot continue without card detection")
                return
        except KeyboardInterrupt:
            print("\nExample interrupted by user")
            return
        except Exception as e:
            print(f"❌ Example failed: {e}")
    
    # Ask about write examples
    print("\n" + "=" * 50)
    print("The next examples will WRITE to your card!")
    choice = input("Continue with write examples? (y/N): ").strip().lower()
    
    if choice.startswith('y'):
        write_examples = [
            example_3_write_and_read_string,
            example_5_data_storage
        ]
        
        for example in write_examples:
            try:
                example()
            except KeyboardInterrupt:
                print("\nExample interrupted by user")
                return
            except Exception as e:
                print(f"❌ Example failed: {e}")
    
    # Ask about interactive demo
    print("\n" + "=" * 50)
    choice = input("Run interactive demo? (y/N): ").strip().lower()
    if choice.startswith('y'):
        try:
            example_4_interactive_demo()
        except KeyboardInterrupt:
            print("\nDemo stopped")
        except Exception as e:
            print(f"❌ Demo failed: {e}")
    
    print("\n🎉 Examples completed!")
    print("Check README.md for more detailed documentation.")

if __name__ == "__main__":
    main()