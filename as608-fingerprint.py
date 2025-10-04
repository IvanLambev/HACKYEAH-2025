import time
import serial
import adafruit_fingerprint

# Open UART once and create the finger object
# Adjust port if needed (e.g. "/dev/ttyS0", "/dev/ttyAMA0")
UART_PORT = "/dev/serial0"
BAUDRATE = 57600

def open_sensor(port=UART_PORT, baudrate=BAUDRATE, timeout=1):
    uart = serial.Serial(port, baudrate=baudrate, timeout=timeout)
    finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)
    return finger

# ---------- Helpers ----------
def _ok_or_raise(code, msg="Command failed"):
    if code != adafruit_fingerprint.OK:
        raise RuntimeError(f"{msg} (code={hex(code)})")

# ---------- List stored template IDs ----------
def list_ids(finger):
    """
    Returns a sorted list of stored template IDs on the sensor.
    """
    rc = finger.read_templates()   # populates finger.templates
    _ok_or_raise(rc, "Failed to read templates")
    # finger.templates is a list of ints (IDs)
    return sorted(finger.templates)

# ---------- Enroll a fingerprint to a specific ID ----------
def enroll_id(finger, location_id, slot=1, timeout=30):
    """
    Enroll a finger into `location_id` on the sensor.
    Returns True on success. Raises RuntimeError on failure.
    """
    start = time.time()
    print(f"Enrolling into ID {location_id}. Place finger...")

    # 1) capture first image
    while True:
        if time.time() - start > timeout:
            raise RuntimeError("Timeout waiting for first finger image")
        r = finger.get_image()
        if r == adafruit_fingerprint.OK:
            print("Image 1 captured")
            break
        elif r == adafruit_fingerprint.NOFINGER:
            time.sleep(0.2)
            continue
        else:
            raise RuntimeError(f"get_image() failed: {hex(r)}")

    # convert to char file 1
    r = finger.image_2_tz(slot)
    _ok_or_raise(r, "image_2_tz (first) failed")

    print("Remove finger...")
    # wait for finger removal
    while True:
        r = finger.get_image()
        if r == adafruit_fingerprint.NOFINGER:
            break
        time.sleep(0.2)

    print("Place same finger again...")
    start2 = time.time()
    # capture second image
    while True:
        if time.time() - start2 > timeout:
            raise RuntimeError("Timeout waiting for second finger image")
        r = finger.get_image()
        if r == adafruit_fingerprint.OK:
            print("Image 2 captured")
            break
        elif r == adafruit_fingerprint.NOFINGER:
            time.sleep(0.2)
            continue
        else:
            raise RuntimeError(f"get_image() (2) failed: {hex(r)}")

    # convert to char file 2 (use the other slot: if slot=1 use 2 for second; but lib uses slot argument)
    second_slot = 2 if slot == 1 else 1
    r = finger.image_2_tz(second_slot)
    _ok_or_raise(r, "image_2_tz (second) failed")

    # create model from char buffers
    r = finger.create_model()
    _ok_or_raise(r, "create_model (combine) failed")
    print("Model created (prints matched)")

    # store model at location_id
    r = finger.store_model(location_id, slot=1)
    _ok_or_raise(r, f"store_model failed for ID {location_id}")
    print(f"Stored model at ID {location_id}")
    return True

# ---------- Delete a stored template ----------
def delete_id(finger, location_id):
    """
    Delete template at location_id. Returns True on success.
    """
    r = finger.delete_model(location_id)
    _ok_or_raise(r, f"delete_model failed for ID {location_id}")
    print(f"Deleted template ID {location_id}")
    return True

# ---------- Get template by ID ----------
def get_template(finger, location_id):
    """
    Get template data by ID from the sensor.
    Returns bytes of the template.
    """
    # load to slot 1
    r = finger.load_model(location_id, slot=1)
    _ok_or_raise(r, f"load_model failed for ID {location_id}")

    # get fingerprint data from char buffer (slot 1)
    data_list = finger.get_fpdata(sensorbuffer="char", slot=1)
    # get_fpdata returns list[int], convert to bytes
    b = bytes(data_list)
    
    return b

# ---------- Display template bytes ----------
def display_template_bytes(template_bytes, bytes_per_line=16):
    """
    Display template bytes in a formatted hex dump style.
    """
    print(f"Template size: {len(template_bytes)} bytes")
    print("-" * 60)
    
    for i in range(0, len(template_bytes), bytes_per_line):
        # Get line of bytes
        line_bytes = template_bytes[i:i + bytes_per_line]
        
        # Format offset
        offset = f"{i:04x}: "
        
        # Format hex bytes
        hex_part = " ".join(f"{b:02x}" for b in line_bytes)
        # Pad hex part to consistent width
        hex_part = hex_part.ljust(bytes_per_line * 3 - 1)
        
        # Format ASCII representation
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in line_bytes)
        
        print(f"{offset}{hex_part} |{ascii_part}|")
    
    print("-" * 60)

# ---------- Dump a template (raw) ----------
def dump_template(finger, location_id, filename=None):
    """
    Loads template from sensor and returns bytes of the template (list of ints -> bytes).
    If filename is provided, writes binary file.
    Note: the returned data is the raw 'char/template' payload from the sensor (512 bytes typical).
    """
    # Use the get_template helper function
    b = get_template(finger, location_id)

    if filename:
        with open(filename, "wb") as f:
            f.write(b)
        print(f"Wrote {len(b)} bytes to {filename}")

    print(f"Dumped template ID {location_id}, {len(b)} bytes")
    return b

# ---------- Example usage ----------
if __name__ == "__main__":
    print("Opening sensor...")
    f = open_sensor()
    print("Sensor ready.")
    try:
        print("Stored IDs:", list_ids(f))
    except Exception as e:
        print("Error listing IDs:", e)

    try:
        # Example: Get template by ID and display it
        template_id = 1
        template_data = get_template(f, template_id)
        print(f"\nTemplate {template_id} retrieved:")
        display_template_bytes(template_data)
        
        # Also dump to file
        dump_template(f, location_id=1, filename="template_id_1.bin")
    except Exception as e:
        print("Error working with template:", e)

    #enroll new finger
    # try:
    #     new_id = 1  # Change as needed
    #     enroll_id(f, new_id)
    # except Exception as e:
    #     print("Error enrolling new finger:", e)
    # print("Done.")


        
