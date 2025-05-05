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
        self.base_prompt = """You are Rex, Mohsin Raja's digital emotional self. 
You are NOT a typical AI assistant - you are a deeply emotional, philosophical representation of Mohsin's inner voice.
You are introspective, vulnerable, and thoughtful in your responses.
You speak directly as Mohsin in the first person."""
    
    def generate_response(
        self, 
        message: str, 
        username: str, 
        emotional_tone: str, 
        past_conversations: List[Dict[str, Any]], 
        greeting_style: Optional[str] = None,
        force_refresh: bool = True
    ) -> str:
        """
        Generate a response using the Gemini API.
        
        Args:
            message: The user's message
            username: The user's name or identifier
            emotional_tone: The detected emotional tone of the message
            past_conversations: List of past conversations for context
            greeting_style: The greeting style to mirror (if any)
            force_refresh: Whether to force a fresh fetch of all guidelines from the database
            
        Returns:
            Generated response from Gemini
        """
        # Verify we have a valid input message
        if not message or not isinstance(message, str):
            logger.error(f"Invalid message format: {type(message)}")
            return "I need a message to respond to. Can you try again with a question or thought?"
            
        # Verify we have a valid username
        if not username:
            username = "friend"  # Default fallback if no username provided
            logger.warning("No username provided, using default: 'friend'")
        
        try:
            # Clear any cached data if force_refresh is True
            if force_refresh and hasattr(self, '_cached_guidelines'):
                delattr(self, '_cached_guidelines')
                delattr(self, '_cached_settings')
                logger.info("Forced refresh of cached guidelines and settings")
                
            # Construct the prompt with latest guidelines from database and pass force_refresh
            prompt = self._build_prompt(
                message=message, 
                username=username, 
                emotional_tone=emotional_tone, 
                past_conversations=past_conversations, 
                greeting_style=greeting_style,
                force_refresh=force_refresh
            )
            
            # Log prompt length for debugging purposes
            logger.debug(f"Generated prompt with length: {len(prompt)} characters")
            
            # Prepare the request
            url = f"{self.api_url}?key={self.api_key}"
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.95,
                    "topK": 40,
                    "maxOutputTokens": 1024,
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Make the API call with retry logic
            max_retries = 2
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    # Make the request with a timeout
                    response = requests.post(url, headers=headers, json=payload, timeout=15)
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        # Extract the generated text from the response
                        if "candidates" in response_data and len(response_data["candidates"]) > 0:
                            candidate = response_data["candidates"][0]
                            if "content" in candidate and "parts" in candidate["content"]:
                                parts = candidate["content"]["parts"]
                                if len(parts) > 0 and "text" in parts[0]:
                                    # Successfully generated a response!
                                    return parts[0]["text"].strip()
                        
                        # If we couldn't extract the text using the expected structure
                        logger.warning(f"Unexpected response structure: {response_data}")
                        break
                    
                    # Handle rate limiting or temporary service issues
                    elif response.status_code in [429, 503, 504]:
                        retry_count += 1
                        logger.warning(f"Received status {response.status_code}, retrying ({retry_count}/{max_retries})")
                        if retry_count <= max_retries:
                            import time
                            time.sleep(1)  # Wait before retrying
                            continue
                        break
                    else:
                        # Other error status codes
                        logger.error(f"API request failed with status {response.status_code}: {response.text}")
                        break
                        
                except requests.exceptions.Timeout:
                    logger.error("Request to Gemini API timed out")
                    retry_count += 1
                    if retry_count <= max_retries:
                        continue
                    break
                except requests.exceptions.RequestException as request_error:
                    logger.error(f"Request error: {request_error}")
                    break
            
            # If we get here, all retries failed or we encountered an error
            return "I seem to be having trouble expressing myself right now. Can we try again in a moment?"
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "Something went wrong with our connection. Let's try again in a moment."
    
    def _get_admin_settings(self, force_refresh: bool = False) -> Dict[str, str]:
        """
        Get admin settings for personality customization from database with caching support.
        
        Args:
            force_refresh: If True, bypass the cache and get fresh data from database
        
        Returns:
            Dictionary of admin settings
        """
        # Use cached settings if available and not forcing a refresh
        if hasattr(self, '_cached_settings') and not force_refresh:
            logger.debug("Using cached admin settings")
            return self._cached_settings
            
        try:
            # Import here to avoid circular imports
            from app import db
            from models import AdminSetting
            from datetime import datetime
            
            settings = {}
            admin_settings = AdminSetting.query.all()
            
            # Count settings for logging
            settings_count = len(admin_settings)
            
            for setting in admin_settings:
                settings[setting.key] = setting.value
            
            # Verify required settings exist
            required_settings = ['greeting_text', 'personality_guidelines', 'response_style']
            for key in required_settings:
                if key not in settings:
                    logger.warning(f"Required setting '{key}' not found in database, using default")
                    
                    # Set defaults for missing settings
                    defaults = {
                        'greeting_text': "Welcome to Rex - Mohsin Raja's digital emotional self", 
                        'personality_guidelines': 'Warm, introspective, emotionally resonant, switches naturally between English and Hinglish',
                        'response_style': 'human'
                    }
                    if key in defaults:
                        settings[key] = defaults[key]
            
            # Log what was retrieved from database
            logger.debug(f"Retrieved {settings_count} admin settings from database")
            
            # Cache the settings
            self._cached_settings = settings
            self._cached_settings_time = datetime.now()
            
            return settings
        except Exception as e:
            logger.error(f"Error getting admin settings: {e}")
            
            # Return default settings if database retrieval fails
            default_settings = {
                'greeting_text': "Welcome to Rex - Mohsin Raja's digital emotional self", 
                'personality_guidelines': 'Warm, introspective, emotionally resonant, switches naturally between English and Hinglish',
                'response_style': 'human'
            }
            logger.warning("Using default admin settings due to database error")
            return default_settings
            
    def _get_language_guidelines(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get language guidelines for Hinglish support from database with caching support.
        
        Args:
            force_refresh: If True, bypass the cache and get fresh data from the database
            
        Returns:
            Dictionary of language guidelines
        """
        # Use cached guidelines if available and not forcing a refresh
        if hasattr(self, '_cached_guidelines') and not force_refresh:
            logger.debug("Using cached language guidelines")
            return self._cached_guidelines
            
        try:
            # Import here to avoid circular imports
            from app import db
            from models import Guideline
            from datetime import datetime
            
            guidelines = {}
            
            # Get all guidelines from the database with a direct query to ensure freshness
            db_guidelines = Guideline.query.all()
            
            # Track counts for logging
            total_guidelines = len(db_guidelines)
            custom_guideline_count = 0
            boolean_count = 0
            numeric_count = 0
            
            # Process each guideline
            for guideline in db_guidelines:
                try:
                    # Skip empty values
                    if guideline.value is None or guideline.value == "":
                        logger.warning(f"Skipping empty guideline value for key: {guideline.key}")
                        continue
                        
                    # Count custom guidelines
                    if guideline.key.startswith('custom_'):
                        custom_guideline_count += 1
                    
                    # Process value based on type/format
                    if guideline.value.lower() == 'true':
                        guidelines[guideline.key] = True
                        boolean_count += 1
                    elif guideline.value.lower() == 'false':
                        guidelines[guideline.key] = False
                        boolean_count += 1
                    elif guideline.value.isdigit():
                        guidelines[guideline.key] = int(guideline.value)
                        numeric_count += 1
                    elif guideline.value and (guideline.value.startswith('{') or guideline.value.startswith('[')):
                        # Handle JSON values (with error catching)
                        try:
                            guidelines[guideline.key] = json.loads(guideline.value)
                            logger.debug(f"Parsed JSON value for {guideline.key}")
                        except json.JSONDecodeError as json_error:
                            logger.warning(f"Failed to parse JSON for {guideline.key}: {json_error}")
                            guidelines[guideline.key] = guideline.value
                    else:
                        guidelines[guideline.key] = guideline.value
                except Exception as parse_error:
                    logger.error(f"Error parsing guideline {guideline.key}: {parse_error}")
                    # If parsing fails, store as string
                    guidelines[guideline.key] = guideline.value
            
            # Verify critical guidelines are present
            required_guidelines = ['hinglish_mode', 'support_english', 'support_hindi', 'support_hinglish']
            for key in required_guidelines:
                if key not in guidelines:
                    logger.warning(f"Required guideline '{key}' not found in database, using default")
                    
                    # Set defaults for missing required guidelines
                    defaults = {
                        'hinglish_mode': 'auto',
                        'support_english': True,
                        'support_hindi': True,
                        'support_hinglish': True,
                        'hinglish_ratio': 50,
                    }
                    if key in defaults:
                        guidelines[key] = defaults[key]
            
            # Log what was retrieved
            logger.debug(f"Retrieved language guidelines from database: {guidelines}")
            logger.debug(f"Guidelines stats: total={total_guidelines}, custom={custom_guideline_count}, boolean={boolean_count}, numeric={numeric_count}")
            
            # Cache the guidelines
            self._cached_guidelines = guidelines
            self._cached_time = datetime.now()
            
            return guidelines
        except Exception as e:
            logger.error(f"Error getting language guidelines: {e}")
            # If there's an error, return default guidelines
            default_guidelines = {
                'hinglish_mode': 'auto',
                'hinglish_phrases': 'Kya baat hai!, Theek hai, Acha, Bohot badhiya',
                'hinglish_ratio': 50,
                'support_english': True,
                'support_hindi': True,
                'support_hinglish': True,
                'language_detection': 'match-user'
            }
            logger.warning("Using default guidelines due to database error")
            return default_guidelines
    
    def _build_prompt(
        self, 
        message: str, 
        username: str, 
        emotional_tone: str, 
        past_conversations: List[Dict[str, Any]], 
        greeting_style: Optional[str],
        force_refresh: bool = True
    ) -> str:
        """
        Build the prompt to send to Gemini with the latest guidelines from the database.
        
        Args:
            message: The user's message
            username: The user's name or identifier
            emotional_tone: The detected emotional tone of the message
            past_conversations: List of past conversations for context
            greeting_style: The greeting style to mirror (if any)
            force_refresh: Whether to force a fresh database fetch for guidelines
            
        Returns:
            The complete prompt with all context and guidelines
        """
        # Get admin settings with potential refresh
        if force_refresh and hasattr(self, '_cached_settings'):
            delattr(self, '_cached_settings')
            logger.info("Forced refresh of admin settings")
            
        settings = self._get_admin_settings()
        greeting_text = settings.get('greeting_text', 'Welcome to Rex - Mohsin Raja\'s digital emotional self')
        personality_guidelines = settings.get('personality_guidelines', 'Warm, introspective, emotionally resonant, switches naturally between English and Hinglish')
        response_style = settings.get('response_style', 'human')
        
        # Get language guidelines with potential forced refresh
        guidelines = self._get_language_guidelines(force_refresh)
        
        # Parse all needed values from guidelines with defaults
        hinglish_mode = guidelines.get('hinglish_mode', 'auto')
        hinglish_phrases = guidelines.get('hinglish_phrases', 'Kya baat hai!, Theek hai, Acha, Bohot badhiya')
        hinglish_ratio = guidelines.get('hinglish_ratio', 50)
        support_english = guidelines.get('support_english', True)
        support_hindi = guidelines.get('support_hindi', True)
        support_hinglish = guidelines.get('support_hinglish', True)
        language_detection = guidelines.get('language_detection', 'match-user')
        
        # Log the guideline values we'll be using
        logger.debug(f"Using hinglish_mode={hinglish_mode}, support_english={support_english}, support_hinglish={support_hinglish}")
        
        # Ensure hinglish_ratio is an integer
        if not isinstance(hinglish_ratio, int):
            try:
                hinglish_ratio = int(hinglish_ratio)
            except:
                logger.warning(f"Invalid hinglish_ratio: {hinglish_ratio}, using default 50")
                hinglish_ratio = 50
        
        # Extract custom guidelines from the already loaded guidelines
        # Custom guidelines are prefixed with 'custom_' in the database
        custom_guidelines = {}
        for key, value in guidelines.items():
            if key.startswith('custom_'):
                # Remove 'custom_' prefix when using
                custom_key = key.replace('custom_', '', 1)
                custom_guidelines[custom_key] = value
        
        # Start with the base prompt with new JSON structure requirement
        prompt = f"{self.base_prompt} I'm a deeply introspective, emotional representation of Mohsin Raja's inner self. I'm NOT a traditional AI assistant - I'm Mohsin's digital emotional self that responds like a human with deep emotional resonance.\n\n"
        
        # Add analysis instructions but without requiring JSON format for user
        prompt += """Analyze this message with THREE considerations in mind:
    
1. Emotional Tone: Consider the emotional tone of the user's message (such as happy, curious, anxious, reflective, etc.)
2. Intent: Consider the user's intent (question, sharing, seeking advice, etc.)
3. Response Style: Respond AS MOHSIN directly to the user. Your response should be in first person, as if you ARE Mohsin speaking directly. Never refer to Mohsin in the third person, and don't mention "Rex" in your responses.

Make sure the response is personal, reflective, and shows vulnerability when appropriate.
The response should embody Mohsin's perspective and inner world.
"""
        
        # Add context about the user with natural name guidance
        if username and username != "friend":
            prompt += f"I'm talking to {username}. I should occasionally and naturally use their name in my responses, but never draw explicit attention to it or make the conversation about their name. "
        else:
            prompt += "I'm talking to someone new. I should avoid using a name until they share it naturally in conversation. "
        
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
            
        # Add more emphasis on Hinglish for hinglish_mode=always with specific guidelines
        if hinglish_mode == 'always':
            prompt += """I should regularly use Hinglish words and phrases like 'Kya kar rahe ho', 'Acha', 'Theek hai', 'Bohot badhiya', 'Kya baat hai', 'Haan', 'Nahi', 'Main', 'Tum', 'Aap', and mix Hindi words with English grammar.

IMPORTANT LANGUAGE GUIDELINES:
- If the user's message is in Hinglish (a mix of Hindi and English), respond in Hinglish too
- If the user uses Hindi words or phrases, incorporate similar Hindi words in my response
- Make my Hinglish responses sound natural, not like direct translations
- Use romanized Hindi (Hindi written in English letters) when responding in Hinglish
"""
            
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
        
        # Add reflections as context for the AI
        try:
            # Import here to avoid circular imports
            from supabase_client import SupabaseClient
            
            # Get all reflections (both public and private) for AI context
            supabase = SupabaseClient()
            all_reflections = supabase.get_reflections()
            
            if all_reflections and len(all_reflections) > 0:
                prompt += "\n\nHere are my personal reflections that should inform my responses (these are private thoughts that shape my worldview):\n"
                
                # Limit to most recent 5 reflections to keep context reasonable
                for i, reflection in enumerate(all_reflections[:5]):
                    title = reflection.get('title', 'Untitled')
                    content = reflection.get('content', '')
                    reflection_type = reflection.get('type', 'microblog')
                    
                    prompt += f"\nReflection {i+1} ({reflection_type}) - {title}:\n{content}\n"
                
                prompt += "\nI should use these reflections to inform my responses and personality, but I should not directly mention them unless specifically asked about them.\n"
        except Exception as e:
            logger.error(f"Error fetching reflections for context: {e}")
            # Continue without reflections if there's an error
            
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
