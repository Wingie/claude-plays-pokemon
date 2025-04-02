#!/usr/bin/env python3
"""
simple_skyemu_analyzer.py - Simple tool for analyzing Pokémon RAM in SkyEmu

This script connects to SkyEmu's HTTP Control Server to extract basic
information about a running Pokémon game, including:
- Player's name
- Player's location
- Inventory
- Pokémon party (names, levels, HP, moves)

Usage:
    python simple_skyemu_analyzer.py [--url URL] 

Example:
    python simple_skyemu_analyzer.py --url http://localhost:8080 --refresh 5
"""

import requests
import argparse
import time
from enum import IntEnum, IntFlag
from dataclasses import dataclass
from typing import List, Optional, Tuple

class StatusCondition(IntFlag):
    """Status conditions for Pokémon"""
    NONE = 0
    SLEEP_MASK = 0b111  # Bits 0-2
    SLEEP = 0b001
    POISON = 0b1000  # Bit 3
    BURN = 0b10000  # Bit 4
    FREEZE = 0b100000  # Bit 5
    PARALYSIS = 0b1000000  # Bit 6
    
    def get_status_name(self) -> str:
        """Get a human-readable status name"""
        if self & self.SLEEP_MASK:
            return "SLEEP"
        elif self & self.PARALYSIS:
            return "PARALYSIS"
        elif self & self.FREEZE:
            return "FREEZE"
        elif self & self.BURN:
            return "BURN"
        elif self & self.POISON:
            return "POISON"
        return "OK"

class SkyEmuClient:
    """Client for communicating with SkyEmu's HTTP Control Server"""
    
    def __init__(self, base_url="http://localhost:8080", debug=False):
        self.base_url = base_url
        self.debug = debug
        
    def log_debug(self, message):
        """Print debug messages if debugging is enabled"""
        if self.debug:
            print(f"DEBUG: {message}")
    
    def read_byte(self, addresses):
        """Read one or multiple bytes at the specified addresses"""
        if isinstance(addresses, int):
            addresses = [addresses]
        
        result = bytearray()
        
        # SkyEmu seems to only support reading one byte at a time
        # So we'll make individual requests for each address
        for addr in addresses:
            # Try different address formats - SkyEmu's API might have specific requirements
            # for how addresses are formatted. We'll try the most likely format first.
            
            # Format 1: Hex without leading zeros (e.g., "2024029")
            addr_hex = f"{addr:X}"
            # Format 2: Might need an exact number of digits for the memory map
            # addr_hex = f"{addr & 0xFFFFFFFF:08X}"
            
            params = {'addr': addr_hex}
            self.log_debug(f"Trying address format: addr={addr_hex}")
            
            try:
                response = requests.get(f"{self.base_url}/read_byte", params=params)
                if response.status_code == 200:
                    # Trim any whitespace and handle the 2-character hex response
                    hex_text = response.text.strip()
                    self.log_debug(f"Read from {addr:08X}: raw='{hex_text}'")
                    
                    try:
                        # Clean up the response - remove any null terminators or other non-hex characters
                        clean_hex = ''.join(c for c in hex_text if c in '0123456789abcdefABCDEF')
                        self.log_debug(f"Cleaned hex value: '{clean_hex}'")
                        
                        if clean_hex:
                            # Try parsing as hex directly
                            byte_val = int(clean_hex, 16)
                            result.append(byte_val)
                            self.log_debug(f"Successfully read byte: 0x{byte_val:02X}")
                        else:
                            self.log_debug(f"Empty hex value for address {addr:08X}")
                            result.append(0)
                    except ValueError as e:
                        # Don't print this as a warning - it's just for very verbose debugging
                        self.log_debug(f"Note: Couldn't parse '{hex_text}' as hex for address {addr:08X}: {e}")
                        result.append(0)  # Append a zero for invalid responses
                else:
                    print(f"Error reading byte at {addr:08X}: {response.status_code}, {response.text}")
                    result.append(0)  # Append a zero for error responses
            except Exception as e:
                print(f"Exception reading byte at {addr:08X}: {e}")
                result.append(0)  # Append a zero for exceptions
        
        return bytes(result)
    
    def read_bytes(self, address, length):
        """Read multiple consecutive bytes starting at address"""
        addresses = [address + i for i in range(length)]
        return self.read_byte(addresses)
    
    def read_pointer(self, pointer_address):
        """Read a 32-bit pointer and return the address it points to"""
        try:
            pointer_bytes = self.read_bytes(pointer_address, 4)
            if not pointer_bytes:
                return 0
            # GBA is little-endian
            return int.from_bytes(pointer_bytes, byteorder='little')
        except Exception as e:
            print(f"Error reading pointer at {pointer_address:08X}: {e}")
            return 0
    
    def read_bytes_via_pointer(self, pointer_address, offset=0, length=1):
        """Read multiple consecutive bytes via a pointer"""
        try:
            target_address = self.read_pointer(pointer_address)
            if target_address == 0:
                print(f"Warning: Null pointer at {pointer_address:08X}")
                return b''
                
            target_address += offset
            if target_address < 0x02000000 or target_address > 0x0A000000:
                print(f"Warning: Pointer {target_address:08X} out of valid range")
                return b''
                
            return self.read_bytes(target_address, length)
        except Exception as e:
            print(f"Error reading via pointer: {e}")
            return b''
    
    def status(self):
        """Get the status of the emulator"""
        try:
            response = requests.get(f"{self.base_url}/status")
            if response.status_code == 200:
                # Handle the case where the response might be empty
                content = response.text.strip()
                if content:
                    try:
                        return response.json()
                    except ValueError:
                        print(f"Non-JSON response from status endpoint: '{content}'")
                        return {"raw_response": content}
                else:
                    print("Status endpoint returned empty response")
                    return {"status": "ok", "emulator": "running"}
            else:
                print(f"Error getting status: {response.status_code}, {response.text}")
                return {}
        except Exception as e:
            print(f"Exception getting status: {e}")
            return {}

