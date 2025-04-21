import os
import logging
import json
from flask import Flask, render_template, request, jsonify
from knowledge_base import KnowledgeBase
from nlp_processor import NLPProcessor

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Initialize knowledge base and NLP processor
knowledge_base = KnowledgeBase("knowledge_data.txt")
nlp_processor = NLPProcessor()

# Store conversation history
conversation_history = {}

@app.route('/')
def index():
    """Render the main page with the chat interface."""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat messages and return responses."""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        user_message = data['message']
        session_id = data.get('session_id', 'default')
        
        # Initialize or retrieve conversation history for this session
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        
        # Add user message to history
        conversation_history[session_id].append({'role': 'user', 'content': user_message})
        
        # Process the user message
        processed_query = nlp_processor.preprocess(user_message)
        logger.debug(f"Processed query: {processed_query}")
        
        # Get response based on the processed query and conversation context
        context = conversation_history[session_id][-5:] if len(conversation_history[session_id]) > 5 else conversation_history[session_id]
        response = knowledge_base.get_response(processed_query, context)
        
        # If no relevant response found
        if not response:
            response = "I'm sorry, I don't have information about that. Please try asking something else."
        
        # Add bot response to history
        conversation_history[session_id].append({'role': 'bot', 'content': response})
        
        return jsonify({
            'response': response,
            'session_id': session_id
        })
    
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        return jsonify({'error': f'Error processing your message: {str(e)}'}), 500

@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """Reset the conversation history for a session."""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id in conversation_history:
            conversation_history[session_id] = []
        
        return jsonify({'status': 'success', 'message': 'Conversation reset successfully'})
    
    except Exception as e:
        logger.error(f"Error resetting conversation: {str(e)}")
        return jsonify({'error': f'Error resetting conversation: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
