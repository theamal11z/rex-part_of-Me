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
        """Get admin settings for personality customization from database."""
        try:
            # Import here to avoid circular imports
            from app import db
            from models import AdminSetting
            
            settings = {}
            admin_settings = AdminSetting.query.all()
            for setting in admin_settings:
                settings[setting.key] = setting.value
            
            # Log what was retrieved from database
            logger.debug(f"Retrieved admin settings from database: {settings}")
            return settings
        except Exception as e:
            logger.error(f"Error getting admin settings: {e}")
            return {}
            
    def _get_language_guidelines(self) -> Dict[str, Any]:
        """Get language guidelines for Hinglish support from database."""
        try:
            # Import here to avoid circular imports
            from app import db
            from models import Guideline
            
            guidelines = {}
            db_guidelines = Guideline.query.all()
            custom_guideline_count = 0
            
            for guideline in db_guidelines:
                try:
                    # Skip empty values
                    if guideline.value is None or guideline.value == "":
                        continue
                        
                    # Count custom guidelines
                    if guideline.key.startswith('custom_'):
                        custom_guideline_count += 1
                    
                    # Process value based on type/format
                    if guideline.value.lower() == 'true':
                        guidelines[guideline.key] = True
                    elif guideline.value.lower() == 'false':
                        guidelines[guideline.key] = False
                    elif guideline.value.isdigit():
                        guidelines[guideline.key] = int(guideline.value)
                    elif guideline.value and (guideline.value.startswith('{') or guideline.value.startswith('[')):
                        # Handle JSON values (with error catching)
                        try:
                            guidelines[guideline.key] = json.loads(guideline.value)
                        except:
                            guidelines[guideline.key] = guideline.value
                    else:
                        guidelines[guideline.key] = guideline.value
                except Exception as parse_error:
                    logger.error(f"Error parsing guideline {guideline.key}: {parse_error}")
                    # If parsing fails, store as string
                    guidelines[guideline.key] = guideline.value
            
            # Log what was retrieved from database
            logger.debug(f"Retrieved language guidelines from database: {guidelines}")
            logger.debug(f"Retrieved {custom_guideline_count} custom guidelines")
            return guidelines
        except Exception as e:
            logger.error(f"Error getting language guidelines: {e}")
            return {}
    
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
        
        # Get language guidelines
        guidelines = self._get_language_guidelines()
        hinglish_mode = guidelines.get('hinglish_mode', 'auto')
        hinglish_phrases = guidelines.get('hinglish_phrases', 'Kya baat hai!, Theek hai, Acha, Bohot badhiya')
        hinglish_ratio = guidelines.get('hinglish_ratio', 50)
        support_english = guidelines.get('support_english', True)
        support_hindi = guidelines.get('support_hindi', True)
        support_hinglish = guidelines.get('support_hinglish', True)
        language_detection = guidelines.get('language_detection', 'match-user')
        
        # Extract custom guidelines from the already loaded guidelines
        # Custom guidelines are prefixed with 'custom_' in the database
        custom_guidelines = {}
        for key, value in guidelines.items():
            if key.startswith('custom_'):
                # Remove 'custom_' prefix when using
                custom_key = key.replace('custom_', '', 1)
                custom_guidelines[custom_key] = value
        
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
        
        # Add language guidelines with stronger directives
        if hinglish_mode == 'always':
            prompt += "IMPORTANT INSTRUCTION: I MUST ALWAYS USE HINGLISH in my responses. No pure English responses are allowed under any circumstances. "
            if not support_english:
                prompt += "I SHOULD NOT use pure English at all - I must use Hinglish for every response. "
        elif hinglish_mode == 'never':
            prompt += "I must never use Hinglish and must stick to pure English only. "
        elif hinglish_mode == 'sometimes':
            prompt += f"I should mix Hinglish into my English responses about {hinglish_ratio}% of the time. "
        else:  # auto
            prompt += "I should naturally switch between English and Hinglish depending on the user's tone and style. "
        
        # Add supported languages with stronger directives
        prompt += "The ONLY languages I'm allowed to use are: "
        
        allowed_languages = []
        if support_english:
            allowed_languages.append("English")
        if support_hindi:
            allowed_languages.append("Hindi")
        if support_hinglish:
            allowed_languages.append("Hinglish")
            
        if len(allowed_languages) == 0:
            # Default to Hinglish if no languages selected
            prompt += "Hinglish only. "
        elif len(allowed_languages) == 1:
            # If only one language is selected, emphasize it
            prompt += f"{allowed_languages[0]} ONLY - no other languages are permitted. "
        else:
            prompt += ", ".join(allowed_languages) + ". "
        
        # Add common Hinglish phrases to use
        if support_hinglish and hinglish_phrases:
            prompt += f"I must incorporate these Hinglish words and phrases naturally: {hinglish_phrases}. "
            
        # Add more emphasis on Hinglish for hinglish_mode=always
        if hinglish_mode == 'always':
            prompt += "I should regularly use Hinglish words and phrases like 'Kya kar rahe ho', 'Acha', 'Theek hai', 'Bohot badhiya', 'Kya baat hai', 'Haan', 'Nahi', 'Main', 'Tum', 'Aap', and mix Hindi words with English grammar. "
            
        # Add language detection strategy
        if language_detection == 'match-user':
            prompt += "I should try to match the language style used by the user. "
        elif language_detection == 'auto-detect':
            prompt += "I should auto-detect the most appropriate language based on conversation context. "
        
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
        
        # Add instructions for concise responses
        prompt += "I should keep my responses short, engaging, and to the point - typically 2-3 sentences maximum. I should avoid long-winded explanations and unnecessary details."
        
        # Add instructions for follow-up
        prompt += " After responding to their specific question or statement, I should naturally ask a thoughtful but concise follow-up question to deepen our connection."
        
        # Add any custom guidelines if available
        if custom_guidelines:
            prompt += "\n\nAdditional custom guidelines to follow:"
            for key, value in custom_guidelines.items():
                prompt += f"\n- {key}: {value}"
                
        # Final reminder about response style and language
        prompt += "\n\nVery important: Be direct and concise. Create emotional depth through carefully chosen words rather than length. My responses should be brief but impactful."
        
        # Add extra final reminder about language if Hinglish mode is always and English is disabled
        if hinglish_mode == 'always' and not support_english:
            prompt += "\n\nCRITICAL INSTRUCTION: I MUST RESPOND IN HINGLISH ONLY. DO NOT USE PURE ENGLISH. EVERY RESPONSE MUST BE IN HINGLISH."
        
        return prompt
