import os
import json
import logging
import re
import math
import time
from collections import defaultdict

class KnowledgeBase:
    """
    An enhanced knowledge base that stores and retrieves information from a text file.
    The file format is a simple structured text where each entry has:
    
    QUESTION: The question or query
    ANSWER: The corresponding answer
    TAGS: Comma-separated list of tags/keywords
    ---
    (separator between entries)
    
    Features improved relevance scoring, fuzzy matching, and context-aware responses.
    """
    
    def __init__(self, file_path):
        """Initialize the knowledge base with the given file path."""
        self.file_path = file_path
        self.data = []
        self.keyword_index = defaultdict(list)
        self.tag_index = defaultdict(list)
        self.logger = logging.getLogger(__name__)
        
        # Cache to store frequent queries
        self.response_cache = {}
        self.cache_limit = 100  # Maximum number of cached responses
        
        # Load knowledge base data
        self.load_data()
    
    def load_data(self):
        """Load data from the knowledge base file."""
        try:
            if not os.path.exists(self.file_path):
                self.logger.warning(f"Knowledge base file {self.file_path} not found. Creating a new one.")
                self._create_default_knowledge_base()
                
            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Split the content by the separator
            entries = content.split('---')
            
            # Clear existing data and indices
            self.data = []
            self.keyword_index = defaultdict(list)
            self.tag_index = defaultdict(list)
            
            for entry in entries:
                if not entry.strip():
                    continue
                
                # Parse entry fields
                question_match = re.search(r'QUESTION:(.*?)(?=ANSWER:|$)', entry, re.DOTALL)
                answer_match = re.search(r'ANSWER:(.*?)(?=TAGS:|$)', entry, re.DOTALL)
                tags_match = re.search(r'TAGS:(.*?)(?=$)', entry, re.DOTALL)
                
                if question_match and answer_match:
                    question = question_match.group(1).strip()
                    answer = answer_match.group(1).strip()
                    tags = tags_match.group(1).strip().split(',') if tags_match else []
                    tags = [tag.strip().lower() for tag in tags]
                    
                    entry_data = {
                        'question': question,
                        'answer': answer,
                        'tags': tags,
                        'created_at': time.time()
                    }
                    
                    self.data.append(entry_data)
                    current_idx = len(self.data) - 1
                    
                    # Index keywords from question for faster retrieval
                    keywords = self._extract_keywords(question)
                    
                    # Create keyword index
                    for keyword in keywords:
                        if len(keyword) > 2:  # Only index keywords longer than 2 characters
                            self.keyword_index[keyword].append(current_idx)
                    
                    # Create tag index
                    for tag in tags:
                        if tag:
                            self.tag_index[tag].append(current_idx)
            
            self.logger.info(f"Loaded {len(self.data)} entries from knowledge base")
            
        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {str(e)}")
            # Create a default knowledge base if loading fails
            self._create_default_knowledge_base()
    
    def _extract_keywords(self, text):
        """Extract keywords from text for indexing."""
        # Convert to lowercase and remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split into words and filter
        words = text.split()
        
        # Return unique keywords
        return set(words)
    
    def _calculate_idf(self, term):
        """Calculate Inverse Document Frequency (IDF) for a term."""
        doc_count = len(self.data)
        term_doc_count = len(self.keyword_index.get(term, [])) or 1
        return math.log(doc_count / term_doc_count) + 1
    
    def _calculate_term_frequency(self, term, text):
        """Calculate normalized term frequency."""
        text_lower = text.lower()
        words = re.findall(r'\w+', text_lower)
        term_count = sum(1 for word in words if word == term)
        
        if not words:
            return 0
        
        return term_count / len(words)
    
    def _create_default_knowledge_base(self):
        """Create a default knowledge base with some example entries."""
        default_data = """QUESTION: What can you help me with?
ANSWER: I'm a chatbot designed to answer questions based on my knowledge base. You can ask me questions about various topics and I'll try to provide relevant information.
TAGS: help, introduction, capabilities
---
QUESTION: How do you work?
ANSWER: I process your questions using natural language processing techniques and match them against my knowledge base to find the most relevant answers. I also maintain some context from our conversation to provide more coherent responses.
TAGS: functionality, explanation, system
---
QUESTION: Who created you?
ANSWER: I was created as a custom chatbot application with a Flask backend that processes natural language queries against a knowledge base file. I was built with Python, Flask, and some basic NLP capabilities.
TAGS: creator, origin, development
"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as file:
                file.write(default_data)
            
            self.logger.info(f"Created default knowledge base at {self.file_path}")
            self.load_data()  # Reload the data
        except Exception as e:
            self.logger.error(f"Error creating default knowledge base: {str(e)}")
    
    def get_response(self, query, context=None):
        """
        Get the most relevant response for a given query, taking into account conversation context.
        
        Args:
            query (list): List of preprocessed tokens from the query
            context (list, optional): List of previous conversation messages
            
        Returns:
            str: The most relevant answer or None if no match found
        """
        if not query:
            return None
        
        # Check cache first for exact query match (as a string)
        cache_key = ' '.join(query)
        if cache_key in self.response_cache:
            return self.response_cache[cache_key]
        
        # Convert query tokens to a set of unique keywords
        query_keywords = set([word.lower() for word in query if len(word) > 2])
        
        # Calculate relevance scores for each entry using TF-IDF weighting
        scores = []
        for idx, entry in enumerate(self.data):
            # Initialize the score
            base_score = 0
            tfidf_score = 0
            tag_score = 0
            question_similarity_score = 0
            context_score = 0
            
            # Score based on TF-IDF for each keyword in the query
            for keyword in query_keywords:
                if len(keyword) <= 2:
                    continue
                
                # Calculate TF-IDF score
                idf = self._calculate_idf(keyword)
                tf = self._calculate_term_frequency(keyword, entry['question'])
                tfidf = tf * idf
                
                # Add to the total TF-IDF score
                tfidf_score += tfidf
                
                # Boost score for direct keyword matches in the index
                if idx in self.keyword_index.get(keyword, []):
                    base_score += 1
            
            # Score based on question similarity using Jaccard similarity
            entry_question_words = set([word.lower() for word in 
                                      re.findall(r'\w+', entry['question']) 
                                      if len(word) > 2])
            
            if entry_question_words:
                intersection = len(query_keywords.intersection(entry_question_words))
                union = len(query_keywords.union(entry_question_words))
                if union > 0:
                    similarity = intersection / union
                    question_similarity_score = similarity * 3  # Weight this higher
            
            # Score based on tag matches
            for tag in entry['tags']:
                if any(tag in keyword for keyword in query_keywords):
                    tag_score += 2  # Weight tag matches higher
                elif any(keyword in tag for keyword in query_keywords):
                    tag_score += 1.5  # Partial tag matches
            
            # Consider context if provided
            if context:
                # Extract context from previous messages
                context_keywords = set()
                for i, message in enumerate(context):
                    if message.get('role') == 'user' and 'content' in message:
                        # Extract words from user messages
                        context_words = set([word.lower() for word in 
                                           re.findall(r'\w+', message['content']) 
                                           if len(word) > 2])
                        
                        # Add recency weighting (more recent messages have higher weight)
                        recency_factor = min(1.0, 0.5 + (i / len(context)))
                        
                        for word in context_words:
                            if idx in self.keyword_index.get(word, []):
                                # Boost score based on context relevance with recency factor
                                context_score += 0.3 * recency_factor
                
                # Boost entries that match the current conversation topic
                if context_keywords:
                    for keyword in context_keywords:
                        if idx in self.keyword_index.get(keyword, []):
                            context_score += 0.2
            
            # Calculate total score with different weights for each component
            total_score = (
                base_score * 1.0 +
                tfidf_score * 1.5 +
                question_similarity_score * 2.0 +
                tag_score * 1.8 +
                context_score * 1.2
            )
            
            scores.append((idx, total_score))
        
        # Sort by score in descending order
        scores.sort(key=lambda x: x[1], reverse=True)
        
        self.logger.debug(f"Query: {query}, Top scores: {scores[:3]}")
        
        # Return the answer of the highest-scoring entry if it meets a minimum threshold
        if scores and scores[0][1] > 0.8:  # Higher threshold for better precision
            best_match_idx = scores[0][0]
            answer = self.data[best_match_idx]['answer']
            
            # Cache the result for future queries
            if len(self.response_cache) >= self.cache_limit:
                # Remove a random key if cache is full
                self.response_cache.pop(next(iter(self.response_cache)))
            self.response_cache[cache_key] = answer
            
            return answer
        
        # Handle "almost" matches with a lower threshold for recall
        elif scores and scores[0][1] > 0.5:
            best_match_idx = scores[0][0]
            return self.data[best_match_idx]['answer']
        
        return None
    
    def add_entry(self, question, answer, tags=None):
        """
        Add a new entry to the knowledge base.
        
        Args:
            question (str): The question or query
            answer (str): The corresponding answer
            tags (list, optional): List of tags/keywords
            
        Returns:
            bool: True if the entry was added successfully, False otherwise
        """
        if not tags:
            tags = []
        
        try:
            # Create the new entry
            entry = {
                'question': question,
                'answer': answer,
                'tags': tags,
                'created_at': time.time()
            }
            
            # Check for duplicate questions (avoid exact duplicates)
            for existing_entry in self.data:
                if existing_entry['question'].lower() == question.lower():
                    self.logger.warning(f"Duplicate question: {question}. Entry not added.")
                    return False
            
            # Add to the data list
            self.data.append(entry)
            current_idx = len(self.data) - 1
            
            # Extract and index keywords
            keywords = self._extract_keywords(question)
            for keyword in keywords:
                if len(keyword) > 2:
                    self.keyword_index[keyword].append(current_idx)
            
            # Index tags
            for tag in tags:
                tag = tag.lower().strip()
                if tag:
                    self.tag_index[tag].append(current_idx)
            
            # Save to file
            try:
                with open(self.file_path, 'a', encoding='utf-8') as file:
                    file.write("\n---\n")
                    file.write(f"QUESTION: {question}\n")
                    file.write(f"ANSWER: {answer}\n")
                    file.write(f"TAGS: {', '.join(tags)}\n")
                
                # Clear cache since the knowledge base has changed
                self.response_cache = {}
                
                self.logger.info(f"Added new entry: {question}")
                return True
            
            except Exception as file_error:
                self.logger.error(f"Error writing to file: {str(file_error)}")
                # Rollback the addition
                self.data.pop()
                return False
            
        except Exception as e:
            self.logger.error(f"Error adding entry to knowledge base: {str(e)}")
            return False
    
    def search_by_tag(self, tag):
        """
        Get entries that have a specific tag.
        
        Args:
            tag (str): The tag to search for
            
        Returns:
            list: List of entries with the specified tag
        """
        if not tag:
            return []
        
        tag = tag.lower().strip()
        entry_indices = self.tag_index.get(tag, [])
        
        return [self.data[idx] for idx in entry_indices]
    
    def get_all_tags(self):
        """
        Get a list of all tags in the knowledge base.
        
        Returns:
            list: List of unique tags
        """
        return list(self.tag_index.keys())
    
    def search_entries(self, query, limit=10):
        """
        Search entries by keyword.
        
        Args:
            query (str): The search query
            limit (int): Maximum number of results to return
            
        Returns:
            list: List of matching entries
        """
        # Extract search keywords
        keywords = self._extract_keywords(query)
        if not keywords:
            return []
        
        # Track matched entries with scores
        entry_scores = defaultdict(float)
        
        # Search by keywords
        for keyword in keywords:
            if len(keyword) <= 2:
                continue
                
            matched_indices = self.keyword_index.get(keyword, [])
            for idx in matched_indices:
                entry_scores[idx] += 1
        
        # Sort by score
        sorted_entries = sorted(
            [(idx, score) for idx, score in entry_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Return the top matches
        return [self.data[idx] for idx, _ in sorted_entries[:limit]]
    
    def get_similar_questions(self, question, limit=5):
        """
        Find questions similar to the input question.
        
        Args:
            question (str): The question to find similar questions for
            limit (int): Maximum number of similar questions to return
            
        Returns:
            list: List of similar questions with their similarity scores
        """
        keywords = self._extract_keywords(question)
        if not keywords:
            return []
        
        # Calculate similarity for each entry
        similarities = []
        for idx, entry in enumerate(self.data):
            entry_keywords = self._extract_keywords(entry['question'])
            
            # Skip entries with no keywords
            if not entry_keywords:
                continue
            
            # Calculate Jaccard similarity
            intersection = len(keywords.intersection(entry_keywords))
            union = len(keywords.union(entry_keywords))
            
            if union > 0:
                similarity = intersection / union
                if similarity > 0.2:  # Only include somewhat similar questions
                    similarities.append((idx, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return the top similar questions
        similar_questions = []
        for idx, similarity in similarities[:limit]:
            similar_questions.append({
                'question': self.data[idx]['question'],
                'similarity': similarity
            })
        
        return similar_questions
