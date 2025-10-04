#!/usr/bin/env python3

"""
RFID Test Suite - Complete testing of RFID_Manager functionality
"""

import sys
import os
import time

# Add the current directory to path so we can import rfid_manager
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rfid_manager import RFID_Manager

def test_card_detection():
    """Test basic card detection functionality."""
    print("=" * 60)
    print("TEST 1: CARD DETECTION")
    print("=" * 60)
    
    rfid = RFID_Manager()
    
    print("Place a card on the reader...")
    if rfid.wait_for_card(timeout=10):
        print("✅ Card detected successfully!")
        
        # Get card info
        info = rfid.get_card_info()
        print(f"Card UID: {info.get('uid', 'Unknown')}")
        print(f"Card Type: {info.get('type', 'Unknown')}")
        print(f"Card Size: {info.get('size', 'Unknown')} bytes")
        
        return True
    else:
        print("❌ No card detected within timeout")
        return False

def test_block_reading():
    """Test reading individual blocks."""
    print("\n" + "=" * 60)
    print("TEST 2: BLOCK READING")
    print("=" * 60)
    
    rfid = RFID_Manager()
    
    if not rfid.is_card_present():
        print("❌ No card present for block reading test")
        return False
    
    print("Reading first 8 blocks...")
    success_count = 0
    
    for block in range(8):
        data = rfid.read_block(block)
        if data:
            hex_data = ' '.join([f'{b:02x}' for b in data])
            ascii_data = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
            print(f"Block {block:2d}: {hex_data} | {ascii_data}")
            success_count += 1
        else:
            print(f"Block {block:2d}: ❌ Read failed")
    
    print(f"\n✅ Successfully read {success_count}/8 blocks")
    return success_count > 0

