document.addEventListener('DOMContentLoaded', function() {
    const sections = document.querySelectorAll('.admin-section');
    const navItems = document.querySelectorAll('.admin-nav-item');
    const conversationList = document.getElementById('conversation-list');
    const messageContainer = document.getElementById('message-container');
    const settingsForm = document.getElementById('settings-form');
    const reflectionForm = document.getElementById('reflection-form');
    const reflectionsList = document.getElementById('reflections-list');
    
    let currentReflectionId = null;
    
    // Navigation
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            const targetSection = this.getAttribute('data-section');
            
            // Hide all sections
            sections.forEach(section => {
                section.classList.remove('active');
            });
            
            // Remove active class from all nav items
            navItems.forEach(navItem => {
                navItem.classList.remove('active');
            });
            
            // Show the target section
            document.getElementById(targetSection).classList.add('active');
            
            // Add active class to clicked nav item
            this.classList.add('active');
            
            // Load data for the selected section
            if (targetSection === 'conversations-section') {
                loadConversations();
            } else if (targetSection === 'settings-section') {
                loadSettings();
            } else if (targetSection === 'reflections-section') {
                loadReflections();
            }
        });
    });
    
    // Initial load
    loadConversations();
    
    // Load conversations
    async function loadConversations() {
        try {
            const response = await fetch('/api/conversations');
            const conversations = await response.json();
            
            // Clear the list
            conversationList.innerHTML = '';
            
            if (conversations.length === 0) {
                conversationList.innerHTML = '<li class="conversation-item">No conversations found</li>';
                return;
            }
            
            // Add each conversation to the list
            conversations.forEach(conversation => {
                const li = document.createElement('li');
                li.className = 'conversation-item';
                li.dataset.id = conversation.id;
                
                const date = new Date(conversation.created_at).toLocaleString();
                
                li.innerHTML = `
                    <div><strong>${conversation.username || 'Anonymous'}</strong></div>
                    <div><small>${date}</small></div>
                    <div>Messages: ${conversation.message_count}</div>
                `;
                
                li.addEventListener('click', () => loadConversationMessages(conversation.id));
                
                conversationList.appendChild(li);
            });
        } catch (error) {
            console.error('Error loading conversations:', error);
            conversationList.innerHTML = '<li class="conversation-item">Error loading conversations</li>';
        }
    }
    
    // Load messages for a conversation
    async function loadConversationMessages(conversationId) {
        try {
            const response = await fetch(`/api/conversation/${conversationId}`);
            const messages = await response.json();
            
            // Clear the container
            messageContainer.innerHTML = '';
            
            if (messages.length === 0) {
                messageContainer.innerHTML = '<div class="message-item">No messages found</div>';
                return;
            }
            
            // Add each message
            messages.forEach(message => {
                const div = document.createElement('div');
                div.className = 'message-item';
                
                const timestamp = new Date(message.timestamp).toLocaleString();
                
                div.innerHTML = `
                    <div class="message-meta">
                        <strong>${message.sender}</strong> 
                        <span class="message-tone">[${message.emotional_tone}]</span> 
                        <span>${timestamp}</span>
                    </div>
                    <div class="message-content">${message.content}</div>
                `;
                
                messageContainer.appendChild(div);
            });
        } catch (error) {
            console.error('Error loading messages:', error);
            messageContainer.innerHTML = '<div class="message-item">Error loading messages</div>';
        }
    }
    
    // Load settings
    async function loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const settings = await response.json();
            
            // Populate the form
            document.getElementById('greeting-text').value = settings.greeting_text || 'Welcome to Rex - Mohsin Raja\'s digital emotional self';
            document.getElementById('personality-guidelines').value = settings.personality_guidelines || 'Warm, introspective, emotionally resonant, switches naturally between English and Hinglish';
            document.getElementById('response-style').value = settings.response_style || 'human';
        } catch (error) {
            console.error('Error loading settings:', error);
            alert('Error loading settings');
        }
    }
    
    // Save settings
    settingsForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        const settings = {
            greeting_text: document.getElementById('greeting-text').value,
            personality_guidelines: document.getElementById('personality-guidelines').value,
            response_style: document.getElementById('response-style').value
        };
        
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Settings saved successfully');
            } else {
                alert('Error saving settings');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            alert('Error saving settings');
        }
    });
    
    // Load reflections
    async function loadReflections() {
        try {
            const response = await fetch('/api/reflections');
            const reflections = await response.json();
            
            // Clear the list
            reflectionsList.innerHTML = '';
            
            if (reflections.length === 0) {
                reflectionsList.innerHTML = '<div>No reflections found</div>';
                return;
            }
            
            // Add each reflection
            reflections.forEach(reflection => {
                const div = document.createElement('div');
                div.className = 'reflection-card';
                
                const date = new Date(reflection.updated_at).toLocaleDateString();
                
                div.innerHTML = `
                    <div class="reflection-title">${reflection.title}</div>
                    <div class="reflection-meta">
                        <div>${reflection.type} • ${date}</div>
                        <div>${reflection.published ? 'Published' : 'Draft'}</div>
                    </div>
                    <div class="reflection-content">${reflection.content.substring(0, 100)}${reflection.content.length > 100 ? '...' : ''}</div>
                    <div class="reflection-actions">
                        <button class="button" onclick="editReflection(${reflection.id})">Edit</button>
                        <button class="button danger" onclick="deleteReflection(${reflection.id})">Delete</button>
                    </div>
                `;
                
                reflectionsList.appendChild(div);
            });
        } catch (error) {
            console.error('Error loading reflections:', error);
            reflectionsList.innerHTML = '<div>Error loading reflections</div>';
        }
    }
    
    // New reflection
    window.newReflection = function() {
        currentReflectionId = null;
        document.getElementById('reflection-title').value = '';
        document.getElementById('reflection-content').value = '';
        document.getElementById('reflection-type').value = 'microblog';
        document.getElementById('reflection-published').checked = false;
        document.getElementById('reflection-form-title').textContent = 'New Reflection';
    };
    
    // Edit reflection
    window.editReflection = async function(id) {
        try {
            const response = await fetch('/api/reflections');
            const reflections = await response.json();
            
            const reflection = reflections.find(r => r.id === id);
            
            if (reflection) {
                currentReflectionId = reflection.id;
                document.getElementById('reflection-title').value = reflection.title;
                document.getElementById('reflection-content').value = reflection.content;
                document.getElementById('reflection-type').value = reflection.type;
                document.getElementById('reflection-published').checked = reflection.published;
                document.getElementById('reflection-form-title').textContent = 'Edit Reflection';
                
                // Switch to the form view
                document.getElementById('reflection-list-container').style.display = 'none';
                document.getElementById('reflection-form-container').style.display = 'block';
            } else {
                alert('Reflection not found');
            }
        } catch (error) {
            console.error('Error loading reflection:', error);
            alert('Error loading reflection');
        }
    };
    
    // Delete reflection
    window.deleteReflection = async function(id) {
        if (confirm('Are you sure you want to delete this reflection?')) {
            try {
                const response = await fetch(`/api/reflections?id=${id}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    loadReflections();
                } else {
                    alert('Error deleting reflection');
                }
            } catch (error) {
                console.error('Error deleting reflection:', error);
                alert('Error deleting reflection');
            }
        }
    };
    
    // Save reflection
    reflectionForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        const reflection = {
            title: document.getElementById('reflection-title').value,
            content: document.getElementById('reflection-content').value,
            type: document.getElementById('reflection-type').value,
            published: document.getElementById('reflection-published').checked
        };
        
        try {
            let url = '/api/reflections';
            let method = 'POST';
            
            if (currentReflectionId) {
                reflection.id = currentReflectionId;
                method = 'PUT';
            }
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(reflection)
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Go back to the list and refresh
                cancelReflectionEdit();
                loadReflections();
            } else {
                alert('Error saving reflection');
            }
        } catch (error) {
            console.error('Error saving reflection:', error);
            alert('Error saving reflection');
        }
    });
    
    // Cancel reflection edit
    window.cancelReflectionEdit = function() {
        document.getElementById('reflection-list-container').style.display = 'block';
        document.getElementById('reflection-form-container').style.display = 'none';
    };
    
    // Show the reflection form when clicking the "New Reflection" button
    document.getElementById('new-reflection-btn').addEventListener('click', function() {
        newReflection();
        document.getElementById('reflection-list-container').style.display = 'none';
        document.getElementById('reflection-form-container').style.display = 'block';
    });
    
    // Logout
    window.logout = function() {
        // Clear the session and redirect to the home page
        fetch('/logout', { method: 'POST' })
            .then(() => {
                window.location.href = '/';
            })
            .catch(error => {
                console.error('Error logging out:', error);
                // Redirect anyway
                window.location.href = '/';
            });
    };
});
