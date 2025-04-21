import os
import json
import logging
import re
from collections import defaultdict

class KnowledgeBase:
    """
    A custom knowledge base that stores and retrieves information from a text file.
    The file format is a simple structured text where each entry has:
    
    QUESTION: The question or query
    ANSWER: The corresponding answer
    TAGS: Comma-separated list of tags/keywords
    ---
    (separator between entries)
    """
    
    def __init__(self, file_path):
        """Initialize the knowledge base with the given file path."""
        self.file_path = file_path
        self.data = []
        self.keyword_index = defaultdict(list)
        self.logger = logging.getLogger(__name__)
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
                        'tags': tags
                    }
                    
                    self.data.append(entry_data)
                    
                    # Index keywords from question and tags for faster retrieval
                    keywords = set([word.lower() for word in re.findall(r'\w+', question)])
                    keywords.update(tags)
                    
                    for keyword in keywords:
                        if len(keyword) > 2:  # Only index keywords longer than 2 characters
                            self.keyword_index[keyword].append(len(self.data) - 1)
            
            self.logger.info(f"Loaded {len(self.data)} entries from knowledge base")
            
        except Exception as e:
            self.logger.error(f"Error loading knowledge base: {str(e)}")
            # Create a default knowledge base if loading fails
            self._create_default_knowledge_base()
    
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
        
        # Convert query tokens to a set of unique keywords
        query_keywords = set([word.lower() for word in query if len(word) > 2])
        
        # Calculate relevance scores for each entry
        scores = []
        for idx, entry in enumerate(self.data):
            score = 0
            
            # Score based on keyword matches in the index
            for keyword in query_keywords:
                if idx in self.keyword_index.get(keyword, []):
                    score += 1
            
            # Score based on question similarity
            entry_question_words = set([word.lower() for word in 
                                       re.findall(r'\w+', entry['question']) 
                                       if len(word) > 2])
            
            # Calculate Jaccard similarity between query and entry question
            if entry_question_words:
                intersection = len(query_keywords.intersection(entry_question_words))
                union = len(query_keywords.union(entry_question_words))
                if union > 0:
                    score += (intersection / union) * 2  # Weight this higher
            
            # Score based on tag matches
            for tag in entry['tags']:
                if tag in query_keywords:
                    score += 1.5  # Weight tag matches higher
            
            # Consider context if provided
            if context:
                # Look for keywords from previous messages that match this entry
                for message in context:
                    if message['role'] == 'user':
                        context_words = set([word.lower() for word in 
                                           re.findall(r'\w+', message['content']) 
                                           if len(word) > 2])
                        for word in context_words:
                            if idx in self.keyword_index.get(word, []):
                                score += 0.2  # Small boost for context relevance
            
            scores.append((idx, score))
        
        # Sort by score in descending order
        scores.sort(key=lambda x: x[1], reverse=True)
        
        self.logger.debug(f"Query: {query}, Top scores: {scores[:3]}")
        
        # Return the answer of the highest-scoring entry if it meets a minimum threshold
        if scores and scores[0][1] > 0.5:
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
                'tags': tags
            }
            
            self.data.append(entry)
            
            # Update the index
            keywords = set([word.lower() for word in re.findall(r'\w+', question)])
            keywords.update([tag.lower() for tag in tags])
            
            for keyword in keywords:
                if len(keyword) > 2:
                    self.keyword_index[keyword].append(len(self.data) - 1)
            
            # Save to file
            with open(self.file_path, 'a', encoding='utf-8') as file:
                file.write("\n---\n")
                file.write(f"QUESTION: {question}\n")
                file.write(f"ANSWER: {answer}\n")
                file.write(f"TAGS: {', '.join(tags)}\n")
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error adding entry to knowledge base: {str(e)}")
            return False
