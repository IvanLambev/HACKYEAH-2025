# RFID Manager - Complete User Manual

> **⚠️ DEPRECATED**: This guide has been moved to [`../../docs/RFID_Technical_Guide.md`](../../docs/RFID_Technical_Guide.md)  
> Please use the new location for the most up-to-date documentation.

## Overview

This RFID Manager library provides a complete Python interface for reading and writing MIFARE Classic cards using a PN532 module on Raspberry Pi with libnfc.

## Features

- ✅ **Card Detection**: Automatic detection and identification of MIFARE Classic cards
- ✅ **Block Operations**: Read/write individual 16-byte blocks
- ✅ **String Operations**: Write/read text strings across multiple blocks
- ✅ **Error Handling**: Robust error recovery and user-friendly messages
- ✅ **Card Display**: Formatted display of card contents
- ✅ **Safety Features**: Protection against accidental overwrites of critical blocks

## Hardware Requirements

- Raspberry Pi (any model with GPIO)
- PN532 RFID/NFC module
- MIFARE Classic 1K or 4K cards

## Wiring (PN532 to Raspberry Pi)

```
PN532    Raspberry Pi
VCC   -> 3.3V (Pin 1)
GND   -> GND (Pin 6)
SDA   -> CE0/GPIO8 (Pin 24)
SCK   -> SCLK/GPIO11 (Pin 23)
MOSI  -> MOSI/GPIO10 (Pin 19)
MISO  -> MISO/GPIO9 (Pin 21)
```

## Software Requirements

### Install libnfc:
```bash
sudo apt-get update
sudo apt-get install libnfc-bin libnfc-dev
```

### Configure libnfc:
```bash
sudo mkdir -p /etc/nfc
sudo tee /etc/nfc/libnfc.conf << EOF
allow_autoscan = true
allow_intrusive_scan = false
log_level = 1
device.name = "pn532_spi"
device.connstring = "pn532_spi:/dev/spidev0.0:500000"
EOF
```

### Test installation:
```bash
nfc-list
# Should show: "NFC device: pn532_spi opened"
```

## Quick Start

### 1. Basic Usage

```python
from rfid_manager import RFID_Manager

# Create RFID manager instance
rfid = RFID_Manager()

# Wait for a card
if rfid.wait_for_card():
    # Get card information
    info = rfid.get_card_info()
    print(f"Card UID: {info['uid']}")
    print(f"Card Type: {info['type']}")
    
    # Read a block
    block_data = rfid.read_block(1)
    if block_data:
        print(f"Block 1 data: {block_data.hex()}")
```

### 2. Running Tests

```bash
cd /home/ivan/Documents/rfid/final_rfid_solution
python test_rfid.py
```

## API Reference

### Class: RFID_Manager

#### Card Detection Methods

##### `is_card_present() -> bool`
Check if a card is currently on the reader.

```python
if rfid.is_card_present():
    print("Card detected!")
```

##### `wait_for_card(timeout=30) -> bool`
Wait for a card to be placed on the reader.

```python
if rfid.wait_for_card(timeout=10):
    print("Card placed within 10 seconds")
```

##### `wait_for_card_removal(timeout=30) -> bool`
Wait for the current card to be removed.

```python
rfid.wait_for_card_removal()
print("Card removed")
```

##### `get_card_info() -> dict`
Get detailed card information.

```python
info = rfid.get_card_info()
print(f"UID: {info['uid']}")
print(f"Type: {info['type']}")
print(f"Size: {info['size']} bytes")
```

#### Block Operations

##### `read_block(block_num: int) -> Optional[bytes]`
Read a single 16-byte block.

```python
# Read block 4
data = rfid.read_block(4)
if data:
    print(f"Block 4: {data.hex()}")
```

##### `read_multiple_blocks(start_block: int, num_blocks: int) -> Optional[bytes]`
Read multiple consecutive blocks.

```python
# Read blocks 4-7
data = rfid.read_multiple_blocks(4, 4)  # 4 blocks starting from block 4
```

##### `write_block(block_num: int, data: bytes) -> bool`
Write 16 bytes to a specific block.

```python
# Write data to block 4
data = b"Hello RFID World"  # Must be exactly 16 bytes
success = rfid.write_block(4, data)
```

#### String Operations

##### `write_string(start_block: int, text: str, max_length=3000) -> bool`
Write a text string across multiple blocks with 4-byte header format. Automatically skips trailer blocks and provides detailed progress information.

```python
# Write a string starting at block 4
text = "This is a test string that can span multiple blocks!"
success = rfid.write_string(4, text)

# Write a longer string (up to 3000 characters)
long_text = "A" * 1000  # 1000 character string
success = rfid.write_string(4, long_text)
```

##### `read_string(start_block: int, max_length=3000) -> Optional[str]`
Read a string written with `write_string()`. Automatically detects old (2-byte) and new (4-byte) header formats.

