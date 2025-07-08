#!/usr/bin/env python3
"""
Convert Eevee v1 dataset to Pixtral format
Multi-turn conversations for strategic Pokemon gameplay
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from robust_action_extractor import PokemonActionExtractor

class PixtralConversationBuilder:
    """Builds multi-turn conversations for Pixtral training"""
    
    def __init__(self):
        self.extractor = PokemonActionExtractor()
        
        # Context transition rules for conversation threading
        self.context_transitions = {
            'navigation': ['battle', 'menu', 'pokemon_center', 'dialogue'],
            'battle': ['navigation', 'post_battle', 'level_up'],
            'menu': ['navigation', 'battle', 'pokemon_center'],
            'pokemon_center': ['navigation'],
            'dialogue': ['navigation', 'battle']
        }
        
        # Conversation length targets
        self.target_lengths = {
            'short': (3, 5),    # Quick tactical decisions
            'medium': (6, 10),  # Strategic sequences
            'long': (11, 15)    # Complex scenarios
        }
    
    def should_break_conversation(self, current_context: str, next_context: str, turn_count: int) -> bool:
        """Determine if conversation should break based on context change"""
        # Always break at major context transitions
        major_transitions = [
            ('navigation', 'battle'),
            ('battle', 'navigation'),
            ('menu', 'battle'),
            ('battle', 'menu')
        ]
        
        if (current_context, next_context) in major_transitions:
            return True
            
        # Break long conversations at natural points
        if turn_count >= 12 and current_context != next_context:
            return True
            
        return False
    
    def create_user_prompt(self, turn_data: Dict[str, Any], session_goal: str, 
                          previous_action: str = "", turn_in_conversation: int = 1) -> str:
        """Create context-aware user prompts"""
        context = turn_data.get("ai_analysis", {}).get("parsed_json", {}).get("context_detected", "navigation")
        
        # Base prompts by context
        if turn_in_conversation == 1:
            # First turn prompts
            base_prompts = {
                'navigation': f"We're exploring the Pokemon world. Goal: {session_goal}. What should we do first?",
                'battle': f"A Pokemon battle has started! Goal: {session_goal}. What's our strategy?",
                'menu': f"We're in a game menu. Goal: {session_goal}. What should we select?",
                'pokemon_center': f"We're at a Pokemon Center. Goal: {session_goal}. How should we proceed?",
                'dialogue': f"We're talking to someone. Goal: {session_goal}. How should we respond?"
            }
        else:
            # Follow-up turn prompts
            base_prompts = {
                'navigation': f"We moved {previous_action}. What's our next move to achieve: {session_goal}?",
                'battle': f"We used {previous_action}. What's our next battle action?",
                'menu': f"We selected {previous_action}. What should we do next in the menu?",
                'pokemon_center': f"After {previous_action}, what's our next step at the Pokemon Center?",
                'dialogue': f"We chose {previous_action}. How should we continue the conversation?"
            }
        
        return base_prompts.get(context, f"After {previous_action}, what should we do next?")
    
    def create_assistant_response(self, turn_data: Dict[str, Any], actions: List[str], 
                                session_goal: str, gpt_response: str) -> str:
        """Create clean, action-focused assistant responses"""
        context = turn_data.get("ai_analysis", {}).get("parsed_json", {}).get("context_detected", "navigation")
        
        # Extract strategic reasoning from original response
        reasoning = ""
        if "Reasoning:" in gpt_response:
            reasoning_lines = [line for line in gpt_response.split('\n') if "Reasoning:" in line]
            if reasoning_lines:
                reasoning = reasoning_lines[0].split("Reasoning:")[-1].strip()
        
        # Extract observations
        observations = ""
        if "Observations:" in gpt_response:
            obs_lines = [line for line in gpt_response.split('\n') if "Observations:" in line]
            if obs_lines:
                observations = obs_lines[0].split("Observations:")[-1].strip()
        
        # Build clean response
        action_text = ", ".join(actions) if actions else "continue"
        
        # Context-specific response templates
        if context == "navigation":
            if observations:
                return f"I can see {observations}. {reasoning if reasoning else 'Moving strategically to achieve our goal.'} Action: {action_text}"
            else:
                return f"{reasoning if reasoning else 'Continuing exploration.'} Action: {action_text}"
        
        elif context == "battle":
            return f"In this battle situation, {reasoning if reasoning else 'attacking strategically'}. Action: {action_text}"
        
        elif context == "menu":
            return f"In the menu, {reasoning if reasoning else 'selecting the appropriate option'}. Action: {action_text}"
        
        else:
            return f"{reasoning if reasoning else 'Proceeding with the plan.'} Action: {action_text}"
    
    def build_conversation_thread(self, turns: List[Dict[str, Any]], session_goal: str) -> Dict[str, Any]:
        """Build a multi-turn conversation from session turns"""
        if not turns:
            return None
            
        messages = []
        previous_action = ""
        
        for i, turn_data in enumerate(turns):
            turn_number = turn_data.get("turn", i + 1)
            image_filename = f"step_{turn_number:04d}_grid.png"
            gpt_response = turn_data.get("gpt_response", "")
            
            # Extract actions using robust extractor
            actions, confidence = self.extractor.extract_actions(turn_data, gpt_response)
            if not actions or confidence < 0.6:
                continue  # Skip turns without clear actions
            
            # Create user message
            user_prompt = self.create_user_prompt(turn_data, session_goal, previous_action, i + 1)
            user_message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image", "image": image_filename}
                ]
            }
            
            # Create assistant message
            assistant_response = self.create_assistant_response(turn_data, actions, session_goal, gpt_response)
            assistant_message = {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": assistant_response}
                ]
            }
            
            messages.extend([user_message, assistant_message])
            previous_action = ", ".join(actions)
        
        if not messages:
            return None
            
        return {
            "messages": messages,
            "metadata": {
                "conversation_length": len(messages) // 2,
                "session_goal": session_goal,
                "contexts": list(set(turn.get("ai_analysis", {}).get("parsed_json", {}).get("context_detected", "unknown") for turn in turns)),
                "total_turns": len(turns)
            }
        }
    
    def split_session_into_conversations(self, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split a session into coherent conversation threads"""
        turns = session_data.get("turns", [])
        session_goal = session_data.get("goal", "pokemon gameplay")
        
        if not turns:
            return []
        
        conversations = []
        current_thread = []
        current_context = None
        
        for turn in turns:
            # Get context for this turn
            turn_context = turn.get("ai_analysis", {}).get("parsed_json", {}).get("context_detected", "navigation")
            
            # Check if we should break the conversation
            should_break = False
            if current_context and current_context != turn_context:
                should_break = self.should_break_conversation(current_context, turn_context, len(current_thread))
            
            # If breaking, save current thread and start new one
            if should_break and current_thread:
                conversation = self.build_conversation_thread(current_thread, session_goal)
                if conversation:
                    conversations.append(conversation)
                current_thread = []
            
            current_thread.append(turn)
            current_context = turn_context
            
            # Also break if thread gets too long
            if len(current_thread) >= 15:
                conversation = self.build_conversation_thread(current_thread, session_goal)
                if conversation:
                    conversations.append(conversation)
                current_thread = []
                current_context = None
        
        # Handle remaining thread
        if current_thread:
            conversation = self.build_conversation_thread(current_thread, session_goal)
            if conversation:
                conversations.append(conversation)
        
        return conversations

