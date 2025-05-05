import os
import logging
import json
import uuid
import requests
from datetime import datetime
from app import db
from models import Conversation, Message, AdminSetting, Reflection, User

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
            conversations = Conversation.query.filter_by(username=username).order_by(
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
            logger.error(f"Error retrieving past conversations: {e}")
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
