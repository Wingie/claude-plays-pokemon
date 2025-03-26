from langchain_core.language_models import BaseLLM
import google.generativeai as genai
import os

class GeminiLLM(BaseLLM):
    def __init__(self, model_name="gemini-2.0-flash"):
        self.model_name = model_name
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(model_name=model_name)
        
    def call(self, prompt, temperature=0.7, max_tokens=None):
        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens or 2048
            }
        )
        return response.text
        
    def stream(self, prompt, temperature=0.7, max_tokens=None):
        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens or 2048
            }
        )
        yield response.text