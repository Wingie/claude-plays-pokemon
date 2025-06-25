#!/usr/bin/env python3
"""
Debug Template Selection Issues
Analyzes Neo4j data to identify template selection problems
"""

import json
from neo4j import GraphDatabase
from typing import Dict, List, Any

class TemplateDebugger:
    def __init__(self, uri: str = "neo4j://localhost:7687", username: str = "neo4j", password: str = "password"):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def close(self):
        if self.driver:
            self.driver.close()
    
    def get_recent_battle_turns(self, limit: int = 10) -> List[Dict]:
        """Get recent turns that should have been battle turns"""
        query = """
        MATCH (t:Turn)-[:HAS_VISUAL_CONTEXT]->(v:VisualContext)
        WHERE v.scene_type = 'battle'
        RETURN t.turn_id AS turn_id, 
               t.gemini_text AS ai_response,
               t.button_presses AS actions,
               v.scene_type AS scene_type,
               v.timestamp AS visual_timestamp
        ORDER BY t.timestamp DESC
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]
    
    def analyze_template_issues(self):
        """Analyze template selection issues in recent battles"""
        print("🔍 TEMPLATE SELECTION DEBUG ANALYSIS")
        print("=" * 60)
        
        battle_turns = self.get_recent_battle_turns()
        
        if not battle_turns:
            print("❌ No battle turns found in Neo4j")
            return
        
        print(f"📊 Found {len(battle_turns)} battle turns")
        print()
        
        for i, turn in enumerate(battle_turns, 1):
            print(f"🎮 Turn {i}: {turn['turn_id']}")
            print(f"   Scene Type: {turn['scene_type']}")
            print(f"   Actions: {turn['actions']}")
            
            # Parse AI response to check for template indicators
            ai_response = turn['ai_response']
            try:
                # Check if response looks like battle strategy or navigation
                if 'continue_battle' in ai_response:
                    template_type = "❌ NAVIGATION (wrong for battle)"
                elif 'battle' in ai_response.lower() and 'reasoning' in ai_response:
                    template_type = "✅ BATTLE (correct)"
                else:
                    template_type = "❓ UNCLEAR"
                    
                print(f"   Template Type: {template_type}")
                print(f"   AI Response Preview: {ai_response[:100]}...")
                
            except Exception as e:
                print(f"   Parse Error: {e}")
            
            print()
        
        return battle_turns
    
    def check_visual_context_data(self):
        """Check what visual context data looks like"""
        print("\n🔍 VISUAL CONTEXT DATA ANALYSIS")
        print("=" * 60)
        
        query = """
        MATCH (t:Turn)-[:HAS_VISUAL_CONTEXT]->(v:VisualContext)
        WHERE v.scene_type = 'battle'
        RETURN v.scene_type AS scene_type,
               v.player_position AS player_position,
               v.valid_movements AS valid_movements,
               v.obstacles AS obstacles,
               v.terrain AS terrain
        ORDER BY v.timestamp DESC
        LIMIT 5
        """
        
        with self.driver.session() as session:
            result = session.run(query, limit=5)
            visual_contexts = [dict(record) for record in result]
        
        if visual_contexts:
            print(f"📊 Found {len(visual_contexts)} visual contexts")
            for i, ctx in enumerate(visual_contexts, 1):
                print(f"\nVisual Context {i}:")
                for key, value in ctx.items():
                    print(f"   {key}: {value}")
        else:
            print("❌ No visual contexts found")

def main():
    debugger = TemplateDebugger()
    
    try:
        # Test connection
        with debugger.driver.session() as session:
            session.run("RETURN 1")
        print("✅ Connected to Neo4j successfully!")
        print()
        
        # Analyze template selection issues
        battle_turns = debugger.analyze_template_issues()
        
        # Check visual context data
        debugger.check_visual_context_data()
        
        # Test the new memory formatting
        print("\n🧠 TESTING NEW BATTLE MEMORY CONTEXT")
        print("=" * 60)
        
        try:
            from neo4j_compact_reader import Neo4jCompactReader
            reader = Neo4jCompactReader()
            recent_turns = reader.get_recent_turns(4)
            if recent_turns:
                compact_memory = reader.format_turns_to_compact_json(recent_turns)
                print("📝 Enhanced Memory Context:")
                print(json.dumps(compact_memory, indent=2))
                
                # Check for battle-specific patterns
                patterns = compact_memory.get("patterns", "")
                if "battle" in patterns:
                    print(f"✅ Battle patterns detected: {patterns}")
                else:
                    print(f"❌ No battle patterns detected: {patterns}")
            else:
                print("❌ No recent turns found")
                
        except Exception as e:
            print(f"❌ Memory test failed: {e}")
        
        # Summary
        print("\n📋 SUMMARY")
        print("=" * 60)
        print("This analysis shows what template selection issues exist.")
        print("Look for turns marked with ❌ NAVIGATION (wrong for battle)")
        print("These indicate the template selection logic is failing.")
        print("\nCHANGES MADE:")
        print("✅ Added debugging output to template selection")
        print("✅ Added safety override for battle scenes")
        print("✅ Enhanced battle prompts with type effectiveness")
        print("✅ Added cursor navigation instructions")
        print("✅ Enhanced memory context with battle patterns")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        debugger.close()

if __name__ == "__main__":
    main()