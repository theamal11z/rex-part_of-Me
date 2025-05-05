import re
import random
from typing import Optional, List, Dict, Any

def detect_language(text: str) -> str:
    """
    Detect whether the text is primarily in English or Hinglish.
    This is a simple heuristic and could be enhanced with proper NLP.
    """
    # Check for common Hinglish words or patterns
    hinglish_patterns = [
        'kya', 'hai', 'nahi', 'acha', 'theek', 'haan', 'kaise',
        'kyun', 'main', 'tum', 'aap', 'yaar', 'bhai', 'dil'
    ]
    
    text_lower = text.lower()
    hinglish_word_count = sum(1 for word in hinglish_patterns if word in text_lower)
    
    # If more than 2 Hinglish words are found, consider it Hinglish
    if hinglish_word_count > 2:
        return 'hinglish'
    return 'english'

def detect_emotion(text: str) -> str:
    """
    Simple emotion detection from text.
    This could be replaced with a more sophisticated ML model.
    """
    text_lower = text.lower()
    
    happy_words = ['happy', 'joy', 'glad', 'good', 'great', 'wonderful', 'amazing', 'love', '😊', '😀', '😁']
    sad_words = ['sad', 'unhappy', 'depressed', 'bad', 'terrible', 'awful', 'miss', 'lost', '😢', '😭', '😔']
    angry_words = ['angry', 'mad', 'frustrated', 'annoyed', 'upset', 'hate', 'fuck', 'damn', '😡', '😠']
    curious_words = ['curious', 'wonder', 'interested', 'how', 'what', 'when', 'where', 'why', '?']
    
    emotions = {
        'happy': sum(1 for word in happy_words if word in text_lower),
        'sad': sum(1 for word in sad_words if word in text_lower),
        'angry': sum(1 for word in angry_words if word in text_lower),
        'curious': sum(1 for word in curious_words if word in text_lower),
    }
    
    # Find the emotion with the highest count
    max_emotion = max(emotions.items(), key=lambda x: x[1])
    
    # If no strong emotion is detected, return 'neutral'
    if max_emotion[1] == 0:
        return 'neutral'
    
    return max_emotion[0]

def extract_username(text: str) -> Optional[str]:
    """
    Try to extract a username from the text.
    """
    # Look for "I am [name]" or "my name is [name]" patterns
    patterns = [
        r"i am (\w+)",
        r"my name is (\w+)",
        r"i'm (\w+)",
        r"call me (\w+)",
        r"this is (\w+)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1).capitalize()
    
    return None

def generate_follow_up_question(context: Dict[str, Any]) -> str:
    """
    Generate a thoughtful follow-up question based on context.
    """
    general_questions = [
        "What brings you here today?",
        "How are you feeling right now?",
        "What's been on your mind lately?",
        "Is there something specific you'd like to talk about?",
        "What are you passionate about?",
        "What's your story?"
    ]
    
    emotional_questions = {
        'happy': [
            "What's bringing you joy today?",
            "What are you celebrating?",
            "What's making you smile right now?"
        ],
        'sad': [
            "What's weighing on your heart?",
            "Would talking about it help?",
            "Is there something I can do to support you?"
        ],
        'angry': [
            "What's frustrating you?",
            "What would help you feel better?",
            "What do you need right now?"
        ],
        'curious': [
            "What are you wondering about?",
            "What sparks your curiosity?",
            "What would you like to explore together?"
        ],
        'neutral': general_questions
    }
    
    emotion = context.get('emotional_tone', 'neutral')
    questions = emotional_questions.get(emotion, general_questions)
    
    return random.choice(questions)
