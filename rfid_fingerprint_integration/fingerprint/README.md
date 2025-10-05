# 👆 Fingerprint Authentication Module

## Overview
This module provides fingerprint-based authentication and encryption capabilities using AS608 biometric sensors. It includes secure AES-256 encryption/decryption of messages and data using fingerprint-derived keys for maximum security.

## Directory Structure
```
fingerprint/
├── core/              # Core components
│   ├── final_fingerprint_crypto.py   # Main fingerprint crypto class
│   └── biometric_crypto.py          # Biometric encryption utilities
├── tests/             # Test scripts and examples
│   ├── enroll.py                     # Fingerprint enrollment
│   ├── demo_encryption.py           # Encryption demonstrations
│   ├── debug_detailed.py            # Detailed debugging tools
│   ├── debug_read.py                 # Debug read functionality
│   ├── as608_menu.py                 # AS608 sensor menu system
│   ├── legacy_fingerprint_menu.py    # Legacy menu interface
│   ├── run_system.py                 # System runner utility
│   └── test_rfid_storage.py          # RFID integration tests
└── README.md          # This file
```

## Installation

### Prerequisites
1. **Hardware Requirements:**
   - AS608 or compatible fingerprint sensor
   - Raspberry Pi or compatible Linux system
   - USB-to-TTL converter or direct GPIO connection

2. **Software Requirements:**
   - Python 3.7 or higher
   - pyserial library
   - RPi.GPIO (for Raspberry Pi)

### Install Dependencies
```bash
# Install Python dependencies
pip install pyserial RPi.GPIO

# For non-Raspberry Pi systems, you may need different GPIO libraries
# pip install gpiozero  # Alternative GPIO library
```

### Hardware Connection
Connect your AS608 fingerprint sensor:
- VCC → 3.3V or 5V (check sensor specifications)
- GND → Ground
- TX → GPIO Pin (default: GPIO 14)
- RX → GPIO Pin (default: GPIO 15)

## Usage

### 1. Enrollment (First Time Setup)
Before using the system, you need to enroll fingerprints:

```bash
cd fingerprint/tests/
python enroll.py
```

**What it does:**
- Guides you through fingerprint enrollment process
- Stores fingerprint templates in sensor memory
- Assigns unique IDs to each fingerprint
- **Expected output:** "Fingerprint enrolled successfully with ID: X"

### 2. Basic Encryption/Decryption
```python
from fingerprint.core.final_fingerprint_crypto import FinalFingerprintCrypto

# Initialize the system
crypto = FinalFingerprintCrypto()

# Connect to sensor
if crypto.connect_sensor():
    # Encrypt a message (requires fingerprint authentication)
    message = "Secret message"
    encrypted_data = crypto.encrypt_message(message)
    
    # Decrypt the message (requires fingerprint authentication)
    decrypted = crypto.decrypt_message(encrypted_data)
    print(f"Decrypted: {decrypted}")
```

### 3. Testing the System
Run system tests to verify everything works:

```bash
cd fingerprint/tests/
python demo_encryption.py
```

**Expected behavior:**
- Prompts for fingerprint authentication
- Encrypts test data
- Decrypts and verifies the data
- Shows success/failure status

## Core Components

### FinalFingerprintCrypto
The main class providing fingerprint-based encryption:

**Key Methods:**
- `connect_sensor()` - Establish connection with fingerprint sensor
- `encrypt_message(text)` - Encrypt text using fingerprint authentication
- `decrypt_message(encrypted_data)` - Decrypt data using fingerprint authentication
- `get_stored_fingerprints()` - List enrolled fingerprints

**Security Features:**
- Uses fingerprint biometrics as encryption key source
- AES-256 encryption with biometric-derived keys
- Secure key derivation from fingerprint templates
- Protection against replay attacks

## Test Scripts

### enroll.py
**Purpose:** Enroll new fingerprints into the system
**Usage:** `python enroll.py`
**What to expect:**
- Interactive enrollment process
- Place finger on sensor when prompted
- System will ask for multiple scans for accuracy
- Success message with assigned fingerprint ID

### debug_detailed.py
**Purpose:** Detailed debugging and sensor diagnostics
**Usage:** `python debug_detailed.py`
**What to expect:**
- Sensor connection status
- Detailed sensor information
- Communication diagnostics
- Error analysis tools

### demo_encryption.py
**Purpose:** Demonstrate encryption/decryption functionality
**Usage:** `python demo_encryption.py`
**What to expect:**
- Interactive demo of encryption process
- Test message encryption and decryption
- Performance measurements
- Success/failure verification

## Troubleshooting

### Common Issues

1. **"Sensor not found" or connection errors:**
   - Check hardware connections
   - Verify GPIO pin assignments
   - Ensure sensor has power
   - Try different baud rates (9600, 57600, 115200)

2. **"No fingerprints enrolled":**
   - Run `enroll.py` first to register fingerprints
   - Ensure enrollment completed successfully
   - Check sensor memory status

3. **Authentication failures:**
   - Clean the fingerprint sensor surface
   - Try different finger positions
   - Re-enroll problematic fingerprints
   - Check for sensor calibration issues

4. **Permission errors (Linux):**
   ```bash
   sudo usermod -a -G dialout $USER
   # Logout and login again
   ```

### Debug Steps
1. Run `debug_detailed.py` to check sensor status
2. Verify hardware connections
3. Test with `demo_encryption.py`
4. Check system logs for errors

## Configuration

### Sensor Settings
Edit the configuration in `final_fingerprint_crypto.py`:
```python
# Default settings
SENSOR_PORT = '/dev/serial0'  # or '/dev/ttyUSB0'
BAUD_RATE = 57600
TIMEOUT = 2.0
```

### Security Settings
```python
# Encryption parameters
AES_KEY_SIZE = 32  # 256-bit keys
SALT_SIZE = 16     # Salt for key derivation
```

## Performance

**Typical Performance:**
- Fingerprint authentication: 1-3 seconds
- Encryption (1KB data): <100ms
- Decryption (1KB data): <100ms
- Enrollment: 10-15 seconds per finger

**Capacity:**
- Up to 200 fingerprint templates (sensor dependent)
- Message size limited by available memory
- No limit on number of encrypted files

## Security Notes

- Fingerprint templates are stored securely in sensor memory
- Encryption keys are derived from biometric data, not stored
- Each encryption uses unique salt for security
- System designed to prevent unauthorized access even if encrypted data is compromised

## API Reference

See the docstrings in `final_fingerprint_crypto.py` for detailed API documentation.