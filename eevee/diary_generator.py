#!/usr/bin/env python3
"""
Pokemon Episode Diary Generator
Creates Pokemon anime-style episode reports from Eevee session logs
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class PokemonEpisodeDiary:
    """Generates Pokemon anime-style episode diaries from session data"""
    
    def __init__(self):
        self.episode_templates = {
            "opening": [
                "🌟 Another exciting day in Ash's Pokemon journey begins!",
                "🎮 Ash powers on his Game Boy Advance, ready for adventure!",
                "🌅 The sun rises over Kanto as Ash starts his Pokemon quest!",
                "⚡ With Pikachu by his side, Ash begins another day of exploration!"
            ],
            "exploration": [
                "Ash carefully navigates through {location} using his Game Boy Advance controls",
                "With determination, Ash explores every corner of {location}",
                "Ash's adventurous spirit leads him deeper into {location}",
                "Using his D-Pad skills, Ash moves through the winding paths of {location}"
            ],
            "battle_start": [
                "⚔️ A trainer appears! Ash's eyes light up with excitement!",
                "🎯 'A Pokemon battle!' Ash exclaims, always ready for a challenge!",
                "⚡ 'Alright!' Ash grins, spotting a trainer ready to battle!",
                "🥊 Ash approaches the trainer, his Game Boy Advance ready for battle!"
            ],
            "victory": [
                "🎉 'Yes! We did it!' Ash cheers as his Pokemon wins the battle!",
                "⭐ Ash and his Pokemon celebrate another victory together!",
                "🏆 'Great job, {pokemon}!' Ash says proudly after the win!",
                "🌟 Victory! Ash's bond with his Pokemon grows stronger!"
            ],
            "stuck_moments": [
                "🤔 'Hmm, this path seems blocked...' Ash scratches his head",
                "🧭 Ash takes a moment to study his surroundings carefully",
                "💭 'Let me try a different approach!' Ash thinks strategically",
                "🔄 Ash adjusts his strategy, determined to find a way forward"
            ],
            "discovery": [
                "✨ 'Wow! I've never seen this area before!' Ash marvels",
                "🗺️ Ash discovers a new part of {location} to explore",
                "👀 'There's so much to see here!' Ash looks around in wonder",
                "🌟 Ash's exploration reveals hidden areas of the Pokemon world"
            ]
        }
    
    def generate_episode_diary(self, session_data: Dict[str, Any], day_number: int = 1) -> str:
        """Generate a Pokemon episode-style diary from session data"""
        
        session_id = session_data.get("session_id", "unknown")
        goal = session_data.get("goal", "explore and have adventures")
        turns = session_data.get("turns", [])
        
        # Detect primary location from AI analysis
        location = self._detect_location(turns)
        
        # Analyze session for key events
        battles = self._detect_battles(turns)
        explorations = self._detect_explorations(turns)
        stuck_moments = self._detect_stuck_patterns(turns)
        discoveries = self._detect_discoveries(turns)
        
        # Generate episode title
        title = self._generate_episode_title(location, battles, explorations, goal, day_number)
        
        # Build episode content
        episode_content = self._build_episode_content(
            title, session_id, goal, location, turns, battles, 
            explorations, stuck_moments, discoveries, day_number
        )
        
        return episode_content
    
    def _detect_location(self, turns: List[Dict]) -> str:
        """Detect the primary location from AI analysis"""
        locations = ["Viridian Forest", "Route 1", "Pallet Town", "Pewter City", "forest", "route"]
        location_counts = {}
        
        for turn in turns:
            analysis = turn.get("ai_analysis", "").lower()
            for location in locations:
                if location.lower() in analysis:
                    location_counts[location] = location_counts.get(location, 0) + 1
        
        if location_counts:
            return max(location_counts.keys(), key=location_counts.get)
        return "the Pokemon world"
    
    def _detect_battles(self, turns: List[Dict]) -> List[Dict]:
        """Detect battle events from session data"""
        battles = []
        for i, turn in enumerate(turns):
            analysis = turn.get("ai_analysis", "").lower()
            if any(word in analysis for word in ["trainer", "battle", "fight", "wild pokemon"]):
                battles.append({
                    "turn": turn.get("turn", i),
                    "description": turn.get("ai_analysis", ""),
                    "buttons": turn.get("button_presses", [])
                })
        return battles
    
    def _detect_explorations(self, turns: List[Dict]) -> List[Dict]:
        """Detect exploration milestones"""
        explorations = []
        movement_turns = []
        
        for turn in turns:
            buttons = turn.get("button_presses", [])
            if any(btn in ["up", "down", "left", "right"] for btn in buttons):
                movement_turns.append(turn)
        
        # Group movement into exploration segments
        for i in range(0, len(movement_turns), 10):  # Every 10 movement turns
            segment = movement_turns[i:i+10]
            if segment:
                explorations.append({
                    "turns": [t.get("turn", 0) for t in segment],
                    "directions": [btn for t in segment for btn in t.get("button_presses", [])],
                    "description": f"Ash explores using careful {', '.join(set([btn for t in segment for btn in t.get('button_presses', [])[:1]]))}, movements"
                })
        
        return explorations
    
    def _detect_stuck_patterns(self, turns: List[Dict]) -> List[Dict]:
        """Detect when Ash gets stuck and has to problem-solve"""
        stuck_moments = []
        for turn in turns:
            analysis = turn.get("ai_analysis", "").lower()
            if any(word in analysis for word in ["stuck", "blocked", "corner", "repeat", "pattern"]):
                stuck_moments.append({
                    "turn": turn.get("turn", 0),
                    "situation": analysis[:100] + "..." if len(analysis) > 100 else analysis,
                    "solution": turn.get("button_presses", [])
                })
        return stuck_moments
    
    def _detect_discoveries(self, turns: List[Dict]) -> List[Dict]:
        """Detect new area discoveries"""
        discoveries = []
        for turn in turns:
            analysis = turn.get("ai_analysis", "").lower()
            if any(word in analysis for word in ["new", "unexplored", "discover", "different"]):
                discoveries.append({
                    "turn": turn.get("turn", 0),
                    "discovery": analysis[:150] + "..." if len(analysis) > 150 else analysis
                })
        return discoveries
    
    def _generate_episode_title(self, location: str, battles: List, explorations: List, goal: str, day_number: int) -> str:
        """Generate an engaging episode title"""
        battle_count = len(battles)
        exploration_count = len(explorations)
        
        if battle_count > 3:
            return f"Day {day_number}: Battle Fever in {location}!"
        elif battle_count > 0:
            return f"Day {day_number}: Ash's Battle Challenge in {location}!"
        elif exploration_count > 5:
            return f"Day {day_number}: The Great {location} Exploration!"
        elif "win" in goal.lower():
            return f"Day {day_number}: Quest for Victory in {location}!"
        else:
            return f"Day {day_number}: Adventure Awaits in {location}!"
    
    def _build_episode_content(self, title: str, session_id: str, goal: str, location: str, 
                             turns: List[Dict], battles: List, explorations: List, 
                             stuck_moments: List, discoveries: List, day_number: int) -> str:
        """Build the complete episode content"""
        
        total_turns = len(turns)
        
        content = f"""# 🎬 {title}

