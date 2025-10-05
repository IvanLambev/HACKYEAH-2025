#!/usr/bin/env python3

"""
RFID_Manager - Complete MIFARE Classic Library for PN532
Author: Assistant
Date: October 2025

This library provides a complete interface for MIFARE Classic cards using PN532 module
with libnfc on Raspberry Pi. It handles reading, writing, authentication, and string operations.
"""

import subprocess
import os
import time
import binascii
from typing import Optional, List, Tuple

class RFID_Manager:
    """
    Complete MIFARE Classic card manager using PN532 and libnfc.
    
    Features:
    - Card detection and identification
    - Block-level reading and writing
    - String reading and writing across multiple blocks
    - Automatic authentication handling
    - Error recovery and robust operation
    """
    
    def __init__(self, temp_dir: str = "/tmp"):
        """
        Initialize the RFID Manager.
        
        Args:
            temp_dir: Directory for temporary files (default: /tmp)
        """
        self.temp_dir = temp_dir
        self.temp_file = os.path.join(temp_dir, "rfid_dump.mfd")
        self.last_error_time = 0
    
    # ================== BASIC CARD OPERATIONS ==================
    
    def is_card_present(self) -> bool:
        """
        Check if a MIFARE Classic card is present on the reader.
        
        Returns:
            bool: True if card is detected, False otherwise
        """
        try:
            result = subprocess.run(['nfc-list'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=3)
            
            if result.returncode == 0:
                return "ISO14443A passive target(s) found:" in result.stdout
            else:
                self._handle_nfc_error(result.stderr)
                return False
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
    
    def wait_for_card(self, timeout: int = 30) -> bool:
        """
        Wait for a card to be placed on the reader.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if card detected within timeout, False otherwise
        """
        start_time = time.time()
        print(f"Waiting for card (timeout: {timeout}s)...")
        
        while time.time() - start_time < timeout:
            if self.is_card_present():
                return True
            time.sleep(0.5)
        
        return False
    
    def wait_for_card_removal(self, timeout: int = 30) -> bool:
        """
        Wait for the current card to be removed from the reader.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if card removed within timeout, False otherwise
        """
        start_time = time.time()
        print("Waiting for card removal...")
        
        while time.time() - start_time < timeout:
            if not self.is_card_present():
                return True
            time.sleep(0.2)
        
        return False
    
    def get_card_info(self) -> dict:
        """
        Get detailed information about the current card.
        
        Returns:
            dict: Card information including UID, type, size, etc.
        """
        try:
            result = subprocess.run(['nfc-list'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=3)
            
            if result.returncode != 0:
                return {"error": "Failed to read card info"}
            
            info = {
                "present": False,
                "uid": None,
                "type": None,
                "size": None,
                "atqa": None,
                "sak": None,
                "writable": None,
                "notes": []
            }
            
            lines = result.stdout.split('\n')
            for line in lines:
                line = line.strip()
                
                if "ISO14443A passive target(s) found:" in line:
                    info["present"] = True
                elif "UID (NFCID1):" in line:
                    uid = line.split(':', 1)[1].strip().replace(' ', '').upper()
                    info["uid"] = uid
                elif "ATQA (SENS_RES):" in line:
                    atqa = line.split(':', 1)[1].strip()
                    info["atqa"] = atqa
                elif "SAK (SEL_RES):" in line:
                    sak = line.split(':', 1)[1].strip()
                    info["sak"] = sak
            
            # Determine card type and size based on SAK value (more reliable than UID length)
            if info["sak"]:
                sak_hex = info["sak"].replace(' ', '')
                if sak_hex == "08":
                    info["type"] = "MIFARE Classic 1K"
                    info["size"] = 1024
                elif sak_hex == "18":
                    info["type"] = "MIFARE Classic 4K"
                    info["size"] = 4096
                elif sak_hex == "09":
                    info["type"] = "MIFARE Mini"
                    info["size"] = 320
                else:
                    # Fallback to UID length if SAK is unknown
                    if info["uid"]:
                        uid_len = len(info["uid"]) // 2
                        if uid_len == 4:
                            info["type"] = "MIFARE Classic 1K"
                            info["size"] = 1024
                        elif uid_len == 7:
                            info["type"] = "MIFARE Classic 4K"  
                            info["size"] = 4096
                        else:
                            info["type"] = f"Unknown (SAK: {sak_hex})"
                            info["size"] = None
                    else:
                        info["type"] = f"Unknown (SAK: {sak_hex})"
                        info["size"] = None
            
            # Skip writeability analysis to avoid circular dependency
            # This will be done lazily when needed
            
            return info
            
        except Exception as e:
            return {"error": f"Exception: {e}"}
    
    def _is_4k_card_quick(self) -> bool:
        """
        Quick check if card is 4K without calling get_card_info() (prevents circular dependency).
        
        Returns:
            bool: True if likely 4K card, False otherwise
        """
        try:
            result = subprocess.run(['nfc-list'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=3)
            
            if result.returncode == 0:
                # Look for SAK value 18 (4K card indicator)
                for line in result.stdout.split('\n'):
                    if "SAK (SEL_RES):" in line:
                        sak = line.split(':', 1)[1].strip().replace(' ', '')
                        return sak == "18"
                        
            return False
        except Exception:
            return False
    
    def check_card_writeability(self) -> dict:
        """
        Check if the current card is likely writable or read-only.
        This is a separate method to avoid circular dependencies.
        
        Returns:
            dict: Writeability analysis results
        """
        result = {
            "writable": "unknown",
            "confidence": "low", 
            "reason": "Not analyzed",
            "demo_blocks_found": 0,
            "total_blocks_checked": 0
        }
        
        try:
            # Use existing card data if available
            data = None
            if os.path.exists(self.temp_file):
                try:
                    with open(self.temp_file, 'rb') as f:
                        data = f.read()
                    if len(data) < 1024:
                        data = None
                except:
                    pass
            
            if not data:
                # Only read card if we don't have cached data
                data = self.read_card_raw()
                
            if not data:
                result["reason"] = "Failed to read card data"
                return result
            
            # Check for common demo/test patterns  
            demo_patterns = [b'TEST-4K', b'TEST-1K', b'DEMO-', b'SAMPLE']
            demo_blocks = 0
            total_checked = 0
            
            # Check first 32 blocks (8 sectors) for better sample
            for block in range(1, min(32, len(data) // 16)):
                if (block + 1) % 4 == 0:  # Skip trailer blocks
                    continue
                    
                block_data = data[block * 16:(block + 1) * 16]
                total_checked += 1
                
                for pattern in demo_patterns:
                    if pattern in block_data:
                        demo_blocks += 1
                        break
            
            result["demo_blocks_found"] = demo_blocks
            result["total_blocks_checked"] = total_checked
            
            if demo_blocks > 0:
                demo_ratio = demo_blocks / total_checked
                if demo_ratio > 0.3:  # 30% or more demo patterns
                    result["writable"] = False
                    result["confidence"] = "high"
                    result["reason"] = f"Demo/test card detected ({demo_blocks}/{total_checked} blocks have demo patterns)"
                elif demo_ratio > 0.1:  # 10% or more demo patterns  
                    result["writable"] = False
                    result["confidence"] = "medium"
                    result["reason"] = f"Likely demo card ({demo_blocks}/{total_checked} blocks have demo patterns)"
                else:
                    result["writable"] = "unknown"
                    result["confidence"] = "low"
                    result["reason"] = f"Some demo patterns found ({demo_blocks}/{total_checked} blocks)"
            else:
                # No demo patterns found - likely writable
                result["writable"] = True
                result["confidence"] = "medium"
                result["reason"] = "No demo patterns detected - likely writable"
                
        except Exception as e:
            result["reason"] = f"Analysis failed: {e}"
            
        return result
    
    def _analyze_card_writeability(self, info: dict):
        """
        Analyze if the card is likely to be writable or read-only.
        
        Args:
            info: Card info dictionary to update
        """
        # This method is now deprecated to avoid circular dependency issues
        # Writeability analysis will be done on-demand when needed
        info["writable"] = "unknown"
    
    # ================== BLOCK OPERATIONS ==================
    
    def read_card_raw(self) -> Optional[bytes]:
        """
        Read the entire card data as raw bytes.
        
        Returns:
            bytes: Raw card data, or None if failed
        """
        try:
            # Check if we already have a valid dump file (must be > 1KB for any useful data)
            if os.path.exists(self.temp_file):
                try:
                    with open(self.temp_file, 'rb') as f:
                        data = f.read()
                    if len(data) >= 1024:  # Must have at least 1KB of data
                        return data
                except:
                    pass
            
            # If no valid dump exists, create one
            # Check card type to determine which tool to use (avoid circular dependency)
            is_4k_card = self._is_4k_card_quick()
            if is_4k_card:
                # Use mfoc for 4K cards - it's more reliable with authentication
                # But first try to reuse existing good dump if available
                good_dump = '/tmp/card4k.mfd'
                if os.path.exists(good_dump):
                    with open(good_dump, 'rb') as f:
                        data = f.read()
                    if len(data) >= 4096:  # Valid 4K card dump
                        # Copy to our temp location
                        with open(self.temp_file, 'wb') as f:
                            f.write(data)
                        return data
                
                # If no good dump exists, try to create one (this may take time)
                result = subprocess.run([
                    'mfoc', '-O', self.temp_file
                ], capture_output=True, text=True, timeout=30)
            else:
                # Use nfc-mfclassic for 1K cards with error tolerance
                # Use 'A' (tolerant) instead of 'a' (halt on errors) for better compatibility
                result = subprocess.run([
                    'nfc-mfclassic', 'r', 'A', 'u', self.temp_file
                ], capture_output=True, text=True, timeout=20)
            
            # Check if we got data
            if os.path.exists(self.temp_file):
                with open(self.temp_file, 'rb') as f:
                    data = f.read()
                if len(data) >= 1024:
                    if result.returncode != 0 and "authentication failed" in result.stderr:
                        print(f"Warning: Some blocks failed authentication")
                    return data
            
            return None
                
        except Exception as e:
            print(f"Read error: {e}")
            return None
    
    def read_block(self, block_num: int) -> Optional[bytes]:
        """
        Read a specific 16-byte block from the card.
        
        Args:
            block_num: Block number (0-63 for 1K cards, 0-255 for 4K cards)
            
        Returns:
            bytes: 16-byte block data, or None if failed
        """
        # Determine max blocks based on card type
        card_info = self.get_card_info()
        max_blocks = 255 if card_info.get('type') == 'MIFARE Classic 4K' else 63
        
        if not (0 <= block_num <= max_blocks):
            print(f"Invalid block number: {block_num} (must be 0-{max_blocks} for {card_info.get('type', 'this card')})")
            return None
        
        data = self.read_card_raw()
        if data and len(data) >= (block_num + 1) * 16:
            start = block_num * 16
            return data[start:start + 16]
        return None
    
    def read_multiple_blocks(self, start_block: int, num_blocks: int) -> Optional[bytes]:
        """
        Read multiple consecutive blocks.
        
        Args:
            start_block: Starting block number
            num_blocks: Number of blocks to read
            
        Returns:
            bytes: Combined data from all blocks, or None if failed
        """
        # Determine max blocks based on card type
        card_info = self.get_card_info()
        max_blocks = 256 if card_info.get('type') == 'MIFARE Classic 4K' else 64
        
        if start_block + num_blocks > max_blocks:
            print(f"Block range exceeds card capacity (max {max_blocks} blocks)")
            return None
        
        result = bytearray()
        for i in range(num_blocks):
            block_data = self.read_block(start_block + i)
            if block_data is None:
                print(f"Failed to read block {start_block + i}")
                return None
            result.extend(block_data)
        
        return bytes(result)
    
    def write_block(self, block_num: int, data: bytes) -> bool:
        """
        Write 16 bytes of data to a specific block.
        
        Args:
            block_num: Block number to write to
            data: Exactly 16 bytes of data
            
        Returns:
            bool: True if successful, False otherwise
        """
        if len(data) != 16:
            print(f"Block data must be exactly 16 bytes, got {len(data)}")
            return False
            
        # Determine max blocks based on card type
        card_info = self.get_card_info()
        max_blocks = 255 if card_info.get('type') == 'MIFARE Classic 4K' else 63
        
        if not (0 <= block_num <= max_blocks):
            print(f"Invalid block number: {block_num} (max {max_blocks} for {card_info.get('type', 'this card')})")
            return False
        
        # Block 0 is read-only (manufacturer data)
        if block_num == 0:
            print("Block 0 is read-only (manufacturer data)")
            return False
        
        # Trailer blocks (3, 7, 11, 15, etc.) contain access keys - be careful
        if (block_num + 1) % 4 == 0:
            print(f"Warning: Block {block_num} is a trailer block (contains access keys)")
            confirm = input("Continue? (y/N): ")
            if not confirm.lower().startswith('y'):
                return False
        
        try:
            # For 4K cards, use a different approach - direct block writing
            if self._is_4k_card_quick():
                result = self._write_single_block_4k(block_num, data)
                if result:
                    print(f"Successfully wrote to block {block_num}")
                    # Invalidate cached dump so next read gets fresh data
                    if os.path.exists(self.temp_file):
                        os.remove(self.temp_file)
                    return True
                else:
                    print(f"Write failed for 4K card block {block_num}")
                    return False
            else:
                # For 1K cards, use the full card approach with retry logic
                card_data = None
                max_retries = 3
                
                for attempt in range(max_retries):
                    card_data = self.read_card_raw()
                    if card_data:
                        break
                    
                    print(f"Read attempt {attempt + 1}/{max_retries} failed, checking connection...")
                    if not self.check_and_recover_connection():
                        print("Cannot recover card connection")
                        return False
                    time.sleep(0.5)
                
                if not card_data:
                    print("Failed to read card after all retry attempts")
                    return False
                
                # Modify the specific block
                card_data = bytearray(card_data)
                start = block_num * 16
                card_data[start:start + 16] = data
                
                # Write modified data to temp file
                write_file = os.path.join(self.temp_dir, "rfid_write.mfd")
                with open(write_file, 'wb') as f:
                    f.write(card_data)
                
                # Use nfc-mfclassic for 1K cards with error tolerance
                result = subprocess.run([
                    'nfc-mfclassic', 'w', 'A', 'u', write_file
                ], capture_output=True, text=True, timeout=20)
                
                os.remove(write_file)
                
                if result.returncode == 0:
                    print(f"Successfully wrote to block {block_num}")
                    # Invalidate cached dump so next read gets fresh data
                    if os.path.exists(self.temp_file):
                        os.remove(self.temp_file)
                    # Add small delay to let card settle
                    time.sleep(0.1)
                    return True
                else:
                    print(f"Write failed: {result.stderr}")
                    # Also invalidate cache on failure to force fresh read attempt
                    if os.path.exists(self.temp_file):
                        os.remove(self.temp_file)
                    return False
                
        except Exception as e:
            print(f"Write error: {e}")
            return False
    
    # ================== STRING OPERATIONS ==================
    
    def write_string(self, start_block: int, text: str, max_length: int = 3000) -> bool:
        """
        Write a string across multiple blocks continuously, automatically skipping trailer blocks.
        Format: [4-byte length][string data...]
        
        This method will:
        - Write strings of any length up to max_length
        - Automatically skip trailer blocks (every 4th block)
        - Handle both 1K and 4K cards efficiently
        - Provide detailed progress information
        
        Args:
            start_block: Starting block number (should not be 0 or trailer block)
            text: String to write (any length up to max_length)
            max_length: Maximum string length allowed (default 3000 chars)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Input validation
        if len(text) > max_length:
            print(f"Error: String too long: {len(text)} > {max_length}")
            return False
        
        # Block 0 is read-only, trailer blocks should be avoided as starting point
        if start_block == 0:
            print("Error: Cannot start writing at block 0 (manufacturer data)")
            return False
        
        if (start_block + 1) % 4 == 0:
            print(f"Warning: Block {start_block} is a trailer block. Starting at next block.")
            start_block += 1
        
        # Convert string to UTF-8 bytes
        text_bytes = text.encode('utf-8')
        char_length = len(text)  # Store character count, not byte count
        
        # Prepare data with 4-byte length header (storing character count)
        data = bytearray()
        data.append((char_length >> 24) & 0xFF)  # Highest byte
        data.append((char_length >> 16) & 0xFF)  # High byte  
        data.append((char_length >> 8) & 0xFF)   # Low byte
        data.append(char_length & 0xFF)          # Lowest byte
        data.extend(text_bytes)
        
        # Pad to complete blocks
        while len(data) % 16 != 0:
            data.append(0)
        
        # Calculate number of 16-byte chunks needed
        chunks_needed = len(data) // 16
        
        # Determine max blocks based on card type
        card_info = self.get_card_info()
        max_blocks = 256 if card_info.get('type') == 'MIFARE Classic 4K' else 64
        
        print(f"Writing string: {len(text)} characters ({len(text_bytes)} bytes)")
        print(f"Need {chunks_needed} blocks, card has {max_blocks} total blocks")
        
        # For 1K cards, warn about space limitations early
        if max_blocks == 64 and chunks_needed > 30:
            print(f"⚠️ Warning: Large string on 1K card. Consider using 4K card for strings > 400 characters.")
        
        # Find available blocks (skip trailer blocks and calculate actual space needed)
        available_blocks = []
        current_block = start_block
        
        while len(available_blocks) < chunks_needed and current_block < max_blocks:
            # Skip trailer blocks (every 4th block: 3, 7, 11, 15, etc.)
            if (current_block + 1) % 4 == 0:
                current_block += 1
                continue
            
            available_blocks.append(current_block)
            current_block += 1
        
        if len(available_blocks) < chunks_needed:
            print(f"Error: Not enough writable blocks available")
            print(f"Need: {chunks_needed}, Available: {len(available_blocks)}")
            return False
        
        print(f"Will use blocks: {available_blocks[:10]}{'...' if len(available_blocks) > 10 else ''}")
        
        # Write data chunk by chunk to available blocks
        success_count = 0
        for i in range(chunks_needed):
            block_num = available_blocks[i]
            chunk_data = data[i * 16:(i + 1) * 16]
            
            print(f"Writing chunk {i+1}/{chunks_needed} to block {block_num}...")
            
            if self.write_block(block_num, chunk_data):
                success_count += 1
            else:
                print(f"❌ Failed to write block {block_num}")
                print(f"Successfully wrote {success_count}/{chunks_needed} blocks before failure")
                return False
        
        print(f"✅ Successfully wrote {success_count}/{chunks_needed} blocks")
        print(f"String written across blocks: {available_blocks[0]} to {available_blocks[chunks_needed-1]}")
        return True
    
    def write_long_string(self, text: str, start_sector: int = 1) -> bool:
        """
        Write very long strings efficiently by using entire sectors.
        This method is optimized for large amounts of data and automatically
        finds the best starting block within the specified sector.
        
        Args:
            text: String to write (can be very long)
            start_sector: Starting sector number (default 1, avoiding sector 0)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Calculate starting block (each sector has 4 blocks, we use the first data block)
        start_block = start_sector * 4
        
        # For sector 0, use block 1 (skip block 0 which is manufacturer data)
        if start_sector == 0:
            start_block = 1
        
        print(f"Writing long string starting from sector {start_sector}, block {start_block}")
        return self.write_string(start_block, text, max_length=10000)
    
    def get_string_info(self, start_block: int) -> dict:
        """
        Get information about a string stored on the card without reading the full content.
        
        Args:
            start_block: Starting block number where string begins
            
        Returns:
            dict: Information about the stored string
        """
        try:
            # Read just the first block to get metadata
            block_data = self.read_block(start_block)
            if not block_data:
                return {"error": "Cannot read starting block"}
            
            # Detect format
            length_4byte = (block_data[0] << 24) | (block_data[1] << 16) | (block_data[2] << 8) | block_data[3]
            length_2byte = (block_data[0] << 8) | block_data[1]
            
            if (0 < length_4byte <= 10000 and 
                (block_data[0] == 0 or (block_data[0] == 0 and block_data[1] == 0))):
                char_count = length_4byte
                format_type = "new (4-byte header)"
                data_start = 4
            elif 0 < length_2byte <= 1000:
                char_count = length_2byte
                format_type = "old (2-byte header)"
                data_start = 2
            else:
                return {"error": "No valid string header found"}
            
            # For accurate block calculation, we need to read more data to get actual byte count
            # For now, give a realistic estimate
            estimated_bytes = max(char_count * 1.1, char_count)  # More realistic UTF-8 estimate (most chars are 1 byte)
            total_data_size = (4 if format_type.startswith("new") else 2) + estimated_bytes
            # Round up to nearest multiple of 16
            blocks_needed = int((total_data_size + 15) // 16)
            
            # Get preview of content (first 50 chars)
            preview_bytes = min(16 - data_start, 50)
            preview = block_data[data_start:data_start + preview_bytes].decode("utf-8", errors="ignore")
            
            return {
                "length": char_count,
                "format": format_type,
                "blocks_needed": blocks_needed,
                "start_block": start_block,
                "estimated_end_block": start_block + blocks_needed + (blocks_needed // 3),  # Account for trailer blocks
                "preview": preview + ("..." if char_count > len(preview) else ""),
                "complete": True
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {e}"}
    
    def read_string(self, start_block: int, max_length: int = 3000) -> Optional[str]:
        """
        Read a string that was written with write_string().
        Automatically handles both old (2-byte) and new (4-byte) length formats.
        
        Args:
            start_block: Starting block number where string begins
            max_length: Maximum expected string length (default 3000)
            
        Returns:
            str: The read string, or None if failed
        """
        start_time = time.time()
        timeout_seconds = 30  # Maximum time allowed for string reading
        
        try:
            # Read the first block to get length header
            block_data = self.read_block(start_block)
            if not block_data:
                print(f"Failed to read starting block {start_block}")
                return None
            
            # Try to detect format by checking if first 4 bytes look like a length
            # New format: 4-byte length header
            length_4byte = (block_data[0] << 24) | (block_data[1] << 16) | (block_data[2] << 8) | block_data[3]
            length_2byte = (block_data[0] << 8) | block_data[1]
            
            # Determine which format we're dealing with
            # Check if it looks like new 4-byte format first
            if (0 < length_4byte <= max_length and 
                (block_data[0] == 0 or (block_data[0] == 0 and block_data[1] == 0))):
                # New 4-byte format (character count stored)
                char_count = length_4byte
                data_start = 4
                header_size = 4
                print(f"Reading string with new format: {char_count} characters")
            elif 0 < length_2byte <= 1000:  # Old format was limited to ~900 characters
                # Old 2-byte format (character count stored)
                char_count = length_2byte
                data_start = 2
                header_size = 2
                print(f"Reading string with old format: {char_count} characters")
            else:
                print(f"No valid string header found in block {start_block}")
                print(f"First 8 bytes: {' '.join(f'{b:02x}' for b in block_data[:8])}")
                return None
            
            if char_count == 0:
                return ""
            
            if char_count > max_length:
                print(f"String too long: {char_count} > {max_length} characters")
                return None
            
            # Start collecting raw bytes from after the length header
            raw_bytes = bytearray()
            bytes_available_first_block = 16 - header_size
            raw_bytes.extend(block_data[data_start:data_start + bytes_available_first_block])
            
            print(f"Copied {bytes_available_first_block} bytes from first block")
            
            # Read additional blocks until we have enough characters, but stop at null padding
            card_info = self.get_card_info()
            max_blocks = 256 if card_info.get('type') == 'MIFARE Classic 4K' else 64
            
            current_block = start_block + 1
            chars_decoded = 0
            
            # Keep reading blocks until we have enough characters
            # Add safety limits to prevent infinite loops
            max_blocks_to_read = min(32, max_blocks - start_block)  # Reasonable limit
            blocks_read = 0
            
            while chars_decoded < char_count and current_block < max_blocks and blocks_read < max_blocks_to_read:
                # Check timeout
                if time.time() - start_time > timeout_seconds:
                    print(f"Timeout after {timeout_seconds}s while reading string")
                    break
                
                # Skip trailer blocks (every 4th block: 3, 7, 11, 15, etc.)
                if (current_block + 1) % 4 == 0:
                    current_block += 1
                    continue
                
                block_data = self.read_block(current_block)
                if not block_data:
                    print(f"Failed to read block {current_block}")
                    break
                
                blocks_read += 1
                
                # For multi-block strings, don't stop on null blocks too early
                # Only stop if we've read enough characters AND hit null padding
                if block_data == b'\x00' * 16:
                    # Try to decode what we have so far first
                    try:
                        test_decode = raw_bytes.decode("utf-8", errors="ignore") 
                        chars_so_far = len(test_decode)
                        if chars_so_far >= char_count:
                            print(f"Block {current_block}: found null padding after reading enough data, stopping")
                            break
                        else:
                            print(f"Block {current_block}: null padding but only have {chars_so_far}/{char_count} chars, continuing...")
                            # Add this null block anyway - it might contain continuation data
                    except:
                        pass
                
                # Add bytes from this block
                raw_bytes.extend(block_data)
                
                # Try to decode what we have so far to count characters
                try:
                    test_decode = raw_bytes.decode("utf-8", errors="ignore")
                    chars_decoded = len(test_decode)
                    print(f"Block {current_block}: copied 16 bytes, now have {chars_decoded} characters ({blocks_read} blocks read)")
                    
                    # If we have enough characters, we can stop
                    if chars_decoded >= char_count:
                        break
                        
                except:
                    # If decode fails, keep reading
                    print(f"Block {current_block}: decode failed, continuing...")
                
                current_block += 1
            
            # Now decode the final string and trim to exact length
            try:
                # Decode all the raw bytes we collected
                full_decoded = raw_bytes.decode("utf-8", errors="ignore")
                
                # Trim to exactly the character count we need
                result = full_decoded[:char_count]
                
                print(f"✅ Successfully read string: {len(result)} characters (from {len(raw_bytes)} raw bytes)")
                return result
                    
            except Exception as e:
                print(f"Error decoding string: {e}")
                # Try simpler fallback - just decode without character counting precision
                try:
                    simple_decode = raw_bytes.decode("utf-8", errors="replace")
                    # Remove null characters and trim whitespace
                    clean_result = simple_decode.replace('\x00', '').rstrip('\x00 ')
                    print(f"⚠️ Using fallback decode: {len(clean_result)} characters")
                    return clean_result
                except Exception as e2:
                    print(f"Fallback decode also failed: {e2}")
                try:
                    result = raw_bytes.decode("utf-8", errors="replace")[:char_count]
                    print(f"Recovered with error replacement: {len(result)} characters")
                    return result
                except:
                    return None
            
        except Exception as e:
            print(f"Error reading string: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # ================== UTILITY FUNCTIONS ==================
    
    def format_card_display(self, num_blocks: int = 16) -> str:
        """
        Create a formatted display of card contents.
        
        Args:
            num_blocks: Number of blocks to display
            
        Returns:
            str: Formatted card contents
        """
        card_data = self.read_card_raw()
        if not card_data:
            return "Failed to read card"
        
        output = []
        output.append("MIFARE Classic Card Contents:")
        output.append("=" * 50)
        
        for block in range(min(num_blocks, len(card_data) // 16)):
            start = block * 16
            block_data = card_data[start:start + 16]
            
            # Format as hex
            hex_str = ' '.join([f'{b:02x}' for b in block_data])
            
            # Format as ASCII (printable chars only)
            ascii_str = ''.join([chr(b) if 32 <= b <= 126 else '.' for b in block_data])
            
            # Mark special blocks
            block_type = ""
            if block == 0:
                block_type = " (UID/Manufacturer)"
            elif (block + 1) % 4 == 0:
                block_type = " (Trailer/Keys)"
            
            output.append(f"Block {block:2d}: {hex_str} | {ascii_str}{block_type}")
        
        return '\n'.join(output)
    
    def _handle_nfc_error(self, stderr: str):
        """Handle NFC communication errors."""
        current_time = time.time()
        if current_time - self.last_error_time > 10:  # Reset every 10 seconds max
            self.last_error_time = current_time
            if "Input / Output Error" in stderr or "Unable to open" in stderr:
                self._reset_pn532()
    
    def _reset_pn532(self):
        """Try to reset PN532 if it gets into bad state."""
        try:
            subprocess.run(['pkill', '-f', 'nfc-'], capture_output=True)
            time.sleep(1)
        except:
            pass
    
    def _write_single_block_4k(self, block_num: int, data: bytes) -> bool:
        """
        Write a single block to 4K card using sector-by-sector approach.
        
        Args:
            block_num: Block number to write
            data: 16 bytes of data to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # First, detect if this is a write-protected card
            original_data = self.read_card_raw()
            if not original_data:
                print("Failed to read card for single block write")
                return False
            
            # Check if this looks like a demo/test card (has TEST-4K pattern)
            block_data = original_data[block_num * 16:(block_num + 1) * 16]
            is_demo_card = b'TEST-4K' in block_data
            if is_demo_card:
                print(f"Warning: This appears to be a demo/test card with write protection")
                print(f"Block {block_num} contains: {block_data}")
                print("Demo cards are often read-only and cannot be modified")
                print("Write operation will likely fail...")
            
            # Create a modified version
            card_data = bytearray(original_data)
            start = block_num * 16
            original_block = bytes(card_data[start:start + 16])
            card_data[start:start + 16] = data
            
            # Create a temporary file with the modified data
            temp_write_file = os.path.join(self.temp_dir, f"block_{block_num}_write.mfd")
            with open(temp_write_file, 'wb') as f:
                f.write(card_data)
            
            try:
                # Try writing with standard approach
                result = subprocess.run([
                    'nfc-mfclassic', 'w', 'A', 'u', temp_write_file
                ], capture_output=True, text=True, timeout=30)
                
                # Parse the output to see if this specific block was written
                written_count = 0
                total_count = 256
                if result.stdout:
                    if "Done," in result.stdout:
                        # Extract number of blocks written
                        import re
                        match = re.search(r'Done, (\d+) of (\d+) blocks written', result.stdout)
                        if match:
                            written_count = int(match.group(1))
                            total_count = int(match.group(2))
                            print(f"nfc-mfclassic wrote {written_count}/{total_count} blocks")
                
                # For demo cards, don't try verification as it can hang
                if is_demo_card:
                    print(f"Skipping verification for demo card (prevents hanging)")
                    if written_count < total_count:
                        print(f"Write likely failed: only {written_count}/{total_count} blocks written")
                        return False
                    else:
                        print(f"Write may have succeeded, but demo cards typically remain unchanged")
                        return False  # Demo cards usually don't change even if write "succeeds"
                
                # For regular cards, do verification
                # Force a fresh read by clearing cache
                if os.path.exists(self.temp_file):
                    os.remove(self.temp_file)
                
                # Add a small delay to let the card settle
                import time
                time.sleep(0.5)
                
                # Read the block back to verify with timeout protection
                try:
                    written_data = self.read_block(block_num)
                    if written_data and written_data == data:
                        return True
                except Exception as e:
                    print(f"Verification read failed: {e}")
                    # If verification fails, assume write didn't work
                    written_data = None
                
                # Check if block changed at all
                if written_data != original_block:
                    print(f"Block {block_num} was partially modified but not as expected")
                    print(f"Original:  {original_block.hex().upper()}")
                    print(f"Expected:  {data.hex().upper()}")
                    print(f"Actual:    {written_data.hex().upper()}")
                    return False
                
                # Block unchanged - likely write-protected
                print(f"Block {block_num} appears to be write-protected")
                print("This card may be:")
                print("  - A demo/test card with permanent data")
                print("  - Write-protected by manufacturer")
                print("  - Using non-standard access conditions")
                return False
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_write_file):
                    os.remove(temp_write_file)
                
        except Exception as e:
            print(f"Error in single block write: {e}")
            return False
    
    def _write_4k_card(self, write_file: str) -> bool:
        """
        Write data to 4K card using appropriate method (legacy method).
        
        Args:
            write_file: Path to file containing card data to write
            
        Returns:
            bool: True if successful, False otherwise
        """
        # This method is deprecated in favor of _write_single_block_4k
        return False
    
    def refresh_cache(self):
        """
        Force a refresh of the cached card data.
        Useful after writing multiple blocks or when reads seem stale.
        """
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        print("Card cache refreshed")
    
    def check_and_recover_connection(self) -> bool:
        """
        Check if card connection is working and attempt recovery if needed.
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        # First, try a simple card presence check
        if not self.is_card_present():
            print("Card not detected - please ensure card is properly placed")
            return False
        
        # Try to read a basic block (block 0 - should always be readable)
        try:
            block0 = self.read_block(0)
            if block0:
                print("Card connection verified")
                return True
        except Exception as e:
            print(f"Card connection issue: {e}")
        
        # If we get here, try to recover
        print("Attempting connection recovery...")
        
        # Clear cache and try to reset connection
        self.refresh_cache()
        self._reset_pn532()
        time.sleep(2)
        
        # Test again
        if self.is_card_present():
            try:
                block0 = self.read_block(0)
                if block0:
                    print("Connection recovered successfully")
                    return True
            except:
                pass
        
        print("Failed to recover card connection")
        return False
    
    def get_available_space(self, start_block: int = 1) -> dict:
        """
        Calculate available space for string storage on the card.
        
        Args:
            start_block: Starting block to calculate from
            
        Returns:
            dict: Space information
        """
        card_info = self.get_card_info()
        max_blocks = 256 if card_info.get('type') == 'MIFARE Classic 4K' else 64
        
        # Count available blocks (skip trailer blocks and block 0)
        available_blocks = []
        for block in range(max(1, start_block), max_blocks):
            if (block + 1) % 4 != 0:  # Skip trailer blocks
                available_blocks.append(block)
        
        total_bytes = len(available_blocks) * 16
        # Reserve 4 bytes for header
        usable_bytes = total_bytes - 4
        # Estimate characters (assume average 1.2 bytes per character for UTF-8)
        estimated_chars = int(usable_bytes * 0.8)
        
        return {
            "card_type": card_info.get('type', 'Unknown'),
            "total_blocks": max_blocks,
            "available_blocks": len(available_blocks),
            "available_bytes": total_bytes,
            "usable_bytes": usable_bytes,
            "estimated_max_chars": estimated_chars,
            "start_block": start_block
        }
    
    # ================== CONVENIENCE METHODS ==================
    
    def quick_read_card(self) -> dict:
        """
        Quickly read and return card information and first few blocks.
        
        Returns:
            dict: Card info and sample data
        """
        result = {
            "info": self.get_card_info(),
            "blocks": {},
            "strings": {}
        }
        
        if not result["info"]["present"]:
            return result
        
        # Read first few blocks
        for block in [0, 1, 4, 5, 8]:
            data = self.read_block(block)
            if data:
                result["blocks"][block] = {
                    "hex": ' '.join([f'{b:02x}' for b in data]),
                    "ascii": ''.join([chr(b) if 32 <= b <= 126 else '.' for b in data])
                }
        
        # Try to read strings from common starting blocks
        for start_block in [1, 4, 8]:
            string_data = self.read_string(start_block)
            if string_data:
                result["strings"][start_block] = string_data
        
        return result