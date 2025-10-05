#!/usr/bin/env python3
import board
import busio
import digitalio
from adafruit_pn532.spi import PN532_SPI
import time
import binascii

# SPI setup (CE0)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs_pin = digitalio.DigitalInOut(board.D8)  # CE0 = GPIO8 ; change to board.D7 if your module uses CE1

pn532 = PN532_SPI(spi, cs_pin, debug=False)

# Check firmware
ic, ver, rev, support = pn532.firmware_version
print(f"Found PN532 with firmware version: {ver}.{rev}")
pn532.SAM_configuration()
print("Waiting for a card...\n")

# Common MIFARE keys (as bytearray)
COMMON_KEYS = [
    bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF'),  # factory default
    bytearray(b'\xA0\xA1\xA2\xA3\xA4\xA5'),
    bytearray(b'\xD3\xF7\xD3\xF7\xD3\xF7'),
    bytearray(b'\x00\x00\x00\x00\x00\x00'),
    bytearray(b'\x01\x02\x03\x04\x05\x06'),
    bytearray(b'\x4D\x3A\x99\xC3\x51\xDD'),
]

def try_auth_all_keys(uid_bytes, block):
    """
    Try all keys and both key types (0 = KEY_A, 1 = KEY_B).
    Return tuple (key, key_type) on success, else (None, None).
    """
    for key in COMMON_KEYS:
        for key_type in (0, 1):
            try:
                ok = pn532.mifare_classic_authenticate_block(uid_bytes, block, key_type, key)
                if ok:
                    return key, key_type
            except Exception as e:
                # Print driver error but continue trying others
                print(f"  auth exception for key {binascii.hexlify(key).decode()} key_type {key_type}: {e}")
    return None, None

def is_trailer_block(block_num):
    return (block_num % 4) == 3

def next_data_block(block_num):
    block_num += 1
    if is_trailer_block(block_num):
        block_num += 1
    return block_num

def read_long_string(uid_bytes, start_block, max_len=900):
    # Authenticate first block with default key assumption already handled outside,
    # but we'll attempt to auth with default key here as a fallback.
    # Caller may want to pass the correct key if found earlier; for simplicity we try default.
    key_default = bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF')

    if not pn532.mifare_classic_authenticate_block(uid_bytes, start_block, 0, key_default):
        # Attempt with Key B too
        pn532.mifare_classic_authenticate_block(uid_bytes, start_block, 1, key_default)

    # Now attempt to read start block
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
        # try default key for each block — this could be adjusted to use found keys
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

        # Try common keys for block 4
        print("Trying to authenticate block 4 with common keys...")
        key, key_type = try_auth_all_keys(uid_bytes, 4)
        if key:
            print(f"✅ Authenticated block 4 with key {binascii.hexlify(key).decode().upper()} (key_type={'A' if key_type==0 else 'B'})")
            # read block 4
            block4 = pn532.mifare_classic_read_block(4)
            print("Block 4 raw data:", block4)
            # If desired, attempt to read the long string starting at block 4:
            s = read_long_string(uid_bytes, 4)
            if s is not None:
                print("Read long string:", s)
            else:
                print("Long string read returned None or failed.")
        else:
            print("❌ Could not authenticate block 4 using common keys (tried Key A and Key B).")
            print("If Arduino read this same card successfully with FF..FF, check:")
            print("  - Did Arduino use CE0 or CE1? (CS pin)")
            print("  - Is the PN532 set to SPI mode on the module jumpers?")
            print("  - Try changing cs_pin to board.D7 (CE1) if your module uses CE1)\n")

        print("Remove card to read again...\n")
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nExiting.")
