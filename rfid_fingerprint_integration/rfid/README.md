# 💳 RFID Card Management Module

## Overview
This module provides comprehensive RFID card management capabilities for MIFARE Classic cards using PN532 NFC modules. It supports reading, writing, authentication, and string operations across multiple card sectors with robust error handling and multi-format support.

## Directory Structure
```
rfid/
├── core/              # Core components
│   └── rfid_manager.py        # Main RFID manager class
├── tests/             # Test scripts and examples  
│   ├── test_rfid.py                  # Main RFID functionality tests
│   ├── examples.py                   # Usage examples
│   ├── final_test.py                 # Comprehensive test suite
│   ├── enhanced_test.py              # Advanced functionality tests
│   ├── hardware_test.py              # Hardware connection diagnostics
│   ├── debug.py                      # RFID debugging tools
│   ├── quick_test_read.py            # Quick card reading test
│   ├── simple_test.py                # Basic RFID tests
│   ├── simple_detection.py           # Card detection tests
│   ├── auth.py                       # Authentication tests
│   ├── main.py                       # Main test runner
│   ├── 2main.py                      # Alternative main runner
│   ├── arduino_style.py              # Arduino-style interface tests
│   ├── legacy_rfid_manager.py        # Legacy manager version
│   ├── libnfc_reader.py              # LibNFC reader tests
│   ├── mfrc522_test.py               # MFRC522 specific tests
│   ├── mfrc522_config_test.py        # MFRC522 configuration tests
│   └── final_rfid_solution_README.md # Detailed technical guide
└── README.md          # This file
```

## Installation

### Prerequisites
1. **Hardware Requirements:**
   - PN532 NFC module or compatible RFID reader
   - MIFARE Classic cards (1K or 4K)
   - Raspberry Pi or Linux system
   - USB connection or I2C/SPI interface

2. **Software Requirements:**
   - Python 3.7 or higher
   - libnfc library
   - nfc-tools package

### Install Dependencies

#### On Raspberry Pi/Debian/Ubuntu:
```bash
# Install system packages
sudo apt update
sudo apt install libnfc-bin libnfc-dev

# Install Python dependencies
pip install subprocess-run

# Test NFC reader
nfc-list
```

#### On other Linux systems:
```bash
# Install libnfc (method varies by distribution)
# For CentOS/RHEL: sudo yum install libnfc-devel
# For Arch: sudo pacman -S libnfc

# Verify installation
which nfc-list
nfc-list
```

### Hardware Connection

#### PN532 via USB:
- Simply connect PN532 module via USB cable
- No additional wiring required

#### PN532 via I2C (Raspberry Pi):
- VCC → 3.3V
- GND → Ground  
- SDA → GPIO 2 (SDA)
- SCL → GPIO 3 (SCL)

## Usage

### 1. Basic Card Detection
Test if your setup works:

```bash
cd rfid/tests/
python simple_detection.py
```

**Expected output:**
- "Card detected!" or "No card found"
- Card UID and type information
- Basic card specifications

### 2. Card Reading and Writing
Test read/write functionality:

```bash
cd rfid/tests/
python test_rfid.py
```

**What it does:**
- Detects card presence
- Reads card information
- Tests string writing capabilities
- Verifies written data
- **Expected:** Successful read/write operations

### 3. Programmatic Usage
```python
from rfid.core.rfid_manager import RFID_Manager

# Initialize RFID manager
rfid = RFID_Manager()

# Wait for card
if rfid.wait_for_card(timeout=10):
    # Get card information
    card_info = rfid.get_card_info()
    print(f"Card Type: {card_info['type']}")
    print(f"UID: {card_info['uid']}")
    
    # Write a string to the card
    message = "Hello, RFID World!"
    if rfid.write_string(start_block=4, text=message):
        print("Write successful!")
        
        # Read the string back
        read_message = rfid.read_string(start_block=4)
        print(f"Read back: {read_message}")
```

### 4. Advanced Operations
```python
# Read specific blocks
block_data = rfid.read_block(block_num=4)

# Write specific blocks  
data = b"1234567890123456"  # Exactly 16 bytes
rfid.write_block(block_num=5, data=data)

# Handle long strings automatically
long_text = "This is a very long message that will span multiple blocks..."
rfid.write_long_string(text=long_text, start_sector=2)
```

## Core Components

### RFID_Manager Class
The main class providing RFID card management:

**Card Operations:**
- `is_card_present()` - Check if card is on reader
- `wait_for_card(timeout)` - Wait for card placement
- `get_card_info()` - Get detailed card information
- `read_card_raw()` - Read entire card as raw bytes

**Block Operations:**
- `read_block(block_num)` - Read 16-byte block
- `write_block(block_num, data)` - Write 16-byte block
- `read_multiple_blocks(start, count)` - Read consecutive blocks

**String Operations:**
- `write_string(start_block, text)` - Write text across multiple blocks
- `read_string(start_block)` - Read text from multiple blocks
- `get_string_info(start_block)` - Get metadata about stored strings

