from as608_menu import open_sensor, list_ids, enroll_id, dump_template

def find_next_available_id(finger, max_id=200):
    """Find the next available ID for enrollment"""
    try:
        stored_ids = list_ids(finger)
        print(f"Currently stored IDs: {stored_ids}")
        
        # Find next available ID starting from 1
        for i in range(1, max_id + 1):
            if i not in stored_ids:
                return i
        
        raise RuntimeError(f"No available IDs (checked 1-{max_id})")
    except Exception as e:
        print(f"Error checking stored IDs: {e}")
        # Fallback: try ID 1 if we can't read stored templates
        return 1

def enroll_new_finger():
    """Enroll a new fingerprint with automatic ID assignment and template backup"""
    try:
        print("Opening fingerprint sensor...")
        finger = open_sensor()
        print("Sensor ready!")
        
        # Find next available ID
        next_id = find_next_available_id(finger)
        print(f"\nEnrolling new fingerprint to ID: {next_id}")
        
        # Enroll the fingerprint
        success = enroll_id(finger, next_id)
        
        if success:
            print(f"\n✅ Fingerprint successfully enrolled to ID {next_id}")
            
            # Save template to file
            template_filename = f"template_id_{next_id}.bin"
            try:
                dump_template(finger, next_id, template_filename)
                print(f"✅ Template saved to {template_filename}")
            except Exception as e:
                print(f"⚠️  Warning: Could not save template file: {e}")
            
            # Show updated list
            try:
                updated_ids = list_ids(finger)
                print(f"\nUpdated stored IDs: {updated_ids}")
            except Exception as e:
                print(f"Could not read updated ID list: {e}")
                
        else:
            print("❌ Enrollment failed")
            
    except Exception as e:
        print(f"❌ Error during enrollment: {e}")

if __name__ == "__main__":
    enroll_new_finger()
