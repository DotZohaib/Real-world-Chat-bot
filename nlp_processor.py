import re
import string
import logging
from collections import Counter

class NLPProcessor:
    """
    A simple NLP processor for handling natural language queries.
    Provides basic tokenization, stopword removal, and other preprocessing steps.
    """
    
    def __init__(self):
        """Initialize the NLP processor with stopwords and other settings."""
        self.logger = logging.getLogger(__name__)
        
        # Common English stopwords
        self.stopwords = {
            'a', 'an', 'the', 'and', 'but', 'or', 'because', 'as', 'until', 'while', 
            'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 
            'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 
            'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
            'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
            'will', 'just', 'don', 'should', 'now', 'i', 'me', 'my', 'myself', 'we',
            'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves',
            'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its',
            'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
            'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
            'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as',
            'until', 'while'
        }
    
    def preprocess(self, text):
        """
        Preprocess the input text:
        1. Convert to lowercase
        2. Remove punctuation
        3. Tokenize
        4. Remove stopwords
        
        Args:
            text (str): The input text to preprocess
            
        Returns:
            list: List of preprocessed tokens
        """
        if not text:
            return []
        
        try:
            # Convert to lowercase
            text = text.lower()
            
            # Remove punctuation
            text = re.sub(f'[{re.escape(string.punctuation)}]', ' ', text)
            
            # Tokenize (split by whitespace)
            tokens = text.split()
            
            # Remove stopwords
            tokens = [token for token in tokens if token not in self.stopwords]
            
            return tokens
        
        except Exception as e:
            self.logger.error(f"Error preprocessing text: {str(e)}")
            return []
    
    def extract_keywords(self, text, n=5):
        """
        Extract the most important keywords from the text.
        
        Args:
            text (str): The input text
            n (int): The number of keywords to extract
            
        Returns:
            list: List of the most important keywords
        """
        tokens = self.preprocess(text)
        
        # Count token frequencies
        token_counts = Counter(tokens)
        
        # Get the n most common tokens
        most_common = token_counts.most_common(n)
        
        # Return just the keywords, not the counts
        return [keyword for keyword, _ in most_common]
    
    def detect_intent(self, text):
        """
        Attempt to detect the user's intent from the text.
        
        Args:
            text (str): The input text
            
        Returns:
            str: The detected intent or None
        """
        text_lower = text.lower()
        
        # Define some basic intent patterns
        greeting_patterns = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
        question_patterns = ['what', 'how', 'why', 'when', 'where', 'who', 'which', 'can you', 'could you']
        farewell_patterns = ['bye', 'goodbye', 'see you', 'farewell', 'exit', 'quit']
        thanks_patterns = ['thank', 'thanks', 'appreciate']
        help_patterns = ['help', 'assist', 'support']
        
        # Check for greetings
        if any(pattern in text_lower for pattern in greeting_patterns):
            return 'greeting'
        
        # Check for questions
        if any(pattern in text_lower for pattern in question_patterns) or text_lower.endswith('?'):
            return 'question'
        
        # Check for farewells
        if any(pattern in text_lower for pattern in farewell_patterns):
            return 'farewell'
        
        # Check for thanks
        if any(pattern in text_lower for pattern in thanks_patterns):
            return 'thanks'
        
        # Check for help requests
        if any(pattern in text_lower for pattern in help_patterns):
            return 'help'
        
        # Default to a general query intent
        return 'general_query'
