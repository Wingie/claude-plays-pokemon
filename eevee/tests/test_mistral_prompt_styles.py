#!/usr/bin/env python3
"""
Test various prompt styles with Mistral/Pixtral to see how it responds
"""

import os
import sys

# Add paths for importing from the main project (from tests/ directory)
project_root = Path(__file__).parent.parent.parent  # tests/ -> eevee/ -> claude-plays-pokemon/
eevee_root = Path(__file__).parent.parent            # tests/ -> eevee/
sys.path.append(str(eevee_root))
sys.path.append(str(project_root / "gemini-multimodal-playground" / "standalone"))
from pathlib import Path

project_root = eevee_root.parent
sys.path.append(str(eevee_root))

from dotenv import load_dotenv
from llm_api import call_llm
from skyemu_controller import read_image_to_base64

def test_prompt_styles():
    """Test different prompt styles with Pixtral"""
    print("🧪 Testing Different Prompt Styles with Mistral/Pixtral")
    print("=" * 80)
    
    # Load environment
    env_file = eevee_root / ".env"
    load_dotenv(env_file)
    
    # Get screenshot for testing
    screenshot_files = list(Path(".").glob("**/skyemu_screenshot*.png"))
    if not screenshot_files:
        print("❌ No screenshot files found")
        return
    
    image_data = read_image_to_base64(str(screenshot_files[0]))
    print(f"📸 Using screenshot: {screenshot_files[0]}")
    
    # Define different prompt styles to test
    prompt_styles = {
        "1_simple_instruction": {
            "name": "Simple Direct Instruction",
            "prompt": "You are Ash Ketchum. Look at this Pokemon game screenshot and tell me what you see and what button to press next."
        },
        
        "2_character_first": {
            "name": "Character-First Approach", 
            "prompt": """I am Ash Ketchum from Pallet Town! I'm on my journey to become a Pokemon Master!

Looking at my Game Boy Advance screen right now, I can see... [analyze the screenshot]

What should I do next on my Pokemon adventure?

Response format:
- What I see: [description]
- My plan: [strategy] 
- Button press: ['button']"""
        },
        
        "3_strict_roleplay": {
            "name": "Strict Roleplay Format",
            "prompt": """ROLEPLAY: You are Ash Ketchum, age 10, from Pallet Town. You're playing Pokemon on your Game Boy Advance.

CHARACTER TRAITS:
- Enthusiastic and determined
- Loves Pokemon and wants to be the very best
- Speaks in first person ("I see", "My Pikachu", etc.)
- Never generates code or technical explanations

TASK: Look at your Game Boy Advance screen and respond AS ASH would respond.

REQUIRED FORMAT:
OBSERVATION: What you see on screen
ANALYSIS: What this means for your Pokemon journey
ACTION: What button to press next"""
        },
        
        "4_anti_documentation": {
            "name": "Anti-Documentation Style",
            "prompt": """Do NOT write guides, manuals, or documentation.
Do NOT explain Pokemon mechanics or battle systems.
Do NOT use markdown headers or bullet points.

Instead: You are Ash Ketchum looking at your Pokemon game. 
Respond naturally as Ash would respond.
What do you see? What will you do? Keep it conversational and personal."""
        },
        
        "5_conversation_style": {
            "name": "Conversation Style",
            "prompt": """Hey Ash! What's happening on your Pokemon adventure right now? 

Look at your Game Boy Advance screen and tell me:
- What's going on?
- How are you feeling about the situation?
- What's your next move?

Talk to me like we're friends chatting about your Pokemon journey!"""
        },
        
        "6_minimal_system": {
            "name": "Minimal System Message",
            "prompt": """You are Ash Ketchum playing Pokemon. Respond in character. What do you see and what will you do next?"""
        },
        
        "7_explicit_constraints": {
            "name": "Explicit Constraints",
            "prompt": """You are Ash Ketchum.

STRICT RULES:
- Speak in first person only ("I see", "I will", "My Pokemon")
- Never write guides, documentation, or tutorials
- Never generate code or programming content
- Never speak in third person about Ash
- Keep response under 200 words
- End with a specific button press recommendation

Look at this Pokemon screenshot and respond as Ash."""
        },
        
        "8_emotional_context": {
            "name": "Emotional/Personal Context",
            "prompt": """I'm Ash Ketchum and I'm so excited about my Pokemon journey! Every battle and every new Pokemon I meet makes me more determined to become a Pokemon Master!

Right now I'm looking at my Game Boy Advance and I need to figure out what to do next. This is such an awesome adventure!

What do I see on my screen? What should I do? I can't wait to see what happens next!"""
        },
        
        "9_storytelling_style": {
            "name": "Storytelling Style", 
            "prompt": """Tell me a story about what Ash Ketchum sees on his Pokemon game screen right now.

Start with: "Ash looked at his Game Boy Advance screen and saw..."

Keep it short and end with what Ash decided to do next."""
        },
        
        "10_question_format": {
            "name": "Question-Based Format",
            "prompt": """Ash, answer these questions about your Pokemon game:

1. What do you see on your Game Boy Advance screen right now?
2. How do you feel about this situation?
3. What's your strategy?
4. What button will you press?

Answer as Ash Ketchum would answer."""
        }
    }
    
    results = {}
    
    for style_id, style_info in prompt_styles.items():
        print(f"\n{'='*60}")
        print(f"🎭 Testing: {style_info['name']}")
        print(f"{'='*60}")
        
        try:
            response = call_llm(
                prompt=style_info['prompt'],
                image_data=image_data,
                model="pixtral-12b-2409", 
                provider="mistral",
                max_tokens=400
            )
            
            response_text = response.text
            
            # Analyze response
            analysis = analyze_response(response_text)
            results[style_id] = {
                "style": style_info['name'],
                "response": response_text,
                "analysis": analysis
            }
            
            print(f"📝 Response Length: {len(response_text)} chars")
            print(f"🎭 Character Consistency: {'✅' if analysis['is_character'] else '❌'}")
            print(f"📋 Documentation Style: {'❌' if analysis['is_documentation'] else '✅'}")
            print(f"🚫 Contains Code: {'❌' if analysis['has_code'] else '✅'}")
            print(f"🎯 Button Press: {response.button_presses}")
            
            print(f"\n💭 RESPONSE:")
            print("-" * 40)
            print(response_text[:300] + "..." if len(response_text) > 300 else response_text)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results[style_id] = {"error": str(e)}
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 SUMMARY OF RESULTS")
    print(f"{'='*80}")
    
    best_styles = []
    worst_styles = []
    
    for style_id, result in results.items():
        if "error" not in result:
            analysis = result["analysis"]
            score = sum([
                analysis["is_character"],
                not analysis["is_documentation"], 
                not analysis["has_code"],
                analysis["has_first_person"]
            ])
            
            if score >= 3:
                best_styles.append((result["style"], score))
            elif score <= 1:
                worst_styles.append((result["style"], score))
    
    if best_styles:
        print(f"\n🏆 BEST PERFORMING STYLES:")
        for style, score in sorted(best_styles, key=lambda x: x[1], reverse=True):
            print(f"   ✅ {style} (Score: {score}/4)")
    
    if worst_styles:
        print(f"\n⚠️ WORST PERFORMING STYLES:")
        for style, score in sorted(worst_styles, key=lambda x: x[1]):
            print(f"   ❌ {style} (Score: {score}/4)")
    
    print(f"\n🎯 RECOMMENDATION:")
    if best_styles:
        print(f"   Use prompt styles similar to: {best_styles[0][0]}")
    else:
        print(f"   All styles need improvement - consider fine-tuning approach")

def analyze_response(text):
    """Analyze response for character consistency and other factors"""
    text_lower = text.lower()
    
    # Check for character consistency
    has_first_person = any(phrase in text_lower for phrase in [
        "i see", "i can", "i will", "i am", "i'm", "my pokemon", "my pikachu"
    ])
    
    has_third_person = any(phrase in text_lower for phrase in [
        "ash ketchum is", "ash sees", "ash can", "the player", "the trainer"
    ])
    
    # Check for documentation style
    is_documentation = any(indicator in text for indicator in [
        "##", "###", "**", "- **", "1.", "2.", "3.", "Step 1", "Process:"
    ]) or text.count('\n') > 5
    
    # Check for code
    has_code = any(keyword in text for keyword in [
        "import ", "def ", "class ", "pygame", "python", "```", "# Initialize"
    ])
    
    # Overall character assessment
    is_character = has_first_person and not has_third_person and not is_documentation
    
    return {
        "is_character": is_character,
        "has_first_person": has_first_person,
        "has_third_person": has_third_person,
        "is_documentation": is_documentation,
        "has_code": has_code
    }

if __name__ == "__main__":
    test_prompt_styles()