def convert_dataset_to_pixtral(input_file: str, output_file: str):
    """Convert entire dataset to Pixtral format"""
    print(f"Converting {input_file} to Pixtral format...")
    
    # Initialize conversation builder
    builder = PixtralConversationBuilder()
    
    # Load original dataset
    original_data = []
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip():
                original_data.append(json.loads(line))
    
    print(f"Loaded {len(original_data)} original training pairs")
    
    # Group by session
    sessions = {}
    for item in original_data:
        session_id = item["metadata"]["session_id"]
        if session_id not in sessions:
            sessions[session_id] = {
                "session_id": session_id,
                "goal": item["metadata"]["goal"],
                "turns": []
            }
        
        # Reconstruct turn data
        gpt_response = item["conversations"][1]["value"]
        turn_data = {
            "turn": item["metadata"]["turn"],
            "gpt_response": gpt_response,
            "ai_analysis": {
                "parsed_json": {
                    "context_detected": item["metadata"].get("context_detected"),
                    "confidence": item["metadata"].get("confidence")
                }
            }
        }
        
        sessions[session_id]["turns"].append(turn_data)
    
    print(f"Grouped into {len(sessions)} sessions")
    
    # Convert each session to conversations
    all_conversations = []
    total_turns_processed = 0
    total_conversations_created = 0
    
    for session_id, session_data in sessions.items():
        conversations = builder.split_session_into_conversations(session_data)
        all_conversations.extend(conversations)
        
        total_turns_processed += len(session_data["turns"])
        total_conversations_created += len(conversations)
        
        if conversations:
            avg_length = sum(conv["metadata"]["conversation_length"] for conv in conversations) / len(conversations)
            print(f"Session {session_id}: {len(conversations)} conversations, avg length: {avg_length:.1f} turns")
    
    # Write to output file
    with open(output_file, 'w') as f:
        for conversation in all_conversations:
            f.write(json.dumps(conversation) + '\n')
    
    print(f"\n✅ Created {len(all_conversations)} Pixtral conversations")
    print(f"📊 Conversion Rate: {total_turns_processed} turns → {total_conversations_created} conversations")
    print(f"📁 Output: {output_file}")
    
    # Generate statistics
    length_distribution = {'short': 0, 'medium': 0, 'long': 0}
    context_distribution = {}
    
    for conv in all_conversations:
        length = conv["metadata"]["conversation_length"]
        if length <= 5:
            length_distribution['short'] += 1
        elif length <= 10:
            length_distribution['medium'] += 1
        else:
            length_distribution['long'] += 1
        
        for context in conv["metadata"]["contexts"]:
            context_distribution[context] = context_distribution.get(context, 0) + 1
    
    print(f"\n📈 Conversation Length Distribution:")
    for length_type, count in length_distribution.items():
        percentage = (count / len(all_conversations)) * 100
        print(f"  {length_type}: {count} ({percentage:.1f}%)")
    
    print(f"\n🎮 Context Distribution:")
    for context, count in sorted(context_distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  {context}: {count}")
    
    return len(all_conversations)

def main():
    input_file = "/Users/wingston/code/claude-plays-pokemon/eevee_v2/training_data/eevee_v1_paligemma_training.jsonl"
    output_file = "/Users/wingston/code/claude-plays-pokemon/eevee_v2/training_data/pixtral_dataset_pokemon.jsonl"
    
    convert_dataset_to_pixtral(input_file, output_file)

if __name__ == "__main__":
    main()