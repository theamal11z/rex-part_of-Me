import os
import logging
import json
import uuid
import requests
from datetime import datetime
from app import db
from models import Conversation, Message, AdminSetting, Reflection, User, Guideline

logger = logging.getLogger(__name__)

class SupabaseClient:
    """
    Client for interacting with Supabase for database operations.
    For this implementation, we're directly using SQLAlchemy since we don't have actual
    Supabase credentials, but in a real implementation, this would use the Supabase API.
    """
    
    def __init__(self):
        # In a real implementation, we'd connect to Supabase using:
        # self.supabase_url = os.environ.get("SUPABASE_URL")
        # self.supabase_key = os.environ.get("SUPABASE_KEY")
        # self.client = create_client(self.supabase_url, self.supabase_key)
        pass
    
    def create_conversation(self, username):
        """Create a new conversation for a user and return the ID."""
        try:
            conversation = Conversation(username=username)
            db.session.add(conversation)
            db.session.commit()
            return conversation.id
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            db.session.rollback()
            return None
    
    def store_message(self, conversation_id, sender, content, role, emotional_tone):
        """Store a message in the database."""
        try:
            message = Message(
                conversation_id=conversation_id,
                sender=sender,
                content=content,
                emotional_tone=emotional_tone
            )
            db.session.add(message)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing message: {e}")
            db.session.rollback()
            return False
    
    def get_past_conversations(self, username, limit=5):
        """Get past conversations for a user."""
        try:
            if not username:
                return []
                
            # Use case insensitive search for username
            conversations = Conversation.query.filter(
                Conversation.username.ilike(f"%{username}%")
            ).order_by(
                Conversation.created_at.desc()
            ).limit(limit).all()
            
            result = []
            for conversation in conversations:
                messages = Message.query.filter_by(conversation_id=conversation.id).order_by(
                    Message.timestamp.asc()
                ).all()
                
                formatted_messages = [{
                    'sender': msg.sender,
                    'content': msg.content,
                    'emotional_tone': msg.emotional_tone,
                    'timestamp': msg.timestamp.isoformat()
                } for msg in messages]
                
                result.append({
                    'id': conversation.id,
                    'created_at': conversation.created_at.isoformat(),
                    'messages': formatted_messages
                })
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving past conversations for {username}: {e}")
            return []
    
    def get_conversation_messages(self, conversation_id):
        """Get all messages for a specific conversation."""
        try:
            messages = Message.query.filter_by(conversation_id=conversation_id).order_by(
                Message.timestamp.asc()
            ).all()
            
            return [{
                'id': msg.id,
                'sender': msg.sender,
                'content': msg.content,
                'emotional_tone': msg.emotional_tone,
                'timestamp': msg.timestamp.isoformat()
            } for msg in messages]
        except Exception as e:
            logger.error(f"Error retrieving conversation messages: {e}")
            return []
    
    def get_all_conversations(self):
        """Get all conversations for admin view."""
        try:
            conversations = Conversation.query.order_by(Conversation.created_at.desc()).all()
            
            return [{
                'id': conv.id,
                'username': conv.username,
                'created_at': conv.created_at.isoformat(),
                'message_count': len(conv.messages)
            } for conv in conversations]
        except Exception as e:
            logger.error(f"Error retrieving all conversations: {e}")
            return []
            
    def get_conversations_by_username(self, username):
        """Get all conversations for a specific username, ordered by most recent first."""
        try:
            if not username:
                return []
                
            # Case-insensitive search for the username
            conversations = Conversation.query.filter(
                Conversation.username.ilike(f"%{username}%")
            ).order_by(Conversation.created_at.desc()).all()
            
            return [{
                'id': conv.id,
                'username': conv.username,
                'created_at': conv.created_at.isoformat(),
                'message_count': len(conv.messages)
            } for conv in conversations]
        except Exception as e:
            logger.error(f"Error retrieving conversations for username {username}: {e}")
            return []
    
    def get_settings(self):
        """Get all admin settings."""
        try:
            settings = AdminSetting.query.all()
            return {setting.key: setting.value for setting in settings}
        except Exception as e:
            logger.error(f"Error retrieving settings: {e}")
            return {}
    
    def update_settings(self, settings_data):
        """Update admin settings."""
        try:
            for key, value in settings_data.items():
                setting = AdminSetting.query.filter_by(key=key).first()
                if setting:
                    setting.value = value
                else:
                    setting = AdminSetting(key=key, value=value)
                    db.session.add(setting)
            
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            db.session.rollback()
            return False
    
    def get_reflections(self, reflection_type=None):
        """
        Get all reflections. Optionally filter by type.
        
        Args:
            reflection_type: Optional filter for 'microblog' or 'story'
        """
        try:
            query = Reflection.query
            
            # Apply type filter if provided
            if reflection_type:
                query = query.filter_by(type=reflection_type)
                
            reflections = query.order_by(Reflection.created_at.desc()).all()
            
            return [{
                'id': ref.id,
                'title': ref.title,
                'content': ref.content,
                'type': ref.type,
                'created_at': ref.created_at.isoformat(),
                'updated_at': ref.updated_at.isoformat(),
                'published': ref.published
            } for ref in reflections]
        except Exception as e:
            logger.error(f"Error retrieving reflections: {e}")
            return []
            
    def get_public_reflections(self, reflection_type=None):
        """
        Get only published reflections for public viewing. Optionally filter by type.
        
        Args:
            reflection_type: Optional filter for 'microblog' or 'story'
        """
        try:
            query = Reflection.query.filter_by(published=True)
            
            # Apply type filter if provided
            if reflection_type:
                query = query.filter_by(type=reflection_type)
                
            reflections = query.order_by(Reflection.created_at.desc()).all()
            
            return [{
                'id': ref.id,
                'title': ref.title,
                'content': ref.content,
                'type': ref.type,
                'created_at': ref.created_at.isoformat()
            } for ref in reflections]
        except Exception as e:
            logger.error(f"Error retrieving public reflections: {e}")
            return []
    
    def create_reflection(self, reflection_data):
        """Create a new reflection."""
        try:
            reflection = Reflection(
                title=reflection_data.get('title', ''),
                content=reflection_data.get('content', ''),
                type=reflection_data.get('type', 'microblog'),
                published=reflection_data.get('published', False)
            )
            db.session.add(reflection)
            db.session.commit()
            return reflection.id
        except Exception as e:
            logger.error(f"Error creating reflection: {e}")
            db.session.rollback()
            return None
    
    def update_reflection(self, reflection_data):
        """Update an existing reflection."""
        try:
            reflection_id = reflection_data.get('id')
            reflection = Reflection.query.get(reflection_id)
            if reflection:
                reflection.title = reflection_data.get('title', reflection.title)
                reflection.content = reflection_data.get('content', reflection.content)
                reflection.type = reflection_data.get('type', reflection.type)
                reflection.published = reflection_data.get('published', reflection.published)
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating reflection: {e}")
            db.session.rollback()
            return False
    
    def delete_reflection(self, reflection_id):
        """Delete a reflection."""
        try:
            reflection = Reflection.query.get(reflection_id)
            if reflection:
                db.session.delete(reflection)
                db.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting reflection: {e}")
            db.session.rollback()
            return False
    
    def get_guidelines(self):
        """Get all language guidelines."""
        try:
            guidelines = Guideline.query.all()
            result = {}
            for guideline in guidelines:
                try:
                    # Handle boolean values stored as strings
                    if guideline.value.lower() == 'true':
                        result[guideline.key] = True
                    elif guideline.value.lower() == 'false':
                        result[guideline.key] = False
                    # Handle numeric values
                    elif guideline.value.isdigit():
                        result[guideline.key] = int(guideline.value)
                    # Try to parse JSON values
                    elif guideline.value.startswith('{') or guideline.value.startswith('['):
                        result[guideline.key] = json.loads(guideline.value)
                    else:
                        result[guideline.key] = guideline.value
                except Exception as inner_e:
                    # If parsing fails, store as string
                    logger.error(f"Error parsing guideline value for {guideline.key}: {inner_e}")
                    result[guideline.key] = guideline.value
            logger.debug(f"Retrieved guidelines: {result}")
            return result
        except Exception as e:
            logger.error(f"Error retrieving guidelines: {e}")
            return {}
    
    def update_guidelines(self, guidelines_data):
        """Update language guidelines."""
        try:
            logger.debug(f"Updating guidelines with data: {guidelines_data}")
            
            for key, value in guidelines_data.items():
                # Special handling for boolean values
                if isinstance(value, bool):
                    # Store boolean as string 'true'/'false'
                    value_str = str(value).lower()
                    logger.debug(f"Converting boolean {value} to string: {value_str} for key {key}")
                # Special handling for numeric values    
                elif isinstance(value, int) or isinstance(value, float):
                    value_str = str(value)
                    logger.debug(f"Converting numeric {value} to string: {value_str} for key {key}")
                # Other non-string values convert to JSON    
                elif not isinstance(value, str):
                    value_str = json.dumps(value)
                    logger.debug(f"Converting complex value to JSON string for key {key}")
                else:
                    value_str = value
                
                guideline = Guideline.query.filter_by(key=key).first()
                if guideline:
                    logger.debug(f"Updating existing guideline {key} from '{guideline.value}' to '{value_str}'")
                    guideline.value = value_str
                else:
                    # Create new guideline with a default description
                    description = {
                        'hinglish_mode': 'Controls when Hinglish should be used in responses',
                        'hinglish_phrases': 'Common Hinglish phrases to incorporate in responses',
                        'hinglish_ratio': 'Percentage of Hinglish to use when mixing with English',
                        'support_english': 'Whether to support English in responses',
                        'support_hindi': 'Whether to support Hindi in responses',
                        'support_hinglish': 'Whether to support Hinglish in responses',
                        'language_detection': 'Strategy for detecting which language to respond in'
                    }.get(key, 'Language guidelines setting')
                    
                    logger.debug(f"Creating new guideline {key} with value '{value_str}'")
                    guideline = Guideline(key=key, value=value_str, description=description)
                    db.session.add(guideline)
            
            db.session.commit()
            
            # Clear any cache that might exist
            if hasattr(self, '_guidelines_cache'):
                delattr(self, '_guidelines_cache')
                
            return True
        except Exception as e:
            logger.error(f"Error updating guidelines: {e}")
            db.session.rollback()
            return False
            
    def get_custom_guidelines(self):
        """Get all custom guidelines."""
        try:
            guidelines = Guideline.query.filter(Guideline.key.startswith('custom_')).all()
            
            result = []
            for guideline in guidelines:
                # Remove 'custom_' prefix for frontend display
                key = guideline.key.replace('custom_', '', 1)
                result.append({
                    'key': key,
                    'value': guideline.value,
                    'description': guideline.description
                })
            
            return result
        except Exception as e:
            logger.error(f"Error retrieving custom guidelines: {e}")
            return []
    
    def create_custom_guideline(self, guideline_data):
        """Create a new custom guideline."""
        try:
            # Add 'custom_' prefix to key to distinguish from system guidelines
            key = f"custom_{guideline_data['key']}"
            value = guideline_data['value']
            description = guideline_data.get('description', '')
            
            # Check if guideline with this key already exists
            existing = Guideline.query.filter_by(key=key).first()
            if existing:
                return False
            
            guideline = Guideline(
                key=key,
                value=value,
                description=description
            )
            db.session.add(guideline)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error creating custom guideline: {e}")
            db.session.rollback()
            return False
    
    def update_custom_guideline(self, guideline_data):
        """Update an existing custom guideline."""
        try:
            # Add 'custom_' prefix to key
            key = f"custom_{guideline_data['key']}"
            value = guideline_data['value']
            description = guideline_data.get('description', '')
            
            guideline = Guideline.query.filter_by(key=key).first()
            if not guideline:
                return False
            
            guideline.value = value
            guideline.description = description
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating custom guideline: {e}")
            db.session.rollback()
            return False
    
    def delete_custom_guideline(self, key):
        """Delete a custom guideline."""
        try:
            # Add 'custom_' prefix to key
            key = f"custom_{key}"
            
            guideline = Guideline.query.filter_by(key=key).first()
            if not guideline:
                return False
            
            db.session.delete(guideline)
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting custom guideline: {e}")
            db.session.rollback()
            return False