@dataclass
class PokemonInfo:
    """Basic Pokémon information"""
    species_id: int
    nickname: str
    level: int
    current_hp: int
    max_hp: int
    status: str
    moves: List[str]
    move_pp: List[int]

@dataclass
class GameState:
    """Basic game state information"""
    player_name: str
    location: str
    x: int
    y: int
    money: int
    party: List[PokemonInfo]
    items: List[Tuple[str, int]]  # (item_name, quantity)

class PokemonGameReader:
    """
    Base class for reading Pokémon game memory
    Subclasses will implement game-specific memory addresses and structures
    """
    def __init__(self, client):
        self.client = client
    
    def read_game_state(self) -> GameState:
        """Read the current game state (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement read_game_state")
    
    def _convert_text(self, bytes_data):
        """Convert Pokémon text format to string (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement _convert_text")

class PokemonFireRedReader(PokemonGameReader):
    """Reader for Pokémon FireRed/LeafGreen"""
    
    # Memory addresses verified from sources:
    # - Data Crystal wiki: Pokémon 3rd Generation/Pokémon FireRed and LeafGreen/RAM map
    # - Technical documents on GBA memory addresses and structures
    ADDRESSES = {
        'party_count': 0x02024029,     # Number of Pokémon in party
        'party_data': 0x02024284,      # Start of party data structure 
        'player_name': 0x02024C0A,     # Player's name
        'player_coords': 0x02037318,   # X, Y coordinates in current map (2 bytes each)
        'map_bank': 0x02037354,        # Map bank (area group)
        'map_id': 0x02037355,          # Map ID within bank
        'money': 0x02025840,           # Money (raw value requires XOR decryption)
        'item_pocket': 0x02025C40,     # Start of item pocket data
    }
    
    # Size of a Pokémon data structure in bytes
    POKEMON_SIZE = 100
    
    def read_game_state(self) -> GameState:
        """Read the current game state for Pokémon FireRed/LeafGreen"""
        try:
            player_name = self._read_player_name()
            x, y = self._read_coordinates()
            location = self._read_location()
            money = self._read_money()
            party = self._read_party_pokemon()
            items = self._read_items()
            
            return GameState(
                player_name=player_name,
                location=location,
                x=x,
                y=y,
                money=money,
                party=party,
                items=items
            )
        except Exception as e:
            print(f"Error reading game state: {e}")
            return GameState(
                player_name="Error",
                location="Unknown",
                x=0,
                y=0,
                money=0,
                party=[],
                items=[]
            )
    
    def _read_player_name(self) -> str:
        """Read the player's name"""
        try:
            name_bytes = self.client.read_bytes(self.ADDRESSES['player_name'], 8)
            if not name_bytes:
                return "Unknown"
            return self._convert_text(name_bytes)
        except Exception as e:
            print(f"Error reading player name: {e}")
            return "Unknown"
    
    def _read_coordinates(self) -> Tuple[int, int]:
        """Read player's current X,Y coordinates"""
        try:
            coords_bytes = self.client.read_bytes(self.ADDRESSES['player_coords'], 4)
            if not coords_bytes or len(coords_bytes) < 4:
                return (0, 0)
                
            x = int.from_bytes(coords_bytes[0:2], byteorder='little')
            y = int.from_bytes(coords_bytes[2:4], byteorder='little')
            return (x, y)
        except Exception as e:
            print(f"Error reading coordinates: {e}")
            return (0, 0)
    
    def _read_location(self) -> str:
        """Read current location name"""
        try:
            # Read the map bank and map ID
            map_data = self.client.read_bytes(self.ADDRESSES['map_bank'], 2)
            if not map_data or len(map_data) < 2:
                return "Unknown Location"
                
            bank = map_data[0]
            map_id = map_data[1]
            
            # For now, just return these as numbers since we don't have a complete mapping
            return f"Map #{bank}-{map_id}"
        except Exception as e:
            print(f"Error reading location: {e}")
            return "Unknown Location"
    
    def _read_money(self) -> int:
        """Read the player's money"""
        try:
            money_bytes = self.client.read_bytes(self.ADDRESSES['money'], 4)
            if not money_bytes or len(money_bytes) < 4:
                return 0
                
            # Money in FireRed is stored with simple encryption (XOR)
            # For simplicity, we'll just display the raw value for now
            return int.from_bytes(money_bytes, byteorder='little')
        except Exception as e:
            print(f"Error reading money: {e}")
            return 0
    
    def _read_party_size(self) -> int:
        """Read number of Pokemon in party"""
        try:
            response = requests.get(f"{self.client.base_url}/read_byte", {'addr': f"{self.ADDRESSES['party_count']:X}"})
            if response.status_code != 200:
                print(f"Error reading party size: {response.status_code}")
                return 0
                
            hex_text = response.text.strip()
            print(f"Raw party size response: '{hex_text}'")
            
            # Clean up the hex string
            clean_hex = ''.join(c for c in hex_text if c in '0123456789abcdefABCDEF')
            if not clean_hex:
                print("No valid hex digits in response")
                return 0
                
            # Parse the hex value
            try:
                size = int(clean_hex, 16)
                print(f"Party size parsed: {size} (0x{size:02X})")
                
                # Validate the size
                if 0 <= size <= 6:
                    print(f"Valid party size detected: {size}")
                    return size
                else:
                    print(f"Suspicious party size value: {size} (0x{size:02X}), capping at 6")
                    return min(size, 6)  # Cap at 6 to prevent problems
            except ValueError as e:
                print(f"Error parsing party size hex '{clean_hex}': {e}")
                return 0
                
        except Exception as e:
            print(f"Error reading party size: {e}")
            return 0
    
    def _read_party_pokemon(self) -> List[PokemonInfo]:
        """Read all Pokemon currently in the party"""
        party = []
        try:
            party_size = self._read_party_size()
            print(f"Party size: {party_size}")
            
            if party_size <= 0 or party_size > 6:
                print(f"Invalid party size: {party_size}")
                return []
            
            for i in range(party_size):
                # Calculate address for this Pokémon
                poke_addr = self.ADDRESSES['party_data'] + (i * self.POKEMON_SIZE)
                print(f"Reading Pokémon at address: {poke_addr:08X}")
                
                try:
                    # Read a block of data for this Pokémon
                    # The first part contains the personality value and OT ID
                    header_data = self.client.read_bytes(poke_addr, 32)
                    if not header_data or len(header_data) < 32:
                        print(f"Failed to read Pokémon header data at {poke_addr:08X}")
                        continue
                    
                    # The second part contains battle stats (after decryption)
                    stats_data = self.client.read_bytes(poke_addr + 32, 68)
                    if not stats_data or len(stats_data) < 68:
                        print(f"Failed to read Pokémon stats data at {poke_addr+32:08X}")
                        continue
                    
                    # Extract nickname - it's stored separately in the FireRed data structure
                    nickname_addr = poke_addr + 8  # Approximate location
                    nickname_data = self.client.read_bytes(nickname_addr, 10)
                    nickname = self._convert_text(nickname_data) if nickname_data else "???"
                    
                    # Read species ID - may require decryption in practice
                    # For simplicity, we're using a guess based on common data structure
                    species_id = header_data[0] | (header_data[1] << 8)  # little-endian
                    
                    # Read basic stats
                    level = stats_data[0x34] if len(stats_data) > 0x34 else 0
                    current_hp = int.from_bytes(stats_data[0x36:0x38], byteorder='little') if len(stats_data) > 0x38 else 0
                    max_hp = int.from_bytes(stats_data[0x38:0x3A], byteorder='little') if len(stats_data) > 0x3A else 0
                    
                    # Read status condition
                    status_value = int.from_bytes(stats_data[0x30:0x34], byteorder='little') if len(stats_data) > 0x34 else 0
                    status = StatusCondition(status_value).get_status_name()
                    
                    # Read moves (simplified)
                    moves = []
                    move_pp = []
                    for j in range(4):
                        if 0x28 + (j * 2) + 1 < len(stats_data):
                            move_id = int.from_bytes(stats_data[0x28 + (j*2):0x28 + (j*2) + 2], byteorder='little')
                            if move_id > 0:
                                moves.append(f"Move #{move_id}")
                                if 0x30 + j < len(stats_data):
                                    move_pp.append(stats_data[0x30 + j])
                    
                    pokemon = PokemonInfo(
                        species_id=species_id,
                        nickname=nickname,
                        level=level,
                        current_hp=current_hp,
                        max_hp=max_hp,
                        status=status,
                        moves=moves,
                        move_pp=move_pp
                    )
                    party.append(pokemon)
                    print(f"Successfully read Pokémon: {nickname} (Level {level})")
                    
                except Exception as e:
                    print(f"Error reading Pokémon at index {i}: {e}")
            
        except Exception as e:
            print(f"Error reading party: {e}")
        
        return party
    
    def _read_items(self) -> List[Tuple[str, int]]:
        """Read all items in inventory"""
        items = []
        try:
            # Try reading the item pocket
            base_addr = self.ADDRESSES['item_pocket']
            
            # Read the item count
            count_bytes = self.client.read_bytes(base_addr, 2)
            if not count_bytes or len(count_bytes) < 2:
                return []
                
            count = int.from_bytes(count_bytes, byteorder='little')
            if count > 30:  # Sanity check
                count = 30
                
            print(f"Item count: {count}")
            
            # Read each item entry (4 bytes each: 2 for item ID, 2 for quantity)
            for i in range(count):
                item_addr = base_addr + 4 + (i * 4)  # Skip the count field
                item_data = self.client.read_bytes(item_addr, 4)
                
                if not item_data or len(item_data) < 4:
                    continue
                    
                item_id = int.from_bytes(item_data[0:2], byteorder='little')
                quantity = int.from_bytes(item_data[2:4], byteorder='little')
                
                if item_id != 0 and quantity != 0:
                    items.append((f"Item #{item_id}", quantity))
            
        except Exception as e:
            print(f"Error reading items: {e}")
        
        return items
    
    def _convert_text(self, bytes_data):
        """
        Convert Pokémon FireRed text format to readable text
        
        In FireRed, the text encoding depends on the specific game release and language.
        This implementation handles the most common formats and includes detailed logging
        to help understand the actual encoding used.
        """
        if not bytes_data:
            return "Unknown"
            
        # Print the raw bytes for debugging
        bytes_hex = ' '.join(f'{b:02X}' for b in bytes_data)
        self.client.log_debug(f"Converting text from bytes: {bytes_hex}")
        
        result = ""
        try:
            # First try the standard FireRed/LeafGreen English encoding
            for b in bytes_data:
                if b == 0xFF:  # String terminator
                    break
                elif b == 0x00:  # Null terminator
                    break
                # Standard ASCII range - often direct ASCII for player names
                elif 32 <= b <= 126:  
                    result += chr(b)
                # FireRed character table 
                elif 0x80 <= b <= 0x99:  # A-Z
                    result += chr(b - 0x80 + ord('A'))
                elif 0xA0 <= b <= 0xB9:  # a-z
                    result += chr(b - 0xA0 + ord('a'))
                elif 0xE0 <= b <= 0xE9:  # 0-9
                    result += str(b - 0xE0)
                # Special characters
                elif b == 0xB0:  # Period
                    result += "."
                elif b == 0xB1:  # Hyphen/dash
                    result += "-"
                elif b == 0xB2:  # Ellipsis
                    result += "..."
                elif b == 0xB3:  # Colon
                    result += ":"
                elif b == 0xE0:  # Space
                    result += " "
                else:
                    # For unknown characters, show hex value
                    result += f"[{b:02X}]"
            
            # If result is empty or just contains unknown characters, try a simpler ASCII approach
            if not result or all(c.startswith('[') for c in result if c not in " .,"):
                self.client.log_debug("First conversion attempt failed, trying direct ASCII")
                result = ""
                for b in bytes_data:
                    if b == 0x00 or b == 0xFF:  # Terminators
                        break
                    elif 32 <= b <= 126:  # ASCII printable
                        result += chr(b)
                    else:
                        # If not ASCII, try to interpret as a standard character
                        result += f"[{b:02X}]"
            
        except Exception as e:
            print(f"Error converting text: {e}")
            
        result = result.strip()
        self.client.log_debug(f"Converted text: '{result}'")
        return result if result else "Unknown"

def print_game_state(state):
    """Print the game state in a readable format"""
    if state is None:
        print("Failed to read game state")
        return
    
    print("\n" + "="*50)
    print("Pokémon Game State")
    print("="*50)
    
    print(f"Player Name: {state.player_name}")
    print(f"Location: {state.location} (X={state.x}, Y={state.y})")
    print(f"Money: ₽{state.money}")
    
    print("\nPokémon Party:")
    if not state.party:
        print("  No Pokémon in party")
    else:
        for i, pokemon in enumerate(state.party):
            print(f"  #{i+1}: {pokemon.nickname} (Species #{pokemon.species_id})")
            print(f"      Level: {pokemon.level}, HP: {pokemon.current_hp}/{pokemon.max_hp}, Status: {pokemon.status}")
            
            if pokemon.moves:
                move_info = []
                for j, move in enumerate(pokemon.moves):
                    if j < len(pokemon.move_pp):
                        move_info.append(f"{move} (PP: {pokemon.move_pp[j]})")
                    else:
                        move_info.append(move)
                print(f"      Moves: {', '.join(move_info)}")
    
    print("\nInventory:")
    if not state.items:
        print("  No items")
    else:
        for item_name, quantity in state.items:
            print(f"  {item_name} x{quantity}")

def main():
    parser = argparse.ArgumentParser(description='Simple Pokémon RAM Analyzer for SkyEmu')
    parser.add_argument('--url', default='http://localhost:8080', help='SkyEmu HTTP server URL')
    parser.add_argument('--refresh', type=int, default=0, help='Refresh interval (seconds, 0 = once)')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    args = parser.parse_args()
    
    # Create client with debug flag from command line args
    client = SkyEmuClient(args.url, debug=args.debug)
    
    # # Try to get SkyEmu status first
    # try:
    #     status = client.status()
    #     print(f"SkyEmu status: {status}")
    # except Exception as e:
    #     print(f"Error connecting to SkyEmu at {args.url}: {e}")
    #     print("Make sure SkyEmu is running with the HTTP server enabled.")
    #     return

    # Test if we can read basic memory addresses before proceeding
    print("\nTesting basic memory access...")
    
    # Use more interesting test addresses based on what we see in debug
    test_addresses = [
        0x02000000,  # Start of WRAM
        0x03000000,  # Start of IRAM
        0x02024029,  # Party count
        0x02024284,  # Party data
        0x02037354,  # Map bank/ID - seeing '4f' and '33' here
    ] 
    
    test_results = []
    
    for addr in test_addresses:
        try:
            response = requests.get(f"{args.url}/read_byte", {'addr': f"{addr:X}"})
            if response.status_code == 200:
                hex_text = response.text.strip()
                # Clean up the hex value
                clean_hex = ''.join(c for c in hex_text if c in '0123456789abcdefABCDEF')
                
                if clean_hex:
                    val = int(clean_hex, 16)
                    test_results.append(f"0x{addr:08X}: OK (raw='{hex_text}', value=0x{val:02X}, dec={val})")
                else:
                    test_results.append(f"0x{addr:08X}: EMPTY RESPONSE")
            else:
                test_results.append(f"0x{addr:08X}: ERROR ({response.status_code})")
        except Exception as e:
            test_results.append(f"0x{addr:08X}: EXCEPTION ({e})")
    
    # Print test results
    print("\nMemory Access Test Results:")
    for result in test_results:
        print(f"  {result}")
    
    # Create reader
    reader = PokemonFireRedReader(client)
    
    if args.refresh > 0:
        try:
            while True:
                state = reader.read_game_state()
                print_game_state(state)
                time.sleep(args.refresh)
        except KeyboardInterrupt:
            print("\nExiting...")
    else:
        state = reader.read_game_state()
        print_game_state(state)
    
if __name__ == "__main__":
    main()
