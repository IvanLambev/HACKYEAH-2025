#!/usr/bin/env python3
import board
import busio
import digitalio
from adafruit_pn532.spi import PN532_SPI
import time
import binascii

# ---- CONFIG ----
USE_CE1 = False   # set True if your PN532 CS is wired to CE1 (GPIO7 / board.D7)
DEBUG_PN532 = True  # set True to enable lower-level PN532 debug from driver
# ----------------

# choose CS pin based on config
cs_pin = digitalio.DigitalInOut(board.D7 if USE_CE1 else board.D8)

# SPI setup
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

# Create PN532 object. debug=True will print low-level traces (helpful if detection issues).
pn532 = PN532_SPI(spi, cs_pin, debug=DEBUG_PN532)
while not spi.try_lock():
    pass
# Try slower SPI speed for better reliability
spi.configure(baudrate=50000)  # Even slower - 50kHz for maximum stability
spi.unlock()
print(f"Using CS pin: {'D7 (CE1)' if USE_CE1 else 'D8 (CE0)'}")
print("SPI configured at 50kHz for maximum stability")

# check firmware
try:
    ic, ver, rev, support = pn532.firmware_version
    print(f"Found PN532 with firmware version: {ver}.{rev}")
except Exception as e:
    print("ERROR: Failed to detect PN532. Check wiring, SPI mode jumpers, and CS pin.")
    print("Driver exception:", e)
    raise

pn532.SAM_configuration()
print("Waiting for a card...\n")

COMMON_KEYS = [
    bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF'),
    bytearray(b'\xA0\xA1\xA2\xA3\xA4\xA5'),
    bytearray(b'\xD3\xF7\xD3\xF7\xD3\xF7'),
    bytearray(b'\x00\x00\x00\x00\x00\x00'),
    bytearray(b'\x01\x02\x03\x04\x05\x06'),
    bytearray(b'\x4D\x3A\x99\xC3\x51\xDD'),
]

def try_auth_all_keys(uid_bytes, block):
    for key in COMMON_KEYS:
        for key_type in (0, 1):  # 0 = KEY A, 1 = KEY B
            try:
                print(f"  Trying key {binascii.hexlify(key).decode().upper()} (key_type={'A' if key_type==0 else 'B'})...")
                # Add a small delay before authentication
                time.sleep(0.1)
                ok = pn532.mifare_classic_authenticate_block(uid_bytes, block, key_type, key)
                if ok:
                    print(f"  ✅ SUCCESS with key {binascii.hexlify(key).decode().upper()}")
                    return key, key_type
                else:
                    print(f"  ❌ Authentication failed (returned False)")
            except Exception as e:
                # print precise exception to help diagnose
                print(f"  ❌ Exception for key {binascii.hexlify(key).decode().upper()} key_type {'A' if key_type==0 else 'B'}: {e}")
                # Add delay after exception
                time.sleep(0.2)
    return None, None

def is_trailer_block(block_num):
    return (block_num % 4) == 3

def next_data_block(block_num):
    block_num += 1
    if is_trailer_block(block_num):
        block_num += 1
    return block_num

def read_long_string(uid_bytes, start_block, max_len=900):
    # Attempt to use default key for reading long string (fallback behavior)
    key_default = bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF')
    # Try to auth (Key A then Key B) for the starting block
    if not pn532.mifare_classic_authenticate_block(uid_bytes, start_block, 0, key_default):
        pn532.mifare_classic_authenticate_block(uid_bytes, start_block, 1, key_default)
    block = pn532.mifare_classic_read_block(start_block)
    if block is None:
        return None
    length = (block[0] << 8) | block[1]
    if length == 0:
        return ""
    if length > max_len:
        return None
    data = bytearray()
    data.extend(block[2:2 + min(14, length)])
    copied = len(data)
    block_num = next_data_block(start_block)
    while copied < length:
        if not pn532.mifare_classic_authenticate_block(uid_bytes, block_num, 0, key_default):
            if not pn532.mifare_classic_authenticate_block(uid_bytes, block_num, 1, key_default):
                return None
        blk = pn532.mifare_classic_read_block(block_num)
        if blk is None:
            return None
        need = length - copied
        copy_now = min(16, need)
        data.extend(blk[:copy_now])
        copied += copy_now
        block_num = next_data_block(block_num)
        if block_num > 63:
            return None
    return data.decode("utf-8", errors="ignore")

try:
    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        if uid is None:
            continue
        uid_bytes = bytes(uid)
        print("Found card UID:", [hex(x) for x in uid_bytes], " (", binascii.hexlify(uid_bytes).decode(), ")")

        if len(uid_bytes) not in (4, 7, 10):
            print("  WARNING: This doesn't look like a MIFARE Classic card (4,7,10 byte UID expected).")
            print("  This script only works with MIFARE Classic cards.")
            print("  Remove card and try another.\n")
            time.sleep(0.6)
            continue
        if len(uid_bytes) == 4:
            print("  (4-byte UID is MIFARE Classic 1K or Mini; 7-byte is 4K; 10-byte is MIFARE Plus)")

        

        # First try block 1 (easier to access than block 4)
        print("Trying to authenticate block 1 with common keys...")
        key, key_type = try_auth_all_keys(uid_bytes, 1)
        if key:
            print(f"✅ Authenticated block 1 with key {binascii.hexlify(key).decode().upper()} (key_type={'A' if key_type==0 else 'B'})")
            block1 = pn532.mifare_classic_read_block(1)
            print("Block 1 raw data:", block1)
        else:
            print("❌ Could not authenticate block 1. Trying block 4...")
            
        # Now try block 4 
        print("Trying to authenticate block 4 with common keys...")
        key, key_type = try_auth_all_keys(uid_bytes, 4)
        if key:
            print(f"✅ Authenticated block 4 with key {binascii.hexlify(key).decode().upper()} (key_type={'A' if key_type==0 else 'B'})")
            block4 = pn532.mifare_classic_read_block(4)
            print("Block 4 raw data:", block4)
            s = read_long_string(uid_bytes, 4)
            if s is not None:
                print("Read long string:", s)
            else:
                print("Long string read returned None or failed.")
        else:
            print("❌ Could not authenticate block 4 using common keys (tried Key A and Key B).")
            print("If Arduino read this card with FF..FF, check:")
            print(" - Which pin did you wire the module SS to on the Arduino? (that maps to CE0/CE1 on Pi)")
            print(" - Confirm the PN532 module is set to SPI mode on its jumpers.")
            print(" - Try toggling USE_CE1 in this script and re-run (CE0 vs CE1).")
            print(" - If the Arduino succeeded, re-check that the Pi CS wire is exactly on that module SS pin.")
        print("\nRemove card to read again...\n")
        time.sleep(0.6)

except KeyboardInterrupt:
    print("\nExiting.")

