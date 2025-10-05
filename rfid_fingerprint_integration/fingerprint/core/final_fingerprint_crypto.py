#!/usr/bin/env python3
"""
Final Fingerprint-Based Encryption System
Uses a hybrid approach: fingerprint for authentication, stored template for key derivation
This ensures consistent keys while still requiring biometric authentication
"""

import sys
import os
# Add the tests directory to Python path to import as608_menu
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests'))

from as608_menu import open_sensor, list_ids, get_template
import adafruit_fingerprint
import hashlib
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class FinalFingerprintCrypto:
    def __init__(self):
        self.finger = None
        self.stored_ids = []
        
    def connect_sensor(self):
        """Connect to the fingerprint sensor."""
        try:
            self.finger = open_sensor()
            if self.finger:
                self.stored_ids = list_ids(self.finger)
                print(f"✅ Connected to sensor. Stored IDs: {self.stored_ids}")
                return True
            return False
        except Exception as e:
            print(f"❌ Sensor connection failed: {e}")
            return False
    
    def simple_finger_detect(self):
        """
        Simple finger detection that just waits for ANY finger.
        We'll verify the identity using the stored templates afterward.
        """
        try:
            print("👆 Place your finger on the sensor...")
            
            # Wait for finger
            while self.finger.get_image() != adafruit_fingerprint.OK:
                time.sleep(0.2)
                
            print("✅ Finger detected")
            return True
            
        except Exception as e:
            print(f"❌ Error detecting finger: {e}")
            return False
    
    def verify_identity_with_stored_templates(self):
        """
        Verify the scanned finger against all stored templates using robust matching.
        Returns the matching finger ID or None.
        """
        try:
            print("👆 Place your finger on the sensor...")
            
            # Direct sensor approach with better error handling
            # Wait for finger with timeout
            max_attempts = 3
            
            for attempt in range(max_attempts):
                try:
                    # Wait for finger detection
                    start_time = time.time()
                    while time.time() - start_time < 10:  # 10 second timeout per attempt
                        if self.finger.get_image() == adafruit_fingerprint.OK:
                            print("✅ Finger detected")
                            break
                        time.sleep(0.1)
                    else:
                        if attempt < max_attempts - 1:
                            print(f"⏱️ Timeout on attempt {attempt + 1}, trying again...")
                            continue
                        else:
                            print("❌ Timeout waiting for finger")
                            return None
                    
                    # Convert image to template
                    if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
                        if attempt < max_attempts - 1:
                            print(f"❌ Template conversion failed on attempt {attempt + 1}, retrying...")
                            continue
                        else:
                            print("❌ Failed to create template from finger")
                            return None
                    
                    # Search for match
                    search_result = self.finger.finger_search()
                    
                    if search_result == adafruit_fingerprint.OK:
                        finger_id = self.finger.finger_id
                        confidence = self.finger.confidence
                        
                        # Check if confidence is acceptable (lower threshold for compatibility)
                        if confidence >= 30:  # Lower threshold
                            if finger_id in self.stored_ids:
                                print(f"✅ Identity verified! ID: {finger_id}, Confidence: {confidence}")
                                return finger_id
                            else:
                                print(f"⚠️ Finger ID {finger_id} not in expected list {self.stored_ids}")
                        else:
                            print(f"⚠️ Low confidence match: {confidence}, trying again...")
                            if attempt < max_attempts - 1:
                                continue
                    
                    elif search_result == adafruit_fingerprint.NOTFOUND:
                        if attempt < max_attempts - 1:
                            print(f"❌ No match on attempt {attempt + 1}, trying again...")
                            continue
                        else:
                            print("❌ No matching identity found after all attempts")
                    
                    else:
                        print(f"❌ Search failed with code: {hex(search_result)}")
                        if attempt < max_attempts - 1:
                            continue
                        
                except Exception as attempt_error:
                    print(f"❌ Error on attempt {attempt + 1}: {attempt_error}")
                    if attempt < max_attempts - 1:
                        continue
            
            return None
                
        except Exception as e:
            print(f"❌ Identity verification error: {e}")
            return None
    
    def authenticate_fingerprint(self):
        """
        Complete authentication: detect finger and verify identity using enhanced matching.
        """
        # The enhanced verify_identity_with_stored_templates now handles detection internally
        finger_id = self.verify_identity_with_stored_templates()
        if finger_id:
            time.sleep(0.3)  # Small delay after successful auth
            
        return finger_id
    
    def get_fingerprint_key(self, finger_id):
        """
        Generate encryption key from stored fingerprint template.
        Always uses the stored template for consistency.
        """
        try:
            # Get the stored template (always consistent)
            template = get_template(self.finger, finger_id)
            if not template:
                print(f"❌ Could not retrieve stored template for ID {finger_id}")
                return None
            
            # Create salt from template
            salt = hashlib.sha256(template).digest()[:16]  # 16-byte salt
            
            # Derive key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,  # 32 bytes = 256 bits for AES-256
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            
            key = kdf.derive(template)
            return key
            
        except Exception as e:
            print(f"❌ Key derivation error: {e}")
            return None
    
    def encrypt_message(self, message, finger_id=None):
        """Encrypt a message using fingerprint-derived key."""
        try:
            # Authenticate if no finger_id provided
            if finger_id is None:
                finger_id = self.authenticate_fingerprint()
                if not finger_id:
                    print("❌ Authentication failed - cannot encrypt")
                    return None
            
            # Get encryption key
            key = self.get_fingerprint_key(finger_id)
            if not key:
                print("❌ Failed to derive encryption key")
                return None
                
            # Generate random nonce
            nonce = os.urandom(16)
            
            # Encrypt
            cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(message.encode('utf-8')) + encryptor.finalize()
            
            print(f"✅ Message encrypted with fingerprint ID {finger_id}")
            return nonce + ciphertext
            
        except Exception as e:
            print(f"❌ Encryption error: {e}")
            return None
    
    def decrypt_message(self, encrypted_data):
        """Decrypt a message using fingerprint authentication."""
        try:
            # Authenticate
            finger_id = self.authenticate_fingerprint()
            if not finger_id:
                print("❌ Authentication failed - cannot decrypt")
                return None
            
            # Get decryption key
            key = self.get_fingerprint_key(finger_id)
            if not key:
                print("❌ Failed to derive decryption key")
                return None
            
            # Extract nonce and ciphertext
            nonce = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            # Decrypt
            cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            message = plaintext.decode('utf-8')
            print(f"✅ Message decrypted successfully")
            return message
            
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            return None


def main():
    """Test the final fingerprint crypto system."""
    crypto = FinalFingerprintCrypto()
    
    if not crypto.connect_sensor():
        print("❌ Failed to connect to fingerprint sensor")
        return
    
    # Test message
    message = "This is my final secure message using biometric encryption!"
    print(f"Original message: \"{message}\"")
    print()
    
    # Encrypt
    print("🔐 ENCRYPTION TEST")
    print("-" * 20)
    encrypted_data = crypto.encrypt_message(message)
    
    if not encrypted_data:
        print("❌ Encryption failed!")
        return
    
    print(f"✅ Encrypted! Data size: {len(encrypted_data)} bytes")
    print()
    
    # Multiple decryption tests
    print("🔓 DECRYPTION TESTS")
    print("-" * 20)
    
    for i in range(3):
        print(f"\nTest {i+1}/3:")
        decrypted = crypto.decrypt_message(encrypted_data)
        
        if decrypted and decrypted == message:
            print("   ✅ SUCCESS!")
        else:
            print("   ❌ FAILED!")
            break
    
    print("\n🎉 Final fingerprint encryption system test complete!")


if __name__ == "__main__":
    main()