## 📺 Pokemon Episode Summary
**Episode #{day_number}** | **Session ID**: {session_id}
**Air Date**: {datetime.now().strftime("%B %d, %Y")}
**Location**: {location}
**Mission**: {goal}

---

## 🌟 Episode Opening
{self.episode_templates["opening"][day_number % len(self.episode_templates["opening"])]}

"Today's mission: {goal}!" Ash declares, gripping his Game Boy Advance with determination.

---

## 🎮 Adventure Summary

**Total Adventure Time**: {total_turns} turns
**Battles Encountered**: {len(battles)}
**Areas Explored**: {len(explorations)}
**Challenges Overcome**: {len(stuck_moments)}
**New Discoveries**: {len(discoveries)}

---

## 🗺️ Ash's Journey Through {location}

"""
        
        # Add exploration narrative
        if explorations:
            content += "### 🧭 Exploration Highlights\n\n"
            for i, exploration in enumerate(explorations[:3]):  # Top 3 explorations
                content += f"""**Scene {i+1}**: Turns {exploration['turns'][0]}-{exploration['turns'][-1]}
{self.episode_templates["exploration"][i % len(self.episode_templates["exploration"])].format(location=location)}
*Ash uses his D-Pad to move: {', '.join(exploration['directions'][:5])}...*

