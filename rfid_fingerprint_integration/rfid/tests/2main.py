import board
import busio
import digitalio
from adafruit_pn532.spi import PN532_SPI
import time

# SPI setup
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
cs_pin = digitalio.DigitalInOut(board.D8)  # CE0 = GPIO8

# Create PN532 object
pn532 = PN532_SPI(spi, cs_pin, debug=False)

# Configure PN532
ic, ver, rev, support = pn532.firmware_version
print("Found PN532 with firmware version: {0}.{1}".format(ver, rev))

pn532.SAM_configuration()

print("Waiting for a card...")

# Default Mifare Classic key
key_default = b'\xFF\xFF\xFF\xFF\xFF\xFF'


def is_trailer_block(block_num):
    return (block_num % 4) == 3


def next_data_block(block_num):
    block_num += 1
    if is_trailer_block(block_num):
        block_num += 1
    return block_num


def read_long_string(uid, start_block, max_len=900):
    uid = bytes(uid)  # ensure UID is in bytes form

    # Authenticate first block
    if not pn532.mifare_classic_authenticate_block(uid, start_block, 0, key_default):
        print(f"Auth failed at block {start_block}")
        return None

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
        if not pn532.mifare_classic_authenticate_block(uid, block_num, 0, key_default):
            print(f"Auth failed at block {block_num}")
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


while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid is None:
        continue

    print("Found card with UID:", [hex(i) for i in uid])
    uid = bytes(uid)  # ✅ Fix: convert UID to bytes before using
    print("Card detected UID:", [hex(x) for x in uid])

    if pn532.mifare_classic_authenticate_block(uid, 4, 0, key_default):
        data = pn532.mifare_classic_read_block(4)
        print("Block 4:", data)
    else:
        print("Auth failed for block 4")

    result = read_long_string(uid, 4)
    if result:
        print("Read string:", result)
    else:
        print("Read failed!")

    print("Remove card to read again...\n")
    time.sleep(1)
