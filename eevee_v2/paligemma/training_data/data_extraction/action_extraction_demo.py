#!/usr/bin/env python3
"""
Action Extraction Demonstration and Testing
Shows the robust action extraction capabilities with real examples
from the Pokemon dataset.
"""

import json
from pathlib import Path
from robust_action_extractor import PokemonActionExtractor, ActionSource
import re

def load_sample_session_data():
    """Load a sample session for demonstration"""
    runs_path = Path("/Users/wingston/code/claude-plays-pokemon/eevee/runs")
    
    # Find first available session
    for session_dir in runs_path.iterdir():
        if session_dir.is_dir():
            session_file = session_dir / "session_data.json"
            if session_file.exists():
                try:
                    with open(session_file, 'r') as f:
                        return json.load(f), session_dir.name
                except:
                    continue
    
    return None, None

def demonstrate_regex_patterns():
    """Demonstrate regex pattern matching capabilities"""
    extractor = PokemonActionExtractor()
    
    # Test cases representing different response formats found in the data
    test_responses = [
        # Standard Strategic Analysis format
        """Strategic Analysis:
        - Context: navigation
        - Observations: open terrain ahead
        - Reasoning: need to move north to explore
        - Confidence: high
        - Recommended Action: up""",
        
        # JSON block format
        """```json
        {
          "button_presses": ["right", "right"],
          "reasoning": "explore_east_path",
          "context_detected": "navigation",
          "confidence": "high"
        }
        ```""",
        
        # Mixed format with action description
        """The next action should be to press A to interact with the NPC and advance the dialogue.""",
        
        # Verbose strategic format
        """Context: battle
        AI Observations: Pikachu vs Caterpie matchup
        Reasoning: Electric moves are super effective against Bug types
        Confidence: high
        Recommended Action: a, a""",
        
        # Complex action description
        """Based on the current position, we should move left then up to reach the Pokemon Center entrance.""",
    ]
    
    print("REGEX PATTERN DEMONSTRATION")
    print("=" * 60)
    
    for i, response in enumerate(test_responses, 1):
        print(f"\nTest Response {i}:")
        print("-" * 30)
        print(response[:100] + "..." if len(response) > 100 else response)
        
        # Create mock turn data
        turn_data = {
            "ai_analysis": {"raw_text": response},
            "strategic_decision": {"raw_response": response}
        }
        
        action = extractor.extract_action(turn_data)
        
        if action:
            print(f"\nExtracted Action:")
            print(f"  Buttons: {action.buttons}")
            print(f"  Source: {action.source.value}")
            print(f"  Confidence: {action.confidence}")
            print(f"  Raw Text: {action.raw_text}")
            
            is_valid, issues = extractor.validate_action(action)
            print(f"  Valid: {is_valid}")
            if issues:
                print(f"  Issues: {issues}")
        else:
            print("\nNo action extracted")

def demonstrate_button_normalization():
    """Demonstrate button normalization capabilities"""
    extractor = PokemonActionExtractor()
    
    # Test various button format inputs
    button_tests = [
        # Standard formats
        "up", "DOWN", "Left", "RIGHT",
        
        # Unicode arrows (from visual analysis)
        "↑", "↓", "←", "→", "⬆", "⬇", "⬅", "➡",
        
        # Action descriptions
        "move_up", "move_north", "go_left", "interact",
        "select", "confirm", "cancel", "back",
        
        # Invalid/edge cases
        "northwest", "diagonal", "jump", "run",
        "", "  ", "unknown_button"
    ]
    
    print("\n\nBUTTON NORMALIZATION DEMONSTRATION")
    print("=" * 60)
    
    print(f"{'Input':<20} {'Normalized':<15} {'Valid'}")
    print("-" * 50)
    
    for button in button_tests:
        normalized = extractor.normalize_button(button)
        is_valid = normalized in extractor.valid_buttons if normalized else False
        
        display_input = f"'{button}'" if button else "''"
        display_norm = normalized if normalized else "None"
        
        print(f"{display_input:<20} {display_norm:<15} {is_valid}")

