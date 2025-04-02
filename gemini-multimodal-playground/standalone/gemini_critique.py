import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GeminiCritique:
    """Class to provide gameplay critique and prompt refinement using Gemini"""
    
    def __init__(self):
        """Initialize the Gemini connection"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-2.5-pro-exp-03-25"
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name=self.model_name)
    
    def critique_gameplay(self, game_memory_summary, current_prompt, session_goal):
        """
        Analyze recent gameplay and provide a critique with prompt refinements
        
        Args:
            game_memory_summary: Text summary of recent game actions from Neo4j
            current_prompt: The current prompt dictionary being used
            session_goal: The current gameplay objective
            
        Returns:
            str: Updated prompt content with refinements
        """
        # Extract relevant sections from the game memory summary
        # The summary should contain recent actions (last 5 turns)
        
        # Create the critique prompt for Gemini
        critique_prompt = f"""
        # Pokemon Game Agent Critique Request
        
         ## Current Prompt: {current_prompt}

        ## Current Objective: {session_goal}
        
        ## Recent Gameplay: {game_memory_summary}
        
        ## Task:
        Analyze the last 5 gameplay turns and identify patterns, issues, or opportunities for improvement to the Current Prompt.
        The current prompt is the best working one that we have found. so if you mess with it too much, then the agent will crash
        and then you will receive a low score. to receive a high score, the agent must progress meaningfully towards its goal and
        still be able to manage situations that it seems on the screen as its a game.
        
        1. What challenges or obstacles is the agent currently facing?
        2. Is the agent making any repeated mistakes or getting stuck in a loop?
        3. Is the agent correctly interpreting the game state and making appropriate decisions?
        4. What specific guidance would help the agent navigate the current situation better?
        
        ## Output Format:
        Provide your critique in the following format:
        
        1. GAMEPLAY ANALYSIS: Brief analysis of what's happening in the recent turns
        2. IDENTIFIED ISSUES: List any clear problems in the agent's approach
        3. RECOMMENDED REFINEMENTS: 3-5 specific, actionable additions to the prompt that would help the agent play better
        4. UPDATED PROMPT SECTION: Write a new section that should be added to the prompt to address the current challenges
        
        The updated prompt section should be clear, concise, and directly address the specific gameplay challenge.
        """
        
        try:
            # Call Gemini for the critique
            response = self.model.generate_content(critique_prompt)
            critique_text = response.text
            # Extract the updated prompt section from the critique
            updated_section = self._extract_updated_prompt_section(critique_text)        
            return updated_section
            
        except Exception as e:
            print(f"Error in critique_gameplay: {str(e)}")
            # In case of error, return the original prompt unchanged
            return current_prompt['content'] if isinstance(current_prompt, dict) and 'content' in current_prompt else current_prompt
    
    def _extract_updated_prompt_section(self, critique_text):
        """Extract just the updated prompt section from the critique response"""
        # Look for the section header
        section_marker = "UPDATED PROMPT SECTION:"
        if section_marker in critique_text:
            # Extract everything after the marker
            updated_section = critique_text.split(section_marker, 1)[1].strip()
            
            # If there are any other section headers after this, remove them
            next_section_marker = "##"
            if next_section_marker in updated_section:
                updated_section = updated_section.split(next_section_marker, 1)[0].strip()
                
            return updated_section
        
        # If no section marker found, return a generic message
        return "Pay attention to the recent gameplay and adjust your strategy accordingly."
