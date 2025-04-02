import requests
import time

def get_player_coords():
    """Get player coordinates from various candidate memory locations"""
    # Potential memory addresses for player coordinates
    coord_addresses = [
        0x02037318,  # Standard FireRed address
        0x020370B8,  # Alternate 1
        0x030031F8   # Alternate 2 (IRAM)
    ]
    
    results = {}
    
    for base_addr in coord_addresses:
        try:
            # Read X coordinate (2 bytes, little-endian)
            x_low = int(requests.get(f"http://localhost:8080/read_byte", {'addr': f"{base_addr:X}"}).text.strip().replace('\x00', ''), 16)
            x_high = int(requests.get(f"http://localhost:8080/read_byte", {'addr': f"{base_addr+1:X}"}).text.strip().replace('\x00', ''), 16)
            
            # Read Y coordinate (2 bytes, little-endian)
            y_low = int(requests.get(f"http://localhost:8080/read_byte", {'addr': f"{base_addr+2:X}"}).text.strip().replace('\x00', ''), 16)
            y_high = int(requests.get(f"http://localhost:8080/read_byte", {'addr': f"{base_addr+3:X}"}).text.strip().replace('\x00', ''), 16)
            
            # Combine bytes
            x = x_low | (x_high << 8)
            y = y_low | (y_high << 8)
            
            # Store results
            results[f"0x{base_addr:08X}"] = (x, y)
        except:
            results[f"0x{base_addr:08X}"] = "Error"
    
    return results

# Simple tracking loop
try:
    prev_coords = {}
    while True:
        coords = get_player_coords()
        
        # Check for changes
        if coords != prev_coords:
            print("\nPlayer coordinates:")
            for addr, pos in coords.items():
                print(f"  {addr}: {pos}")
        
        prev_coords = coords
        time.sleep(0.5)
except KeyboardInterrupt:
    print("\nExiting...")