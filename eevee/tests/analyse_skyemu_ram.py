#!/usr/bin/env python3
"""
simple_skyemu_analyzer.py - Simple tool for analyzing Pokémon RAM in SkyEmu

This script connects to SkyEmu's HTTP Control Server to extract basic
information about a running Pokémon game, including:
- Player's name
- Player's location
- Inventory
- Pokémon party (names, levels, HP, moves)
"""

import requests
import argparse
import time
import sys # Added for stderr printing
from enum import IntEnum, IntFlag
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any

# --- Enums and Dataclasses (remain the same) ---
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

# --- SkyEmuClient Class ---
class SkyEmuClient:
    """Client for communicating with SkyEmu's HTTP Control Server"""

    def __init__(self, base_url="http://localhost:8080", debug=False):
        self.base_url = base_url
        self.debug = debug
        # Use a session for potential connection reuse
        self.session = requests.Session()

    def log_debug(self, message):
        """Print debug messages if debugging is enabled"""
        if self.debug:
            print(f"DEBUG: {message}", file=sys.stderr) # Print debug to stderr

    def read_byte(self, addresses):
        """Read one or multiple bytes at the specified addresses.
           Returns bytes or None on failure for any byte."""
        if isinstance(addresses, int):
            addresses = [addresses]

        result = bytearray()

        for addr in addresses:
            addr_hex = f"{addr:X}" # Use uppercase hex, consistent with debug output
            params = {'addr': addr_hex}
            self.log_debug(f"Requesting byte at {addr:08X} (param: addr={addr_hex})")

            try:
                response = self.session.get(f"{self.base_url}/read_byte", params=params, timeout=1) # Add timeout
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                # *** THE FIX IS HERE ***
                # Trim whitespace AND potential null bytes from the response text
                hex_text = response.text.strip('\x00 \t\n\r')
                self.log_debug(f"Read from {addr:08X}: raw='{response.text}', cleaned='{hex_text}'")

                if len(hex_text) == 2: # Expect exactly 2 hex characters
                    try:
                        byte_val = int(hex_text, 16)
                        result.append(byte_val)
                        self.log_debug(f"Successfully parsed byte: 0x{byte_val:02X}")
                    except ValueError as e:
                        print(f"Error: Could not parse hex '{hex_text}' from {addr:08X}: {e}", file=sys.stderr)
                        return None # Indicate failure
                else:
                    print(f"Error: Unexpected response length '{hex_text}' (expected 2 hex chars) from {addr:08X}", file=sys.stderr)
                    return None # Indicate failure

            except requests.exceptions.RequestException as e:
                print(f"Error reading byte at {addr:08X}: {e}", file=sys.stderr)
                return None # Indicate failure
            except Exception as e:
                # Catch other potential errors during processing
                print(f"Unexpected error processing byte at {addr:08X}: {e}", file=sys.stderr)
                return None # Indicate failure

        return bytes(result)

    def read_bytes(self, address, length):
        """Read multiple consecutive bytes starting at address"""
        # Optimized: Read bytes one by one using the fixed read_byte
        data = bytearray()
        for i in range(length):
            byte_val = self.read_byte(address + i)
            if byte_val is None:
                self.log_debug(f"Failed to read byte at {address + i:08X}, stopping read_bytes.")
                return None # Propagate failure
            # read_byte now returns bytes, so access the first element
            if len(byte_val) == 1:
                 data.append(byte_val[0])
            else:
                 # This case should ideally not happen with the current read_byte logic
                 print(f"Error: read_byte returned unexpected data: {byte_val}", file=sys.stderr)
                 return None
        return bytes(data)

    def read_pointer(self, pointer_address):
        """Read a 32-bit pointer and return the address it points to"""
        try:
            pointer_bytes = self.read_bytes(pointer_address, 4)
            if pointer_bytes is None or len(pointer_bytes) < 4:
                print(f"Error reading pointer bytes at {pointer_address:08X}", file=sys.stderr)
                return None # Indicate failure
            # GBA is little-endian
            return int.from_bytes(pointer_bytes, byteorder='little')
        except Exception as e:
            print(f"Error processing pointer at {pointer_address:08X}: {e}", file=sys.stderr)
            return None

    def read_bytes_via_pointer(self, pointer_address, offset=0, length=1):
        """Read multiple consecutive bytes via a pointer"""
        try:
            target_address = self.read_pointer(pointer_address)
            if target_address is None:
                print(f"Error: Failed to resolve pointer at {pointer_address:08X}", file=sys.stderr)
                return None
            if target_address == 0:
                print(f"Warning: Null pointer encountered at {pointer_address:08X}", file=sys.stderr)
                # Depending on context, might want to return b'' or None. Let's return None for consistency.
                return None

            target_address += offset
            # Basic GBA RAM range check (adjust if needed for ROM/IO etc.)
            if not (0x02000000 <= target_address < 0x04000000): # EWRAM + IWRAM range
                print(f"Warning: Pointer {target_address:08X} (from {pointer_address:08X} + offset {offset}) seems out of valid RAM range", file=sys.stderr)
                # Decide if this is fatal. Let's try reading anyway but log warning.
                # return None

            data = self.read_bytes(target_address, length)
            if data is None:
                print(f"Error: Failed reading {length} bytes at pointed address {target_address:08X}", file=sys.stderr)
                return None
            return data
        except Exception as e:
            print(f"Error reading via pointer {pointer_address:08X}: {e}", file=sys.stderr)
            return None

    def status(self):
        """Get the status of the emulator"""
        try:
            response = self.session.get(f"{self.base_url}/status", timeout=1)
            response.raise_for_status()
            content = response.text.strip()
            if content:
                try:
                    # Attempt JSON parsing first
                    return response.json()
                except ValueError:
                    # Handle the non-JSON case seen in the output
                    print(f"Warning: Non-JSON response from status endpoint:\n'''{content}'''", file=sys.stderr)
                    # Create a dictionary mimicking expected structure or just raw data
                    status_data = {"raw_response": content}
                    # Attempt to parse key info from raw response if needed
                    if "MODE: RUN" in content: status_data["mode"] = "RUN"
                    if "ROM Loaded: true" in content: status_data["rom_loaded"] = True
                    # ... add more parsing if necessary
                    return status_data
            else:
                print("Warning: Status endpoint returned empty response", file=sys.stderr)
                # Return a default status indicating it's likely running if the request succeeded
                return {"status": "ok", "emulator": "running", "warning": "empty_response"}
        except requests.exceptions.RequestException as e:
            print(f"Error getting status: {e}", file=sys.stderr)
            return None # Indicate failure
        except Exception as e:
            print(f"Unexpected error getting status: {e}", file=sys.stderr)
            return None