**Utility Functions:**
- `format_card_display()` - Display card contents
- `refresh_cache()` - Clear cached data
- `check_and_recover_connection()` - Connection recovery

## Test Scripts

### test_rfid.py
**Purpose:** Comprehensive RFID functionality testing
**Usage:** `python test_rfid.py`
**What to expect:**
- Card detection and information display
- String write/read cycle testing
- Data verification
- Performance measurements

### examples.py  
**Purpose:** Usage examples and demonstrations
**Usage:** `python examples.py`
**What to expect:**
- Step-by-step examples
- Different use cases
- Best practices demonstration

### quick_test_read.py
**Purpose:** Quick card reading test
**Usage:** `python quick_test_read.py`
**What to expect:**
- Fast card detection
- Basic information display
- Minimal functionality test

### hardware_test.py
**Purpose:** Hardware connection diagnostics
**Usage:** `python hardware_test.py`
**What to expect:**
- NFC reader detection
- Connection status
- Hardware capability testing

## Supported Cards

### MIFARE Classic 1K
- **Capacity:** 1024 bytes (1KB)
- **Sectors:** 16 sectors, 4 blocks each
- **Usable blocks:** ~45 blocks (excluding system blocks)
- **String capacity:** ~700 characters

### MIFARE Classic 4K  
- **Capacity:** 4096 bytes (4KB)
- **Sectors:** 40 sectors (32×4 blocks + 8×16 blocks)
- **Usable blocks:** ~230 blocks
- **String capacity:** ~3600 characters

### Card Structure
```
Block 0:  Manufacturer data (read-only)
Block 1:  User data
Block 2:  User data  
Block 3:  Sector trailer (keys & access conditions)
Block 4:  User data (next sector)
...
```

## Troubleshooting

### Common Issues

1. **"No NFC reader found":**
   ```bash
   # Check if libnfc detects reader
   nfc-list
   
   # Check USB connections
   lsusb | grep -i nfc
   
   # Check permissions
   sudo usermod -a -G plugdev $USER
   ```

2. **"Card not detected":**
   - Ensure card is placed properly on reader
   - Try different card positions
   - Check for interference from other devices
   - Test with different cards

3. **"Authentication failed":**
   - Most cards use default keys (FFFFFFFFFFFF)
   - Some cards may be write-protected
   - Try different sectors/blocks
   - Check if card is demo/test card (read-only)

4. **"Write failed":**
   - Verify card is writable (not demo card)
   - Check block number (avoid block 0 and trailers)
   - Ensure proper card positioning
   - Try different access keys

### Debug Steps
1. Run `nfc-list` to verify hardware
2. Test with `simple_detection.py`
3. Use `debug.py` for detailed diagnostics
4. Check `hardware_test.py` results
5. Try `examples.py` for guided testing

## Configuration

### Reader Settings
```python
# Timeout settings
DEFAULT_TIMEOUT = 30  # seconds
READ_TIMEOUT = 20     # seconds
WRITE_TIMEOUT = 20    # seconds

# File paths
TEMP_DIR = "/tmp"
DUMP_FILE = "rfid_dump.mfd"
```

### Card Access Settings
```python
# Default MIFARE keys
DEFAULT_KEY_A = "FFFFFFFFFFFF"
DEFAULT_KEY_B = "FFFFFFFFFFFF" 

# Block ranges (1K card)
USABLE_BLOCKS = range(1, 64)  # Excluding block 0 and trailers
TRAILER_BLOCKS = [3, 7, 11, 15, ...]  # Sector trailers
```

## Performance

**Typical Performance (MIFARE Classic 1K):**
- Card detection: 0.5-2 seconds
- Single block read: 50-100ms
- Single block write: 100-200ms
- Full card read: 2-5 seconds
- String write (100 chars): 1-3 seconds

**Capacity Limits:**
- 1K card: ~700 character strings
- 4K card: ~3600 character strings
- Block size: 16 bytes fixed
- Practical block usage: ~75% (excluding system blocks)

## Security Notes

- Default MIFARE keys are widely known
- Consider changing access keys for sensitive applications
- Sector trailers contain authentication keys
- Block 0 contains immutable manufacturer data
- Write protection available via access conditions

## Error Handling

The system includes robust error handling:
- Automatic retry mechanisms
- Connection recovery
- Cache invalidation on failures
- Graceful degradation for partial failures

## Additional Documentation

### Detailed Technical Guide
For comprehensive technical documentation, API reference, and advanced usage examples, see:
- **[`../docs/RFID_Technical_Guide.md`](../docs/RFID_Technical_Guide.md)** - Complete technical manual with detailed API documentation, troubleshooting, and advanced examples
- **`tests/final_rfid_solution_README.md`** - Legacy detailed guide (deprecated, use docs/RFID_Technical_Guide.md instead)

### API Reference
See the docstrings in `rfid_manager.py` for detailed API documentation and method parameters.