def test_string_operations():
    """Test string writing and reading with various lengths."""
    print("\n" + "=" * 60)
    print("TEST 3: STRING OPERATIONS")
    print("=" * 60)
    
    rfid = RFID_Manager()
    
    if not rfid.is_card_present():
        print("❌ No card present for string operations test")
        return False
    
    # Check available space first
    space_info = rfid.get_available_space(4)  # Starting from block 4
    print(f"Available space: {space_info['estimated_max_chars']} characters ({space_info['available_blocks']} blocks)")
    
    # Clear some blocks first to avoid interference, but do it gently
    print("Clearing test area (gentle approach)...")
    empty_block = b'\x00' * 16
    cleared_count = 0
    failed_count = 0
    
    # Clear in smaller batches with delays
    for i, block in enumerate(range(4, 24)):  # Reduced range to avoid overloading
        if (block + 1) % 4 != 0:  # Skip trailer blocks
            try:
                if rfid.write_block(block, empty_block):
                    cleared_count += 1
                else:
                    failed_count += 1
                    
                # Add delay every few blocks to avoid overwhelming the card
                if (i + 1) % 3 == 0:
                    time.sleep(0.2)
                    
            except Exception as e:
                failed_count += 1
                print(f"Failed to clear block {block}: {e}")
                
            # If we have too many failures, stop clearing
            if failed_count > 3:
                print("Too many failures during clearing, stopping...")
                break
    
    # Invalidate cache after clearing to force fresh read
    import os
    if os.path.exists(rfid.temp_file):
        os.remove(rfid.temp_file)
    
    # Give the card/reader time to settle
    time.sleep(1)
    
    print(f"Test area cleared: {cleared_count} blocks cleared, {failed_count} failures. Cache refreshed.")
    
    # Test data with various lengths
    test_strings = [
        "Short string",
        "This is a medium-length test string with numbers: 12345 and special chars: áéíóú ñ @#$%^&*()",
        f"Timestamp and details: {time.strftime('%Y-%m-%d %H:%M:%S')} - System info and various data points",
        "Long string test: " + "This is a repeated phrase to make the string longer. " * 10,
        "Very long string: " + "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20,
    ]
    
    start_block = 4  # Safe starting block
    success_count = 0
    
    for i, test_string in enumerate(test_strings):
        print(f"\n--- Test {i+1}: String length {len(test_string)} characters ---")
        print(f"Preview: '{test_string[:50]}{'...' if len(test_string) > 50 else ''}'")
        
        # Get string info before writing
        print(f"Writing to block {start_block}...")
        
        # Check connection before writing
        if not rfid.check_and_recover_connection():
            print("❌ Card connection lost, skipping this test")
            continue
        
        # Write string
        if rfid.write_string(start_block, test_string):
            print("✅ Write successful")
            
            # Get info about the written string
            info = rfid.get_string_info(start_block)
            if "error" not in info:
                print(f"String info: {info['length']} characters, {info['blocks_needed']} blocks, format: {info['format']}")
            
            # Read back
            print("Reading back...")
            # Force a fresh read by clearing cache
            rfid.refresh_cache()
            read_string = rfid.read_string(start_block)
            if read_string == test_string:
                print("✅ Read back matches perfectly!")
                success_count += 1
            elif read_string:
                print(f"⚠️ Read back differs:")
                print(f"  Expected length: {len(test_string)}")
                print(f"  Got length: {len(read_string)}")
                print(f"  First 100 chars match: {test_string[:100] == read_string[:100]}")
                if len(test_string) != len(read_string):
                    print(f"  Length mismatch!")
                else:
                    # Same length but different content - let's find where they differ
                    for i, (c1, c2) in enumerate(zip(test_string, read_string)):
                        if c1 != c2:
                            print(f"  First difference at position {i}: expected '{c1}' ({ord(c1)}), got '{c2}' ({ord(c2)})")
                            break
                    # Show first 50 chars of each
                    print(f"  Expected start: '{test_string[:50]}'")
                    print(f"  Got start:      '{read_string[:50]}'")
            else:
                print("❌ Failed to read back string")
        else:
            print("❌ Write failed")
        
        # Move to next safe area (skip several blocks to avoid conflicts)
        start_block += max(8, (len(test_string) // 200) + 4)
        
        # Pause between tests
        time.sleep(0.5)
    
    print(f"\n✅ String tests completed: {success_count}/{len(test_strings)} successful")
    
    # Test very long string if we have space
    if success_count > 2:
        print(f"\n--- Bonus Test: Very Long String ---")
        very_long_text = "Ultra long string test: " + ("This sentence will be repeated many times to create a very long string for testing the multi-block storage capability. " * 50)
        print(f"Testing string of {len(very_long_text)} characters...")
        
        if rfid.write_long_string(very_long_text, start_sector=8):
            print("✅ Very long string write successful")
            read_back = rfid.read_string(8 * 4)  # Sector 8, block 32
            if read_back == very_long_text:
                print("✅ Very long string read back perfectly!")
                success_count += 1
            else:
                print(f"⚠️ Very long string read back differs (lengths: {len(very_long_text)} vs {len(read_back) if read_back else 'None'})")
        else:
            print("❌ Very long string write failed")
    
    return success_count > 0

def test_card_display():
    """Test the card display functionality."""
    print("\n" + "=" * 60)
    print("TEST 4: CARD DISPLAY")
    print("=" * 60)
    
    rfid = RFID_Manager()
    
    if not rfid.check_and_recover_connection():
        print("❌ No card present or connection failed for display test")
        return False
    
    print(rfid.format_card_display(16))
    return True

def test_quick_read():
    """Test the quick read functionality."""
    print("\n" + "=" * 60)
    print("TEST 5: QUICK READ")
    print("=" * 60)
    
    rfid = RFID_Manager()
    
    if not rfid.check_and_recover_connection():
        print("❌ No card present or connection failed for quick read test")
        return False
    
    result = rfid.quick_read_card()
    
    print("Card Information:")
    for key, value in result["info"].items():
        print(f"  {key}: {value}")
    
    print("\nSample Blocks:")
    for block, data in result["blocks"].items():
        print(f"  Block {block}: {data['hex']}")
    
    print("\nFound Strings:")
    if result["strings"]:
        for block, string in result["strings"].items():
            print(f"  Block {block}: '{string}'")
    else:
        print("  No strings found")
    
    return True

def interactive_test():
    """Interactive testing mode."""
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE")
    print("=" * 60)
    
    rfid = RFID_Manager()
    
    while True:
        print("\nOptions:")
        print("1. Check card presence")
        print("2. Get card info")
        print("3. Read specific block")
        print("4. Write to block")
        print("5. Write string")
        print("6. Read string")
        print("7. Write long string")
        print("8. Get string info")
        print("9. Check available space")
        print("10. Refresh card cache")
        print("11. Check/recover connection")
        print("12. Display card contents")
        print("13. Quick read")
        print("14. Exit")
        
        try:
            choice = input("\nEnter choice (1-14): ").strip()
            
            if choice == '1':
                if rfid.is_card_present():
                    print("✅ Card is present")
                else:
                    print("❌ No card detected")
            
            elif choice == '2':
                info = rfid.get_card_info()
                for key, value in info.items():
                    print(f"  {key}: {value}")
            
            elif choice == '3':
                block_num = int(input("Enter block number (0-63): "))
                data = rfid.read_block(block_num)
                if data:
                    hex_data = ' '.join([f'{b:02x}' for b in data])
                    ascii_data = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
                    print(f"Block {block_num}: {hex_data} | {ascii_data}")
                else:
                    print("❌ Failed to read block")
            
            elif choice == '4':
                block_num = int(input("Enter block number (1-62, avoid 0 and trailer blocks): "))
                hex_input = input("Enter 32 hex characters (16 bytes): ").replace(' ', '')
                if len(hex_input) == 32:
                    try:
                        data = bytes.fromhex(hex_input)
                        if rfid.write_block(block_num, data):
                            print("✅ Write successful")
                        else:
                            print("❌ Write failed")
                    except ValueError:
                        print("❌ Invalid hex input")
                else:
                    print("❌ Must provide exactly 32 hex characters")
            
            elif choice == '5':
                start_block = int(input("Enter starting block number: "))
                text = input("Enter text to write: ")
                if rfid.write_string(start_block, text):
                    print("✅ String write successful")
                else:
                    print("❌ String write failed")
            
            elif choice == '6':
                start_block = int(input("Enter starting block number: "))
                text = rfid.read_string(start_block)
                if text is not None:
                    print(f"✅ Read string: '{text}'")
                else:
                    print("❌ Failed to read string or no string found")
            
            elif choice == '7':
                sector = int(input("Enter starting sector (1-15 for 4K, 1-15 for 1K): "))
                text = input("Enter long text to write: ")
                if rfid.write_long_string(text, sector):
                    print("✅ Long string write successful")
                else:
                    print("❌ Long string write failed")
            
            elif choice == '8':
                start_block = int(input("Enter starting block number: "))
                info = rfid.get_string_info(start_block)
                if "error" not in info:
                    print(f"String Info:")
                    for key, value in info.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"❌ {info['error']}")
            
            elif choice == '9':
                start_block = int(input("Enter starting block for space calculation (default 1): ") or "1")
                space_info = rfid.get_available_space(start_block)
                print(f"Available Space:")
                for key, value in space_info.items():
                    print(f"  {key}: {value}")
            
            elif choice == '10':
                rfid.refresh_cache()
                print("✅ Card cache refreshed")
            
            elif choice == '11':
                if rfid.check_and_recover_connection():
                    print("✅ Card connection is working")
                else:
                    print("❌ Card connection failed")
            
            elif choice == '12':
                num_blocks = int(input("Enter number of blocks to display (1-64): "))
                print("\n" + rfid.format_card_display(num_blocks))
            
            elif choice == '13':
                result = rfid.quick_read_card()
                print("\nQuick Read Results:")
                print(f"Card Info: {result['info']}")
                print(f"Blocks: {len(result['blocks'])} blocks read")
                print(f"Strings: {len(result['strings'])} strings found")
            
            elif choice == '14':
                break
            
            else:
                print("❌ Invalid choice")
                
        except ValueError:
            print("❌ Invalid input")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main test function."""
    print("RFID Manager Test Suite")
    print("Make sure your PN532 is connected and a card is available")
    print()
    
    # Check if we can run basic NFC commands
    try:
        import subprocess
        result = subprocess.run(['nfc-list'], capture_output=True, text=True, timeout=3)
        if result.returncode != 0:
            print("❌ Error: nfc-list failed. Make sure libnfc is properly installed and configured.")
            print(f"Error: {result.stderr}")
            return
    except Exception as e:
        print(f"❌ Error: Cannot run nfc-list: {e}")
        return
    
    print("✅ libnfc is working")
    print()
    
    # Run tests
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Card Detection
    total_tests += 1
    if test_card_detection():
        tests_passed += 1
    
    if tests_passed == 0:
        print("\n❌ Card detection failed. Cannot continue with other tests.")
        return
    
    # Test 2: Block Reading
    total_tests += 1
    if test_block_reading():
        tests_passed += 1
    
    # Ask user if they want to do write tests (they modify the card)
    print("\n" + "=" * 60)
    print("The following tests will MODIFY your card contents!")
    choice = input("Continue with write tests? (y/N): ").strip().lower()
    
    if choice.startswith('y'):
        # Test 3: String Operations
        total_tests += 1
        if test_string_operations():
            tests_passed += 1
    
    # Test 4: Card Display (read-only)
    total_tests += 1
    if test_card_display():
        tests_passed += 1
    
    # Test 5: Quick Read (read-only)
    total_tests += 1
    if test_quick_read():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Your RFID setup is working perfectly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    # Interactive mode
    choice = input("\nEnter interactive mode? (y/N): ").strip().lower()
    if choice.startswith('y'):
        interactive_test()
    
    print("\nTest suite completed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()