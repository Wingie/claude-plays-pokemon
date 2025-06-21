#!/usr/bin/env python3
"""
Test Pokemon Episode Diary Generation
Test the diary system with the completed 100-turn session
"""

import json
from pathlib import Path

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
from diary_generator import PokemonEpisodeDiary

def test_diary_generation():
    """Test diary generation with the completed session"""
    
    # Load the completed 100-turn session
    session_file = Path("/Users/wingston/code/claude-plays-pokemon/eevee/runs/session_20250621_125351/session_data.json")
    
    if not session_file.exists():
        print(f"❌ Session file not found: {session_file}")
        return
    
    print(f"📖 Loading session data from: {session_file}")
    
    # Load session data
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    print(f"✅ Loaded session: {session_data['session_id']}")
    print(f"🎯 Goal: {session_data['goal']}")
    print(f"⏱️  Turns: {len(session_data['turns'])}")
    
    # Create diary generator
    diary_gen = PokemonEpisodeDiary()
    
    # Generate episode diary
    print(f"\n🎬 Generating Pokemon episode diary...")
    
    episode_content = diary_gen.generate_episode_diary(session_data, day_number=1)
    
    # Save the diary
    runs_dir = "/Users/wingston/code/claude-plays-pokemon/eevee/runs"
    diary_path = diary_gen.save_episode_diary(session_data, runs_dir, day_number=1)
    
    print(f"✅ Episode diary generated successfully!")
    print(f"📁 Saved to: {diary_path}")
    
    # Show a preview of the diary content
    print(f"\n📺 EPISODE PREVIEW:")
    print("=" * 60)
    print(episode_content[:500] + "..." if len(episode_content) > 500 else episode_content)
    print("=" * 60)
    
    return diary_path

if __name__ == "__main__":
    diary_path = test_diary_generation()
    print(f"\n🎉 Test completed! Check out the episode diary at: {diary_path}")