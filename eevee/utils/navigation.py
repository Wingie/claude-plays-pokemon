"""
Navigation Utilities for Eevee
Handles Pokemon game menu navigation, state tracking, and common navigation patterns
"""

import time
from typing import Dict, List, Tuple, Optional
from enum import Enum

class MenuState(Enum):
    """Common Pokemon game menu states"""
    OVERWORLD = "overworld"
    MAIN_MENU = "main_menu"
    POKEMON_MENU = "pokemon_menu"
    POKEMON_DETAIL = "pokemon_detail"
    POKEMON_MOVES = "pokemon_moves"
    BAG_MENU = "bag_menu"
    BAG_ITEMS = "bag_items"
    BAG_POKEBALLS = "bag_pokeballs"
    BAG_KEY_ITEMS = "bag_key_items"
    BATTLE_MENU = "battle_menu"
    BATTLE_FIGHT = "battle_fight"
    BATTLE_POKEMON = "battle_pokemon"
    BATTLE_BAG = "battle_bag"
    TOWN_MAP = "town_map"
    POKEDEX = "pokedex"
    SAVE_MENU = "save_menu"
    OPTIONS_MENU = "options_menu"
    UNKNOWN = "unknown"

class NavigationHelper:
    """Helper class for Pokemon game navigation"""
    
    def __init__(self, controller):
        """
        Initialize navigation helper
        
        Args:
            controller: PokemonController instance for button input
        """
        self.controller = controller
        self.menu_stack = []  # Track menu navigation history
        self.current_state = MenuState.UNKNOWN
        self.state_confidence = 0.0
        
        # Common navigation sequences
        self.navigation_sequences = {
            "to_pokemon_menu": ["start", "up", "a"],  # Main menu -> Pokemon
            "to_bag_menu": ["start", "down", "a"],     # Main menu -> Bag
            "to_main_menu": ["start"],                 # Overworld -> Main menu
            "close_menu": ["b"],                       # Close current menu
            "close_all_menus": ["b", "b", "b", "b"],   # Force close multiple menus
            "to_overworld": ["b", "b", "b", "b", "b"]  # Return to overworld from anywhere
        }
        
        # Menu detection patterns (can be enhanced with AI vision)
        self.menu_indicators = {
            MenuState.MAIN_MENU: ["POKEMON", "BAG", "SAVE"],
            MenuState.POKEMON_MENU: ["LV", "HP", "MOVES"],
            MenuState.BAG_MENU: ["ITEMS", "KEY ITEMS", "POKé BALLS"],
            MenuState.BATTLE_MENU: ["FIGHT", "BAG", "POKEMON", "RUN"]
        }
    
    def navigate_to_pokemon_menu(self, retries: int = 3) -> bool:
        """
        Navigate to Pokemon menu from current state
        
        Args:
            retries: Number of attempts if navigation fails
            
        Returns:
            True if successfully navigated to Pokemon menu
        """
        for attempt in range(retries):
            try:
                if self.current_state == MenuState.POKEMON_MENU:
                    return True
                
                # Return to overworld first if we're deep in menus
                if self.current_state not in [MenuState.OVERWORLD, MenuState.MAIN_MENU]:
                    self._return_to_overworld()
                
                # Navigate to main menu, then Pokemon
                self._execute_sequence(self.navigation_sequences["to_pokemon_menu"])
                
                # Verify we reached Pokemon menu
                time.sleep(1)
                if self._verify_menu_state(MenuState.POKEMON_MENU):
                    self.current_state = MenuState.POKEMON_MENU
                    self._push_menu_state(MenuState.POKEMON_MENU)
                    return True
                
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(0.5)
        
        return False
    
    def navigate_to_bag_menu(self, retries: int = 3) -> bool:
        """
        Navigate to Bag menu from current state
        
        Args:
            retries: Number of attempts if navigation fails
            
        Returns:
            True if successfully navigated to Bag menu
        """
        for attempt in range(retries):
            try:
                if self.current_state == MenuState.BAG_MENU:
                    return True
                
                # Return to overworld first if we're deep in menus
                if self.current_state not in [MenuState.OVERWORLD, MenuState.MAIN_MENU]:
                    self._return_to_overworld()
                
                # Navigate to main menu, then Bag
                self._execute_sequence(self.navigation_sequences["to_bag_menu"])
                
                # Verify we reached Bag menu
                time.sleep(1)
                if self._verify_menu_state(MenuState.BAG_MENU):
                    self.current_state = MenuState.BAG_MENU
                    self._push_menu_state(MenuState.BAG_MENU)
                    return True
                
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(0.5)
        
        return False
    
    def return_to_overworld(self, retries: int = 3) -> bool:
        """
        Return to overworld from any menu state
        
        Args:
            retries: Number of attempts if navigation fails
            
        Returns:
            True if successfully returned to overworld
        """
        for attempt in range(retries):
            try:
                if self.current_state == MenuState.OVERWORLD:
                    return True
                
                self._return_to_overworld()
                
                # Verify we're in overworld
                time.sleep(1)
                if self._verify_menu_state(MenuState.OVERWORLD):
                    self.current_state = MenuState.OVERWORLD
                    self.menu_stack = []
                    return True
                
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(0.5)
        
        return False
    
    def navigate_pokemon_list(self, direction: str, steps: int = 1) -> bool:
        """
        Navigate within Pokemon list
        
        Args:
            direction: "up" or "down"
            steps: Number of steps to move
            
        Returns:
            True if navigation completed
        """
        try:
            for _ in range(steps):
                self.controller.press_button(direction)
                time.sleep(0.3)
            return True
        except Exception:
            return False
    
    def select_pokemon(self, pokemon_index: int = 0) -> bool:
        """
        Select a specific Pokemon by index in the party
        
        Args:
            pokemon_index: Index of Pokemon to select (0-5)
            
        Returns:
            True if Pokemon selected successfully
        """
        try:
            # Ensure we're in Pokemon menu
            if not self.navigate_to_pokemon_menu():
                return False
            
            # Navigate to the desired Pokemon
            for _ in range(pokemon_index):
                self.controller.press_button('down')
                time.sleep(0.3)
            
            # Select the Pokemon
            self.controller.press_button('a')
            time.sleep(0.5)
            
            self.current_state = MenuState.POKEMON_DETAIL
            self._push_menu_state(MenuState.POKEMON_DETAIL)
            return True
            
        except Exception:
            return False
    
    def navigate_bag_category(self, category: str) -> bool:
        """
        Navigate to specific bag category
        
        Args:
            category: "items", "pokeballs", "key_items", or "berries"
            
        Returns:
            True if category selected successfully
        """
        try:
            # Ensure we're in bag menu
            if not self.navigate_to_bag_menu():
                return False
            
            # Navigate to desired category
            category_mapping = {
                "items": 0,
                "key_items": 1, 
                "pokeballs": 2,
                "berries": 3
            }
            
            target_position = category_mapping.get(category.lower(), 0)
            
            # Navigate to category
            for _ in range(target_position):
                self.controller.press_button('right')
                time.sleep(0.3)
            
            # Select category
            self.controller.press_button('a')
            time.sleep(0.5)
            
            return True
            
        except Exception:
            return False
    
    def _execute_sequence(self, sequence: List[str]):
        """Execute a sequence of button presses"""
        for button in sequence:
            self.controller.press_button(button)
            time.sleep(0.4)
    
    def _return_to_overworld(self):
        """Force return to overworld by pressing B multiple times"""
        self._execute_sequence(self.navigation_sequences["to_overworld"])
        time.sleep(1)
    
    def _verify_menu_state(self, expected_state: MenuState) -> bool:
        """
        Verify current menu state (placeholder for AI vision integration)
        
        Args:
            expected_state: Expected menu state to verify
            
        Returns:
            True if state matches (simplified implementation)
        """
        # This is a simplified version - in full implementation,
        # this would use AI vision to analyze the current screen
        # and determine the actual menu state
        
        # For now, assume navigation was successful
        # Real implementation would capture screenshot and analyze
        return True
    
    def _push_menu_state(self, state: MenuState):
        """Push menu state onto navigation stack"""
        self.menu_stack.append(state)
        if len(self.menu_stack) > 10:  # Limit stack size
            self.menu_stack.pop(0)
    
    def _pop_menu_state(self) -> Optional[MenuState]:
        """Pop menu state from navigation stack"""
        if self.menu_stack:
            return self.menu_stack.pop()
        return None
    
    def get_navigation_path(self, target_state: MenuState) -> List[str]:
        """
        Get navigation path to reach target state from current state
        
        Args:
            target_state: Target menu state
            
        Returns:
            List of button sequences to reach target
        """
        # Simplified navigation planning
        if target_state == MenuState.POKEMON_MENU:
            return self.navigation_sequences["to_pokemon_menu"]
        elif target_state == MenuState.BAG_MENU:
            return self.navigation_sequences["to_bag_menu"]
        elif target_state == MenuState.OVERWORLD:
            return self.navigation_sequences["to_overworld"]
        else:
            return self.navigation_sequences["close_all_menus"]
    
    def get_current_state(self) -> Tuple[MenuState, float]:
        """
        Get current menu state and confidence
        
        Returns:
            Tuple of (current_state, confidence_score)
        """
        return self.current_state, self.state_confidence
    
    def reset_navigation_state(self):
        """Reset navigation state tracking"""
        self.current_state = MenuState.UNKNOWN
        self.state_confidence = 0.0
        self.menu_stack = []