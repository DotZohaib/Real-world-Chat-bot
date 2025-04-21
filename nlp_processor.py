import re
import string
import logging
import math
from collections import Counter

class NLPProcessor:
    """
    An enhanced NLP processor for handling natural language queries.
    Provides advanced tokenization, stopword removal, entity recognition, 
    and semantic analysis for better query understanding.
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
        
        # Intent patterns
        self.intent_patterns = {
            'greeting': [
                'hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 
                'good evening', 'howdy', 'what\'s up', 'how are you', 'nice to meet you'
            ],
            'farewell': [
                'bye', 'goodbye', 'see you', 'farewell', 'exit', 'quit', 'later', 
                'take care', 'have a good day', 'until next time', 'bye bye'
            ],
            'thanks': [
                'thank', 'thanks', 'appreciate', 'grateful', 'thank you', 'thanks a lot',
                'much appreciated', 'thank you very much'
            ],
            'help': [
                'help', 'assist', 'support', 'guide', 'explain', 'show me', 'how do i',
                'can you help', 'need help', 'assistance', 'instructions'
            ],
            'affirmation': [
                'yes', 'yeah', 'yep', 'correct', 'right', 'sure', 'absolutely', 
                'definitely', 'indeed', 'agree', 'affirmative', 'ok', 'okay'
            ],
            'negation': [
                'no', 'nope', 'not', 'never', 'negative', 'disagree', 'don\'t', 
                'do not', 'nah', 'won\'t', 'nothing', 'nowhere', 'nobody'
            ],
            'clarification': [
                'what do you mean', 'explain', 'clarify', 'elaborate', 'i don\'t understand',
                'confused', 'unclear', 'can you explain', 'what is', 'definition'
            ],
            'comparison': [
                'compare', 'difference', 'versus', 'vs', 'better', 'worse', 'best',
                'different', 'similar', 'same as', 'alternative', 'prefer'
            ]
        }
        
        # Common question starters
        self.question_starters = [
            'what', 'how', 'why', 'when', 'where', 'who', 'which', 'whose', 'whom',
            'can you', 'could you', 'would you', 'will you', 'should i', 'do you',
            'are there', 'is there', 'are you', 'is it'
        ]
        
        # Domain-specific terms for better matching
        self.domain_terms = {
            'chatbot': ['chatbot', 'bot', 'assistant', 'ai', 'artificial intelligence'],
            'knowledge': ['knowledge', 'information', 'data', 'facts', 'learn', 'know'],
            'technical': ['code', 'programming', 'software', 'app', 'application', 'web'],
            'functionality': ['function', 'capability', 'feature', 'ability', 'can do']
        }
    
    def preprocess(self, text):
        """
        Enhanced preprocessing of input text:
        1. Convert to lowercase
        2. Handle contractions
        3. Remove punctuation
        4. Tokenize with more sophisticated rules
        5. Remove stopwords
        6. Handle negations by preserving "not" + word pairs
        
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
            
            # Handle common contractions
            text = self._expand_contractions(text)
            
            # Preserve question marks for intent detection
            has_question_mark = '?' in text
            
            # Remove punctuation but preserve words
            text = re.sub(f'[{re.escape(string.punctuation)}]', ' ', text)
            
            # Tokenize (split by whitespace)
            tokens = text.split()
            
            # Handle negations
            negation_tokens = self._handle_negations(tokens)
            
            # Remove stopwords (except for preserved negations)
            filtered_tokens = []
            for token in negation_tokens:
                if '_not' in token or token not in self.stopwords:
                    filtered_tokens.append(token)
            
            # Add question indicator if there was a question mark
            if has_question_mark and filtered_tokens:
                filtered_tokens.append('question_mark')
            
            return filtered_tokens
        
        except Exception as e:
            self.logger.error(f"Error preprocessing text: {str(e)}")
            return []
    
    def _expand_contractions(self, text):
        """
        Expand common English contractions.
        
        Args:
            text (str): Text containing contractions
            
        Returns:
            str: Text with expanded contractions
        """
        # Common contractions mapping
        contractions = {
            "can't": "cannot",
            "won't": "will not",
            "n't": " not",
            "'ve": " have",
            "'re": " are",
            "'m": " am",
            "'ll": " will",
            "'d": " would",
            "'s": " is"
        }
        
        # Replace contractions
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text
    
    def _handle_negations(self, tokens):
        """
        Handle negations by combining 'not' with the following word.
        
        Args:
            tokens (list): List of tokens
            
        Returns:
            list: Tokens with handled negations
        """
        result = []
        i = 0
        while i < len(tokens):
            if tokens[i] in ['not', 'no', 'never'] and i + 1 < len(tokens):
                # Combine negation with the following word
                result.append(f"{tokens[i+1]}_not")
                i += 2
            else:
                result.append(tokens[i])
                i += 1
        
        return result
    
    def extract_keywords(self, text, n=5):
        """
        Extract the most important keywords from the text using TF-IDF-like weighting.
        
        Args:
            text (str): The input text
            n (int): The number of keywords to extract
            
        Returns:
            list: List of the most important keywords
        """
        tokens = self.preprocess(text)
        
        # Count token frequencies
        token_counts = Counter(tokens)
        
        # Apply a simple weight that prioritizes longer and less common words
        weighted_tokens = {}
        for token, count in token_counts.items():
            # Formula: count * (length of word) - gives more weight to longer words
            weighted_tokens[token] = count * min(len(token), 10) * 0.1
            
            # Boost domain-specific terms
            for domain, terms in self.domain_terms.items():
                if token in terms:
                    weighted_tokens[token] *= 1.5
        
        # Sort by weight and take top n
        sorted_tokens = sorted(weighted_tokens.items(), key=lambda x: x[1], reverse=True)
        
        # Return just the keywords, not the weights
        keywords = [keyword for keyword, _ in sorted_tokens[:n]]
        
        # Add any missed domain terms that appear in the original text
        if len(keywords) < n:
            text_lower = text.lower()
            for domain, terms in self.domain_terms.items():
                for term in terms:
                    if term in text_lower and term not in keywords:
                        keywords.append(term)
                        if len(keywords) >= n:
                            break
                if len(keywords) >= n:
                    break
        
        return keywords
    
    def detect_intent(self, text):
        """
        Advanced intent detection using pattern matching and contextual clues.
        
        Args:
            text (str): The input text
            
        Returns:
            str: The detected intent or 'general_query' if no specific intent is found
        """
        if not text:
            return 'general_query'
            
        text_lower = text.lower()
        
        # Check for question marks (explicit questions)
        is_question = '?' in text_lower or any(text_lower.startswith(starter) for starter in self.question_starters)
        
        # Check each intent pattern
        matched_intents = {}
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    matched_intents[intent] = matched_intents.get(intent, 0) + 1
        
        # Find the intent with the most matches
        best_intent = None
        best_score = 0
        for intent, score in matched_intents.items():
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # Question intent overrides others in certain cases
        if is_question and not (best_intent in ['greeting', 'farewell'] and best_score > 1):
            return 'question'
        
        # Return the best matched intent or default to general query
        return best_intent if best_intent else 'general_query'
    
    def calculate_similarity(self, tokens1, tokens2):
        """
        Calculate similarity between two sets of tokens using Jaccard similarity.
        
        Args:
            tokens1 (list): First list of tokens
            tokens2 (list): Second list of tokens
            
        Returns:
            float: Similarity score between 0 and 1
        """
        if not tokens1 or not tokens2:
            return 0.0
            
        set1 = set(tokens1)
        set2 = set(tokens2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
            
        return intersection / union
    
    def extract_entities(self, text):
        """
        Extract potential named entities and important phrases from text.
        
        Args:
            text (str): Input text
            
        Returns:
            dict: Dictionary of entity types and their values
        """
        entities = {
            'dates': [],
            'names': [],
            'technical_terms': [],
            'actions': []
        }
        
        # Very simple pattern matching for demonstration purposes
        text_lower = text.lower()
        
        # Extract dates using regex
        date_patterns = [
            r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}',  # DD/MM/YYYY or similar
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}(st|nd|rd|th)?,? \d{2,4}',  # Month Day, Year
            r'yesterday|today|tomorrow'  # Relative dates
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                entities['dates'].extend(matches)
        
        # Extract potential names (capitalized words not at the start of a sentence)
        name_pattern = r'(?<!\. )[A-Z][a-z]+'
        names = re.findall(name_pattern, text)
        entities['names'] = [name for name in names if name.lower() not in self.stopwords]
        
        # Extract technical terms
        for term_type, terms in self.domain_terms.items():
            for term in terms:
                if term in text_lower:
                    entities['technical_terms'].append(term)
        
        # Extract action verbs
        action_verbs = ['create', 'delete', 'update', 'add', 'remove', 'send', 'receive', 
                        'build', 'design', 'develop', 'learn', 'explain', 'compare']
        for verb in action_verbs:
            if verb in text_lower:
                entities['actions'].append(verb)
        
        return entities
    
    def analyze_sentiment(self, text):
        """
        Perform basic sentiment analysis on text.
        
        Args:
            text (str): Input text
            
        Returns:
            dict: Sentiment analysis with polarity score and labels
        """
        text_lower = text.lower()
        
        # Basic positive and negative word lists
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'helpful',
            'useful', 'thank', 'thanks', 'appreciate', 'happy', 'glad', 'love', 'like',
            'best', 'better', 'awesome', 'nice', 'well', 'positive', 'correct', 'right'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'poor', 'useless', 'unhelpful',
            'wrong', 'hate', 'dislike', 'worst', 'worse', 'negative', 'error', 'fail',
            'problem', 'issue', 'bug', 'difficult', 'hard', 'complicated', 'confused'
        ]
        
        # Count occurrences
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Check for negations
        negations = ['not', 'no', 'never', 'cannot', 'shouldn\'t', 'wouldn\'t', 'don\'t', 'doesn\'t']
        negation_count = sum(1 for neg in negations if neg in text_lower)
        
        # If there's an odd number of negations, it flips the sentiment
        if negation_count % 2 == 1:
            positive_count, negative_count = negative_count, positive_count
        
        # Calculate polarity score (-1.0 to 1.0)
        total = positive_count + negative_count
        if total == 0:
            polarity = 0.0  # Neutral
        else:
            polarity = (positive_count - negative_count) / total
        
        # Determine sentiment label
        if polarity >= 0.5:
            sentiment = 'positive'
        elif polarity <= -0.5:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'polarity': polarity,
            'sentiment': sentiment,
            'positive_score': positive_count,
            'negative_score': negative_count
        }
    
    def get_context_relevance(self, query, context_messages, n=5):
        """
        Determine which context messages are most relevant to the current query.
        
        Args:
            query (str): The current query
            context_messages (list): List of previous messages
            n (int): Number of most relevant context messages to return
            
        Returns:
            list: List of indices of the most relevant context messages
        """
        if not query or not context_messages:
            return []
            
        query_tokens = self.preprocess(query)
        
        # Calculate relevance scores for each context message
        relevance_scores = []
        for i, msg in enumerate(context_messages):
            if msg.get('role') == 'user':
                msg_tokens = self.preprocess(msg.get('content', ''))
                similarity = self.calculate_similarity(query_tokens, msg_tokens)
                
                # Decay factor based on position (more recent = more relevant)
                recency_factor = 1.0 - (0.1 * (len(context_messages) - i - 1))
                recency_factor = max(0.1, recency_factor)  # Ensure minimum weight
                
                relevance_scores.append((i, similarity * recency_factor))
            else:
                relevance_scores.append((i, 0))  # Bot messages get 0 relevance
        
        # Sort by relevance score (descending)
        relevance_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return indices of top N most relevant context messages
        return [idx for idx, score in relevance_scores[:n] if score > 0]
