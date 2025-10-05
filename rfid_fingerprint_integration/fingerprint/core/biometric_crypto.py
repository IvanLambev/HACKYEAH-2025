#!/usr/bin/env python3
"""
BiometricCrypto - Final Fingerprint Encryption Library
Simple, robust biometric encryption using AS608 fingerprint sensor
"""

import os
import time
import hashlib
import adafruit_fingerprint
import serial
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


class BiometricCrypto:
    """Fingerprint-based encryption system using AS608 sensor."""
    
    def __init__(self, port='/dev/serial0', baudrate=57600):
        self.port = port
        self.baudrate = baudrate
        self.sensor = None
        self.stored_ids = []
        
    def connect(self):
        """Connect to fingerprint sensor."""
        try:
            uart = serial.Serial(self.port, baudrate=self.baudrate, timeout=1)
            self.sensor = adafruit_fingerprint.Adafruit_Fingerprint(uart)
            
            # Test connection and get stored IDs
            self.stored_ids = self._get_stored_ids()
            return True
            
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def _get_stored_ids(self):
        """Get list of enrolled fingerprint IDs."""
        stored = []
        if self.sensor.read_templates() == adafruit_fingerprint.OK:
            for i in range(500):  # AS608 supports up to 500 templates
                if self.sensor.templates[i]:
                    stored.append(i)
        return stored
    
    def _get_template(self, finger_id):
        """Get stored template for given finger ID."""
        try:
            if self.sensor.load_model(finger_id) == adafruit_fingerprint.OK:
                if self.sensor.get_fpdata("char", 1) == adafruit_fingerprint.OK:
                    return self.sensor.fpdata
            return None
        except:
            return None
    
    def authenticate(self):
        """Authenticate user with fingerprint scan."""
        try:
            print("👆 Place finger on sensor...")
            
            # Wait for finger detection
            while self.sensor.get_image() != adafruit_fingerprint.OK:
                time.sleep(0.2)
                
            print("✅ Finger detected")
            
            # Convert to template and search
            if self.sensor.image_2_tz(1) != adafruit_fingerprint.OK:
                print("❌ Template creation failed")
                return None
                
            if self.sensor.finger_search() != adafruit_fingerprint.OK:
                print("❌ No match found")
                return None
                
            finger_id = self.sensor.finger_id
            confidence = self.sensor.confidence
            
            if finger_id in self.stored_ids:
                print(f"✅ Authenticated! ID: {finger_id}, Confidence: {confidence}")
                time.sleep(0.5)  # Sensor cooldown
                return finger_id
                
            print("❌ ID not recognized")
            return None
            
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None
    
    def _derive_key(self, finger_id):
        """Derive encryption key from stored fingerprint template."""
        try:
            # Get stored template (always consistent)
            template = self._get_template(finger_id)
            if not template:
                return None
            
            # Create salt from template hash
            salt = hashlib.sha256(template).digest()[:16]
            
            # Derive 256-bit key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            
            return kdf.derive(template)
            
        except Exception as e:
            print(f"Key derivation error: {e}")
            return None
    
    def encrypt(self, message, finger_id=None):
        """
        Encrypt message using fingerprint authentication.
        
        Args:
            message (str): Message to encrypt
            finger_id (int, optional): Use specific finger ID, or authenticate if None
            
        Returns:
            bytes: Encrypted data or None if failed
        """
        try:
            # Authenticate if no finger_id provided
            if finger_id is None:
                finger_id = self.authenticate()
                if not finger_id:
                    return None
            
            # Get encryption key
            key = self._derive_key(finger_id)
            if not key:
                print("❌ Key derivation failed")
                return None
            
            # Generate random nonce
            nonce = os.urandom(16)
            
            # Encrypt using AES-CTR
            cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(message.encode('utf-8')) + encryptor.finalize()
            
            print(f"✅ Encrypted with fingerprint ID {finger_id}")
            return nonce + ciphertext
            
        except Exception as e:
            print(f"❌ Encryption error: {e}")
            return None
    
    def decrypt(self, encrypted_data):
        """
        Decrypt message using fingerprint authentication.
        
        Args:
            encrypted_data (bytes): Data to decrypt
            
        Returns:
            str: Decrypted message or None if failed
        """
        try:
            # Authenticate user
            finger_id = self.authenticate()
            if not finger_id:
                return None
            
            # Get decryption key
            key = self._derive_key(finger_id)
            if not key:
                print("❌ Key derivation failed")
                return None
            
            # Extract nonce and ciphertext
            nonce = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            # Decrypt using AES-CTR
            cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            message = plaintext.decode('utf-8')
            print("✅ Decrypted successfully")
            return message
            
        except Exception as e:
            print(f"❌ Decryption error: {e}")
            return None
    
    def get_info(self):
        """Get sensor and enrollment information."""
        return {
            'connected': self.sensor is not None,
            'stored_fingerprints': self.stored_ids,
            'total_enrolled': len(self.stored_ids)
        }