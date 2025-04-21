document.addEventListener('DOMContentLoaded', function() {
    // Chat application state
    const APP_STATE = {
        activeConversationId: null,
        conversations: {},
        currentSessionId: generateId(),
        isNewConversation: true
    };

    // DOM elements
    const elements = {
        appContainer: document.getElementById('app-container'),
        chatContainer: document.getElementById('chat-container'),
        messageInput: document.getElementById('message-input'),
        sendButton: document.getElementById('send-button'),
        resetButton: document.getElementById('reset-button'),
        chatMessages: document.getElementById('chat-messages'),
        conversationList: document.getElementById('conversation-list'),
        newChatButton: document.getElementById('new-chat-button'),
        toggleSidebarButton: document.getElementById('toggle-sidebar'),
        sidebar: document.getElementById('sidebar'),
        welcomeContainer: document.getElementById('welcome-container'),
        exampleQueries: document.querySelectorAll('.example-query'),
        chatTitle: document.getElementById('chat-title')
    };

    // Initialize the application
    initializeApp();

    // Main initialization function
    function initializeApp() {
        // Load conversations from local storage
        loadConversationsFromStorage();
        
        // Set up event listeners
        setupEventListeners();
        
        // Initial UI setup
        renderConversationList();
        
        // Show welcome screen or last conversation
        if (Object.keys(APP_STATE.conversations).length === 0) {
            showWelcomeScreen();
        } else {
            // Load the last active conversation or the latest one
            const lastConversationId = localStorage.getItem('lastActiveConversation') || 
                                      Object.keys(APP_STATE.conversations).sort((a, b) => {
                                          return APP_STATE.conversations[b].timestamp - APP_STATE.conversations[a].timestamp;
                                      })[0];
            
            if (lastConversationId && APP_STATE.conversations[lastConversationId]) {
                loadConversation(lastConversationId);
            } else {
                showWelcomeScreen();
            }
        }
    }

    // Set up all event listeners
    function setupEventListeners() {
        // Message sending
        elements.sendButton.addEventListener('click', sendMessage);
        elements.messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Reset conversation
        elements.resetButton.addEventListener('click', resetCurrentConversation);
        
        // New chat button
        if (elements.newChatButton) {
            elements.newChatButton.addEventListener('click', startNewConversation);
        }
        
        // Toggle sidebar on mobile
        if (elements.toggleSidebarButton) {
            elements.toggleSidebarButton.addEventListener('click', toggleSidebar);
        }
        
        // Example queries
        elements.exampleQueries.forEach(query => {
            query.addEventListener('click', function() {
                const queryText = this.querySelector('p').textContent;
                startNewConversation();
                elements.messageInput.value = queryText;
                sendMessage();
            });
        });
        
        // Handle copy button clicks for messages
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('copy-message-btn') || 
                e.target.parentElement.classList.contains('copy-message-btn')) {
                const btn = e.target.classList.contains('copy-message-btn') ? 
                            e.target : e.target.parentElement;
                const messageId = btn.getAttribute('data-message-id');
                copyMessageToClipboard(messageId);
            }
        });
        
        // Handle delete conversation button clicks
        document.addEventListener('click', function(e) {
            if (e.target.classList.contains('delete-conversation')) {
                e.stopPropagation();
                const conversationId = e.target.getAttribute('data-conversation-id');
                deleteConversation(conversationId);
            }
        });
    }

    // Load conversations from localStorage
    function loadConversationsFromStorage() {
        try {
            const savedConversations = localStorage.getItem('chatConversations');
            if (savedConversations) {
                APP_STATE.conversations = JSON.parse(savedConversations);
            }
        } catch (error) {
            console.error('Error loading conversations from storage:', error);
            // If there's an error, start fresh
            APP_STATE.conversations = {};
            localStorage.setItem('chatConversations', JSON.stringify({}));
        }
    }

    // Save current state to localStorage
    function saveToLocalStorage() {
        try {
            localStorage.setItem('chatConversations', JSON.stringify(APP_STATE.conversations));
            if (APP_STATE.activeConversationId) {
                localStorage.setItem('lastActiveConversation', APP_STATE.activeConversationId);
            }
        } catch (error) {
            console.error('Error saving to local storage:', error);
            showNotification('Error saving chat history to local storage.', 'error');
        }
    }

    // Generate a unique ID
    function generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    // Start a new conversation
    function startNewConversation() {
        // Create a new conversation
        const conversationId = generateId();
        const timestamp = Date.now();
        
        APP_STATE.conversations[conversationId] = {
            id: conversationId,
            title: 'New Conversation',
            messages: [],
            timestamp: timestamp,
            sessionId: generateId()
        };
        
        // Set as active conversation
        APP_STATE.activeConversationId = conversationId;
        APP_STATE.currentSessionId = APP_STATE.conversations[conversationId].sessionId;
        APP_STATE.isNewConversation = true;
        
        // Update UI
        renderConversationList();
        elements.chatMessages.innerHTML = '';
        elements.chatTitle.textContent = 'New Conversation';
        
        // Hide welcome screen if visible
        if (elements.welcomeContainer) {
            elements.welcomeContainer.style.display = 'none';
        }
        
        // Focus on input
        elements.messageInput.focus();
        
        // Save to storage
        saveToLocalStorage();
        
        // Close sidebar on mobile
        if (window.innerWidth < 992) {
            elements.sidebar.classList.remove('show');
        }
    }

    // Load an existing conversation
    function loadConversation(conversationId) {
        if (!APP_STATE.conversations[conversationId]) {
            console.error('Conversation not found:', conversationId);
            return;
        }
        
        // Set as active conversation
        APP_STATE.activeConversationId = conversationId;
        APP_STATE.currentSessionId = APP_STATE.conversations[conversationId].sessionId;
        APP_STATE.isNewConversation = false;
        
        // Update UI
        elements.chatMessages.innerHTML = '';
        elements.chatTitle.textContent = APP_STATE.conversations[conversationId].title;
        
        // Mark as active in the list
        renderConversationList();
        
        // Render messages
        APP_STATE.conversations[conversationId].messages.forEach(message => {
            if (message.role === 'user') {
                renderUserMessage(message);
            } else if (message.role === 'bot') {
                renderBotMessage(message);
            } else if (message.role === 'error') {
                renderErrorMessage(message);
            }
        });
        
        // Hide welcome screen if visible
        if (elements.welcomeContainer) {
            elements.welcomeContainer.style.display = 'none';
        }
        
        // Scroll to bottom
        scrollToBottom();
        
        // Save active conversation to storage
        localStorage.setItem('lastActiveConversation', conversationId);
        
        // Close sidebar on mobile
        if (window.innerWidth < 992) {
            elements.sidebar.classList.remove('show');
        }
    }

    // Delete a conversation
    function deleteConversation(conversationId) {
        if (!APP_STATE.conversations[conversationId]) {
            return;
        }
        
        // Confirm deletion
        if (!confirm('Are you sure you want to delete this conversation?')) {
            return;
        }
        
        // Remove from state
        delete APP_STATE.conversations[conversationId];
        
        // Save to storage
        saveToLocalStorage();
        
        // If active conversation was deleted
        if (APP_STATE.activeConversationId === conversationId) {
            const conversationIds = Object.keys(APP_STATE.conversations);
            if (conversationIds.length > 0) {
                // Load the most recent conversation
                const mostRecentId = conversationIds.sort((a, b) => {
                    return APP_STATE.conversations[b].timestamp - APP_STATE.conversations[a].timestamp;
                })[0];
                loadConversation(mostRecentId);
            } else {
                // No conversations left, show welcome screen
                APP_STATE.activeConversationId = null;
                showWelcomeScreen();
            }
        }
        
        // Update UI
        renderConversationList();
    }

    // Render the list of conversations in the sidebar
    function renderConversationList() {
        if (!elements.conversationList) return;
        
        elements.conversationList.innerHTML = '';
        
        // Sort conversations by timestamp (newest first)
        const sortedIds = Object.keys(APP_STATE.conversations).sort((a, b) => {
            return APP_STATE.conversations[b].timestamp - APP_STATE.conversations[a].timestamp;
        });
        
        sortedIds.forEach(id => {
            const conversation = APP_STATE.conversations[id];
            const isActive = id === APP_STATE.activeConversationId;
            
            const conversationElement = document.createElement('div');
            conversationElement.className = `conversation-item ${isActive ? 'active' : ''}`;
            conversationElement.innerHTML = `
                <i class="fas fa-comments"></i>
                <div class="conversation-title">${escapeHTML(conversation.title)}</div>
                <button class="delete-conversation" data-conversation-id="${id}" title="Delete conversation">
                    <i class="fas fa-trash-alt"></i>
                </button>
            `;
            
            conversationElement.addEventListener('click', function() {
                loadConversation(id);
            });
            
            elements.conversationList.appendChild(conversationElement);
        });
    }

    // Update conversation title based on the first user message
    function updateConversationTitle(userMessage) {
        if (!APP_STATE.activeConversationId || !APP_STATE.isNewConversation) {
            return;
        }
        
        // Create a title from the first user message
        const maxTitleLength = 30;
        let title = userMessage.trim();
        
        // Truncate if necessary
        if (title.length > maxTitleLength) {
            title = title.substring(0, maxTitleLength) + '...';
        }
        
        // Update state
        APP_STATE.conversations[APP_STATE.activeConversationId].title = title;
        APP_STATE.isNewConversation = false;
        
        // Update UI
        elements.chatTitle.textContent = title;
        renderConversationList();
        
        // Save to storage
        saveToLocalStorage();
    }

    // Show welcome screen
    function showWelcomeScreen() {
        if (!elements.welcomeContainer) return;
        
        elements.welcomeContainer.style.display = 'flex';
        elements.chatMessages.innerHTML = '';
        elements.chatTitle.textContent = 'New Conversation';
    }

    // Toggle sidebar on mobile
    function toggleSidebar() {
        if (elements.sidebar) {
            elements.sidebar.classList.toggle('show');
        }
    }

    // Send a message to the backend
    function sendMessage() {
        const message = elements.messageInput.value.trim();
        if (!message) {
            return; // Don't send empty messages
        }
        
        // Create a new conversation if none is active
        if (!APP_STATE.activeConversationId) {
            startNewConversation();
        }
        
        // Generate message ID
        const messageId = generateId();
        
        // Add user message to chat
        const userMessage = {
            id: messageId,
            content: message,
            role: 'user',
            timestamp: new Date().toISOString()
        };
        
        // Save to conversation
        APP_STATE.conversations[APP_STATE.activeConversationId].messages.push(userMessage);
        APP_STATE.conversations[APP_STATE.activeConversationId].timestamp = Date.now();
        
        // Update title if this is the first message
        updateConversationTitle(message);
        
        // Render the message
        renderUserMessage(userMessage);
        
        // Clear input field
        elements.messageInput.value = '';
        
        // Show loading indicator
        const loadingIndicator = addLoadingIndicator();
        
        // Save to storage
        saveToLocalStorage();
        
        // Send to backend API
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: APP_STATE.currentSessionId
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
            
            // Add bot response to chat
            const botMessageId = generateId();
            let botMessage;
            
            if (data.error) {
                botMessage = {
                    id: botMessageId,
                    content: data.error,
                    role: 'error',
                    timestamp: new Date().toISOString()
                };
                renderErrorMessage(botMessage);
            } else {
                botMessage = {
                    id: botMessageId,
                    content: data.response,
                    role: 'bot',
                    timestamp: new Date().toISOString()
                };
                renderBotMessage(botMessage);
            }
            
            // Save to conversation
            APP_STATE.conversations[APP_STATE.activeConversationId].messages.push(botMessage);
            APP_STATE.conversations[APP_STATE.activeConversationId].timestamp = Date.now();
            
            // Save to storage
            saveToLocalStorage();
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            // Remove loading indicator
            loadingIndicator.remove();
            
            // Add error message
            const errorMessageId = generateId();
            const errorMessage = {
                id: errorMessageId,
                content: "Sorry, I couldn't process your message. Please try again.",
                role: 'error',
                timestamp: new Date().toISOString()
            };
            
            renderErrorMessage(errorMessage);
            
            // Save to conversation
            APP_STATE.conversations[APP_STATE.activeConversationId].messages.push(errorMessage);
            APP_STATE.conversations[APP_STATE.activeConversationId].timestamp = Date.now();
            
            // Save to storage
            saveToLocalStorage();
            
            console.error('Error:', error);
            
            // Scroll to bottom
            scrollToBottom();
        });
    }

    // Reset the current conversation
    function resetCurrentConversation() {
        if (!APP_STATE.activeConversationId) return;
        
        // Confirm reset
        if (!confirm('Are you sure you want to reset this conversation? This will clear all messages but keep the conversation in your history.')) {
            return;
        }
        
        // Reset on backend
        fetch('/api/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: APP_STATE.currentSessionId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Generate new session ID
            const newSessionId = generateId();
            APP_STATE.currentSessionId = newSessionId;
            APP_STATE.conversations[APP_STATE.activeConversationId].sessionId = newSessionId;
            
            // Clear chat messages but keep conversation in list
            APP_STATE.conversations[APP_STATE.activeConversationId].messages = [];
            elements.chatMessages.innerHTML = '';
            
            // Update timestamp
            APP_STATE.conversations[APP_STATE.activeConversationId].timestamp = Date.now();
            
            // Save to storage
            saveToLocalStorage();
            
            // Update UI
            renderConversationList();
            
            // Show notification
            showNotification('Conversation has been reset.', 'success');
        })
        .catch(error => {
            console.error('Error resetting conversation:', error);
            showNotification('Failed to reset conversation. Please try again.', 'error');
        });
    }

    // Copy message text to clipboard
    function copyMessageToClipboard(messageId) {
        // Find the message across all conversations
        let messageContent = null;
        
        Object.values(APP_STATE.conversations).some(conversation => {
            const message = conversation.messages.find(m => m.id === messageId);
            if (message) {
                messageContent = message.content;
                return true;
            }
            return false;
        });
        
        if (!messageContent) return;
        
        // Copy to clipboard
        navigator.clipboard.writeText(messageContent)
            .then(() => {
                showNotification('Message copied to clipboard!', 'success');
            })
            .catch(err => {
                console.error('Failed to copy text: ', err);
                showNotification('Failed to copy message.', 'error');
            });
    }

    // Show a notification to the user
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
                <span>${escapeHTML(message)}</span>
            </div>
        `;
        
        // Add to DOM
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remove after delay
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }

    // Render a user message
    function renderUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message user-message';
        messageElement.setAttribute('data-message-id', message.id);
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageElement.innerHTML = `
            <div class="message-content">
                <p>${escapeHTML(message.content)}</p>
                <div class="message-timestamp">${timestamp}</div>
            </div>
            <div class="message-avatar">
                <img src="/static/img/user-avatar.svg" alt="User">
            </div>
            <div class="message-actions">
                <button class="message-action-btn copy-message-btn" data-message-id="${message.id}" title="Copy message">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
        `;
        
        elements.chatMessages.appendChild(messageElement);
        scrollToBottom();
    }

    // Render a bot message
    function renderBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        messageElement.setAttribute('data-message-id', message.id);
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                <img src="/static/img/bot-avatar.svg" alt="Bot">
            </div>
            <div class="message-content">
                <p>${formatMessage(escapeHTML(message.content))}</p>
                <div class="message-timestamp">${timestamp}</div>
            </div>
            <div class="message-actions">
                <button class="message-action-btn copy-message-btn" data-message-id="${message.id}" title="Copy message">
                    <i class="fas fa-copy"></i>
                </button>
            </div>
        `;
        
        elements.chatMessages.appendChild(messageElement);
        scrollToBottom();
    }

    // Render an error message
    function renderErrorMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message error-message';
        messageElement.setAttribute('data-message-id', message.id);
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageElement.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="message-content">
                <p>${escapeHTML(message.content)}</p>
                <div class="message-timestamp">${timestamp}</div>
            </div>
        `;
        
        elements.chatMessages.appendChild(messageElement);
        scrollToBottom();
    }

    // Add loading indicator 
    function addLoadingIndicator() {
        const loadingElement = document.createElement('div');
        loadingElement.className = 'message bot-message loading';
        loadingElement.innerHTML = `
            <div class="message-avatar">
                <img src="/static/img/bot-avatar.svg" alt="Bot">
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        `;
        elements.chatMessages.appendChild(loadingElement);
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
        
        // Convert `text` to inline code
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Convert ```text``` to code blocks
        text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
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
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }
    
    // Add CSS for notifications
    addNotificationStyles();
    
    function addNotificationStyles() {
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            .notification {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 300px;
                padding: 12px 16px;
                border-radius: 8px;
                background-color: rgba(30, 35, 45, 0.9);
                color: white;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                transform: translateY(-20px);
                opacity: 0;
                transition: all 0.3s ease;
            }
            
            .notification.show {
                transform: translateY(0);
                opacity: 1;
            }
            
            .notification-content {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            .notification-success {
                border-left: 4px solid #28a745;
            }
            
            .notification-error {
                border-left: 4px solid #dc3545;
            }
            
            .notification-info {
                border-left: 4px solid #17a2b8;
            }
        `;
        document.head.appendChild(styleElement);
    }
});