```python
# Read string starting from block 4
text = rfid.read_string(4)
if text:
    print(f"Read: {text}")
```

##### `write_long_string(text: str, start_sector=1) -> bool`
Write very long strings efficiently by using entire sectors. Optimized for large amounts of data.

```python
# Write a very long string starting from sector 1
long_text = "This is a very long string that could be several thousand characters..."
success = rfid.write_long_string(long_text, start_sector=1)
```

##### `get_string_info(start_block: int) -> dict`
Get information about a stored string without reading the full content.

```python
# Get string metadata
info = rfid.get_string_info(4)
print(f"String length: {info['length']} characters")
print(f"Format: {info['format']}")
print(f"Preview: {info['preview']}")
```

#### Card Analysis Methods

##### `check_card_writeability() -> dict`
Analyze if the current card is writable or read-only (detects demo cards).

```python
analysis = rfid.check_card_writeability()
print(f"Writable: {analysis['writable']}")
print(f"Confidence: {analysis['confidence']}")
print(f"Reason: {analysis['reason']}")
```

##### `get_available_space(start_block=1) -> dict`
Calculate available storage space for strings on the card.

```python
space = rfid.get_available_space(start_block=4)
print(f"Card type: {space['card_type']}")
print(f"Available blocks: {space['available_blocks']}")
print(f"Estimated max characters: {space['estimated_max_chars']}")
```

#### Maintenance Methods

##### `refresh_cache()`
Force refresh of cached card data. Useful after writing multiple blocks.

```python
# After writing several blocks
rfid.refresh_cache()  # Force fresh read on next operation
```

##### `check_and_recover_connection() -> bool`
Check card connection and attempt recovery if needed.

```python
if not rfid.check_and_recover_connection():
    print("Card connection failed - check card placement")
```

#### Utility Methods

##### `format_card_display(num_blocks=16) -> str`
Get a formatted display of card contents.

```python
print(rfid.format_card_display(16))
```

##### `quick_read_card() -> dict`
Quick read of card info and sample blocks.

```python
result = rfid.quick_read_card()
print(f"UID: {result['info']['uid']}")
print(f"Blocks read: {len(result['blocks'])}")
```

## Block Layout (MIFARE Classic 1K)

MIFARE Classic 1K cards have 64 blocks (0-63), organized in 16 sectors:

```
Sector 0:  Blocks 0-3   (Block 0 = UID, Block 3 = Keys)
Sector 1:  Blocks 4-7   (Block 7 = Keys)
Sector 2:  Blocks 8-11  (Block 11 = Keys)
...
Sector 15: Blocks 60-63 (Block 63 = Keys)
```

### Special Blocks:
- **Block 0**: Manufacturer data (UID) - **READ ONLY**
- **Trailer blocks** (3, 7, 11, 15, etc.): Access keys and control bits
- **Data blocks**: All others can store user data

### Safe Blocks for Data:
Blocks 1, 2, 4, 5, 6, 8, 9, 10, 12, 13, 14, etc. (avoid 0 and trailer blocks)

## Example Programs

### Example 1: Card Reader
```python
from rfid_manager import RFID_Manager
import time

rfid = RFID_Manager()

print("Card Reader - Place cards on the reader")
while True:
    if rfid.wait_for_card(timeout=5):
        info = rfid.get_card_info()
        print(f"Card detected: {info['uid']} ({info['type']})")
        
        rfid.wait_for_card_removal()
        print("Card removed")
    else:
        print("Waiting for card...")
```

### Example 2: Data Logger
```python
from rfid_manager import RFID_Manager
import datetime

rfid = RFID_Manager()

def log_card_access():
    if rfid.wait_for_card():
        info = rfid.get_card_info()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Write access log to card
        log_entry = f"Access: {timestamp}"
        rfid.write_string(4, log_entry)
        
        print(f"Logged access for card {info['uid']} at {timestamp}")
        
        # Read back to verify
        stored_log = rfid.read_string(4)
        print(f"Verification: {stored_log}")

log_card_access()
```

### Example 3: Data Storage
```python
from rfid_manager import RFID_Manager

rfid = RFID_Manager()

def store_user_data():
    if not rfid.wait_for_card():
        return
    
    # Check if card is writable first
    writeability = rfid.check_card_writeability()
    if writeability['writable'] == False:
        print(f"Card is not writable: {writeability['reason']}")
        return
    
    # Get user input
    name = input("Enter name: ")
    email = input("Enter email: ")
    
    # Store data in different blocks
    rfid.write_string(4, f"Name: {name}")
    rfid.write_string(8, f"Email: {email}")
    
    print("Data stored successfully!")
    
    # Verify by reading back
    stored_name = rfid.read_string(4)
    stored_email = rfid.read_string(8)
    
    print(f"Stored: {stored_name}")
    print(f"Stored: {stored_email}")

store_user_data()
```

