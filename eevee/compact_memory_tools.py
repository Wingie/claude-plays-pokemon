"""
Compact Memory Tools for Live Session
Simple remember/recall functions with minimal overhead
"""

import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

class CompactMemory:
    """Ultra-simple memory system for live sessions"""
    
    def __init__(self, session_name: str = "live"):
        self.session_name = session_name
        self.memory_file = Path(f"memory_{session_name}.json")
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from file"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_memory(self):
        """Save memory to file"""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            print(f"⚠️ Memory save failed: {e}")
    
    def remember(self, key: str, value: Any) -> bool:
        """Remember something"""
        try:
            self.memory[key] = {
                'value': value,
                'timestamp': time.time(),
                'session': self.session_name
            }
            self._save_memory()
            return True
        except:
            return False
    
    def recall(self, key: str, default: Any = None) -> Any:
        """Recall something"""
        if key in self.memory:
            return self.memory[key]['value']
        return default
    
    def learn(self, context: str, action: str, success: bool) -> bool:
        """Learn from outcome"""
        learning_key = f"learn_{context}"
        
        if learning_key not in self.memory:
            self.memory[learning_key] = []
        
        self.memory[learning_key].append({
            'action': action,
            'success': success,
            'timestamp': time.time()
        })
        
        self._save_memory()
        return True
    
    def get_best_action(self, context: str) -> Optional[str]:
        """Get best action for context based on learning"""
        learning_key = f"learn_{context}"
        
        if learning_key not in self.memory:
            return None
        
        # Find most successful action
        actions = {}
        for entry in self.memory[learning_key]:
            action = entry['action']
            if action not in actions:
                actions[action] = {'success': 0, 'total': 0}
            
            actions[action]['total'] += 1
            if entry['success']:
                actions[action]['success'] += 1
        
        # Return action with highest success rate
        best_action = None
        best_rate = 0
        
        for action, stats in actions.items():
            rate = stats['success'] / stats['total']
            if rate > best_rate:
                best_rate = rate
                best_action = action
        
        return best_action

def add_memory_tools_to_agent(agent, session_name: str = "live"):
    """Add compact memory tools to any agent"""
    
    # Create compact memory instance
    memory = CompactMemory(session_name)
    
    # Add methods to agent
    agent.remember = memory.remember
    agent.recall = memory.recall
    agent.learn = memory.learn
    agent.get_best_action = memory.get_best_action
    agent._compact_memory = memory
    
    print(f"🧠 Compact memory tools added to agent (session: {session_name})")
    return True

def create_memory_enhanced_eevee(eevee_agent, session_name: str = None):
    """Enhanced version that actually works"""
    
    if session_name is None:
        session_name = f"eevee_{int(time.time())}"
    
    try:
        # Add compact memory tools
        success = add_memory_tools_to_agent(eevee_agent, session_name)
        
        if success:
            print(f"✅ Memory-enhanced Eevee created with compact tools")
            
            # Add some default memories for Pokemon
            eevee_agent.remember("battle_hp_critical", "heal")
            eevee_agent.remember("battle_level_advantage", "attack")
            eevee_agent.remember("battle_type_effective", "use_super_effective_move")
            
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Memory enhancement failed: {e}")
        return False

# Compact memory functions for direct use
_global_memory = None

def init_memory(session_name: str = "global"):
    """Initialize global memory"""
    global _global_memory
    _global_memory = CompactMemory(session_name)
    return _global_memory

def remember(key: str, value: Any) -> bool:
    """Global remember function"""
    if _global_memory is None:
        init_memory()
    return _global_memory.remember(key, value)

def recall(key: str, default: Any = None) -> Any:
    """Global recall function"""
    if _global_memory is None:
        init_memory()
    return _global_memory.recall(key, default)

def learn(context: str, action: str, success: bool) -> bool:
    """Global learn function"""
    if _global_memory is None:
        init_memory()
    return _global_memory.learn(context, action, success)

def get_best_action(context: str) -> Optional[str]:
    """Global get best action function"""
    if _global_memory is None:
        init_memory()
    return _global_memory.get_best_action(context)

# Test function
def test_compact_memory():
    """Test the compact memory system"""
    print("🧪 Testing Compact Memory Tools")
    
    # Test basic remember/recall
    memory = CompactMemory("test")
    
    # Remember battle strategies
    memory.remember("battle_strategy_hp_low", {"action": "heal", "priority": "critical"})
    memory.remember("battle_strategy_level_advantage", {"action": "attack", "move": "any"})
    
    # Recall strategies
    hp_strategy = memory.recall("battle_strategy_hp_low")
    level_strategy = memory.recall("battle_strategy_level_advantage")
    
    print(f"✅ HP Strategy: {hp_strategy}")
    print(f"✅ Level Strategy: {level_strategy}")
    
    # Test learning
    memory.learn("hp_critical", "heal", True)
    memory.learn("hp_critical", "attack", False)
    memory.learn("level_advantage", "attack", True)
    
    # Get best actions
    best_hp_action = memory.get_best_action("hp_critical")
    best_level_action = memory.get_best_action("level_advantage")
    
    print(f"✅ Best HP Action: {best_hp_action}")
    print(f"✅ Best Level Action: {best_level_action}")
    
    print("🎉 Compact memory test complete!")

if __name__ == "__main__":
    test_compact_memory()