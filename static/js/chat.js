document.addEventListener('DOMContentLoaded', function() {
    // Chat elements
    const chatContainer = document.getElementById('chat-container');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const resetButton = document.getElementById('reset-button');
    const chatMessages = document.getElementById('chat-messages');
    
    // Store the session ID (generate a random one for now)
    let sessionId = Math.random().toString(36).substring(2, 15);
    
    // Add a welcome message
    addBotMessage("Hi there! I'm your custom chatbot. How can I help you today?");
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    resetButton.addEventListener('click', resetConversation);
    
    // Function to send a message
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) {
            return; // Don't send empty messages
        }
        
        // Add user message to chat
        addUserMessage(message);
        
        // Clear input field
        messageInput.value = '';
        
        // Show loading indicator
        const loadingIndicator = addLoadingIndicator();
        
        // Send to backend API
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Remove loading indicator
            loadingIndicator.remove();
            
            // Update session ID if provided
            if (data.session_id) {
                sessionId = data.session_id;
            }
            
            // Add bot response to chat
            if (data.error) {
                addErrorMessage(data.error);
            } else {
                addBotMessage(data.response);
            }
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            // Remove loading indicator
            loadingIndicator.remove();
            
            // Add error message
            addErrorMessage("Sorry, I couldn't process your message. Please try again.");
            console.error('Error:', error);
            
            // Scroll to bottom
            scrollToBottom();
        });
    }
    
    // Reset the conversation
    function resetConversation() {
        fetch('/api/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Clear chat messages
            chatMessages.innerHTML = '';
            
            // Add a fresh welcome message
            addBotMessage("Hi there! I'm your custom chatbot. How can I help you today?");
            
            // Generate a new session ID
            sessionId = Math.random().toString(36).substring(2, 15);
        })
        .catch(error => {
            console.error('Error resetting conversation:', error);
            addErrorMessage("Sorry, I couldn't reset the conversation. Please try again.");
        });
    }
    
    // Helper functions for adding messages to the chat
    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${escapeHTML(message)}</p>
            </div>
            <div class="message-avatar">
                <i class="fas fa-user"></i>
            </div>
        `;
        chatMessages.appendChild(messageElement);
        scrollToBottom();
    }
    
    function addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <p>${formatMessage(escapeHTML(message))}</p>
            </div>
        `;
        chatMessages.appendChild(messageElement);
        scrollToBottom();
    }
    
    function addErrorMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message error-message';
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="message-content">
                <p>${escapeHTML(message)}</p>
            </div>
        `;
        chatMessages.appendChild(messageElement);
        scrollToBottom();
    }
    
    function addLoadingIndicator() {
        const loadingElement = document.createElement('div');
        loadingElement.className = 'message bot-message loading';
        loadingElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        chatMessages.appendChild(loadingElement);
        scrollToBottom();
        return loadingElement;
    }
    
    // Format message with markdown-like syntax
    function formatMessage(text) {
        // Convert URLs to links
        text = text.replace(
            /(https?:\/\/[^\s]+)/g, 
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        // Convert *text* to bold
        text = text.replace(/\*(.*?)\*/g, '<strong>$1</strong>');
        
        // Convert _text_ to italic
        text = text.replace(/_(.*?)_/g, '<em>$1</em>');
        
        // Convert newlines to <br>
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }
    
    // Escape HTML to prevent XSS
    function escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Scroll to the bottom of the chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