def analyze_real_session_data():
    """Analyze real session data to show extraction performance"""
    extractor = PokemonActionExtractor()
    
    session_data, session_name = load_sample_session_data()
    if not session_data:
        print("\n\nNo session data available for analysis")
        return
    
    print(f"\n\nREAL SESSION ANALYSIS: {session_name}")
    print("=" * 60)
    
    turns = session_data.get("turns", [])
    total_turns = len(turns)
    successful_extractions = 0
    source_counts = {}
    context_counts = {}
    
    print(f"Analyzing {total_turns} turns from session...")
    
    # Analyze first 10 turns for detailed output
    for i, turn in enumerate(turns[:10]):
        turn_num = turn.get("turn", i+1)
        
        action = extractor.extract_action(turn)
        
        if action:
            successful_extractions += 1
            source_counts[action.source.value] = source_counts.get(action.source.value, 0) + 1
            context_counts[action.context] = context_counts.get(action.context, 0) + 1
            
            print(f"\nTurn {turn_num}:")
            print(f"  Action: {action.buttons}")
            print(f"  Source: {action.source.value}")
            print(f"  Context: {action.context}")
            print(f"  Confidence: {action.confidence:.2f}")
            
            is_valid, issues = extractor.validate_action(action)
            if not is_valid:
                print(f"  Validation Issues: {issues}")
        else:
            print(f"\nTurn {turn_num}: No action extracted")
    
    # Process remaining turns for statistics
    for turn in turns[10:]:
        action = extractor.extract_action(turn)
        if action:
            successful_extractions += 1
            source_counts[action.source.value] = source_counts.get(action.source.value, 0) + 1
            context_counts[action.context] = context_counts.get(action.context, 0) + 1
    
    print(f"\n\nSession Statistics:")
    print(f"  Total Turns: {total_turns}")
    print(f"  Successful Extractions: {successful_extractions}")
    print(f"  Success Rate: {successful_extractions/total_turns:.2%}")
    
    print(f"\nAction Sources:")
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")
    
    print(f"\nContexts Detected:")
    for context, count in sorted(context_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {context}: {count}")

def demonstrate_validation_rules():
    """Demonstrate action validation capabilities"""
    extractor = PokemonActionExtractor()
    
    # Create test actions with various issues
    from robust_action_extractor import ExtractedAction, ActionSource
    
    test_actions = [
        # Valid actions
        ExtractedAction(["up"], ActionSource.PARSED_JSON, 0.9, "up", "navigation"),
        ExtractedAction(["a"], ActionSource.PARSED_JSON, 0.9, "a", "battle"),
        ExtractedAction(["left", "left"], ActionSource.PARSED_JSON, 0.8, "left, left", "navigation"),
        
        # Invalid actions
        ExtractedAction([], ActionSource.PARSED_JSON, 0.9, "", "navigation"),  # No buttons
        ExtractedAction(["invalid_button"], ActionSource.PARSED_JSON, 0.9, "invalid", "navigation"),  # Invalid button
        ExtractedAction(["up", "down"], ActionSource.PARSED_JSON, 0.9, "up, down", "navigation"),  # Conflicting directions
        ExtractedAction(["left", "right"], ActionSource.PARSED_JSON, 0.9, "left, right", "navigation"),  # Conflicting directions
        ExtractedAction(["up", "right", "a", "b", "start"], ActionSource.PARSED_JSON, 0.9, "too many", "navigation"),  # Too many buttons
        ExtractedAction(["up"], ActionSource.PARSED_JSON, 0.9, "up", "battle"),  # Wrong context
    ]
    
    print("\n\nVALIDATION RULES DEMONSTRATION")
    print("=" * 60)
    
    for i, action in enumerate(test_actions, 1):
        is_valid, issues = extractor.validate_action(action)
        
        print(f"\nTest {i}: {action.buttons}")
        print(f"  Context: {action.context}")
        print(f"  Valid: {is_valid}")
        if issues:
            print(f"  Issues: {', '.join(issues)}")

def main():
    """Run all demonstrations"""
    print("POKEMON ACTION EXTRACTION SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Run demonstrations
    demonstrate_regex_patterns()
    demonstrate_button_normalization()
    demonstrate_validation_rules()
    analyze_real_session_data()
    
    print("\n\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print("\nThe robust action extraction system provides:")
    print("✓ Multiple extraction sources with priority ordering")
    print("✓ Comprehensive button normalization (standard, unicode, phrases)")
    print("✓ Regex pattern matching for various response formats")
    print("✓ Pokemon-specific validation rules")
    print("✓ Confidence scoring and error handling")
    print("✓ Detailed metadata and source tracking")

if __name__ == "__main__":
    main()