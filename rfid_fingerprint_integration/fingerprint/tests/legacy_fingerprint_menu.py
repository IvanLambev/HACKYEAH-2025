#!/usr/bin/env python3
"""
Fingerprint Encryption System with RFID Card Storage
Complete biometric encryption system with MIFARE card storage capability
"""

from final_fingerprint_crypto import FinalFingerprintCrypto
from rfid_manager import RFID_Manager
import os
import json
import time
import subprocess
import base64
from datetime import datetime


class FingerprintCryptoMenu:
    def __init__(self):
        self.crypto = FinalFingerprintCrypto()
        self.rfid = RFID_Manager()
        self.encrypted_messages = []  # Store encrypted messages for testing
        self.connected = False
        
    def connect_to_sensor(self):
        """Connect to the fingerprint sensor."""
        if self.connected:
            print("✅ Already connected to sensor")
            return True
            
        print("🔌 Connecting to fingerprint sensor...")
        if self.crypto.connect_sensor():
            self.connected = True
            print("✅ Successfully connected!")
            return True
        else:
            print("❌ Failed to connect to sensor")
            return False
    
    def show_main_menu(self):
        """Display the main menu."""
        print("\n" + "="*60)
        print("🔐 FINGERPRINT ENCRYPTION + RFID CARD SYSTEM")
        print("="*60)
        print("1. 📡 Connect to Sensor")
        print("2. 📋 Show Sensor Status")
        print("3. 🔐 Encrypt Message")
        print("4. 🔓 Decrypt Message")
        print("5. 📝 Encrypt & Save to File")
        print("6. 📖 Decrypt from File")
        print("💳 === RFID CARD OPERATIONS === (Requires compatible card)")
        print("11. 🏷️  Check Card Status")
        print("12. 💾 Save Encrypted Message to Card")
        print("13. 📂 Read Encrypted Message from Card")
        print("14. 🧹 Clear Card Data")
        print("15. 📊 Show Card Contents")
        print("💡 === SYSTEM TESTS === (Memory-based - Always works!)")
        print("7. 🧪 Run System Test")
        print("8. 🔄 Test Multiple Decryptions")
        print("9. 📊 Show Encrypted Messages")
        print("10. 🧹 Clear All Messages")
        print("0. 🚪 Exit")
        print("="*60)
    
    def show_sensor_status(self):
        """Show current sensor status and stored fingerprints."""
        if not self.connected:
            print("❌ Not connected to sensor")
            return
            
        print("\n📡 SENSOR STATUS")
        print("-" * 30)
        print(f"Connected: ✅ Yes")
        print(f"Stored fingerprint IDs: {self.crypto.stored_ids}")
        print(f"Number of fingerprints: {len(self.crypto.stored_ids)}")
        
        if self.crypto.stored_ids:
            print("\nStored fingerprints:")
            for finger_id in self.crypto.stored_ids:
                print(f"  • ID {finger_id}: Ready for authentication")
        else:
            print("⚠️  No fingerprints enrolled!")
            print("   Use the enrollment script to add fingerprints first.")
    
    def encrypt_message_interactive(self):
        """Interactive message encryption."""
        if not self.connected:
            print("❌ Please connect to sensor first")
            return
            
        print("\n🔐 ENCRYPT MESSAGE")
        print("-" * 20)
        
        message = input("Enter message to encrypt: ").strip()
        if not message:
            print("❌ Empty message, cancelling")
            return
            
        print(f"\nMessage: \"{message}\"")
        print("Please authenticate with your fingerprint...")
        
        encrypted_data = self.crypto.encrypt_message(message)
        
        if encrypted_data:
            # Store for later decryption tests
            entry = {
                'message': message,
                'encrypted_data': encrypted_data,
                'timestamp': datetime.now().isoformat(),
                'size': len(encrypted_data)
            }
            self.encrypted_messages.append(entry)
            
            print(f"\n✅ Message encrypted successfully!")
            print(f"   Original size: {len(message)} characters")
            print(f"   Encrypted size: {len(encrypted_data)} bytes")
            print(f"   Stored as message #{len(self.encrypted_messages)}")
        else:
            print("❌ Encryption failed!")
    
    def decrypt_message_interactive(self):
        """Interactive message decryption."""
        if not self.connected:
            print("❌ Please connect to sensor first")
            return
            
        if not self.encrypted_messages:
            print("❌ No encrypted messages available")
            print("   Please encrypt a message first")
            return
            
        print("\n🔓 DECRYPT MESSAGE")
        print("-" * 20)
        
        # Show available messages
        print("Available encrypted messages:")
        for i, entry in enumerate(self.encrypted_messages, 1):
            timestamp = entry['timestamp'][:19].replace('T', ' ')
            print(f"  {i}. \"{entry['message'][:50]}...\" ({timestamp})")
        
        try:
            choice = int(input(f"\nSelect message to decrypt (1-{len(self.encrypted_messages)}): "))
            if 1 <= choice <= len(self.encrypted_messages):
                entry = self.encrypted_messages[choice - 1]
                
                print(f"\nDecrypting message: \"{entry['message'][:50]}...\"")
                print("Please authenticate with your fingerprint...")
                
                decrypted = self.crypto.decrypt_message(entry['encrypted_data'])
                
                if decrypted:
                    print(f"\n✅ Decryption successful!")
                    print(f"   Original: \"{entry['message']}\"")
                    print(f"   Decrypted: \"{decrypted}\"")
                    
                    if decrypted == entry['message']:
                        print("   ✅ Messages match perfectly!")
                    else:
                        print("   ❌ Messages don't match!")
                else:
                    print("❌ Decryption failed!")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def encrypt_to_file(self):
        """Encrypt a message and save to file."""
        if not self.connected:
            print("❌ Please connect to sensor first")
            return
            
        print("\n📝 ENCRYPT & SAVE TO FILE")
        print("-" * 30)
        
        message = input("Enter message to encrypt: ").strip()
        if not message:
            print("❌ Empty message, cancelling")
            return
            
        filename = input("Enter filename (without extension): ").strip()
        if not filename:
            filename = f"encrypted_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        filename += ".enc"
        
        print(f"\nEncrypting message to file: {filename}")
        print("Please authenticate with your fingerprint...")
        
        encrypted_data = self.crypto.encrypt_message(message)
        
        if encrypted_data:
            try:
                # Save to file with metadata
                file_data = {
                    'encrypted_data': encrypted_data.hex(),
                    'original_message_length': len(message),
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0'
                }
                
                with open(filename, 'w') as f:
                    json.dump(file_data, f, indent=2)
                
                print(f"✅ Message encrypted and saved to {filename}")
                print(f"   File size: {os.path.getsize(filename)} bytes")
                
            except Exception as e:
                print(f"❌ Failed to save file: {e}")
        else:
            print("❌ Encryption failed!")
    
    def decrypt_from_file(self):
        """Decrypt a message from file."""
        if not self.connected:
            print("❌ Please connect to sensor first")
            return
            
        print("\n📖 DECRYPT FROM FILE")
        print("-" * 20)
        
        # List .enc files
        enc_files = [f for f in os.listdir('.') if f.endswith('.enc')]
        
        if not enc_files:
            print("❌ No encrypted files found in current directory")
            return
            
        print("Available encrypted files:")
        for i, filename in enumerate(enc_files, 1):
            size = os.path.getsize(filename)
            print(f"  {i}. {filename} ({size} bytes)")
        
        try:
            choice = int(input(f"\nSelect file to decrypt (1-{len(enc_files)}): "))
            if 1 <= choice <= len(enc_files):
                filename = enc_files[choice - 1]
                
                try:
                    with open(filename, 'r') as f:
                        file_data = json.load(f)
                    
                    encrypted_data = bytes.fromhex(file_data['encrypted_data'])
                    
                    print(f"\nDecrypting file: {filename}")
                    print("Please authenticate with your fingerprint...")
                    
                    decrypted = self.crypto.decrypt_message(encrypted_data)
                    
                    if decrypted:
                        print(f"\n✅ File decrypted successfully!")
                        print(f"   Message: \"{decrypted}\"")
                        print(f"   Original length: {file_data.get('original_message_length', 'unknown')}")
                        print(f"   Encrypted on: {file_data.get('timestamp', 'unknown')}")
                    else:
                        print("❌ Decryption failed!")
                        
                except Exception as e:
                    print(f"❌ Error reading file: {e}")
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Please enter a valid number")
    
    def run_system_test(self):
        """Run comprehensive system test."""
        if not self.connected:
            print("❌ Please connect to sensor first")
            return
            
        print("\n🧪 SYSTEM TEST")
        print("-" * 15)
        
        test_message = "System test message - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Test message: \"{test_message}\"")
        print("\n1️⃣ Testing encryption...")
        
        encrypted_data = self.crypto.encrypt_message(test_message)
        
        if not encrypted_data:
            print("❌ Encryption test failed!")
            return
            
        print("✅ Encryption successful!")
        
        print("\n2️⃣ Testing single decryption...")
        
        decrypted = self.crypto.decrypt_message(encrypted_data)
        
        if decrypted != test_message:
            print("❌ Decryption test failed!")
            return
            
        print("✅ Single decryption successful!")
        
        print("\n3️⃣ Testing multiple decryptions...")
        
        for i in range(3):
            print(f"   Decryption {i+1}/3...")
            decrypted = self.crypto.decrypt_message(encrypted_data)
            
            if decrypted != test_message:
                print(f"❌ Multiple decryption test failed at attempt {i+1}")
                return
                
        print("✅ Multiple decryptions successful!")
        print("\n🎉 ALL TESTS PASSED! System is working perfectly!")
    
    def test_multiple_decryptions(self):
        """Test multiple consecutive decryptions."""
        if not self.connected:
            print("❌ Please connect to sensor first")
            return
            
        print("\n🔄 MULTIPLE DECRYPTION TEST")
        print("-" * 30)
        
        num_tests = input("How many decryptions to test? (default: 5): ").strip()
        try:
            num_tests = int(num_tests) if num_tests else 5
        except ValueError:
            num_tests = 5
            
        test_message = f"Multi-decrypt test - {datetime.now().strftime('%H:%M:%S')}"
        
        print(f"\nTest message: \"{test_message}\"")
        print("Encrypting...")
        
        encrypted_data = self.crypto.encrypt_message(test_message)
        
        if not encrypted_data:
            print("❌ Initial encryption failed!")
            return
            
        print(f"✅ Encrypted successfully!")
        print(f"\nNow testing {num_tests} consecutive decryptions...")
        
        success_count = 0
        
        for i in range(num_tests):
            print(f"\n--- Decryption {i+1}/{num_tests} ---")
            
            decrypted = self.crypto.decrypt_message(encrypted_data)
            
            if decrypted == test_message:
                print(f"✅ Success!")
                success_count += 1
            else:
                print(f"❌ Failed!")
                break
                
        print(f"\n📊 RESULTS: {success_count}/{num_tests} decryptions successful")
        
        if success_count == num_tests:
            print("🎉 PERFECT! All decryptions worked!")
        else:
            print(f"⚠️  {num_tests - success_count} decryptions failed")
    
    def show_encrypted_messages(self):
        """Show all stored encrypted messages."""
        if not self.encrypted_messages:
            print("❌ No encrypted messages stored")
            return
            
        print(f"\n📊 STORED ENCRYPTED MESSAGES ({len(self.encrypted_messages)} total)")
        print("-" * 50)
        
        for i, entry in enumerate(self.encrypted_messages, 1):
            timestamp = entry['timestamp'][:19].replace('T', ' ')
            preview = entry['message'][:40] + "..." if len(entry['message']) > 40 else entry['message']
            
            print(f"{i:2d}. {preview}")
            print(f"    Size: {entry['size']} bytes | Time: {timestamp}")
            print()
    
    def clear_all_messages(self):
        """Clear all stored encrypted messages."""
        if not self.encrypted_messages:
            print("❌ No messages to clear")
            return
            
        count = len(self.encrypted_messages)
        confirm = input(f"Clear all {count} encrypted messages? (y/N): ").strip().lower()
        
        if confirm == 'y':
            self.encrypted_messages.clear()
            print(f"✅ Cleared {count} messages")
        else:
            print("❌ Cancelled")
    
    # ================== RFID CARD OPERATIONS ==================
    
    def check_card_status(self):
        """Check RFID card status and information."""
        print("\n🏷️ CHECKING RFID CARD STATUS")
        print("-" * 35)
        
        print("Place MIFARE Classic card on NFC reader...")
        
        if not self.rfid.wait_for_card(timeout=10):
            print("❌ No card detected within 10 seconds")
            return
            
        print("✅ Card detected!")
        
        # Get card information
        card_info = self.rfid.get_card_info()
        
        print(f"\n📋 CARD INFORMATION:")
        print(f"   UID: {card_info.get('uid', 'Unknown')}")
        print(f"   Type: {card_info.get('type', 'Unknown')}")
        print(f"   Size: {card_info.get('size', 'Unknown')}")
        print(f"   Present: {'✅' if card_info.get('present', False) else '❌'}")
        
        # Check for existing encrypted data
        print(f"\n🔍 CHECKING FOR ENCRYPTED DATA:")
        
        for start_block in [1, 4, 8]:
            string_info = self.rfid.get_string_info(start_block)
            if not string_info.get('error'):
                print(f"   Block {start_block}: Found {string_info['length']} chars")
                print(f"      Preview: \"{string_info['preview']}\"")
            else:
                print(f"   Block {start_block}: No data")
        
        # Show available space
        space_info = self.rfid.get_available_space()
        print(f"\n💾 STORAGE CAPACITY:")
        print(f"   Card Type: {space_info['card_type']}")
        print(f"   Available Blocks: {space_info['available_blocks']}")
        print(f"   Max Characters: ~{space_info['estimated_max_chars']}")
    
    def save_to_card(self):
        """Save encrypted message to RFID card using the same method as test_rfid.py."""
        if not self.connected:
            print("❌ Please connect to fingerprint sensor first")
            return
            
        print("\n💾 SAVE ENCRYPTED MESSAGE TO CARD")
        print("-" * 40)
        
        print("Place MIFARE Classic card on NFC reader...")
        if not self.rfid.wait_for_card(timeout=10):
            print("❌ No card detected")
            return
            
        # Check connection before writing (same as test_rfid.py)
        if not self.rfid.check_and_recover_connection():
            print("❌ Card connection lost")
            return
            
        # Get message to encrypt
        message = input("\nEnter message to encrypt and save to card: ").strip()
        if not message:
            print("❌ Empty message")
            return
            
        print(f"\nMessage: \"{message}\" ({len(message)} chars)")
        print("🔐 Encrypting with fingerprint authentication...")
        
        # Encrypt the message using fingerprint
        encrypted_data = self.crypto.encrypt_message(message)
        
        if not encrypted_data:
            print("❌ Encryption failed!")
            return
        
        print(f"✅ Message encrypted! ({len(encrypted_data)} bytes)")
        
        # Convert encrypted binary data to base64 string so we can use write_string()
        # Format: "ENCRYPTED:" + base64_encoded_data + ":" + original_message_length
        encrypted_b64 = base64.b64encode(encrypted_data).decode('ascii')
        card_string = f"ENCRYPTED:{encrypted_b64}:{len(message)}"
        
        print(f"Prepared card string: {len(card_string)} characters")
        
        # Use sector 2 instead of sector 1 for better compatibility
        start_block = 8  # Sector 2, block 8 - known to work reliably
        
        print(f"Writing to block {start_block}...")
        
        # Write string using the same method as test_rfid.py
        if self.rfid.write_string(start_block, card_string):
            print("✅ Write successful")
            
            # Get info about the written string (same as test_rfid.py)
            info = self.rfid.get_string_info(start_block)
            if "error" not in info:
                print(f"String info: {info['length']} characters, {info['blocks_needed']} blocks, format: {info['format']}")
            
            # Verify by reading back (same as test_rfid.py)
            print("Reading back...")
            # Force a fresh read by clearing cache (same as test_rfid.py)
            self.rfid.refresh_cache()
            read_string = self.rfid.read_string(start_block)
            
            if read_string == card_string:
                print("✅ Read back matches perfectly!")
                print("✅ Message is securely stored on card.")
                print("   You can now use 'Read Encrypted Message from Card' to retrieve it.")
            else:
                print(f"⚠️ Read back differs:")
                if read_string:
                    print(f"  Expected length: {len(card_string)}")
                    print(f"  Got length: {len(read_string)}")
                    print(f"  First 100 chars match: {card_string[:100] == read_string[:100]}")
                else:
                    print("  Failed to read back string")
        else:
            print("❌ Write failed")
    
    def read_from_card(self):
        """Read and decrypt message from RFID card using the same method as test_rfid.py."""
        if not self.connected:
            print("❌ Please connect to fingerprint sensor first")
            return
            
        print("\n📂 READ ENCRYPTED MESSAGE FROM CARD")
        print("-" * 40)
        
        print("Place MIFARE Classic card on NFC reader...")
        if not self.rfid.wait_for_card(timeout=10):
            print("❌ No card detected")
            return
            
        print("✅ Card detected!")
        print("🔍 Reading encrypted data...")
        
        # Use sector 2 for reading (same as writing)
        start_block = 8  # Sector 2, block 8 - same as writing
        
        # Force a fresh read by clearing cache (same as test_rfid.py)
        self.rfid.refresh_cache()
        
        # Read the string using the same method as test_rfid.py
        card_string = self.rfid.read_string(start_block)
        
        if not card_string:
            print("❌ No data found on card at block 8")
            print("   Make sure you've saved an encrypted message first (option 12)")
            return
        
        print(f"✅ Read {len(card_string)} characters from card")
        
        # Parse our format: "ENCRYPTED:" + base64_data + ":" + original_length
        if not card_string.startswith("ENCRYPTED:"):
            print("❌ Invalid format - not an encrypted message")
            print(f"   Found: '{card_string[:50]}...'")
            return
        
        try:
            # Split the format: ENCRYPTED:base64data:length
            parts = card_string.split(":")
            if len(parts) != 3:
                print("❌ Invalid encrypted message format")
                return
            
            encrypted_b64 = parts[1]
            original_length = int(parts[2])
            
            # Decode the base64 encrypted data
            encrypted_data = base64.b64decode(encrypted_b64)
            
            print(f"📋 Message info:")
            print(f"   Original length: {original_length} characters")
            print(f"   Encrypted size: {len(encrypted_data)} bytes")
            
        except Exception as e:
            print(f"❌ Error parsing card data: {e}")
            return
        
        print(f"\n🔓 Decrypting with fingerprint authentication...")
        
        # Decrypt using fingerprint
        decrypted_message = self.crypto.decrypt_message(encrypted_data)
        
        if decrypted_message:
            print(f"\n✅ SUCCESSFULLY DECRYPTED!")
            print(f"📄 Message: \"{decrypted_message}\"")
            print(f"   Length: {len(decrypted_message)} characters")
            
            # Verify length matches what we stored
            if len(decrypted_message) == original_length:
                print("   ✅ Length verification passed")
            else:
                print("   ⚠️ Length mismatch - possible data corruption")
        else:
            print("❌ Decryption failed!")
            print("   Make sure you're using the same finger that encrypted the message")
    
    def clear_card_data(self):
        """Clear all data from RFID card."""
        print("\n🧹 CLEAR CARD DATA")
        print("-" * 20)
        
        print("Place MIFARE Classic card on NFC reader...")
        if not self.rfid.wait_for_card(timeout=10):
            print("❌ No card detected")
            return
            
        print("✅ Card detected!")
        
        # Check what's on the card first
        has_data = False
        for start_block in [1, 4, 8]:
            info = self.rfid.get_string_info(start_block)
            if not info.get('error'):
                print(f"Found data at block {start_block}: {info['length']} chars")
                has_data = True
        
        if not has_data:
            print("❌ No data found on card")
            return
            
        # Confirm clearing
        confirm = input("\n⚠️ This will permanently erase all data on the card. Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return
            
        print("🧹 Clearing card data...")
        
        # Write empty blocks to clear data
        success_count = 0
        for block in [1, 2, 4, 5, 6, 8, 9, 10, 12, 13, 14]:  # Skip trailer blocks
            empty_data = b'\x00' * 16
            if self.rfid.write_block(block, empty_data):
                success_count += 1
            
        if success_count > 0:
            print(f"✅ Cleared {success_count} blocks")
            print("Card is now ready for new data")
        else:
            print("❌ Failed to clear card data")
    
    def show_card_contents(self):
        """Show raw card contents for debugging."""
        print("\n📊 CARD CONTENTS (RAW)")
        print("-" * 25)
        
        print("Place MIFARE Classic card on NFC reader...")
        if not self.rfid.wait_for_card(timeout=10):
            print("❌ No card detected")
            return
            
        print("✅ Card detected! Reading contents...")
        
        # Display formatted card contents
        display = self.rfid.format_card_display(num_blocks=16)
        print(f"\n{display}")
        
        # Show string data if any
        print(f"\n🔤 STRING DATA ANALYSIS:")
        for start_block in [1, 4, 8]:
            info = self.rfid.get_string_info(start_block)
            if not info.get('error'):
                print(f"Block {start_block}: {info['length']} chars - \"{info['preview']}\"")
            else:
                print(f"Block {start_block}: No readable string data")
    
    def run(self):
        """Run the interactive menu."""
        print("🔐 Fingerprint Encryption System Menu")
        print("====================================")
        
        while True:
            self.show_main_menu()
            
            try:
                choice = input("\nEnter your choice (0-10): ").strip()
                
                if choice == '0':
                    print("\n👋 Goodbye!")
                    break
                elif choice == '1':
                    self.connect_to_sensor()
                elif choice == '2':
                    self.show_sensor_status()
                elif choice == '3':
                    self.encrypt_message_interactive()
                elif choice == '4':
                    self.decrypt_message_interactive()
                elif choice == '5':
                    self.encrypt_to_file()
                elif choice == '6':
                    self.decrypt_from_file()
                elif choice == '7':
                    self.run_system_test()
                elif choice == '8':
                    self.test_multiple_decryptions()
                elif choice == '9':
                    self.show_encrypted_messages()
                elif choice == '10':
                    self.clear_all_messages()
                elif choice == '11':
                    self.check_card_status()
                elif choice == '12':
                    self.save_to_card()
                elif choice == '13':
                    self.read_from_card()
                elif choice == '14':
                    self.clear_card_data()
                elif choice == '15':
                    self.show_card_contents()
                else:
                    print("❌ Invalid choice. Please enter 0-15.")
                    
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("Press Enter to continue...")


if __name__ == "__main__":
    menu = FingerprintCryptoMenu()
    menu.run()