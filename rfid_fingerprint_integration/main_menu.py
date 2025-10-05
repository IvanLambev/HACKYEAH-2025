#!/usr/bin/env python3
"""
Main Menu - Biometric Security System
====================================

Combined Fingerprint + RFID Authentication System
This is the main entry point for the biometric security system.

Usage:
    python main_menu.py

Features:
- Fingerprint authentication with encryption
- RFID card storage and retrieval
- Combined biometric security workflows
- Interactive menu system

Author: Assistant
Date: October 2025
"""

import sys
import os

# Add the local directories to the Python path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fingerprint', 'core'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rfid', 'core'))

from final_fingerprint_crypto import FinalFingerprintCrypto
from rfid_manager import RFID_Manager
import json
import time
import base64
from datetime import datetime


class BiometricSecurityMenu:
    """Main menu class for the biometric security system."""
    
    def __init__(self):
        """Initialize the biometric security system."""
        print("🔐 Initializing Biometric Security System...")
        
        # Initialize components
        self.fingerprint = FinalFingerprintCrypto()
        self.rfid = RFID_Manager()
        
        # Session data
        self.encrypted_messages = []
        self.connected = False
        
        print("✅ System initialized successfully!")
    
    def connect_to_sensor(self):
        """Connect to the fingerprint sensor."""
        if self.connected:
            print("✅ Already connected to sensor")
            return True
            
        print("🔌 Connecting to fingerprint sensor...")
        if self.fingerprint.connect_sensor():
            self.connected = True
            print("✅ Successfully connected!")
            return True
        else:
            print("❌ Failed to connect to sensor")
            return False
    
    def show_main_menu(self):
        """Display the main menu."""
        print("\n" + "="*70)
        print("🔐 BIOMETRIC SECURITY SYSTEM - MAIN MENU")
        print("="*70)
        print("📡 SYSTEM OPERATIONS")
        print("1. 🔌 Connect to Fingerprint Sensor")
        print("2. 📋 Show System Status")
        print("3. 🚪 Exit")
        print()
        print("🔐 FINGERPRINT OPERATIONS")
        print("11. 🔐 Encrypt Message with Fingerprint")
        print("12. 🔓 Decrypt Message with Fingerprint")
        print("13. 📝 Encrypt & Save to File")
        print("14. 📖 Decrypt from File")
        print("15. 🧪 Run Fingerprint System Test")
        print()
        print("💳 RFID CARD OPERATIONS")
        print("21. 🏷️  Check RFID Card Status")
        print("22. 💾 Save Encrypted Message to Card")
        print("23. 📂 Read Encrypted Message from Card")
        print("24. 🧹 Clear Card Data")
        print("25. 📊 Show Card Contents")
        print()
        print("💡 SYSTEM TESTS & UTILITIES")
        print("31. 🔄 Test Multiple Decryptions")
        print("32. 📊 Show Encrypted Messages")
        print("33. 🧹 Clear All Messages")
        print("="*70)
    
    def show_system_status(self):
        """Show current system status."""
        print("\n📡 BIOMETRIC SECURITY SYSTEM STATUS")
        print("-" * 40)
        print(f"Fingerprint Sensor: {'✅ Connected' if self.connected else '❌ Not Connected'}")
        
        if self.connected:
            print(f"Stored fingerprint IDs: {self.fingerprint.stored_ids}")
            print(f"Number of fingerprints: {len(self.fingerprint.stored_ids)}")
        
        # Check RFID reader
        print(f"RFID Reader: {'✅ Available' if self.rfid.is_card_present() else '⚠️  No card detected'}")
        print(f"Session Messages: {len(self.encrypted_messages)} encrypted messages stored")
        
        if self.connected and not self.fingerprint.stored_ids:
            print("\n⚠️  No fingerprints enrolled!")
            print("   Use the enrollment script in fingerprint/tests/ to add fingerprints first.")
    
    def encrypt_message_interactive(self):
        """Interactive message encryption using fingerprint."""
        if not self.connected:
            print("❌ Please connect to fingerprint sensor first (option 1)")
            return
            
        print("\n🔐 ENCRYPT MESSAGE WITH FINGERPRINT")
        print("-" * 35)
        
        message = input("Enter message to encrypt: ").strip()
        if not message:
            print("❌ Empty message, cancelling")
            return
            
        print(f"\nMessage: \"{message}\"")
        print("Please authenticate with your fingerprint...")
        
        encrypted_data = self.fingerprint.encrypt_message(message)
        
        if encrypted_data:
            # Store for later use
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
        """Interactive message decryption using fingerprint."""
        if not self.connected:
            print("❌ Please connect to fingerprint sensor first (option 1)")
            return
            
        if not self.encrypted_messages:
            print("❌ No encrypted messages available")
            print("   Please encrypt a message first (option 11)")
            return
            
        print("\n🔓 DECRYPT MESSAGE WITH FINGERPRINT")
        print("-" * 35)
        
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
                
                decrypted = self.fingerprint.decrypt_message(entry['encrypted_data'])
                
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
            print("❌ Please connect to fingerprint sensor first (option 1)")
            return
            
        print("\n📝 ENCRYPT & SAVE TO FILE")
        print("-" * 25)
        
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
        
        encrypted_data = self.fingerprint.encrypt_message(message)
        
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
            print("❌ Please connect to fingerprint sensor first (option 1)")
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
                    
                    decrypted = self.fingerprint.decrypt_message(encrypted_data)
                    
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
    
    def run_fingerprint_test(self):
        """Run comprehensive fingerprint system test."""
        if not self.connected:
            print("❌ Please connect to fingerprint sensor first (option 1)")
            return
            
        print("\n🧪 FINGERPRINT SYSTEM TEST")
        print("-" * 25)
        
        test_message = "System test message - " + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Test message: \"{test_message}\"")
        print("\n1️⃣ Testing encryption...")
        
        encrypted_data = self.fingerprint.encrypt_message(test_message)
        
        if not encrypted_data:
            print("❌ Encryption test failed!")
            return
            
        print("✅ Encryption successful!")
        
        print("\n2️⃣ Testing decryption...")
        
        decrypted = self.fingerprint.decrypt_message(encrypted_data)
        
        if decrypted != test_message:
            print("❌ Decryption test failed!")
            return
            
        print("✅ Decryption successful!")
        print("\n🎉 FINGERPRINT SYSTEM TEST PASSED!")
    
    def check_rfid_card_status(self):
        """Check RFID card status and information."""
        print("\n🏷️ CHECKING RFID CARD STATUS")
        print("-" * 30)
        
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
    
    def save_to_rfid_card(self):
        """Save encrypted message to RFID card."""
        if not self.connected:
            print("❌ Please connect to fingerprint sensor first (option 1)")
            return
            
        print("\n💾 SAVE ENCRYPTED MESSAGE TO RFID CARD")
        print("-" * 40)
        
        print("Place MIFARE Classic card on NFC reader...")
        if not self.rfid.wait_for_card(timeout=10):
            print("❌ No card detected")
            return
            
        # Get message to encrypt
        message = input("\nEnter message to encrypt and save to card: ").strip()
        if not message:
            print("❌ Empty message")
            return
            
        print(f"\nMessage: \"{message}\" ({len(message)} chars)")
        print("🔐 Encrypting with fingerprint authentication...")
        
        # Encrypt the message using fingerprint
        encrypted_data = self.fingerprint.encrypt_message(message)
        
        if not encrypted_data:
            print("❌ Encryption failed!")
            return
        
        print(f"✅ Message encrypted! ({len(encrypted_data)} bytes)")
        
        # Convert encrypted binary data to base64 string for card storage
        encrypted_b64 = base64.b64encode(encrypted_data).decode('ascii')
        card_string = f"ENCRYPTED:{encrypted_b64}:{len(message)}"
        
        print(f"Prepared card string: {len(card_string)} characters")
        
        # Write to card
        start_block = 8  # Use sector 2 for reliability
        
        print(f"Writing to block {start_block}...")
        
        if self.rfid.write_string(start_block, card_string):
            print("✅ Message securely stored on card!")
            print("   Use option 23 to read it back.")
        else:
            print("❌ Failed to write to card")
    
    def read_from_rfid_card(self):
        """Read and decrypt message from RFID card."""
        if not self.connected:
            print("❌ Please connect to fingerprint sensor first (option 1)")
            return
            
        print("\n📂 READ ENCRYPTED MESSAGE FROM RFID CARD")
        print("-" * 45)
        
        print("Place MIFARE Classic card on NFC reader...")
        if not self.rfid.wait_for_card(timeout=10):
            print("❌ No card detected")
            return
            
        print("✅ Card detected!")
        print("🔍 Reading encrypted data...")
        
        # Read from card
        start_block = 8  # Same block as writing
        
        card_string = self.rfid.read_string(start_block)
        
        if not card_string:
            print("❌ No data found on card")
            print("   Make sure you've saved an encrypted message first (option 22)")
            return
        
        print(f"✅ Read {len(card_string)} characters from card")
        
        # Parse the format: "ENCRYPTED:" + base64_data + ":" + original_length
        if not card_string.startswith("ENCRYPTED:"):
            print("❌ Invalid format - not an encrypted message")
            return
        
        try:
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
        decrypted_message = self.fingerprint.decrypt_message(encrypted_data)
        
        if decrypted_message:
            print(f"\n✅ SUCCESSFULLY DECRYPTED!")
            print(f"📄 Message: \"{decrypted_message}\"")
            print(f"   Length: {len(decrypted_message)} characters")
        else:
            print("❌ Decryption failed!")
    
    def clear_rfid_card_data(self):
        """Clear all data from RFID card."""
        print("\n🧹 CLEAR RFID CARD DATA")
        print("-" * 25)
        
        print("Place MIFARE Classic card on NFC reader...")
        if not self.rfid.wait_for_card(timeout=10):
            print("❌ No card detected")
            return
            
        print("✅ Card detected!")
        
        # Confirm clearing
        confirm = input("\n⚠️ This will permanently erase all data on the card. Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("❌ Cancelled")
            return
            
        print("🧹 Clearing card data...")
        
        # Write empty blocks to clear data
        success_count = 0
        for block in [1, 2, 4, 5, 6, 8, 9, 10, 12, 13, 14]:
            empty_data = b'\x00' * 16
            if self.rfid.write_block(block, empty_data):
                success_count += 1
            
        if success_count > 0:
            print(f"✅ Cleared {success_count} blocks")
            print("Card is now ready for new data")
        else:
            print("❌ Failed to clear card data")
    
    def show_rfid_card_contents(self):
        """Show raw RFID card contents."""
        print("\n📊 RFID CARD CONTENTS")
        print("-" * 25)
        
        print("Place MIFARE Classic card on NFC reader...")
        if not self.rfid.wait_for_card(timeout=10):
            print("❌ No card detected")
            return
            
        print("✅ Card detected! Reading contents...")
        
        # Display formatted card contents
        display = self.rfid.format_card_display(num_blocks=16)
        print(f"\n{display}")
    
    def test_multiple_decryptions(self):
        """Test multiple consecutive decryptions."""
        if not self.connected:
            print("❌ Please connect to fingerprint sensor first (option 1)")
            return
            
        print("\n🔄 MULTIPLE DECRYPTION TEST")
        print("-" * 30)
        
        num_tests = input("How many decryptions to test? (default: 3): ").strip()
        try:
            num_tests = int(num_tests) if num_tests else 3
        except ValueError:
            num_tests = 3
            
        test_message = f"Multi-decrypt test - {datetime.now().strftime('%H:%M:%S')}"
        
        print(f"\nTest message: \"{test_message}\"")
        print("Encrypting...")
        
        encrypted_data = self.fingerprint.encrypt_message(test_message)
        
        if not encrypted_data:
            print("❌ Initial encryption failed!")
            return
            
        print(f"✅ Encrypted successfully!")
        print(f"\nNow testing {num_tests} consecutive decryptions...")
        
        success_count = 0
        
        for i in range(num_tests):
            print(f"\n--- Decryption {i+1}/{num_tests} ---")
            
            decrypted = self.fingerprint.decrypt_message(encrypted_data)
            
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
    
    def run(self):
        """Run the main interactive menu."""
        print("🔐 Biometric Security System")
        print("============================\n")
        
        while True:
            self.show_main_menu()
            
            try:
                choice = input("\nEnter your choice: ").strip()
                
                if choice == '3':
                    print("\n👋 Goodbye!")
                    break
                elif choice == '1':
                    self.connect_to_sensor()
                elif choice == '2':
                    self.show_system_status()
                elif choice == '11':
                    self.encrypt_message_interactive()
                elif choice == '12':
                    self.decrypt_message_interactive()
                elif choice == '13':
                    self.encrypt_to_file()
                elif choice == '14':
                    self.decrypt_from_file()
                elif choice == '15':
                    self.run_fingerprint_test()
                elif choice == '21':
                    self.check_rfid_card_status()
                elif choice == '22':
                    self.save_to_rfid_card()
                elif choice == '23':
                    self.read_from_rfid_card()
                elif choice == '24':
                    self.clear_rfid_card_data()
                elif choice == '25':
                    self.show_rfid_card_contents()
                elif choice == '31':
                    self.test_multiple_decryptions()
                elif choice == '32':
                    self.show_encrypted_messages()
                elif choice == '33':
                    self.clear_all_messages()
                else:
                    print("❌ Invalid choice. Please try again.")
                    
                input("\nPress Enter to continue...")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("Press Enter to continue...")


if __name__ == "__main__":
    menu = BiometricSecurityMenu()
    menu.run()