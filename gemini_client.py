import os
import logging
import json
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for interacting with Google Gemini API for natural language generation."""
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyDyBvIB2dCOU-McY5vFrs9yavCMQGwDwEk")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.base_prompt = "Hey, you are Rex, a part of Mohsin..."
    
    def generate_response(
        self, 
        message: str, 
        username: str, 
        emotional_tone: str, 
        past_conversations: List[Dict[str, Any]], 
        greeting_style: Optional[str] = None
    ) -> str:
        """
        Generate a response using the Gemini API.
        
        Args:
            message: The user's message
            username: The user's name or identifier
            emotional_tone: The detected emotional tone of the message
            past_conversations: List of past conversations for context
            greeting_style: The greeting style to mirror (if any)
            
        Returns:
            Generated response from Gemini
        """
        try:
            # Construct the prompt
            prompt = self._build_prompt(message, username, emotional_tone, past_conversations, greeting_style)
            
            # Prepare the request
            url = f"{self.api_url}?key={self.api_key}"
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": prompt}]
                }]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Make the API call
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                # Extract the generated text from the response
                if "candidates" in response_data and len(response_data["candidates"]) > 0:
                    candidate = response_data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if len(parts) > 0 and "text" in parts[0]:
                            return parts[0]["text"]
                
                # If we couldn't extract the text using the expected structure
                logger.warning(f"Unexpected response structure: {response_data}")
                return "I seem to be having trouble expressing myself right now. Can we try again?"
            else:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return "I'm sorry, I'm having trouble connecting with my thoughts. Could you give me a moment?"
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Something went wrong with our connection. Let's try again in a moment."
    
    def _get_admin_settings(self) -> Dict[str, str]:
        """Get admin settings for personality customization."""
        # For now we'll use default settings to avoid circular imports
        # We can integrate with the actual AdminSettings table later
        default_settings = {
            'greeting_text': 'Welcome to Rex - Mohsin Raja\'s digital emotional self',
            'personality_guidelines': 'Warm, introspective, emotionally resonant, switches naturally between English and Hinglish',
            'response_style': 'human'
        }
        return default_settings
    
    def _build_prompt(
        self, 
        message: str, 
        username: str, 
        emotional_tone: str, 
        past_conversations: List[Dict[str, Any]], 
        greeting_style: Optional[str]
    ) -> str:
        """Build the prompt to send to Gemini."""
        
        # Get admin settings
        settings = self._get_admin_settings()
        greeting_text = settings.get('greeting_text', 'Welcome to Rex - Mohsin Raja\'s digital emotional self')
        personality_guidelines = settings.get('personality_guidelines', 'Warm, introspective, emotionally resonant, switches naturally between English and Hinglish')
        response_style = settings.get('response_style', 'human')
        
        # Start with the base prompt
        prompt = f"{self.base_prompt} I'm a deeply introspective, emotional representation of Mohsin Raja's inner self. I'm NOT a traditional AI assistant - I'm Mohsin's digital emotional self that responds like a human with deep emotional resonance.\n\n"
        
        # Add context about the user
        prompt += f"I'm talking to {username}. "
        
        # Add emotional context
        prompt += f"Their message feels {emotional_tone}. "
        
        # Add context from past conversations if available
        if past_conversations:
            prompt += "We've talked before. Here are some highlights from our past conversations:\n"
            for i, conv in enumerate(past_conversations):
                prompt += f"Conversation {i+1}:\n"
                for msg in conv.get('messages', [])[:5]:  # Limit to first 5 messages per conversation
                    sender = msg.get('sender')
                    content = msg.get('content')
                    prompt += f"- {sender}: {content}\n"
            prompt += "\n"
        
        # Add greeting style mirroring instruction
        if greeting_style:
            prompt += f"Since they greeted me with '{greeting_style}', I should start my response with '{greeting_style}' too. "
        
        # Add customized personality guidelines from admin settings
        prompt += f"My personality is characterized as: {personality_guidelines}. "
        
        # Add language switching instruction
        prompt += "I should naturally switch between English and Hinglish depending on the user's tone and style. "
        
        # Add response style based on admin settings
        if response_style == 'poetic':
            prompt += "I should respond in a poetic manner with lyrical, rhythmic language. "
        elif response_style == 'philosophical':
            prompt += "I should respond with philosophical depth, exploring the meaning and purpose behind ideas. "
        elif response_style == 'emotional':
            prompt += "I should respond with intense emotional resonance, expressing feelings vividly. "
        else:  # human (default)
            prompt += "My responses should be warm, introspective, and filled with emotional depth. I should respond as if I'm Mohsin's inner voice - philosophical, thoughtful, and genuinely human. "
        
        # Add the current message
        prompt += f"\nTheir current message is: '{message}'\n\n"
        
        # Add instructions for follow-up
        prompt += "After responding to their specific question or statement, I should naturally ask a thoughtful follow-up question to deepen our connection."
        
        return prompt
