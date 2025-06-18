"""
Pokemon Data Parser for Eevee
Parses and structures Pokemon-related information from AI analysis text
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Pokemon:
    """Data class for Pokemon information"""
    name: str = ""
    level: int = 0
    current_hp: int = 0
    max_hp: int = 0
    types: List[str] = None
    status: str = "normal"  # normal, poison, sleep, paralysis, burn, freeze
    moves: List[Dict[str, Any]] = None
    position_in_party: int = 0
    
    def __post_init__(self):
        if self.types is None:
            self.types = []
        if self.moves is None:
            self.moves = []
    
    def hp_percentage(self) -> float:
        """Calculate HP percentage"""
        if self.max_hp > 0:
            return (self.current_hp / self.max_hp) * 100
        return 0.0
    
    def is_healthy(self) -> bool:
        """Check if Pokemon is in good health"""
        return self.hp_percentage() > 50 and self.status == "normal"
    
    def needs_healing(self) -> bool:
        """Check if Pokemon needs healing"""
        return self.hp_percentage() < 25 or self.status != "normal"

@dataclass 
class Move:
    """Data class for Pokemon move information"""
    name: str = ""
    pp_current: int = 0
    pp_max: int = 0
    move_type: str = ""
    power: int = 0
    accuracy: int = 0
    
    def pp_percentage(self) -> float:
        """Calculate PP percentage remaining"""
        if self.pp_max > 0:
            return (self.pp_current / self.pp_max) * 100
        return 0.0
    
    def is_usable(self) -> bool:
        """Check if move can be used"""
        return self.pp_current > 0

class PokemonParser:
    """Parses Pokemon information from AI analysis text"""
    
    def __init__(self):
        # Regex patterns for parsing Pokemon data
        self.pokemon_patterns = {
            "name_level": r"(\w+)\s+(?:LV|Lv|Level|level)\.?\s*(\d+)",
            "hp_status": r"(\d+)\s*/\s*(\d+)\s*HP",
            "hp_fraction": r"HP:\s*(\d+)\s*/\s*(\d+)",
            "status_condition": r"(?:status|condition):\s*(\w+)",
            "moves_section": r"(?:moves|attacks):\s*(.*?)(?:\n\n|$)",
            "move_with_pp": r"(\w+(?:\s+\w+)*)\s*\(?(\d+)\s*/\s*(\d+)\s*PP\)?",
            "move_simple": r"(\w+(?:\s+\w+)*)\s*\(([^)]+)\)",
            "type_info": r"(?:type|types):\s*([\w\s,/]+)",
            "position": r"(?:position|slot|#)\s*(\d+)"
        }
        
        # Common Pokemon types
        self.pokemon_types = {
            "normal", "fire", "water", "electric", "grass", "ice", "fighting",
            "poison", "ground", "flying", "psychic", "bug", "rock", "ghost",
            "dragon", "dark", "steel", "fairy"
        }
        
        # Status conditions
        self.status_conditions = {
            "poison", "poisoned", "sleep", "sleeping", "paralysis", "paralyzed",
            "burn", "burned", "freeze", "frozen", "normal", "healthy", "ok"
        }
    
    def parse_pokemon_party(self, analysis_text: str) -> List[Pokemon]:
        """
        Parse Pokemon party information from analysis text
        
        Args:
            analysis_text: AI analysis containing Pokemon party information
            
        Returns:
            List of Pokemon objects with parsed data
        """
        pokemon_list = []
        
        # Split text into sections that might contain individual Pokemon
        sections = self._split_into_pokemon_sections(analysis_text)
        
        for i, section in enumerate(sections):
            pokemon = self._parse_single_pokemon(section, i)
            if pokemon.name:  # Only add if we found a valid Pokemon
                pokemon_list.append(pokemon)
        
        return pokemon_list
    
    def parse_pokemon_moves(self, analysis_text: str) -> List[Move]:
        """
        Parse Pokemon moves from analysis text
        
        Args:
            analysis_text: AI analysis containing move information
            
        Returns:
            List of Move objects
        """
        moves = []
        
        # Look for moves section
        moves_match = re.search(self.pokemon_patterns["moves_section"], analysis_text, re.IGNORECASE | re.DOTALL)
        if moves_match:
            moves_text = moves_match.group(1)
        else:
            moves_text = analysis_text
        
        # Parse individual moves
        move_matches = re.finditer(self.pokemon_patterns["move_with_pp"], moves_text, re.IGNORECASE)
        for match in move_matches:
            move = Move(
                name=match.group(1).strip(),
                pp_current=int(match.group(2)),
                pp_max=int(match.group(3))
            )
            moves.append(move)
        
        # Also try simpler move patterns if PP parsing didn't work
        if not moves:
            simple_move_matches = re.finditer(self.pokemon_patterns["move_simple"], moves_text, re.IGNORECASE)
            for match in simple_move_matches:
                move = Move(
                    name=match.group(1).strip(),
                    pp_current=0,  # Unknown
                    pp_max=0      # Unknown
                )
                moves.append(move)
        
        return moves
    
    def parse_party_summary(self, analysis_text: str) -> Dict[str, Any]:
        """
        Parse high-level party summary information
        
        Args:
            analysis_text: AI analysis text
            
        Returns:
            Dictionary with party summary statistics
        """
        summary = {
            "party_size": 0,
            "healthy_pokemon": 0,
            "fainted_pokemon": 0,
            "pokemon_needing_healing": 0,
            "total_hp_percentage": 0.0,
            "status_conditions": {},
            "average_level": 0.0
        }
        
        # Parse Pokemon list
        pokemon_list = self.parse_pokemon_party(analysis_text)
        summary["party_size"] = len(pokemon_list)
        
        if pokemon_list:
            total_hp_percentage = 0
            total_level = 0
            
            for pokemon in pokemon_list:
                # Health statistics
                hp_pct = pokemon.hp_percentage()
                total_hp_percentage += hp_pct
                
                if hp_pct <= 0:
                    summary["fainted_pokemon"] += 1
                elif pokemon.is_healthy():
                    summary["healthy_pokemon"] += 1
                elif pokemon.needs_healing():
                    summary["pokemon_needing_healing"] += 1
                
                # Status condition tracking
                status = pokemon.status.lower()
                if status in summary["status_conditions"]:
                    summary["status_conditions"][status] += 1
                else:
                    summary["status_conditions"][status] = 1
                
                # Level tracking
                total_level += pokemon.level
            
            summary["total_hp_percentage"] = total_hp_percentage / len(pokemon_list)
            summary["average_level"] = total_level / len(pokemon_list)
        
        return summary
    
    def _split_into_pokemon_sections(self, text: str) -> List[str]:
        """Split analysis text into sections likely containing individual Pokemon"""
        # Split by common Pokemon delimiters
        sections = []
        
        # Try splitting by numbered lists
        numbered_sections = re.split(r'\n\s*\d+\.\s*', text)
        if len(numbered_sections) > 1:
            sections.extend(numbered_sections[1:])  # Skip first empty section
        
        # Try splitting by bullet points
        bullet_sections = re.split(r'\n\s*[-•*]\s*', text)
        if len(bullet_sections) > 1 and not sections:
            sections.extend(bullet_sections[1:])
        
        # Try splitting by line breaks with Pokemon names
        lines = text.split('\n')
        current_section = ""
        for line in lines:
            if re.search(r'\b[A-Z][a-z]+\s+(?:LV|Lv|Level)\s*\d+', line):
                if current_section:
                    sections.append(current_section)
                current_section = line
            else:
                current_section += "\n" + line
        
        if current_section:
            sections.append(current_section)
        
        # If no clear sections found, treat whole text as one section
        if not sections:
            sections = [text]
        
        return sections
    
    def _parse_single_pokemon(self, section: str, position: int) -> Pokemon:
        """Parse a single Pokemon from a text section"""
        pokemon = Pokemon(position_in_party=position)
        
        # Parse name and level
        name_level_match = re.search(self.pokemon_patterns["name_level"], section, re.IGNORECASE)
        if name_level_match:
            pokemon.name = name_level_match.group(1)
            pokemon.level = int(name_level_match.group(2))
        
        # Parse HP
        hp_matches = [
            re.search(self.pokemon_patterns["hp_status"], section, re.IGNORECASE),
            re.search(self.pokemon_patterns["hp_fraction"], section, re.IGNORECASE)
        ]
        
        for hp_match in hp_matches:
            if hp_match:
                pokemon.current_hp = int(hp_match.group(1))
                pokemon.max_hp = int(hp_match.group(2))
                break
        
        # Parse status condition
        status_match = re.search(self.pokemon_patterns["status_condition"], section, re.IGNORECASE)
        if status_match:
            status = status_match.group(1).lower()
            if status in self.status_conditions:
                pokemon.status = status
        
        # Parse types
        type_match = re.search(self.pokemon_patterns["type_info"], section, re.IGNORECASE)
        if type_match:
            type_text = type_match.group(1).lower()
            for ptype in self.pokemon_types:
                if ptype in type_text:
                    pokemon.types.append(ptype)
        
        # Parse moves
        pokemon.moves = self._parse_moves_from_section(section)
        
        return pokemon
    
    def _parse_moves_from_section(self, section: str) -> List[Dict[str, Any]]:
        """Parse moves from a Pokemon section"""
        moves = []
        
        # Look for move patterns
        move_matches = re.finditer(self.pokemon_patterns["move_with_pp"], section, re.IGNORECASE)
        for match in move_matches:
            move_data = {
                "name": match.group(1).strip(),
                "pp_current": int(match.group(2)),
                "pp_max": int(match.group(3))
            }
            moves.append(move_data)
        
        return moves
    
    def format_pokemon_report(self, pokemon_list: List[Pokemon]) -> str:
        """Format Pokemon list into a readable report"""
        if not pokemon_list:
            return "No Pokemon found in party."
        
        report_lines = [f"🎮 Pokemon Party Report ({len(pokemon_list)} Pokemon)"]
        report_lines.append("=" * 50)
        
        for i, pokemon in enumerate(pokemon_list, 1):
            report_lines.append(f"\n{i}. {pokemon.name} (Level {pokemon.level})")
            
            # HP status
            if pokemon.max_hp > 0:
                hp_pct = pokemon.hp_percentage()
                hp_status = "🟢" if hp_pct > 70 else "🟡" if hp_pct > 30 else "🔴"
                report_lines.append(f"   HP: {pokemon.current_hp}/{pokemon.max_hp} ({hp_pct:.1f}%) {hp_status}")
            
            # Status condition
            if pokemon.status != "normal":
                report_lines.append(f"   Status: {pokemon.status.upper()} ⚠️")
            
            # Types
            if pokemon.types:
                report_lines.append(f"   Type(s): {', '.join(pokemon.types).title()}")
            
            # Moves
            if pokemon.moves:
                report_lines.append("   Moves:")
                for move in pokemon.moves:
                    if isinstance(move, dict):
                        move_name = move.get("name", "Unknown")
                        pp_current = move.get("pp_current", 0)
                        pp_max = move.get("pp_max", 0)
                        if pp_max > 0:
                            pp_pct = (pp_current / pp_max) * 100
                            pp_status = "🟢" if pp_pct > 50 else "🟡" if pp_pct > 20 else "🔴"
                            report_lines.append(f"     • {move_name}: {pp_current}/{pp_max} PP {pp_status}")
                        else:
                            report_lines.append(f"     • {move_name}")
        
        return "\n".join(report_lines)
    
    def get_battle_ready_pokemon(self, pokemon_list: List[Pokemon]) -> List[Pokemon]:
        """Get list of Pokemon ready for battle"""
        return [p for p in pokemon_list if p.is_healthy() and p.current_hp > 0]
    
    def get_pokemon_needing_healing(self, pokemon_list: List[Pokemon]) -> List[Pokemon]:
        """Get list of Pokemon that need healing"""
        return [p for p in pokemon_list if p.needs_healing()]