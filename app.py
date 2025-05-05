import os
import logging
import secrets
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", secrets.token_hex(16))
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension
db.init_app(app)

# Import after db initialization to avoid circular imports
from models import User, Conversation, Message, AdminSetting, Reflection, Guideline
from supabase_client import SupabaseClient
from gemini_client import GeminiClient

# Initialize clients
supabase = SupabaseClient()
gemini = GeminiClient()

# JWT token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.secret_key, algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '')
    username = data.get('username', 'Anonymous')
    conversation_id = data.get('conversation_id')
    
    # Extract emotional tone (could be enhanced with NLP in production)
    emotional_tone = "neutral"  # Default
    if '?' in message:
        emotional_tone = "curious"
    if any(word in message.lower() for word in ['happy', 'glad', 'great', 'good']):
        emotional_tone = "happy"
    if any(word in message.lower() for word in ['sad', 'upset', 'bad', 'terrible']):
        emotional_tone = "sad"
    
    # Check for admin panel trigger
    if message.strip().lower() == "heyopenhereiam":
        return jsonify({
            'message': "Admin panel access requested. Please provide credentials.",
            'admin_request': True
        })
    
    # Handle conversation storage
    past_conversations = []
    
    # For username lookup - only get past conversations if username is provided
    if username:
        # First check if there are any existing conversations for this username
        existing_conversations = supabase.get_conversations_by_username(username)
        
        if existing_conversations and not conversation_id:
            # Use the most recent conversation for this username if no specific ID provided
            conversation_id = existing_conversations[0].get('id')
            app.logger.debug(f"Using existing conversation {conversation_id} for username {username}")
            
        # Get past conversations for context regardless of whether we found one or not
        past_conversations = supabase.get_past_conversations(username, limit=3)
    
    # If we still don't have a conversation ID, create a new one
    if not conversation_id:
        app.logger.debug(f"Creating new conversation for username {username}")
        conversation_id = supabase.create_conversation(username)
    
    # Store the user message
    supabase.store_message(conversation_id, username, message, "user", emotional_tone)
    
    # Get response from Gemini
    greeting_style = detect_greeting_style(message)
    gemini_response = gemini.generate_response(message, username, emotional_tone, past_conversations, greeting_style)
    
    # Handle JSON response format
    try:
        # Try to parse as JSON
        import json
        response_data = json.loads(gemini_response)
        
        # Extract the response field from the JSON
        if "response" in response_data:
            response = response_data["response"]
            # Store additional metadata about emotional tone and intent in logs
            app.logger.info(f"Detected emotional tone: {response_data.get('emotionalTone', 'unknown')}")
            app.logger.info(f"Detected intent: {response_data.get('intent', 'unknown')}")
        else:
            # Fallback if response field is missing
            response = gemini_response
            app.logger.warning(f"JSON response missing 'response' field: {gemini_response}")
    except Exception as e:
        # If not valid JSON or other error, use the whole response
        response = gemini_response
        app.logger.warning(f"Failed to parse JSON response: {e}")
    
    # Store the assistant's response
    supabase.store_message(conversation_id, "Rex", response, "assistant", "matching")
    
    return jsonify({
        'message': response,
        'conversation_id': conversation_id
    })

@app.route('/admin-login', methods=['POST'])
def admin_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    # Hardcoded admin credentials as per requirements
    # In a production environment, these would be securely stored in the database
    if email == "theamal@rex.com" and password == "maothiskian11":
        # Generate JWT token
        token = jwt.encode({
            'user_id': 1,  # Admin user ID
            'exp': datetime.utcnow() + timedelta(days=1)
        }, app.secret_key)
        
        session['token'] = token
        return jsonify({'success': True, 'token': token})
    
    return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/admin')
@token_required
def admin_panel(current_user):
    return render_template('admin.html')

@app.route('/api/conversations')
@token_required
def get_conversations(current_user):
    conversations = supabase.get_all_conversations()
    return jsonify(conversations)