### Example 4: Large Data Storage
```python
from rfid_manager import RFID_Manager

rfid = RFID_Manager()

def store_large_document():
    if not rfid.wait_for_card():
        return
    
    # Check available space
    space = rfid.get_available_space()
    print(f"Available space: {space['estimated_max_chars']} characters")
    
    # Read a large text file
    try:
        with open("document.txt", "r") as f:
            document = f.read()
        
        if len(document) > space['estimated_max_chars']:
            print(f"Document too large! {len(document)} > {space['estimated_max_chars']}")
            return
        
        # Use write_long_string for optimal storage
        success = rfid.write_long_string(document, start_sector=1)
        
        if success:
            print(f"Document stored successfully! ({len(document)} characters)")
            
            # Get info about stored string
            info = rfid.get_string_info(4)  # Sector 1 starts at block 4
            print(f"Storage info: {info}")
        else:
            print("Failed to store document")
            
    except FileNotFoundError:
        print("Document file not found")

store_large_document()
```

## Troubleshooting

### Common Issues

#### "nfc-list: ERROR: Unable to open NFC device"
- Check wiring connections
- Verify PN532 is in SPI mode (check jumpers)
- Ensure libnfc configuration is correct
- Try restarting the Raspberry Pi

#### "No card detected"
- Ensure card is placed flat on the PN532 antenna
- Try different card positions
- Check if card is MIFARE Classic (not NTAG or other types)
- Verify PN532 power supply is stable

#### "Authentication failed for block"
- This is normal for some blocks on certain cards
- The library handles this gracefully
- Most data can still be read/written to available blocks

#### "Write failed"
- Check if trying to write to block 0 (read-only)
- Ensure card is not write-protected
- Verify the card hasn't been removed during operation

#### "Demo/Test Cards are Read-Only"
- Cards containing "TEST-4K" or similar patterns are often demo cards
- Demo cards are manufactured as read-only for testing purposes
- Use blank cards for write operations
- The library will detect and warn about demo cards automatically
- Use `check_card_writeability()` to verify if a card can be written to

#### "Connection Issues After Multiple Operations"
- Use `refresh_cache()` to clear stale cached data
- Call `check_and_recover_connection()` if operations start failing
- Remove and replace card if connection recovery fails

### Performance Tips

1. **Keep cards steady**: Don't move cards during read/write operations
2. **Use appropriate timeouts**: Adjust timeout values based on your needs
3. **Handle exceptions**: Always check return values and handle errors
4. **Avoid trailer blocks**: Don't write to blocks 3, 7, 11, 15, etc. unless necessary
5. **Check writeability first**: Use `check_card_writeability()` before writing to avoid demo cards
6. **Monitor available space**: Use `get_available_space()` to plan your data storage
7. **Use long string methods**: For large data, prefer `write_long_string()` over multiple `write_string()` calls

## Safety Notes

⚠️ **Important Safety Information:**

1. **Block 0 is READ-ONLY**: Never attempt to write to block 0 (contains UID)
2. **Trailer blocks contain keys**: Writing to blocks 3, 7, 11, 15, etc. can lock the card
3. **Always verify writes**: Read back important data to ensure it was written correctly
4. **Use safe blocks**: Blocks 1, 2, 4, 5, 6, 8, 9, 10, etc. are safe for user data
5. **Test with sacrificial cards**: Test your code with cards you don't mind corrupting

## Technical Details

### String Storage Format
When using `write_string()`, data is stored as:
- **New Format (4-byte header)**: Bytes 0-3: Character count (big-endian 32-bit integer)
- **Old Format (2-byte header)**: Bytes 0-1: Character count (big-endian 16-bit integer) 
- Remaining bytes: UTF-8 encoded string data
- Padding: Zeros to fill complete 16-byte blocks

The library automatically detects which format when reading and uses the new 4-byte format for writing (supports up to 3000+ characters vs 900 in old format).

### Block Structure
Each block is exactly 16 bytes:
- Data blocks: 16 bytes of user data
- Trailer blocks: 6 bytes Key A + 4 bytes access bits + 6 bytes Key B

### Error Recovery
The library includes automatic error recovery:
- Timeout handling for hanging operations
- Process cleanup for stuck NFC operations
- Graceful handling of partial read failures

## Version Information

- **Version**: 2.0
- **Date**: October 2025
- **Compatible with**: Raspberry Pi OS, libnfc 1.8.0+
- **Hardware**: PN532 module via SPI
- **Cards**: MIFARE Classic 1K/4K

### Version 2.0 New Features:
- Enhanced string storage (4-byte headers, up to 3000+ characters)
- Automatic demo card detection with `check_card_writeability()`
- Available space calculation with `get_available_space()`
- Connection recovery and maintenance tools
- Improved error handling and timeout management
- Better 4K card support with specialized write methods
- Long string optimization with `write_long_string()`

## Support

For issues or questions:
1. Check this manual first
2. Run the test suite: `python test_rfid.py`
3. Verify hardware connections
4. Check libnfc installation: `nfc-list`

---

**Happy RFID coding! 🎉**