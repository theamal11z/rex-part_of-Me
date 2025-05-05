// Terminal functionality
document.addEventListener('DOMContentLoaded', function() {
    const terminalContent = document.querySelector('.terminal-content');
    const terminalInput = document.getElementById('terminal-input');
    const loginModal = document.getElementById('login-modal');
    const loginForm = document.getElementById('login-form');
    const navItems = document.querySelectorAll('.nav-item');
    const appViews = document.querySelectorAll('.app-view');
    const reflectionsTabs = document.querySelectorAll('.reflections-tab');
    const reflectionsList = document.getElementById('reflections-list');
    
    let conversationId = null;
    let username = 'Anonymous';
    let isWaitingForResponse = false;
    let currentReflectionType = 'microblog';
    
    // Initial welcome message
    addSystemMessage("Welcome to Rex - Mohsin Raja's digital emotional self");
    addSystemMessage("Type a message to start the conversation...");
    
    // Focus the input field when the page loads
    terminalInput.focus();
    
    // Handle user input
    terminalInput.addEventListener('keydown', async function(event) {
        if (event.key === 'Enter' && !isWaitingForResponse) {
            const message = terminalInput.value.trim();
            if (message === '') return;
            
            // Check for admin panel trigger
            if (message.toLowerCase() === 'heyopenhereiam') {
                showLoginModal();
                terminalInput.value = '';
                return;
            }
            
            // Check if the message contains a name introduction
            const nameMatch = message.match(/(?:i am|i'm|my name is|call me) (\w+)/i);
            if (nameMatch && nameMatch[1]) {
                username = nameMatch[1].charAt(0).toUpperCase() + nameMatch[1].slice(1);
            }
            
            // Add user message to the terminal
            addUserMessage(message);
            terminalInput.value = '';
            
            // Prevent multiple requests
            isWaitingForResponse = true;
            
            // Show loading indicator
            const loadingElement = document.createElement('div');
            loadingElement.className = 'terminal-message rex loading-message';
            loadingElement.innerHTML = `
                <span class="loading">
                    <div></div><div></div><div></div><div></div>
                </span>
            `;
            terminalContent.appendChild(loadingElement);
            scrollToBottom();
            
            try {
                // Send the message to the server
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        username: username,
                        conversation_id: conversationId
                    })
                });
                
                const data = await response.json();
                
                // Remove loading indicator
                terminalContent.removeChild(loadingElement);
                
                if (data.admin_request) {
                    // Show admin login modal
                    showLoginModal();
                } else {
                    // Store the conversation ID
                    if (data.conversation_id) {
                        conversationId = data.conversation_id;
                    }
                    
                    // Add Rex's response with typing animation
                    addRexMessage(data.message);
                }
            } catch (error) {
                console.error('Error:', error);
                // Remove loading indicator
                terminalContent.removeChild(loadingElement);
                addSystemMessage('Error connecting to Rex. Please try again.');
            } finally {
                isWaitingForResponse = false;
            }
        }
    });
    
    // Handle clicks on the terminal to focus the input
    document.querySelector('.terminal-container').addEventListener('click', function() {
        terminalInput.focus();
    });
    
    // Handle admin login
    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch('/admin-login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    password: password
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Redirect to admin panel
                window.location.href = '/admin';
            } else {
                alert('Invalid credentials. Please try again.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Login failed. Please try again.');
        }
    });
    
    // Function to add a system message to the terminal
    function addSystemMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'terminal-message system';
        messageElement.textContent = message;
        terminalContent.appendChild(messageElement);
        scrollToBottom();
    }
    
    // Function to add a user message to the terminal
    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'terminal-message user';
        messageElement.textContent = message;
        terminalContent.appendChild(messageElement);
        scrollToBottom();
    }
    
    // Function to add Rex's message with typing animation
    function addRexMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'terminal-message rex';
        
        const contentElement = document.createElement('span');
        contentElement.className = 'content';
        messageElement.appendChild(contentElement);
        
        terminalContent.appendChild(messageElement);
        scrollToBottom();
        
        // Split message into characters for typing animation
        const characters = message.split('');
        let index = 0;
        
        // Type out the characters one by one
        const typingInterval = setInterval(() => {
            if (index < characters.length) {
                contentElement.textContent += characters[index];
                index++;
                scrollToBottom();
            } else {
                clearInterval(typingInterval);
                // Add typing class to enable cursor blinking at the end
                contentElement.classList.add('typing');
                
                // Remove typing class after a few seconds
                setTimeout(() => {
                    contentElement.classList.remove('typing');
                }, 3000);
            }
        }, 30); // Adjust typing speed here
    }
    
    // Function to scroll to the bottom of the terminal
    function scrollToBottom() {
        terminalContent.scrollTop = terminalContent.scrollHeight;
    }
    
    // Function to show the login modal
    function showLoginModal() {
        loginModal.style.display = 'flex';
        document.getElementById('email').focus();
    }
    
    // Function to hide the login modal
    window.closeLoginModal = function() {
        loginModal.style.display = 'none';
        terminalInput.focus();
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === loginModal) {
            closeLoginModal();
        }
    });
    
    // Initialize reflections view if elements exist
    if (navItems.length > 0 && reflectionsTabs.length > 0 && reflectionsList) {
        // Load initial reflections
        loadReflections(currentReflectionType);
        
        // Handle view navigation
        navItems.forEach(item => {
            item.addEventListener('click', function() {
                const targetView = this.getAttribute('data-view');
                
                // Update navigation items
                navItems.forEach(navItem => navItem.classList.remove('active'));
                this.classList.add('active');
                
                // Update views
                appViews.forEach(view => view.classList.remove('active'));
                document.getElementById(targetView).classList.add('active');
                
                // If switching to reflections view, load reflections
                if (targetView === 'reflections-view') {
                    loadReflections(currentReflectionType);
                }
                
                // Focus on input if switching to terminal view
                if (targetView === 'terminal-view') {
                    terminalInput.focus();
                }
            });
        });
        
        // Handle reflections tab switching
        reflectionsTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const type = this.getAttribute('data-type');
                
                // Update tabs
                reflectionsTabs.forEach(item => item.classList.remove('active'));
                this.classList.add('active');
                
                // Update reflection type and load
                currentReflectionType = type;
                loadReflections(currentReflectionType);
            });
        });
    }
    
    // Function to load reflections
    function loadReflections(type) {
        if (!reflectionsList) return;
        
        // Show loading state
        reflectionsList.innerHTML = `
            <div class="reflection-card skeleton">
                <div class="skeleton-title"></div>
                <div class="skeleton-content"></div>
                <div class="skeleton-date"></div>
            </div>
            <div class="reflection-card skeleton">
                <div class="skeleton-title"></div>
                <div class="skeleton-content"></div>
                <div class="skeleton-date"></div>
            </div>
        `;
        
        // Fetch reflections from API
        fetch(`/api/reflections/public?type=${type}`)
            .then(response => response.json())
            .then(reflections => {
                // Clear loading state
                reflectionsList.innerHTML = '';
                
                if (reflections.length === 0) {
                    reflectionsList.innerHTML = `
                        <div class="no-reflections">
                            <p>No ${type}s found.</p>
                        </div>
                    `;
                    return;
                }
                
                // Add each reflection
                reflections.forEach(reflection => {
                    const card = document.createElement('div');
                    card.className = 'reflection-card';
                    
                    const date = new Date(reflection.created_at).toLocaleDateString();
                    
                    card.innerHTML = `
                        <h3 class="reflection-title">${reflection.title}</h3>
                        <div class="reflection-meta">
                            <span>${date}</span>
                        </div>
                        <div class="reflection-content">
                            ${reflection.content}
                        </div>
                    `;
                    
                    reflectionsList.appendChild(card);
                });
            })
            .catch(error => {
                console.error('Error loading reflections:', error);
                reflectionsList.innerHTML = `
                    <div class="no-reflections">
                        <p>Error loading reflections. Please try again.</p>
                    </div>
                `;
            });
    }
});
