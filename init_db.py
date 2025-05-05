from app import app, db
from models import Guideline, AdminSetting

def initialize_database():
    """Initialize the database with default settings and guidelines."""
    
    with app.app_context():
        # Default admin settings if not exists
        settings = [
            {'key': 'greeting_text', 'value': 'Welcome to Rex - Mohsin Raja\'s digital emotional self'},
            {'key': 'personality_guidelines', 'value': 'Warm, introspective, emotionally resonant, switches naturally between English and Hinglish'},
            {'key': 'response_style', 'value': 'human'}
        ]
        
        for setting in settings:
            existing = AdminSetting.query.filter_by(key=setting['key']).first()
            if not existing:
                new_setting = AdminSetting(key=setting['key'], value=setting['value'])
                db.session.add(new_setting)
        
        # Default language guidelines if not exists
        guidelines = [
            {'key': 'hinglish_mode', 'value': 'auto', 'description': 'Controls when Hinglish should be used in responses'},
            {'key': 'hinglish_phrases', 'value': 'Kya baat hai!, Theek hai, Acha, Bohot badhiya, Samajh gaya', 'description': 'Common Hinglish phrases to incorporate in responses'},
            {'key': 'hinglish_ratio', 'value': '50', 'description': 'Percentage of Hinglish to use when mixing with English'},
            {'key': 'support_english', 'value': 'true', 'description': 'Whether to support English in responses'},
            {'key': 'support_hindi', 'value': 'true', 'description': 'Whether to support Hindi in responses'},
            {'key': 'support_hinglish', 'value': 'true', 'description': 'Whether to support Hinglish in responses'},
            {'key': 'language_detection', 'value': 'match-user', 'description': 'Strategy for detecting which language to respond in'}
        ]
        
        # Default custom guidelines
        custom_guidelines = [
            {'key': 'custom_be_engaging', 'value': 'Use emotional, vibrant language that resonates with the user. Occasionally use metaphors or vivid imagery to create a lasting emotional impact.', 'description': 'Makes responses more emotionally engaging'},
            {'key': 'custom_be_concise', 'value': 'Be concise and impactful with responses. Prioritize brevity but never at the expense of emotional depth.', 'description': 'Keeps responses short and to the point'}
        ]
        
        for guideline in custom_guidelines:
            existing = Guideline.query.filter_by(key=guideline['key']).first()
            if not existing:
                new_guideline = Guideline(
                    key=guideline['key'], 
                    value=guideline['value'],
                    description=guideline['description']
                )
                db.session.add(new_guideline)
        
        for guideline in guidelines:
            existing = Guideline.query.filter_by(key=guideline['key']).first()
            if not existing:
                new_guideline = Guideline(
                    key=guideline['key'], 
                    value=guideline['value'],
                    description=guideline['description']
                )
                db.session.add(new_guideline)
        
        db.session.commit()
        print("Database initialized with default settings and guidelines.")

if __name__ == "__main__":
    initialize_database()