@app.route('/api/conversation/<conversation_id>')
@token_required
def get_conversation_messages(current_user, conversation_id):
    messages = supabase.get_conversation_messages(conversation_id)
    return jsonify(messages)

@app.route('/api/settings', methods=['GET', 'POST'])
@token_required
def manage_settings(current_user):
    if request.method == 'GET':
        settings = supabase.get_settings()
        return jsonify(settings)
    else:
        data = request.json
        supabase.update_settings(data)
        return jsonify({'success': True})

@app.route('/api/reflections', methods=['GET', 'POST', 'PUT', 'DELETE'])
@token_required
def manage_reflections(current_user):
    if request.method == 'GET':
        # Check if we're filtering by type
        reflection_type = request.args.get('type')
        reflections = supabase.get_reflections(reflection_type)
        return jsonify(reflections)
    elif request.method == 'POST':
        data = request.json
        reflection_id = supabase.create_reflection(data)
        return jsonify({'success': True, 'id': reflection_id})
    elif request.method == 'PUT':
        data = request.json
        supabase.update_reflection(data)
        return jsonify({'success': True})
    elif request.method == 'DELETE':
        reflection_id = request.args.get('id')
        supabase.delete_reflection(reflection_id)
        return jsonify({'success': True})
        
@app.route('/api/reflections/public', methods=['GET'])
def get_public_reflections():
    """Get published reflections for public viewing"""
    reflection_type = request.args.get('type')
    reflections = supabase.get_public_reflections(reflection_type)
    return jsonify(reflections)

@app.route('/api/guidelines', methods=['GET', 'POST'])
@token_required
def manage_guidelines(current_user):
    """Manage language guidelines for Hinglish support and language detection"""
    if request.method == 'GET':
        guidelines = supabase.get_guidelines()
        return jsonify(guidelines)
    else:
        data = request.json
        success = supabase.update_guidelines(data)
        return jsonify({'success': success})
        
@app.route('/api/custom-guidelines', methods=['GET', 'POST', 'PUT', 'DELETE'])
@token_required
def manage_custom_guidelines(current_user):
    """Manage custom guidelines for Gemini prompts"""
    if request.method == 'GET':
        # Get all custom guidelines
        custom_guidelines = supabase.get_custom_guidelines()
        return jsonify(custom_guidelines)
    
    elif request.method == 'POST':
        # Create a new custom guideline
        guideline_data = request.json
        success = supabase.create_custom_guideline(guideline_data)
        return jsonify({'success': success})
    
    elif request.method == 'PUT':
        # Update an existing custom guideline
        guideline_data = request.json
        success = supabase.update_custom_guideline(guideline_data)
        return jsonify({'success': success})
    
    elif request.method == 'DELETE':
        # Delete a custom guideline
        guideline_key = request.args.get('key')
        if not guideline_key:
            return jsonify({'success': False, 'error': 'No key provided'})
        
        success = supabase.delete_custom_guideline(guideline_key)
        return jsonify({'success': success})
        
@app.route('/logout', methods=['POST'])
def logout():
    """Log out the current user by clearing the session."""
    session.clear()
    return jsonify({'success': True})

def detect_greeting_style(message):
    """Detect the greeting style from the user's message."""
    message = message.lower().strip()
    
    greetings = {
        "hi": "Hi",
        "hello": "Hello",
        "hey": "Hey",
        "yo": "Yo",
        "sup": "Sup",
        "namaste": "Namaste",
        "hola": "Hola",
        "greetings": "Greetings"
    }
    
    for greeting in greetings:
        if message.startswith(greeting):
            return greetings[greeting]
    
    return None  # No specific greeting detected

# Initialize the database and tables
with app.app_context():
    db.create_all()
    
    # Create admin user if it doesn't exist
    admin = User.query.filter_by(email="theamal@rex.com").first()
    if not admin:
        from werkzeug.security import generate_password_hash
        admin = User(
            username="admin",
            email="theamal@rex.com",
            password_hash=generate_password_hash("maothiskian11")
        )
        db.session.add(admin)
        db.session.commit()
