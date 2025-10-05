# as608_utils.py
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

# ---------- Match/Identify a fingerprint ----------
def match_finger(finger, timeout=30, slot=1, verbose=True):
    """
    Match a fingerprint against all stored templates on the sensor.
    
    Args:
        finger: The fingerprint sensor object
        timeout: Maximum time to wait for finger placement (seconds)
        slot: Char buffer slot to use (1 or 2)
        verbose: Whether to print detailed status messages
    
    Returns:
        dict: {
            'success': bool,
            'id': int or None,        # Matched template ID
            'confidence': int or None, # Match confidence score (0-255)
            'error': str or None       # Error message if failed
        }
    """
    if verbose:
        print(f"Place finger on sensor for identification...")
    
    start_time = time.time()
    
    # Step 1: Capture finger image
    while True:
        if time.time() - start_time > timeout:
            return {
                'success': False,
                'id': None,
                'confidence': None,
                'error': f'Timeout after {timeout} seconds waiting for finger'
            }
        
        r = finger.get_image()
        if r == adafruit_fingerprint.OK:
            if verbose:
                print("✅ Finger image captured")
            break
        elif r == adafruit_fingerprint.NOFINGER:
            time.sleep(0.1)
            continue
        else:
            return {
                'success': False,
                'id': None,
                'confidence': None,
                'error': f'Failed to capture image: {hex(r)}'
            }
    
    # Step 2: Convert image to template
    r = finger.image_2_tz(slot)
    if r != adafruit_fingerprint.OK:
        return {
            'success': False,
            'id': None,
            'confidence': None,
            'error': f'Failed to convert image to template: {hex(r)}'
        }
    
    if verbose:
        print("🔍 Searching for match...")
    
    # Step 3: Search for match in stored templates
    r = finger.finger_search()
    
    if r == adafruit_fingerprint.OK:
        # Match found
        matched_id = finger.finger_id
        confidence = finger.confidence
        
        if verbose:
            print(f"✅ Match found!")
            print(f"   ID: {matched_id}")
            print(f"   Confidence: {confidence}/255 ({confidence/255*100:.1f}%)")
        
        return {
            'success': True,
            'id': matched_id,
            'confidence': confidence,
            'error': None
        }
    
    elif r == adafruit_fingerprint.NOTFOUND:
        # No match found
        if verbose:
            print("❌ No match found - finger not recognized")
        
        return {
            'success': False,
            'id': None,
            'confidence': None,
            'error': 'Fingerprint not found in database'
        }
    
    else:
        # Search failed for other reason
        return {
            'success': False,
            'id': None,
            'confidence': None,
            'error': f'Search failed: {hex(r)}'
        }

# ---------- Quick match with retry ----------
def quick_match(finger, max_attempts=3, timeout_per_attempt=10, min_confidence=50):
    """
    Attempt to match a fingerprint with retry logic and confidence filtering.
    
    Args:
        finger: The fingerprint sensor object
        max_attempts: Maximum number of attempts
        timeout_per_attempt: Timeout for each attempt (seconds)
        min_confidence: Minimum confidence score to accept (0-255)
    
    Returns:
        dict: Same as match_finger() but with attempt information
    """
    print(f"Quick match: Up to {max_attempts} attempts, min confidence {min_confidence}/255")
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n--- Attempt {attempt}/{max_attempts} ---")
        
        result = match_finger(finger, timeout=timeout_per_attempt, verbose=True)
        
        if result['success']:
            if result['confidence'] >= min_confidence:
                print(f"✅ High-confidence match accepted!")
                result['attempts'] = attempt
                return result
            else:
                print(f"⚠️ Low confidence ({result['confidence']}/255), trying again...")
                continue
        else:
            if "Timeout" in result['error']:
                print(f"⏱️ Attempt {attempt} timed out, trying again...")
                continue
            elif "not found" in result['error']:
                print(f"❌ Finger not recognized on attempt {attempt}")
                # For "not found", we might want to try again in case of poor placement
                continue
            else:
                # Other errors are probably not retry-worthy
                print(f"❌ Error on attempt {attempt}: {result['error']}")
                result['attempts'] = attempt
                return result
    
    # All attempts exhausted
    return {
        'success': False,
        'id': None,
        'confidence': None,
        'error': f'Failed after {max_attempts} attempts',
        'attempts': max_attempts
    }

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
        stored_ids = list_ids(f)
        print("Stored IDs:", stored_ids)
        
        if stored_ids:
            print(f"\n🔍 Ready to test fingerprint matching!")
            print(f"Available templates: {stored_ids}")
            print("Uncomment the matching demo below to test.")
        else:
            print("\n⚠️ No fingerprints enrolled yet.")
            print("Uncomment the enrollment demo below to add fingerprints first.")
            
    except Exception as e:
        print("Error listing IDs:", e)

    # === FINGERPRINT MATCHING DEMO ===
    # Uncomment to test the new matching functions:
    try:
        print("\n=== FINGERPRINT MATCHING TEST ===")
        result = match_finger(f, timeout=15)
        if result['success']:
            print(f"🎉 Matched ID {result['id']} with confidence {result['confidence']}")
        else:
            print(f"❌ Match failed: {result['error']}")
    except Exception as e:
        print("Error during matching:", e)

    # === QUICK MATCH WITH RETRY DEMO ===
    # Uncomment to test retry logic:
    try:
        print("\n=== QUICK MATCH WITH RETRY TEST ===")
        result = quick_match(f, max_attempts=3, min_confidence=50)
        if result['success']:
            print(f"🎉 High-confidence match: ID {result['id']}, confidence {result['confidence']}")
            print(f"   Succeeded on attempt {result['attempts']}")
        else:
            print(f"❌ Failed after {result['attempts']} attempts: {result['error']}")
    except Exception as e:
        print("Error during quick match:", e)

    # === TEMPLATE MANAGEMENT DEMOS ===
    # try:
    #     # Example: Get template by ID and display it
    #     template_id = 1
    #     template_data = get_template(f, template_id)
    #     print(f"\nTemplate {template_id} retrieved:")
    #     display_template_bytes(template_data)
        
    #     # Also dump to file
    #     dump_template(f, location_id=1, filename="template_id_1.bin")
    # except Exception as e:
    #     print("Error working with template:", e)

    # === ENROLLMENT DEMO ===
    # try:
    #     new_id = 1  # Change as needed
    #     enroll_id(f, new_id)
    # except Exception as e:
    #     print("Error enrolling new finger:", e)
    
    print("Done.")


        
