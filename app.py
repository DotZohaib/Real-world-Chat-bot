import os
import logging
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
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
        conversation_history[session_id].append({
            'role': 'user', 
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Detect user intent
        intent = nlp_processor.detect_intent(user_message)
        
        # Process the user message
        processed_query = nlp_processor.preprocess(user_message)
        logger.debug(f"Processed query: {processed_query}")
        
        # Extract keywords for better context understanding
        keywords = nlp_processor.extract_keywords(user_message)
        logger.debug(f"Extracted keywords: {keywords}")
        
        # Get response based on the processed query and conversation context
        context = conversation_history[session_id][-5:] if len(conversation_history[session_id]) > 5 else conversation_history[session_id]
        response = knowledge_base.get_response(processed_query, context)
        
        # If no relevant response found
        if not response:
            if intent == 'greeting':
                response = "Hello! How can I help you today with your questions?"
            elif intent == 'farewell':
                response = "Goodbye! Feel free to come back anytime you have questions."
            elif intent == 'thanks':
                response = "You're welcome! Is there anything else I can help you with?"
            else:
                response = "I'm sorry, I don't have information about that in my knowledge base. Please try asking something else or rephrasing your question."
        
        # Add bot response to history
        conversation_history[session_id].append({
            'role': 'bot', 
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Add a small delay to simulate thinking (better UX)
        time.sleep(0.5)
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
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
        
        return jsonify({
            'status': 'success', 
            'message': 'Conversation reset successfully',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error resetting conversation: {str(e)}")
        return jsonify({'error': f'Error resetting conversation: {str(e)}'}), 500

@app.route('/api/export', methods=['POST'])
def export_conversation():
    """Export a conversation history as JSON."""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or session_id not in conversation_history:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Get the conversation history for this session
        history = conversation_history[session_id]
        
        return jsonify({
            'status': 'success',
            'conversation': history,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error exporting conversation: {str(e)}")
        return jsonify({'error': f'Error exporting conversation: {str(e)}'}), 500

@app.route('/api/add-knowledge', methods=['POST'])
def add_knowledge():
    """Add a new entry to the knowledge base (could be protected with authentication in production)."""
    try:
        data = request.get_json()
        if not data or 'question' not in data or 'answer' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        
        question = data['question']
        answer = data['answer']
        tags = data.get('tags', [])
        
        # Add the entry to the knowledge base
        success = knowledge_base.add_entry(question, answer, tags)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Knowledge entry added successfully'
            })
        else:
            return jsonify({
                'error': 'Failed to add knowledge entry'
            }), 500
    
    except Exception as e:
        logger.error(f"Error adding knowledge: {str(e)}")
        return jsonify({'error': f'Error adding knowledge: {str(e)}'}), 500

@app.route('/favicon.ico')
def favicon():
    """Serve the favicon."""
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'),
                               'chat-logo.svg', mimetype='image/svg+xml')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
