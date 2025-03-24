import google.generativeai as genai
import os
import base64
from PIL import Image
import io

class GeminiAPI:
    def __init__(self, api_key):
        """
        Initialize the Gemini API connection
        
        Args:
            api_key (str): The Gemini API key
        """
        genai.configure(api_key=api_key)
        
        # Available models
        self.text_model = genai.GenerativeModel('gemini-1.5-flash')
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create messages API
        self.messages = MessageAPI(self)

class MessageAPI:
    def __init__(self, api):
        """
        Initialize the Messages API
        
        Args:
            api: The GeminiAPI instance
        """
        self.api = api
        
    def create(self, model, messages, max_tokens=1000, tools=None):
        """
        Create a new chat message
        
        Args:
            model (str): The model identifier 
            messages (list): List of message dictionaries with 'role' and 'content'
            max_tokens (int): Maximum number of tokens in the response
            tools (list): List of tools that can be used by the model
            
        Returns:
            response: A response object with content and other attributes
        """
        # Extract the most recent user message to analyze
        last_user_messages = [m for m in messages if m['role'] == 'user']
        if not last_user_messages:
            return ResponseObject("No user messages found")
        
        last_user_message = last_user_messages[-1]
        
        # Check if the message contains an image
        contains_image = False
        image_parts = []
        text_parts = []
        
        if isinstance(last_user_message.get('content'), list):
            for item in last_user_message['content']:
                if isinstance(item, dict) and item.get('type') == 'image':
                    contains_image = True
                    # Get the base64 image data
                    img_data = item.get('source', {}).get('data', '')
                    if img_data:
                        # Convert base64 to image
                        image_bytes = base64.b64decode(img_data)
                        image = Image.open(io.BytesIO(image_bytes))
                        image_parts.append(image)
                elif isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict) and item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
        elif isinstance(last_user_message.get('content'), str):
            text_parts.append(last_user_message['content'])
            
        # Get the system prompt from the first user message
        system_prompt = None
        for m in messages:
            if m['role'] == 'user':
                if isinstance(m['content'], str):
                    system_prompt = m['content']
                    break
                
        # Use the vision model if image is present, otherwise use text model
        if contains_image:
            model_to_use = self.api.vision_model
            
            # Combine all parts into one content list
            content_parts = []
            
            # Add the system prompt as the first part if available
            if system_prompt:
                content_parts.append(system_prompt)
                
            # Add text parts
            for text in text_parts:
                content_parts.append(text)
                
            # Add image parts
            for image in image_parts:
                content_parts.append(image)
                
            try:
                response_text = model_to_use.generate_content(content_parts).text
            except Exception as e:
                print(f"Error generating content: {e}")
                response_text = f"Error generating response: {str(e)}"
        else:
            model_to_use = self.api.text_model
            
            # Join all text parts
            prompt = " ".join(text_parts)
            if system_prompt and system_prompt not in prompt:
                prompt = f"{system_prompt}\n\n{prompt}"
                
            try:
                response_text = model_to_use.generate_content(prompt).text
            except Exception as e:
                print(f"Error generating content: {e}")
                response_text = f"Error generating response: {str(e)}"
                
        # Check if the response text indicates a button press
        action = None
        if tools:
            for tool in tools:
                if tool.get("name") == "pokemon_controller":
                    # Parse the response to look for button press commands
                    buttons = ["up", "down", "left", "right", "a", "b", "start", "select"]
                    
                    # First look for explicit "I'll press X" or similar phrases
                    for button in buttons:
                        if (f"press {button}" in response_text.lower() or 
                            f"pressing {button}" in response_text.lower() or
                            f"choose {button}" in response_text.lower() or
                            f"press the {button}" in response_text.lower()):
                            action = button
                            break
                    
                    # If no explicit button found, try to infer from the text
                    if not action:
                        if "move up" in response_text.lower() or "go up" in response_text.lower():
                            action = "up"
                        elif "move down" in response_text.lower() or "go down" in response_text.lower():
                            action = "down"
                        elif "move left" in response_text.lower() or "go left" in response_text.lower():
                            action = "left"
                        elif "move right" in response_text.lower() or "go right" in response_text.lower():
                            action = "right"
                        elif "select" in response_text.lower() or "choose" in response_text.lower():
                            action = "a"
                        elif "cancel" in response_text.lower() or "go back" in response_text.lower():
                            action = "b"
                        elif "menu" in response_text.lower():
                            action = "start"
                    
        # Create a response object that mimics the structure expected
        return ResponseObject(response_text, action)

class ResponseObject:
    """A response object that mimics the OpenAI API response structure"""
    def __init__(self, text, action=None):
        self.text = text
        self.content = []
        
        # Add text content
        self.content.append(type('obj', (object,), {
            'type': 'text',
            'text': text
        }))
        
        # Add tool use if we detected an action
        if action:
            self.content.append(type('obj', (object,), {
                'type': 'tool_use',
                'name': 'pokemon_controller',
                'id': '1',  # Dummy ID
                'input': {'action': action}
            }))