# --- PokemonGameReader Base Class (remains the same) ---
class PokemonGameReader:
    """
    Base class for reading Pokémon game memory
    Subclasses will implement game-specific memory addresses and structures
    """
    def __init__(self, client: SkyEmuClient):
        self.client = client

    def read_game_state(self) -> Optional[GameState]: # Return Optional
        """Read the current game state (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement read_game_state")

    def _convert_text(self, bytes_data: bytes) -> str:
        """Convert Pokémon text format to string (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement _convert_text")


# --- PokemonFireRedReader Class ---
class PokemonFireRedReader(PokemonGameReader):
    """Reader for Pokémon FireRed/LeafGreen"""

    # Updated addresses based on Data Crystal official documentation
    ADDRESSES = {
        'party_count': 0x02024029,     # Number of Pokémon in party (part of PlayerData struct)
        'party_data': 0x02024284,      # Start of party Pokémon data array (6 * 100 bytes)
        
        # DMA-protected save blocks (from Data Crystal)
        'save_block_8_ptr': 0x03005008,  # Pointer to SaveBlock (map data)
        'save_block_1_ptr': 0x0300500C,  # Pointer to SaveBlock (personal data)
        'save_block_2_ptr': 0x03005010,  # Pointer to SaveBlock (box data)
        
        # Player coordinates (from SaveBlock map data)
        'player_coords_x_offset': 0x0000,   # X coordinate offset from SaveBlock8
        'player_coords_y_offset': 0x0002,   # Y coordinate offset from SaveBlock8
        
        # Map data (from SaveBlock map data)
        'map_id_offset': 0x0004,          # Current Map offset from SaveBlock8
        'map_bank_offset': 0x0005,        # Current Map Bank offset from SaveBlock8
        
        # Player data (from SaveBlock personal data)
        'player_name_offset': 0x0000,     # Player name offset from SaveBlock1 (8 bytes)
        
        # Money addresses (from SaveBlock map data, Data Crystal confirmed)
        'money_hidden_offset': 0x0218,    # Money_Hidden offset from SaveBlock8
        'money_key_offset': 0x0F20,       # Money encryption key offset from SaveBlock1

        # Item Pockets (Addresses relative to start of Save Block 1 at 0x02025840)
        # These offsets are added to the start address of Save Block 1
        'items_pocket_start_offset': 0x044C, # Offset for Items pocket count + data
        'key_items_pocket_start_offset': 0x04F0, # Offset for Key Items pocket count + data
        'pokeballs_pocket_start_offset': 0x0570, # Offset for Poke Balls pocket count + data
        'tms_hms_pocket_start_offset': 0x05E8, # Offset for TMs/HMs pocket count + data
        'berries_pocket_start_offset': 0x0740, # Offset for Berries pocket count + data

        # Base address for Save Block 1 (where money, items etc. are)
        'save_block_1': 0x02025840,
        'save_block_2': 0x0202402C, # Player Data including name, party count
        # Note: Save Block locations can sometimes shift slightly based on game events/checksums
    }

    POKEMON_SIZE = 100 # Size of a party Pokémon struct
    MAX_PARTY_SIZE = 6
    PLAYER_NAME_LENGTH = 7 # Max 7 chars + terminator

    # Item structure: 2 bytes ID, 2 bytes quantity
    ITEM_ENTRY_SIZE = 4

    # Text encoding map (Based on common English FR/LG)
    TEXT_MAP = {
        0x00: "<NULL>", 0x01: "À", 0x02: "Á", 0x03: "Â", 0x04: "Ç", 0x05: "È", 0x06: "É",
        0x07: "Ê", 0x08: "Ë", 0x09: "Ì", 0x0B: "Î", 0x0C: "Ï", 0x0D: "Ò", 0x0E: "Ó",
        0x0F: "Ô", 0x10: "Œ", 0x11: "Ù", 0x12: "Ú", 0x13: "Û", 0x14: "Ñ", 0x15: "ß",
        0x16: "à", 0x17: "á", 0x19: "ç", 0x1A: "è", 0x1B: "é", 0x1C: "ê", 0x1D: "ë",
        0x1E: "ì", 0x20: "î", 0x21: "ï", 0x22: "ò", 0x23: "ó", 0x24: "ô", 0x25: "œ",
        0x26: "ù", 0x27: "ú", 0x28: "û", 0x29: "ñ", 0x2A: "º", 0x2B: "ª", 0x2D: "&",
        0x2E: "+", 0x34: "[Lv]", 0x35: "=", 0x36: ";",
        # ... (add more if needed)
        0x51: "¿", 0x52: "¡", 0x53: "[PK]", 0x54: "[MN]", 0x55: "[PO]", 0x56: "[ké]",
        0x57: "[BL]", 0x58: "[OC]", 0x59: "[K]", 0x5A: "Í", 0x5B: "%", 0x5C: "(",
        0x5D: ")",
        # ...
        0x79: "0", 0x7A: "1", 0x7B: "2", 0x7C: "3", 0x7D: "4", 0x7E: "5", 0x7F: "6",
        0x80: "7", 0x81: "8", 0x82: "9",
        # ...
        0x88: "]", # Check this one
        0x90: "}",
        # ...
        0xA1: "!", 0xA2: "?", 0xA3: ".", 0xA4: "-", 0xA5: "·", 0xA6: "...", 0xA7: "«",
        0xA8: "»", 0xA9: "'", 0xAA: "'", 0xAB: "♂", 0xAC: "♀", 0xAD: "$", 0xAE: ",",
        0xAF: "×", 0xB0: "/",
        0xB1: "A", 0xB2: "B", 0xB3: "C", 0xB4: "D", 0xB5: "E", 0xB6: "F", 0xB7: "G",
        0xB8: "H", 0xB9: "I", 0xBA: "J", 0xBB: "K", 0xBC: "L", 0xBD: "M", 0xBE: "N",
        0xBF: "O", 0xC0: "P", 0xC1: "Q", 0xC2: "R", 0xC3: "S", 0xC4: "T", 0xC5: "U",
        0xC6: "V", 0xC7: "W", 0xC8: "X", 0xC9: "Y", 0xCA: "Z",
        0xCB: "a", 0xCC: "b", 0xCD: "c", 0xCE: "d", 0xCF: "e", 0xD0: "f", 0xD1: "g",
        0xD2: "h", 0xD3: "i", 0xD4: "j", 0xD5: "k", 0xD6: "l", 0xD7: "m", 0xD8: "n",
        0xD9: "o", 0xDA: "p", 0xDB: "q", 0xDC: "r", 0xDD: "s", 0xDE: "t", 0xDF: "u",
        0xE0: "v", 0xE1: "w", 0xE2: "x", 0xE3: "y", 0xE4: "z",
        # ...
        0xE9: "<RIVAL>",
        0xEE: "'",
        0xEF: "'",
        # ...
        0xF0: ":",
        # ...
        0xF6: "[PLAYER]", # Example control code
        0xF7: "[PKMN]",   # Example control code
        0xFB: " ",        # Space
        0xFF: "<TERM>"    # Terminator
    }

    # Pokemon species names (Gen 1-3 up to FireRed/LeafGreen)
    SPECIES_NAMES = {
        0: "???", 1: "Bulbasaur", 2: "Ivysaur", 3: "Venusaur", 4: "Charmander", 5: "Charmeleon",
        6: "Charizard", 7: "Squirtle", 8: "Wartortle", 9: "Blastoise", 10: "Caterpie", 11: "Metapod",
        12: "Butterfree", 13: "Weedle", 14: "Kakuna", 15: "Beedrill", 16: "Pidgey", 17: "Pidgeotto",
        18: "Pidgeot", 19: "Rattata", 20: "Raticate", 21: "Spearow", 22: "Fearow", 23: "Ekans",
        24: "Arbok", 25: "Pikachu", 26: "Raichu", 27: "Sandshrew", 28: "Sandslash", 29: "Nidoran♀",
        30: "Nidorina", 31: "Nidoqueen", 32: "Nidoran♂", 33: "Nidorino", 34: "Nidoking", 35: "Clefairy",
        36: "Clefable", 37: "Vulpix", 38: "Ninetales", 39: "Jigglypuff", 40: "Wigglytuff", 41: "Zubat",
        42: "Golbat", 43: "Oddish", 44: "Gloom", 45: "Vileplume", 46: "Paras", 47: "Parasect",
        48: "Venonat", 49: "Venomoth", 50: "Diglett", 51: "Dugtrio", 52: "Meowth", 53: "Persian",
        54: "Psyduck", 55: "Golduck", 56: "Mankey", 57: "Primeape", 58: "Growlithe", 59: "Arcanine",
        60: "Poliwag", 61: "Poliwhirl", 62: "Poliwrath", 63: "Abra", 64: "Kadabra", 65: "Alakazam",
        66: "Machop", 67: "Machoke", 68: "Machamp", 69: "Bellsprout", 70: "Weepinbell", 71: "Victreebel",
        72: "Tentacool", 73: "Tentacruel", 74: "Geodude", 75: "Graveler", 76: "Golem", 77: "Ponyta",
        78: "Rapidash", 79: "Slowpoke", 80: "Slowbro", 81: "Magnemite", 82: "Magneton", 83: "Farfetch'd",
        84: "Doduo", 85: "Dodrio", 86: "Seel", 87: "Dewgong", 88: "Grimer", 89: "Muk", 90: "Shellder",
        91: "Cloyster", 92: "Gastly", 93: "Haunter", 94: "Gengar", 95: "Onix", 96: "Drowzee",
        97: "Hypno", 98: "Krabby", 99: "Kingler", 100: "Voltorb", 101: "Electrode", 102: "Exeggcute",
        103: "Exeggutor", 104: "Cubone", 105: "Marowak", 106: "Hitmonlee", 107: "Hitmonchan", 108: "Lickitung",
        109: "Koffing", 110: "Weezing", 111: "Rhyhorn", 112: "Rhydon", 113: "Chansey", 114: "Tangela",
        115: "Kangaskhan", 116: "Horsea", 117: "Seadra", 118: "Goldeen", 119: "Seaking", 120: "Staryu",
        121: "Starmie", 122: "Mr. Mime", 123: "Scyther", 124: "Jynx", 125: "Electabuzz", 126: "Magmar",
        127: "Pinsir", 128: "Tauros", 129: "Magikarp", 130: "Gyarados", 131: "Lapras", 132: "Ditto",
        133: "Eevee", 134: "Vaporeon", 135: "Jolteon", 136: "Flareon", 137: "Porygon", 138: "Omanyte",
        139: "Omastar", 140: "Kabuto", 141: "Kabutops", 142: "Aerodactyl", 143: "Snorlax", 144: "Articuno",
        145: "Zapdos", 146: "Moltres", 147: "Dratini", 148: "Dragonair", 149: "Dragonite", 150: "Mewtwo",
        151: "Mew"
    }

    # Pokemon experience growth rate tables (Gen 3)
    # Each entry represents experience needed to reach that level
    EXPERIENCE_TABLES = {
        'fast': [0, 6, 21, 51, 100, 172, 274, 409, 583, 800, 1064, 1382, 1757, 2195, 2700, 3276, 3930, 4665, 5487, 6400, 7408, 8518, 9733, 11059, 12500, 14060, 15746, 17561, 19511, 21600, 23832, 26214, 28749, 31443, 34300, 37324, 40522, 43897, 47455, 51200, 55136, 59270, 63605, 68147, 72900, 77868, 83058, 88473, 94119, 100000, 106120, 112486, 119101, 125971, 133100, 140492, 148154, 156089, 164303, 172800, 181584, 190662, 200037, 209715, 219700, 229996, 240610, 251545, 262807, 274400, 286328, 298598, 311213, 324179, 337500, 351180, 365226, 379641, 394431, 409600, 425152, 441094, 457429, 474163, 491300, 508844, 526802, 545177, 563975, 583200, 602856, 622950, 643485, 664467, 685900, 707788, 730138, 752953, 776239, 800000],
        'medium_fast': [0, 8, 27, 64, 125, 216, 343, 512, 729, 1000, 1331, 1728, 2197, 2744, 3375, 4096, 4913, 5832, 6859, 8000, 9261, 10648, 12167, 13824, 15625, 17576, 19683, 21952, 24389, 27000, 29791, 32768, 35937, 39304, 42875, 46656, 50653, 54872, 59319, 64000, 68921, 74088, 79507, 85184, 91125, 97336, 103823, 110592, 117649, 125000, 132651, 140608, 148877, 157464, 166375, 175616, 185193, 195112, 205379, 216000, 226981, 238328, 250047, 262144, 274625, 287496, 300763, 314432, 328509, 343000, 357911, 373248, 389017, 405224, 421875, 438976, 456533, 474552, 493039, 512000, 531441, 551368, 571787, 592704, 614125, 636056, 658503, 681472, 704969, 729000, 753571, 778688, 804357, 830584, 857375, 884736, 912673, 941192, 970299, 1000000],
        'medium_slow': [0, 9, 57, 96, 135, 179, 236, 314, 419, 560, 742, 973, 1261, 1612, 2035, 2535, 3120, 3798, 4575, 5460, 6458, 7577, 8825, 10208, 11735, 13411, 15244, 17242, 19411, 21760, 24294, 27021, 29949, 33084, 36435, 40007, 43808, 47846, 52127, 56660, 61450, 66505, 71833, 77440, 83335, 89523, 96012, 102810, 109923, 117360, 125126, 133229, 141677, 150476, 159635, 169159, 179056, 189334, 199999, 211060, 222522, 234393, 246681, 259392, 272535, 286115, 300140, 314618, 329555, 344960, 360838, 377197, 394043, 411384, 429235, 447591, 466464, 485862, 505791, 526260, 547274, 568841, 590969, 613664, 636935, 660787, 685228, 710266, 735907, 762160, 789030, 816525, 844653, 873420, 902835, 932903, 963632, 995030, 1027103, 1059860],
        'slow': [0, 10, 33, 80, 156, 270, 428, 640, 911, 1250, 1663, 2160, 2746, 3430, 4218, 5120, 6141, 7290, 8573, 10000, 11576, 13310, 15208, 17280, 19531, 21970, 24603, 27440, 30486, 33750, 37238, 40960, 44921, 49130, 53593, 58320, 63316, 68590, 74148, 80000, 86151, 92610, 99383, 106480, 113906, 121670, 129778, 138240, 147061, 156250, 165813, 175760, 186096, 196830, 207968, 219520, 231491, 243890, 256723, 270000, 283726, 297910, 312558, 327680, 343281, 359370, 375953, 393040, 410636, 428750, 447388, 466560, 486271, 506530, 527343, 548720, 570666, 593190, 616298, 640000, 664301, 689210, 714733, 740880, 767656, 795070, 823128, 851840, 881211, 911250, 941963, 973360, 1005446, 1038230, 1071718, 1105920, 1140841, 1176490, 1212873, 1250000],
        'erratic': [0, 15, 52, 122, 237, 406, 637, 942, 1326, 1800, 2369, 3041, 3822, 4719, 5737, 6881, 8155, 9564, 11111, 12800, 14632, 16610, 18737, 21012, 23437, 26012, 28737, 31610, 34632, 37800, 41111, 44564, 48155, 51881, 55737, 59719, 63822, 68041, 72369, 76800, 81326, 85942, 90637, 95406, 100237, 105122, 110052, 115015, 120001, 125000, 131324, 137795, 144410, 151165, 158056, 165079, 172229, 179503, 186894, 194400, 202013, 209728, 217540, 225443, 233431, 241496, 249633, 257834, 267406, 276458, 286328, 296358, 305767, 316074, 326531, 336255, 346965, 357812, 367807, 378880, 390077, 400293, 411686, 423190, 433572, 445239, 457001, 467489, 479378, 491346, 501878, 513934, 526049, 536557, 548720, 560922, 571333, 583539, 591882, 600000],
        'fluctuating': [0, 4, 13, 32, 65, 112, 178, 276, 393, 540, 745, 967, 1230, 1591, 1957, 2457, 3046, 3732, 4526, 5440, 6482, 7666, 9003, 10506, 12187, 14060, 16140, 18439, 20974, 23760, 26811, 30146, 33780, 37731, 42017, 46656, 50653, 55969, 60505, 66560, 71677, 78533, 84277, 91998, 98415, 107069, 114205, 123863, 131766, 142500, 151222, 163105, 172697, 185807, 196322, 210739, 222231, 238036, 250562, 267840, 281456, 300293, 315059, 335544, 351520, 373744, 390991, 415050, 433631, 459620, 479600, 507617, 529063, 559209, 582187, 614566, 639146, 673863, 700115, 737280, 765275, 804997, 834809, 877201, 908905, 954084, 987754, 1035837, 1071552, 1122660, 1160499, 1214753, 1254796, 1312322, 1354652, 1415577, 1460276, 1524731, 1571884, 1640000]
    }
    
    # Pokemon species to growth rate mapping (Gen 1-3 Pokemon)
    # Most Pokemon use medium_fast growth, so we'll define exceptions
    SPECIES_GROWTH_RATES = {}
    
    # Initialize with medium_fast as default for all known Pokemon (1-386)
    for i in range(1, 387):
        SPECIES_GROWTH_RATES[i] = 'medium_fast'
    
    # Fast growth Pokemon (mainly Bug types and some Normal types)
    fast_growth_pokemon = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
    for pokemon_id in fast_growth_pokemon:
        SPECIES_GROWTH_RATES[pokemon_id] = 'fast'

    # Common move names (subset)
    MOVE_NAMES = {
        0: "---", 1: "Pound", 2: "Karate Chop", 3: "DoubleSlap", 4: "Comet Punch", 5: "Mega Punch",
        6: "Pay Day", 7: "Fire Punch", 8: "Ice Punch", 9: "ThunderPunch", 10: "Scratch", 11: "ViceGrip",
        12: "Guillotine", 13: "Razor Wind", 14: "Swords Dance", 15: "Cut", 16: "Gust", 17: "Wing Attack",
        18: "Whirlwind", 19: "Fly", 20: "Bind", 21: "Slam", 22: "Vine Whip", 23: "Stomp", 24: "Double Kick",
        25: "Mega Kick", 26: "Jump Kick", 27: "Rolling Kick", 28: "Sand Attack", 29: "Headbutt", 30: "Horn Attack",
        31: "Fury Attack", 32: "Horn Drill", 33: "Tackle", 34: "Body Slam", 35: "Wrap", 36: "Take Down",
        37: "Thrash", 38: "Double-Edge", 39: "Tail Whip", 40: "Poison Sting", 41: "Twineedle", 42: "Pin Missile",
        43: "Leer", 44: "Bite", 45: "Growl", 46: "Roar", 47: "Sing", 48: "Supersonic", 49: "SonicBoom",
        50: "Disable", 51: "Acid", 52: "Ember", 53: "Flamethrower", 54: "Mist", 55: "Water Gun",
        56: "Hydro Pump", 57: "Surf", 58: "Ice Beam", 59: "Blizzard", 60: "Psybeam", 61: "BubbleBeam",
        62: "Aurora Beam", 63: "Hyper Beam", 64: "Peck", 65: "Drill Peck", 66: "Submission", 67: "Low Kick",
        68: "Counter", 69: "Seismic Toss", 70: "Strength", 71: "Absorb", 72: "Mega Drain", 73: "Leech Seed",
        74: "Growth", 75: "Razor Leaf", 76: "SolarBeam", 77: "PoisonPowder", 78: "Stun Spore", 79: "Sleep Powder",
        80: "Petal Dance", 81: "String Shot", 82: "Dragon Rage", 83: "Fire Spin", 84: "ThunderShock",
        85: "Thunderbolt", 86: "Thunder Wave", 87: "Thunder", 88: "Rock Throw", 89: "Earthquake", 90: "Fissure",
        91: "Dig", 92: "Toxic", 93: "Confusion", 94: "Psychic", 95: "Hypnosis", 96: "Meditate",
        97: "Agility", 98: "Quick Attack", 99: "Rage", 100: "Teleport", 101: "Night Shade", 102: "Mimic",
        103: "Screech", 104: "Double Team", 105: "Recover", 106: "Harden", 107: "Minimize", 108: "SmokeScreen",
        109: "Confuse Ray", 110: "Withdraw", 111: "Defense Curl", 112: "Barrier", 113: "Light Screen", 114: "Haze",
        115: "Reflect", 116: "Focus Energy", 117: "Bide", 118: "Metronome", 119: "Mirror Move", 120: "Selfdestruct",
        121: "Egg Bomb", 122: "Lick", 123: "Smog", 124: "Sludge", 125: "Bone Club", 126: "Fire Blast",
        127: "Waterfall", 128: "Clamp", 129: "Swift", 130: "Skull Bash", 131: "Spike Cannon", 132: "Constrict",
        133: "Amnesia", 134: "Kinesis", 135: "Softboiled", 136: "Hi Jump Kick", 137: "Glare", 138: "Dream Eater",
        139: "Poison Gas", 140: "Barrage", 141: "Leech Life", 142: "Lovely Kiss", 143: "Sky Attack", 144: "Transform",
        145: "Bubble", 146: "Dizzy Punch", 147: "Spore", 148: "Flash", 149: "Psywave", 150: "Splash",
        151: "Acid Armor", 152: "Crabhammer", 153: "Explosion", 154: "Fury Swipes", 155: "Bonemerang", 156: "Rest",
        157: "Rock Slide", 158: "Hyper Fang", 159: "Sharpen", 160: "Conversion", 161: "Tri Attack", 162: "Super Fang",
        163: "Slash", 164: "Substitute", 165: "Struggle"
    }

    def read_game_state(self) -> Optional[GameState]: # Return Optional
        """Read the current game state for Pokémon FireRed/LeafGreen"""
        try:
            # Read interdependent data first
            party_size = self._read_party_size()
            if party_size is None: return None # Critical failure

            money = self._read_money()
            if money is None: money = -1 # Assign default if fails but continue

            player_name = self._read_player_name()
            x, y = self._read_coordinates()
            location = self._read_location() # Depends on coords read

            # Read complex structures
            party = self._read_party_pokemon(party_size) # Pass known size
            items = self._read_all_item_pockets()

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
            # Log the specific error during game state assembly
            print(f"Error assembling game state: {e}", file=sys.stderr)
            # Optionally log traceback: import traceback; traceback.print_exc()
            return None

    def get_compact_game_state(self) -> Dict[str, Any]:
        """
        Get standardized compact game state for visual analysis integration
        
        Returns:
            Dict with complete RAM data structure for AI decision-making
        """
        try:
            # Get full game state using existing method
            game_state = self.read_game_state()
            if not game_state:
                return {
                    "ram_available": False,
                    "error": "Failed to read game state"
                }
            
            # Extract map bank and ID from location string
            map_bank = None
            map_id = None
            location_name = game_state.location
            
            # Parse location format: "Location Name [Bank X, Map Y]"
            import re
            bank_match = re.search(r'Bank (\d+)', location_name)
            map_match = re.search(r'Map (\d+)', location_name)
            
            if bank_match and map_match:
                map_bank = int(bank_match.group(1))
                map_id = int(map_match.group(1))
                # Extract clean location name (before the bracket)
                clean_location = location_name.split(' [Bank')[0]
            else:
                clean_location = location_name
            
            # Convert Pokemon party to compact format for AI decision-making
            party_data = []
            for i, pokemon in enumerate(game_state.party):
                pokemon_info = {
                    "slot": i + 1,
                    "species_id": pokemon.species_id,
                    "nickname": pokemon.nickname,
                    "level": pokemon.level,
                    "current_hp": pokemon.current_hp,
                    "max_hp": pokemon.max_hp,
                    "hp_percentage": round((pokemon.current_hp / pokemon.max_hp * 100), 1) if pokemon.max_hp > 0 else 0,
                    "status": pokemon.status,
                    "is_fainted": pokemon.current_hp == 0,
                    "moves": pokemon.moves,
                    "move_pp": pokemon.move_pp
                }
                
                # Add battle readiness assessment
                if pokemon.current_hp == 0:
                    pokemon_info["battle_status"] = "fainted"
                elif pokemon.current_hp < (pokemon.max_hp * 0.2):
                    pokemon_info["battle_status"] = "critical_hp"
                elif pokemon.current_hp < (pokemon.max_hp * 0.5):
                    pokemon_info["battle_status"] = "low_hp"
                elif pokemon.status != "OK":
                    pokemon_info["battle_status"] = "status_condition"
                else:
                    pokemon_info["battle_status"] = "healthy"
                
                party_data.append(pokemon_info)
            
            # Calculate party summary for quick AI assessment
            total_pokemon = len(party_data)
            healthy_pokemon = len([p for p in party_data if p["battle_status"] == "healthy"])
            fainted_pokemon = len([p for p in party_data if p["is_fainted"]])
            critical_pokemon = len([p for p in party_data if p["battle_status"] in ["critical_hp", "low_hp"]])
            
            party_summary = {
                "total_pokemon": total_pokemon,
                "healthy_pokemon": healthy_pokemon,
                "fainted_pokemon": fainted_pokemon,
                "critical_pokemon": critical_pokemon,
                "needs_healing": critical_pokemon > 0 or fainted_pokemon > 0,
                "party_health_status": "critical" if fainted_pokemon >= total_pokemon - 1 else 
                                    "poor" if critical_pokemon > healthy_pokemon else
                                    "good" if healthy_pokemon >= total_pokemon * 0.7 else "fair"
            }
            
            # Convert items to compact format
            items_data = []
            for item_name, quantity in game_state.items:
                if quantity > 0:  # Only include items we have
                    items_data.append({
                        "name": item_name,
                        "quantity": quantity
                    })
            
            # Return comprehensive game state for AI decision-making
            return {
                "ram_available": True,
                "timestamp": time.time(),
                
                # Location data
                "location": {
                    "map_bank": map_bank,
                    "map_id": map_id,
                    "x": game_state.x,
                    "y": game_state.y,
                    "location_name": clean_location,
                    "raw_location": location_name
                },
                
                # Player data
                "player": {
                    "name": game_state.player_name,
                    "money": game_state.money if game_state.money >= 0 else "unknown"
                },
                
                # Pokemon party data (complete for battle decisions)
                "party": party_data,
                "party_summary": party_summary,
                
                # Items data
                "items": items_data,
                "item_count": len(items_data),
                
                # Quick status for AI prompts
                "quick_status": {
                    "needs_healing": party_summary["needs_healing"],
                    "at_pokemon_center": "pokemon center" in clean_location.lower() or "pokecenter" in clean_location.lower(),
                    "in_battle": False,  # This would need additional detection logic
                    "can_battle": healthy_pokemon > 0,
                    "emergency_situation": fainted_pokemon >= total_pokemon - 1
                }
            }
            
        except Exception as e:
            return {
                "ram_available": False,
                "error": f"RAM analysis failed: {str(e)}",
                "timestamp": time.time()
            }

    def _read_player_name(self) -> str:
        """Read the player's name using Data Crystal documented address"""
        try:
            # Read SaveBlock1 pointer (personal data) for player name
            save_block_1_addr = self.client.read_pointer(self.ADDRESSES['save_block_1_ptr'])
            if save_block_1_addr is None:
                self.client.log_debug("Failed to read SaveBlock1 pointer for player name")
                return "Pointer Error"
            
            # Read player name from SaveBlock1 + offset (Data Crystal: Name = [0x0300500C] + 0x0000, 8 bytes)
            name_addr = save_block_1_addr + self.ADDRESSES['player_name_offset']
            name_bytes = self.client.read_bytes(name_addr, 8)  # 8 bytes as per Data Crystal
            if name_bytes is None:
                self.client.log_debug(f"Failed to read player name bytes from {name_addr:08X}")
                return "Read Error"
            
            self.client.log_debug(f"Read player name from {name_addr:08X}: {name_bytes.hex()}")
            return self._convert_text(name_bytes)
        except Exception as e:
            print(f"Error processing player name: {e}", file=sys.stderr)
            return "Processing Error"

    def _read_coordinates(self) -> Tuple[int, int]:
        """Read player's current X,Y coordinates via SaveBlock8 pointer using Data Crystal addresses"""
        try:
            # Read SaveBlock8 pointer first
            save_block_8_addr = self.client.read_pointer(self.ADDRESSES['save_block_8_ptr'])
            if save_block_8_addr is None:
                self.client.log_debug("Failed to read SaveBlock8 pointer")
                return (0, 0)
            
            self.client.log_debug(f"SaveBlock8 address: 0x{save_block_8_addr:08X}")
            
            # Read X coordinate (Data Crystal: X = [0x03005008] + 0x000)
            x_addr = save_block_8_addr + self.ADDRESSES['player_coords_x_offset']
            x_bytes = self.client.read_bytes(x_addr, 2)
            if x_bytes is None or len(x_bytes) < 2:
                self.client.log_debug(f"Failed to read X coordinate bytes at {x_addr:08X}")
                return (0, 0)
            
            # Read Y coordinate (Data Crystal: Y = [0x03005008] + 0x002)
            y_addr = save_block_8_addr + self.ADDRESSES['player_coords_y_offset']
            y_bytes = self.client.read_bytes(y_addr, 2)
            if y_bytes is None or len(y_bytes) < 2:
                self.client.log_debug(f"Failed to read Y coordinate bytes at {y_addr:08X}")
                return (0, 0)

            # Read as unsigned 16-bit integers, little-endian
            x = int.from_bytes(x_bytes, byteorder='little', signed=False)
            y = int.from_bytes(y_bytes, byteorder='little', signed=False)
            self.client.log_debug(f"Read coordinates from 0x{x_addr:08X},0x{y_addr:08X}: X={x}, Y={y}")
            return (x, y)
        except Exception as e:
            print(f"Error reading/processing coordinates: {e}", file=sys.stderr)
            return (-1, -1)

    def _read_location(self) -> str:
        """Read current location (Map Bank and Map ID) via SaveBlock8 pointer using Data Crystal addresses"""
        try:
            # Read SaveBlock8 pointer first
            save_block_8_addr = self.client.read_pointer(self.ADDRESSES['save_block_8_ptr'])
            if save_block_8_addr is None:
                self.client.log_debug("Failed to read SaveBlock8 pointer for location")
                return "Unknown Location (Pointer Error)"
            
            # Read map ID and bank from SaveBlock8 (Data Crystal: Map=[0x03005008]+0x0004, Bank=[0x03005008]+0x0005)
            map_id_addr = save_block_8_addr + self.ADDRESSES['map_id_offset']
            bank_addr = save_block_8_addr + self.ADDRESSES['map_bank_offset']
            
            map_id_byte = self.client.read_byte(map_id_addr)
            bank_byte = self.client.read_byte(bank_addr)

            if bank_byte is None or map_id_byte is None:
                self.client.log_debug("Failed to read map bank or map ID bytes.")
                return "Unknown Location (Read Error)"

            map_id = map_id_byte[0]
            bank = bank_byte[0]
            self.client.log_debug(f"Read location from 0x{map_id_addr:08X},0x{bank_addr:08X}: Bank={bank}, MapID={map_id}")

            # Map name lookup dictionary - CONFIRMED LOCATIONS ONLY
            # Only includes locations we've verified through actual gameplay
            map_names = {
                # CONFIRMED: Bank 1 
                (1, 0): "Viridian Forest",  # ✅ CONFIRMED via actual gameplay
                
                # CONFIRMED: Bank 3 (Major Cities/Areas)
                (3, 2): "Pewter City",  # ✅ CONFIRMED via actual gameplay
                
                # CONFIRMED: Bank 6 (Pokemon Centers) 
                (6, 5): "Pokemon Center",  # ✅ CONFIRMED via actual gameplay - generic interior
                
                # CONFIRMED: Bank 15 (Routes)
                (15, 3): "Route 2",  # ✅ CONFIRMED via actual gameplay
                
                # NOTE: All other locations removed until confirmed by actual gameplay
                # This prevents AI confusion from incorrect location names
            }
            
            location_name = map_names.get((bank, map_id), f"Map #{bank}-{map_id}")
            # Always show the raw bank/map ID for debugging
            return f"{location_name} [Bank {bank}, Map {map_id}]"
        except Exception as e:
            print(f"Error reading/processing location: {e}", file=sys.stderr)
            return "Unknown Location (Processing Error)"

    def is_in_pokemon_center(self) -> bool:
        """Check if the player is currently in a Pokemon Center"""
        try:
            save_block_8_addr = self.client.read_pointer(self.ADDRESSES['save_block_8_ptr'])
            if save_block_8_addr is None:
                return False
            
            bank_addr = save_block_8_addr + self.ADDRESSES['map_bank_offset']
            map_id_addr = save_block_8_addr + self.ADDRESSES['map_id_offset']
            
            bank_byte = self.client.read_byte(bank_addr)
            map_id_byte = self.client.read_byte(map_id_addr)

            if bank_byte is None or map_id_byte is None:
                return False

            bank = bank_byte[0]
            map_id = map_id_byte[0]
            
            # Pokemon Centers are in bank 6 (based on actual game data)
            if bank == 6:
                return True
            
            return False
        except Exception:
            return False

    def _read_money(self) -> Optional[int]:
        """Read the player's money using Data Crystal documented addresses"""
        try:
            # Read SaveBlock8 pointer (map data) for hidden money value
            save_block_8_addr = self.client.read_pointer(self.ADDRESSES['save_block_8_ptr'])
            if save_block_8_addr is None:
                self.client.log_debug("Failed to read SaveBlock8 pointer for money")
                return None
            
            # Read SaveBlock1 pointer (personal data) for encryption key
            save_block_1_addr = self.client.read_pointer(self.ADDRESSES['save_block_1_ptr'])
            if save_block_1_addr is None:
                self.client.log_debug("Failed to read SaveBlock1 pointer for money key")
                return None
            
            self.client.log_debug(f"SaveBlock8 address: 0x{save_block_8_addr:08X}")
            self.client.log_debug(f"SaveBlock1 address: 0x{save_block_1_addr:08X}")
            
            # 1. Read the encrypted money value from SaveBlock8 + offset (Data Crystal: Money_Hidden = [0x03005008] + 0x0218)
            money_addr = save_block_8_addr + self.ADDRESSES['money_hidden_offset']
            encrypted_money_bytes = self.client.read_bytes(money_addr, 4)
            if encrypted_money_bytes is None or len(encrypted_money_bytes) < 4:
                self.client.log_debug("Failed to read encrypted money bytes.")
                return None
            encrypted_money = int.from_bytes(encrypted_money_bytes, byteorder='little')
            self.client.log_debug(f"Read encrypted money from 0x{money_addr:08X}: 0x{encrypted_money:08X}")

            # 2. Read the XOR key from SaveBlock1 + key offset (Data Crystal: Key = [0x0300500C] + 0x0F20)
            key_addr = save_block_1_addr + self.ADDRESSES['money_key_offset']
            key_bytes = self.client.read_bytes(key_addr, 4)
            if key_bytes is None or len(key_bytes) < 4:
                self.client.log_debug("Failed to read money encryption key.")
                return None
            
            key = int.from_bytes(key_bytes, byteorder='little')
            self.client.log_debug(f"Read money key from 0x{key_addr:08X}: 0x{key:08X}")

            # 3. Decrypt using XOR (Data Crystal: Money = Money_Hidden XOR Key)
            decrypted_money = encrypted_money ^ key
            self.client.log_debug(f"Decrypted money: {decrypted_money} (0x{decrypted_money:08X})")

            # Sanity check - money shouldn't exceed 999999
            if 0 <= decrypted_money <= 999999:
                return decrypted_money
            else:
                self.client.log_debug(f"Money value {decrypted_money} outside valid range, returning 0")
                return 0

        except Exception as e:
            print(f"Error reading/decrypting money: {e}", file=sys.stderr)
            return None

    def _read_party_size(self) -> Optional[int]:
        """Read number of Pokemon in party"""
        try:
            size_byte = self.client.read_byte(self.ADDRESSES['party_count'])
            if size_byte is None:
                print("Error: Failed to read party size byte.", file=sys.stderr)
                return None

            # read_byte returns bytes, access the first element
            party_size = size_byte[0]
            self.client.log_debug(f"Read party size byte value: {party_size} (0x{party_size:02X})")

            if 0 <= party_size <= self.MAX_PARTY_SIZE:
                self.client.log_debug(f"Valid party size: {party_size}")
                return party_size
            else:
                # This could indicate a memory reading issue or corrupted save data
                print(f"Warning: Invalid party size read: {party_size}. Assuming 0.", file=sys.stderr)
                return 0 # Return a safe default

        except IndexError:
             print("Error: Received empty data when reading party size.", file=sys.stderr)
             return None
        except Exception as e:
            print(f"Error processing party size: {e}", file=sys.stderr)
            return None

    def _decrypt_pokemon_data(self, poke_data: bytes) -> bytes:
        """Decrypt Pokemon data using PID and OT ID, handling substructure ordering"""
        if len(poke_data) < self.POKEMON_SIZE:
            return poke_data
        
        try:
            # Extract PID and OT ID from the first 8 bytes (these are unencrypted)
            personality_id = int.from_bytes(poke_data[0:4], byteorder='little')
            ot_id = int.from_bytes(poke_data[4:8], byteorder='little')
            
            # Generate decryption key (PID XOR OT ID)
            key = personality_id ^ ot_id
            self.client.log_debug(f"Decryption key: PID(0x{personality_id:08X}) ^ OT(0x{ot_id:08X}) = 0x{key:08X}")
            
            # Decrypt the data section (bytes 32-79, the 48 encrypted bytes)
            decrypted_data = bytearray(poke_data)
            for i in range(32, 80, 4):  # Decrypt 4 bytes at a time
                if i + 4 <= len(poke_data):
                    encrypted_word = int.from_bytes(poke_data[i:i+4], byteorder='little')
                    decrypted_word = encrypted_word ^ key
                    decrypted_data[i:i+4] = decrypted_word.to_bytes(4, byteorder='little')
            
            # Now handle substructure ordering based on PID % 24
            # The 48 bytes are arranged as 4 substructures of 12 bytes each
            # Order depends on personality_id % 24
            
            # Substructure order table (G=Growth, A=Attacks, E=EVs, M=Misc)
            substructure_orders = [
                'GAEM', 'GAME', 'GEAM', 'GEMA', 'GMAE', 'GMEA',
                'AGEM', 'AGME', 'AEGM', 'AEMG', 'AMGE', 'AMEG',
                'EGAM', 'EGMA', 'EAGM', 'EAMG', 'EMGA', 'EMAG',
                'MGAE', 'MGEA', 'MAGE', 'MAEG', 'MEGA', 'MEAG'
            ]
            
            order = substructure_orders[personality_id % 24]
            self.client.log_debug(f"Substructure order for PID % 24 = {personality_id % 24}: {order}")
            
            # Extract the four 12-byte substructures in their encrypted order
            substruct_data = {}
            for i, substruct_type in enumerate(order):
                start_offset = 32 + (i * 12)
                substruct_data[substruct_type] = decrypted_data[start_offset:start_offset + 12]
            
            # Rearrange into correct order: GAEM
            correct_order = 'GAEM'
            reordered_data = bytearray(poke_data)  # Start with original
            for i, substruct_type in enumerate(correct_order):
                start_offset = 32 + (i * 12)
                reordered_data[start_offset:start_offset + 12] = substruct_data[substruct_type]
            
            return bytes(reordered_data)
        except Exception as e:
            self.client.log_debug(f"Error decrypting Pokemon data: {e}")
            return poke_data  # Return original data if decryption fails

    def _read_party_pokemon(self, party_size: int) -> List[PokemonInfo]:
        """Read all Pokemon currently in the party, given the known size"""
        party = []
        if not (0 < party_size <= self.MAX_PARTY_SIZE):
            self.client.log_debug(f"Skipping party read due to invalid size: {party_size}")
            return [] # Return empty list if size is invalid/zero

        try:
            # Read the entire party block at once for potentially better performance
            base_party_addr = self.ADDRESSES['party_data']
            total_party_bytes = party_size * self.POKEMON_SIZE
            party_block = self.client.read_bytes(base_party_addr, total_party_bytes)

            if party_block is None or len(party_block) < total_party_bytes:
                print(f"Error: Failed to read sufficient party data (needed {total_party_bytes}, got {len(party_block) if party_block else 0})", file=sys.stderr)
                return [] # Cannot proceed

            for i in range(party_size):
                try:
                    poke_offset = i * self.POKEMON_SIZE
                    poke_data = party_block[poke_offset : poke_offset + self.POKEMON_SIZE]
                    self.client.log_debug(f"Processing Pokémon {i+1} data (offset {poke_offset})...")

                    if len(poke_data) < self.POKEMON_SIZE:
                         print(f"Warning: Incomplete data for Pokémon {i+1}", file=sys.stderr)
                         continue # Skip this pokemon

                    # Decrypt the Pokemon data
                    decrypted_data = self._decrypt_pokemon_data(poke_data)

                    # Read unencrypted fields first
                    personality_id = int.from_bytes(decrypted_data[0:4], byteorder='little')
                    ot_id = int.from_bytes(decrypted_data[4:8], byteorder='little')

                    # Nickname (10 bytes, null-terminated, using game's encoding)
                    nickname_bytes = decrypted_data[8:18]
                    nickname = self._convert_text(nickname_bytes)

                    # Now read from properly decrypted and reordered substructures
                    # Growth substructure (offset 32): Species ID at bytes 0-1
                    growth_start = 32
                    species_id = int.from_bytes(decrypted_data[growth_start:growth_start+2], byteorder='little')
                    
                    # Item held at bytes 2-3 (could be useful)
                    held_item = int.from_bytes(decrypted_data[growth_start+2:growth_start+4], byteorder='little')
                    
                    # Experience at bytes 4-7 (could calculate level from this)
                    experience = int.from_bytes(decrypted_data[growth_start+4:growth_start+8], byteorder='little')

                    # Attacks substructure (offset 44): Move IDs and PP
                    attacks_start = 44
                    moves = []
                    move_pp = []
                    for j in range(4):
                        move_offset = attacks_start + (j * 2)  # Move IDs: 0, 2, 4, 6
                        pp_offset = attacks_start + 8 + j      # PP values: 8, 9, 10, 11
                        
                        if len(decrypted_data) > move_offset + 1:
                            move_id = int.from_bytes(decrypted_data[move_offset:move_offset+2], byteorder='little')
                            if move_id > 0:
                                move_name = self.MOVE_NAMES.get(move_id, f"Move #{move_id}")
                                moves.append(move_name)
                                if len(decrypted_data) > pp_offset:
                                    move_pp.append(decrypted_data[pp_offset])
                                else:
                                    move_pp.append(0)

                    # Calculate level from experience using species-specific growth rate
                    level = self._calculate_level_from_experience(species_id, experience)
                    
                    # HP and status from party stats (bytes 80+ in the 100-byte structure)
                    # Current HP is at offset 86 in the full structure
                    current_hp = int.from_bytes(decrypted_data[86:88], byteorder='little') if len(decrypted_data) > 87 else 0
                    max_hp = int.from_bytes(decrypted_data[88:90], byteorder='little') if len(decrypted_data) > 89 else 0
                    
                    # Status condition at offset 80
                    status_bytes = decrypted_data[80:84] if len(decrypted_data) > 83 else b'\x00\x00\x00\x00'
                    status_value = int.from_bytes(status_bytes, byteorder='little')
                    status = StatusCondition(status_value).get_status_name()

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
                    self.client.log_debug(f"Processed Pokémon {i+1}: {nickname} (Species #{species_id}, Lvl {level})")

                except IndexError as ie:
                     print(f"Error processing Pokémon at index {i}: Data access out of bounds ({ie}). Skipping.", file=sys.stderr)
                except Exception as e:
                    print(f"Error processing Pokémon at index {i}: {e}", file=sys.stderr)

        except Exception as e:
            print(f"General error reading party block: {e}", file=sys.stderr)

        return party

    def _read_item_pocket(self, pocket_name: str, start_offset: int, capacity: int) -> List[Tuple[str, int]]:
        """Helper to read a specific item pocket."""
        items = []
        try:
            pocket_addr = self.ADDRESSES['save_block_1'] + start_offset
            self.client.log_debug(f"Reading {pocket_name} pocket at 0x{pocket_addr:08X}, capacity {capacity}")

            # Read the entire pocket data based on capacity (Item ID + Quantity per slot)
            pocket_data_size = capacity * self.ITEM_ENTRY_SIZE
            pocket_data = self.client.read_bytes(pocket_addr, pocket_data_size)

            if pocket_data is None or len(pocket_data) < pocket_data_size:
                print(f"Error: Failed to read sufficient data for {pocket_name} pocket.", file=sys.stderr)
                return []

            item_count = 0
            for i in range(capacity):
                item_offset = i * self.ITEM_ENTRY_SIZE
                item_entry = pocket_data[item_offset : item_offset + self.ITEM_ENTRY_SIZE]

                if len(item_entry) < self.ITEM_ENTRY_SIZE:
                    print(f"Warning: Incomplete item data in {pocket_name} at slot {i}", file=sys.stderr)
                    continue

                item_id = int.from_bytes(item_entry[0:2], byteorder='little')
                quantity = int.from_bytes(item_entry[2:4], byteorder='little')

                # Item ID 0 marks the end or an empty slot. Quantity needs validation.
                if item_id == 0:
                    # Some pockets might be terminated early, others fully populated with empty slots
                    # Let's assume 0 means end for general items, but TMs/Berries might have count elsewhere
                    # For simplicity now, just stop if ID is 0
                    self.client.log_debug(f"Found item ID 0 in {pocket_name} slot {i}, stopping pocket read.")
                    break

                # Quantity should generally be > 0 for valid items. TM/HM quantity is often 1 or 0.
                # Berries quantity is stored differently (usually in berry pouch structure).
                # Key Items usually have quantity 1.
                # For now, just filter quantity 0 for general items.
                if quantity > 0:
                    # TODO: Add Item Name lookup based on item_id
                    item_name = f"Item #{item_id}"
                    items.append((item_name, quantity))
                    item_count += 1
                else:
                    self.client.log_debug(f"Ignoring item ID {item_id} in {pocket_name} slot {i} due to quantity {quantity}.")


            self.client.log_debug(f"Found {item_count} items in {pocket_name} pocket.")

        except Exception as e:
            print(f"Error reading {pocket_name} items: {e}", file=sys.stderr)

        return items

    def _read_all_item_pockets(self) -> List[Tuple[str, int]]:
        """Read all standard item pockets"""
        all_items = []

        # Capacities from Bulbapedia/common sources (verify!)
        # Note: Actual *count* of items might be stored separately or implicitly (e.g., terminated by item ID 0)
        # These capacities define the maximum number of *slots*.
        pockets_info = [
            ("Items", self.ADDRESSES['items_pocket_start_offset'], 42), # Adjusted capacity
            ("Key Items", self.ADDRESSES['key_items_pocket_start_offset'], 30),
            ("Poké Balls", self.ADDRESSES['pokeballs_pocket_start_offset'], 16), # Adjusted capacity
            ("TMs/HMs", self.ADDRESSES['tms_hms_pocket_start_offset'], 64),
            ("Berries", self.ADDRESSES['berries_pocket_start_offset'], 46), # Adjusted capacity
        ]

        for name, offset, capacity in pockets_info:
             pocket_items = self._read_item_pocket(name, offset, capacity)
             if pocket_items:
                 # Add a prefix to distinguish pockets if desired
                 # all_items.extend([(f"[{name}] {item_name}", qty) for item_name, qty in pocket_items])
                 all_items.extend(pocket_items)

        return all_items

    def _calculate_level_from_experience(self, species_id: int, experience: int) -> int:
        """Calculate Pokemon level from experience points using species-specific growth rate"""
        try:
            # Get the growth rate for this species (default to medium_fast if unknown)
            growth_rate = self.SPECIES_GROWTH_RATES.get(species_id, 'medium_fast')
            exp_table = self.EXPERIENCE_TABLES.get(growth_rate, self.EXPERIENCE_TABLES['medium_fast'])
            
            # Find the highest level where the required experience is <= current experience
            level = 1
            for i in range(1, min(101, len(exp_table))):  # Pokemon can be level 1-100
                if experience >= exp_table[i]:
                    level = i
                else:
                    break
            
            self.client.log_debug(f"Species {species_id} ({growth_rate} growth): {experience} exp = level {level}")
            return max(1, min(100, level))  # Ensure level is between 1-100
        except Exception as e:
            self.client.log_debug(f"Error calculating level: {e}, defaulting to 1")
            return 1

    def _convert_text(self, bytes_data: bytes) -> str:
        """Convert Pokémon FireRed text bytes to a readable string."""
        if not bytes_data:
            return ""

        bytes_hex = ' '.join(f'{b:02X}' for b in bytes_data)
        self.client.log_debug(f"Converting text from bytes: {bytes_hex}")

        result = ""
        try:
            for byte in bytes_data:
                if byte == 0xFF:  # End of string terminator
                    break
                elif byte == 0x00: # Sometimes used as terminator, especially if buffer wasn't filled
                    # Often indicates padding, treat as end unless we know it's part of text.
                    # For player names/nicknames, usually means end.
                    break

                char = self.TEXT_MAP.get(byte)
                if char is not None:
                    result += char
                # Fallback for bytes not in the map (e.g., basic ASCII if used)
                elif 0x20 <= byte <= 0x7E: # Printable ASCII range
                     result += chr(byte)
                     self.client.log_debug(f"Using direct ASCII for byte 0x{byte:02X}")
                else:
                    result += f"[{byte:02X}]" # Show unknown bytes as hex

        except Exception as e:
            print(f"Error during text conversion: {e}", file=sys.stderr)
            # Return raw hex as fallback on error?
            return f"[Conversion Error: {bytes_hex}]"

        # Strip potential trailing nulls/spaces represented in the map or added
        final_result = result.replace("<NULL>", "").replace("<TERM>", "").strip()
        self.client.log_debug(f"Converted text: '{final_result}'")
        # Return "Unknown" only if the conversion resulted in an effectively empty string
        return final_result if final_result else "Unknown"


# --- Printing Function ---
def print_game_state(state: Optional[GameState]): # Accept Optional
    """Print the game state in a readable format"""
    print("\n" + "="*50)
    print("Pokémon Game State")
    print("="*50)

    if state is None:
        print("!! Failed to read complete game state !!")
        print("Check debug output for specific errors.")
        return

    print(f"Player Name: {state.player_name}")
    print(f"Location: {state.location} (X={state.x}, Y={state.y})")
    
    # Check if in Pokemon Center
    reader_instance = None  # We'd need to pass this to the function or make it a method
    # For now, just check if location name contains "Pokemon Center"
    in_pokemon_center = "Pokemon Center" in state.location
    if in_pokemon_center:
        print("  🏥 Currently in a Pokemon Center - Healing available!")
    
    # Handle potential negative money if read failed
    money_str = f"₽{state.money}" if state.money >= 0 else f"Read Error (Value: {state.money})"
    print(f"Money: {money_str}")

    print("\nPokémon Party:")
    if not state.party:
        print("  No Pokémon in party (or failed to read)")
    else:
        # Check if data looks potentially decrypted
        likely_encrypted = any(p.level == 0 and p.max_hp == 0 and p.species_id != 0 for p in state.party)
        if likely_encrypted:
             print("  (Warning: Party data might be encrypted/incorrectly read)")

        for i, pokemon in enumerate(state.party):
            species_name = PokemonFireRedReader.SPECIES_NAMES.get(pokemon.species_id, f"Species #{pokemon.species_id}")
            nickname = pokemon.nickname if pokemon.nickname not in ["Unknown", ""] else species_name
            print(f"  #{i+1}: {nickname}")
            print(f"      Species: {species_name} (#{pokemon.species_id})")
            print(f"      Level: {pokemon.level}, HP: {pokemon.current_hp}/{pokemon.max_hp}, Status: {pokemon.status}")

            if pokemon.moves:
                move_info = []
                for j, move in enumerate(pokemon.moves):
                    pp_str = f"(PP: {pokemon.move_pp[j]})" if j < len(pokemon.move_pp) else ""
                    move_info.append(f"{move} {pp_str}")
                print(f"      Moves: {', '.join(move_info)}")
            else:
                print("      Moves: None")

    print("\nInventory:")
    if not state.items:
        print("  No items (or failed to read)")
    else:
        for item_name, quantity in state.items:
            print(f"  {item_name} x{quantity}")

# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(description='Simple Pokémon RAM Analyzer for SkyEmu')
    parser.add_argument('--url', default='http://localhost:8080', help='SkyEmu HTTP server URL (default: http://localhost:8080)')
    parser.add_argument('--refresh', type=float, default=0, help='Refresh interval in seconds (0 = run once; e.g., 0.5 for faster updates)')
    parser.add_argument('--debug', action='store_true', help='Enable detailed debug output to stderr')
    args = parser.parse_args()

    # Create client with debug flag
    client = SkyEmuClient()

    # Basic memory access test (optional but recommended)
    print("\nTesting basic memory access...")
    test_addresses = [
        0x02000000, # Start of EWRAM
        0x03000000, # Start of IWRAM
        PokemonFireRedReader.ADDRESSES['party_count'], # Known game data address
        PokemonFireRedReader.ADDRESSES['save_block_1'], # Another known address
    ]
    all_tests_ok = True
    for addr in test_addresses:
        data = client.read_byte(addr)
        if data is not None and len(data) == 1:
             val = data[0]
             print(f"  Read 0x{addr:08X}: OK (Value: 0x{val:02X})")
             if args.debug: # Log raw value only in debug
                 client.log_debug(f"Raw byte value for 0x{addr:08X}: {val}")
        else:
             print(f"  Read 0x{addr:08X}: FAILED")
             all_tests_ok = False

    if not all_tests_ok:
        print("\nError: Basic memory access test failed. Cannot proceed.", file=sys.stderr)
        print("Check SkyEmu connection, ROM loaded status, and memory permissions.", file=sys.stderr)
        return 1

    # Create game reader instance
    reader = PokemonFireRedReader(client)

    # Main loop or single run
    if args.refresh > 0:
        print(f"\nStarting continuous refresh every {args.refresh} seconds. Press Ctrl+C to stop.")
        try:
            while True:
                state = reader.read_game_state()
                # Clear console (optional, works on many terminals)
                # print("\033[H\033[J", end="")
                print_game_state(state)
                time.sleep(args.refresh)
        except KeyboardInterrupt:
            print("\nExiting...")
    else:
        print("\nReading game state once...")
        state = reader.read_game_state()
        print_game_state(state)

    return 0 # Exit successfully

if __name__ == "__main__":
    sys.exit(main()) # Exit with the return code of main