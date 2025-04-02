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
    
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
    
    def read_byte(self, addresses):
        """Read one or multiple bytes at the specified addresses"""
        if isinstance(addresses, int):
            addresses = [addresses]
        
        params = []
        for addr in addresses:
            params.append(('addr', f"{addr:08X}"))
        
        response = requests.get(f"{self.base_url}/read_byte", params=params)
        if response.status_code == 200:
            # Convert hex string to bytes
            return bytes.fromhex(response.text)
        else:
            raise Exception(f"Failed to read bytes: {response.status_code}, {response.text}")
    
    def read_bytes(self, address, length):
        """Read multiple consecutive bytes starting at address"""
        addresses = [address + i for i in range(length)]
        return self.read_byte(addresses)
    
    def read_pointer(self, pointer_address):
        """Read a 32-bit pointer and return the address it points to"""
        pointer_bytes = self.read_bytes(pointer_address, 4)
        # GBA is little-endian
        return int.from_bytes(pointer_bytes, byteorder='little')
    
    def read_bytes_via_pointer(self, pointer_address, offset=0, length=1):
        """Read multiple consecutive bytes via a pointer"""
        target_address = self.read_pointer(pointer_address) + offset
        return self.read_bytes(target_address, length)
    
    def status(self):
        """Get the status of the emulator"""
        response = requests.get(f"{self.base_url}/status")
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get status: {response.status_code}, {response.text}")

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
    
    # These addresses are starting guesses based on research
    # They will likely need to be adjusted through testing
    ADDRESSES = {
        'party_data': 0x02024284,
        'party_size': 0x02024029,
        'player_ptr': 0x03005008,
        'trainer_ptr': 0x0300500C,
        'money_ptr': 0x0300500C,
        'money_offset': 0x0290,
        'player_name_offset': 0x0000,
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
            return None
    
    def _read_player_name(self) -> str:
        """Read the player's name"""
        try:
            # Try reading via pointer first
            name_bytes = self.client.read_bytes_via_pointer(
                self.ADDRESSES['trainer_ptr'],
                self.ADDRESSES['player_name_offset'],
                8  # Name length (guess)
            )
            return self._convert_text(name_bytes)
        except:
            # Fallback to fixed address if pointer fails
            try:
                name_bytes = self.client.read_bytes(0x02024C0A, 8)
                return self._convert_text(name_bytes)
            except:
                return "Unknown"
    
    def _read_coordinates(self) -> Tuple[int, int]:
        """Read player's current X,Y coordinates"""
        try:
            # Try reading via pointer first
            x_bytes = self.client.read_bytes_via_pointer(
                self.ADDRESSES['player_ptr'],
                0x000,  # X offset
                2       # 2 bytes
            )
            y_bytes = self.client.read_bytes_via_pointer(
                self.ADDRESSES['player_ptr'],
                0x002,  # Y offset
                2       # 2 bytes
            )
            
            x = int.from_bytes(x_bytes, byteorder='little')
            y = int.from_bytes(y_bytes, byteorder='little')
            return (x, y)
        except:
            # Fallback to fixed addresses if pointer fails
            try:
                x_bytes = self.client.read_bytes(0x02037318, 2)
                y_bytes = self.client.read_bytes(0x0203731A, 2)
                
                x = int.from_bytes(x_bytes, byteorder='little')
                y = int.from_bytes(y_bytes, byteorder='little')
                return (x, y)
            except:
                return (0, 0)
    
    def _read_location(self) -> str:
        """Read current location name"""
        try:
            # Try reading via pointer
            map_id_bytes = self.client.read_bytes_via_pointer(
                self.ADDRESSES['player_ptr'],
                0x005,  # Map ID offset
                1       # 1 byte
            )
            map_id = map_id_bytes[0]
            return f"Map #{map_id}"
        except:
            # Fallback to fixed address
            try:
                map_id_bytes = self.client.read_byte(0x02037354)
                map_id = map_id_bytes[0]
                return f"Map #{map_id}"
            except:
                return "Unknown Location"
    
    def _read_money(self) -> int:
        """Read the player's money"""
        try:
            # Try reading via pointer
            money_bytes = self.client.read_bytes_via_pointer(
                self.ADDRESSES['money_ptr'],
                self.ADDRESSES['money_offset'],
                4  # Money is 4 bytes
            )
            return int.from_bytes(money_bytes, byteorder='little')
        except:
            # Fallback to fixed address
            try:
                money_bytes = self.client.read_bytes(0x02025840, 4)
                return int.from_bytes(money_bytes, byteorder='little')
            except:
                return 0
    
    def _read_party_size(self) -> int:
        """Read number of Pokemon in party"""
        try:
            size_byte = self.client.read_byte(self.ADDRESSES['party_size'])
            return size_byte[0]
        except:
            # Fallback
            try:
                size_byte = self.client.read_byte(0x02024029)
                return size_byte[0]
            except:
                return 0
    
    def _read_party_pokemon(self) -> List[PokemonInfo]:
        """Read all Pokemon currently in the party"""
        party = []
        try:
            party_size = self._read_party_size()
            
            for i in range(party_size):
                # Calculate address for this Pokémon
                base_addr = self.ADDRESSES['party_data'] + (i * self.POKEMON_SIZE)
                
                try:
                    # Read species ID (might be at offset 0x20 after decryption)
                    species_id_bytes = self.client.read_bytes(base_addr + 0x08, 2)
                    species_id = int.from_bytes(species_id_bytes, byteorder='little')
                    
                    # Read nickname (around offset 0x08, but exact location may vary)
                    nickname_bytes = self.client.read_bytes(base_addr + 0x08, 10)
                    nickname = self._convert_text(nickname_bytes)
                    
                    # Read level (might be at offset 0x54)
                    level_byte = self.client.read_byte(base_addr + 0x54)
                    level = level_byte[0]
                    
                    # Read current HP (might be at offset 0x56)
                    current_hp_bytes = self.client.read_bytes(base_addr + 0x56, 2)
                    current_hp = int.from_bytes(current_hp_bytes, byteorder='little')
                    
                    # Read max HP (might be at offset 0x58)
                    max_hp_bytes = self.client.read_bytes(base_addr + 0x58, 2)
                    max_hp = int.from_bytes(max_hp_bytes, byteorder='little')
                    
                    # Read status (might be at offset 0x50)
                    status_bytes = self.client.read_bytes(base_addr + 0x50, 4)
                    status_value = int.from_bytes(status_bytes, byteorder='little')
                    status = StatusCondition(status_value).get_status_name()
                    
                    # Read moves (this is a simplification - would need decryption in reality)
                    # Move data might be around offset 0x28
                    moves = []
                    move_pp = []
                    for j in range(4):
                        move_offset = base_addr + 0x28 + (j * 2)
                        pp_offset = base_addr + 0x30 + j
                        
                        try:
                            move_id_bytes = self.client.read_bytes(move_offset, 2)
                            move_id = int.from_bytes(move_id_bytes, byteorder='little')
                            
                            if move_id != 0:
                                moves.append(f"Move #{move_id}")
                                
                                pp_byte = self.client.read_byte(pp_offset)
                                move_pp.append(pp_byte[0])
                        except:
                            # If we can't read a move, just skip it
                            pass
                    
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
                except Exception as e:
                    # If we fail to read one Pokémon, continue with others
                    print(f"Error reading Pokémon {i+1}: {e}")
        except Exception as e:
            print(f"Error reading party: {e}")
        
        return party
    
    def _read_items(self) -> List[Tuple[str, int]]:
        """Read all items in inventory (simplified)"""
        # This is a placeholder - would need proper implementation
        # Item storage in FireRed is more complex with multiple pouches
        items = []
        try:
            # Try a likely address for the item storage
            item_storage_addr = 0x02025C40
            
            # Read first few items as a test
            for i in range(10):
                try:
                    item_id_bytes = self.client.read_bytes(item_storage_addr + (i * 4), 2)
                    quantity_bytes = self.client.read_bytes(item_storage_addr + (i * 4) + 2, 2)
                    
                    item_id = int.from_bytes(item_id_bytes, byteorder='little')
                    quantity = int.from_bytes(quantity_bytes, byteorder='little')
                    
                    if item_id != 0 and quantity != 0:
                        items.append((f"Item #{item_id}", quantity))
                except:
                    # If we can't read an item, just skip it
                    pass
        except:
            pass
        
        return items
    
    def _convert_text(self, bytes_data):
        """
        Convert Pokémon FireRed text format to ASCII (simplified)
        
        This is a placeholder implementation. The actual text encoding 
        in FireRed is different and more complex.
        """
        result = ""
        for b in bytes_data:
            if b == 0xFF:  # Terminator (guess)
                break
            elif 0x80 <= b <= 0x99:  # A-Z (guess based on Red)
                result += chr(b - 0x80 + ord("A"))
            elif 0xA0 <= b <= 0xB9:  # a-z (guess)
                result += chr(b - 0xA0 + ord("a"))
            elif 0x00 <= b <= 0x09:  # Numbers 0-9 (guess)
                result += str(b)
            elif b == 0x00:  # Null terminator
                break
            elif 32 <= b <= 126:  # Printable ASCII
                result += chr(b)
            else:
                result += f"[{b:02X}]"  # Unknown character
                
        return result.strip()

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
    args = parser.parse_args()
    
    client = SkyEmuClient()

    reader = PokemonFireRedReader(client)
    state = reader.read_game_state()
    print_game_state(state)
    
if __name__ == "__main__":
    main()