"""
        
        # Add battle scenes
        if battles:
            content += "### ⚔️ Battle Scenes\n\n"
            for i, battle in enumerate(battles[:3]):  # Top 3 battles
                content += f"""**Battle {i+1}**: Turn {battle['turn']}
{self.episode_templates["battle_start"][i % len(self.episode_templates["battle_start"])]}

*Ash's Analysis*: "{battle['description'][:100]}..."
*Battle Actions*: {', '.join(battle['buttons'])}

{self.episode_templates["victory"][i % len(self.episode_templates["victory"])].format(pokemon="his Pokemon")}

"""
        
        # Add problem-solving moments
        if stuck_moments:
            content += "### 🧠 Problem-Solving Moments\n\n"
            for i, moment in enumerate(stuck_moments[:3]):  # Top 3 moments
                content += f"""**Challenge {i+1}**: Turn {moment['turn']}
{self.episode_templates["stuck_moments"][i % len(self.episode_templates["stuck_moments"])]}

*The Situation*: "{moment['situation']}"
*Ash's Solution*: Uses {', '.join(moment['solution'])} on his Game Boy Advance

"""
        
        # Add discoveries
        if discoveries:
            content += "### ✨ Amazing Discoveries\n\n"
            for i, discovery in enumerate(discoveries[:3]):  # Top 3 discoveries
                content += f"""**Discovery {i+1}**: Turn {discovery['turn']}
{self.episode_templates["discovery"][i % len(self.episode_templates["discovery"])].format(location=location)}

*What Ash Found*: "{discovery['discovery']}"

"""
        
        # Add episode ending
        content += f"""---

## 🌅 Episode Conclusion

After {total_turns} turns of adventure in {location}, Ash has proven once again that determination and friendship can overcome any challenge! 

**Today's Achievements**:
- ✅ Explored {len(explorations)} different areas
- ✅ Faced {len(battles)} exciting battles
- ✅ Solved {len(stuck_moments)} tricky challenges
- ✅ Made {len(discoveries)} amazing discoveries

"What an incredible day!" Ash says, looking at his Game Boy Advance with satisfaction. "Tomorrow, we'll have even more adventures in the world of Pokemon!"

*Pikachu*: "Pika pika!" ⚡

---

## 🎵 End Credits
*To be continued in tomorrow's adventure...*

**Next Episode Preview**: 
Will Ash discover new Pokemon? What challenges await in his next exploration? Find out in the next exciting episode of Ash's Kanto Journey!

---
*🎮 Generated from Ash's Game Boy Advance adventure logs*
*📱 Powered by Eevee v1 AI System*
"""
        
        return content
    
    def save_episode_diary(self, session_data: Dict[str, Any], runs_dir: str, day_number: int = 1) -> str:
        """Save the episode diary to a file"""
        diary_content = self.generate_episode_diary(session_data, day_number)
        
        # Create diary filename
        session_id = session_data.get("session_id", "unknown")
        diary_filename = f"diary_day_{day_number}.md"
        diary_path = Path(runs_dir) / f"session_{session_id}" / diary_filename
        
        # Ensure directory exists
        diary_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write diary file
        with open(diary_path, 'w', encoding='utf-8') as f:
            f.write(diary_content)
        
        return str(diary_path)
    
    def get_next_day_number(self, runs_dir: str) -> int:
        """Determine the next day number based on existing diaries"""
        runs_path = Path(runs_dir)
        if not runs_path.exists():
            return 1
            
        max_day = 0
        for session_dir in runs_path.iterdir():
            if session_dir.is_dir() and session_dir.name.startswith("session_"):
                for diary_file in session_dir.glob("diary_day_*.md"):
                    try:
                        day_num = int(diary_file.stem.split("_")[-1])
                        max_day = max(max_day, day_num)
                    except ValueError:
                        continue
        
        return max_day + 1

# Example usage
if __name__ == "__main__":
    # Test with sample data
    sample_session = {
        "session_id": "20250621_125351",
        "goal": "explore viridian forest and win all pokemon battles",
        "turns": [
            {
                "turn": 1,
                "ai_analysis": "Ash is in Viridian Forest, ready to explore!",
                "button_presses": ["right"]
            },
            {
                "turn": 15,
                "ai_analysis": "Ash spots a trainer ahead and gets excited for battle!",
                "button_presses": ["up", "a"]
            }
        ]
    }
    
    diary_gen = PokemonEpisodeDiary()
    episode = diary_gen.generate_episode_diary(sample_session, 1)
    print(episode)