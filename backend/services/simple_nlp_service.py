"""
Simple NLP service for text similarity without heavy dependencies
Uses basic text processing and cosine similarity with TF-IDF vectors
"""

import re
import math
from collections import Counter
from typing import List, Dict, Tuple

class SimpleNLPService:
    def __init__(self, similarity_threshold=0.7):
        self.similarity_threshold = similarity_threshold
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 
            'with', 'by', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 
            'may', 'might', 'must', 'can', 'it', 'he', 'she', 'they', 'we', 'you', 
            'i', 'me', 'him', 'her', 'them', 'us', 'my', 'your', 'his', 'her', 
            'their', 'our', 'this', 'that', 'these', 'those'
        }
    
    def preprocess_text(self, text: str) -> str:
        """Basic text preprocessing"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and digits, keep only letters and spaces
        text = re.sub(r'[^a-z\s]', ' ', text)
        
        # Remove extra whitespaces
        text = ' '.join(text.split())
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words, removing stop words"""
        text = self.preprocess_text(text)
        words = text.split()
        return [word for word in words if word not in self.stop_words and len(word) > 2]
    
    def create_item_text(self, item_data: Dict) -> str:
        """Create comprehensive text representation of an item"""
        text_parts = []
        
        # Add title and description (most important)
        if item_data.get('title'):
            text_parts.append(item_data['title'])
        if item_data.get('description'):
            text_parts.append(item_data['description'])
        
        # Add category and brand
        if item_data.get('category'):
            text_parts.append(f"category {item_data['category']}")
        if item_data.get('brand'):
            text_parts.append(f"brand {item_data['brand']}")
        
        # Add color information
        if item_data.get('color'):
            text_parts.append(f"color {item_data['color']}")
        
        # Add condition for found items
        if item_data.get('condition'):
            text_parts.append(f"condition {item_data['condition']}")
        
        # Add location context
        if item_data.get('lost_location'):
            text_parts.append(f"lost at {item_data['lost_location']}")
        elif item_data.get('found_location'):
            text_parts.append(f"found at {item_data['found_location']}")
        
        return ' '.join(text_parts)
    
    def calculate_tf_idf_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity using TF-IDF and cosine similarity"""
        # Tokenize both texts
        tokens1 = self.tokenize(text1)
        tokens2 = self.tokenize(text2)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # Create combined vocabulary
        vocab = set(tokens1 + tokens2)
        
        if not vocab:
            return 0.0
        
        # Calculate term frequencies
        tf1 = Counter(tokens1)
        tf2 = Counter(tokens2)
        
        # Create TF-IDF vectors
        vec1 = []
        vec2 = []
        
        for term in vocab:
            # Simple TF-IDF (without full corpus IDF calculation)
            tf1_val = tf1.get(term, 0) / len(tokens1) if tokens1 else 0
            tf2_val = tf2.get(term, 0) / len(tokens2) if tokens2 else 0
            
            vec1.append(tf1_val)
            vec2.append(tf2_val)
        
        return self.cosine_similarity(vec1, vec2)
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def calculate_jaccard_similarity(self, text1: str, text2: str) -> float:
        """Calculate Jaccard similarity between two texts"""
        tokens1 = set(self.tokenize(text1))
        tokens2 = set(self.tokenize(text2))
        
        if not tokens1 and not tokens2:
            return 1.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate combined similarity score"""
        if not text1 or not text2:
            return 0.0
        
        # Calculate different similarity measures
        tf_idf_sim = self.calculate_tf_idf_similarity(text1, text2)
        jaccard_sim = self.calculate_jaccard_similarity(text1, text2)
        
        # Combine similarities (weighted average)
        combined_similarity = (0.7 * tf_idf_sim) + (0.3 * jaccard_sim)
        
        return combined_similarity
    
    def generate_item_embedding(self, item_data: Dict) -> List[float]:
        """Generate a simple 'embedding' (just tokenized text for now)"""
        item_text = self.create_item_text(item_data)
        tokens = self.tokenize(item_text)
        
        # Create a simple word frequency vector as embedding
        word_counts = Counter(tokens)
        
        # Get top 50 most common words as features
        vocab_size = 50
        top_words = [word for word, _ in word_counts.most_common(vocab_size)]
        
        # Create embedding vector
        embedding = []
        for word in top_words:
            embedding.append(word_counts.get(word, 0))
        
        # Pad or truncate to fixed size
        while len(embedding) < vocab_size:
            embedding.append(0.0)
        
        return embedding[:vocab_size]
    
    def find_similar_items(self, target_text: str, candidate_texts: List[str], 
                          candidate_ids: List[int], threshold: float = None) -> List[Tuple[int, float]]:
        """Find similar items based on text similarity"""
        if threshold is None:
            threshold = self.similarity_threshold
        
        similar_items = []
        
        for item_id, candidate_text in zip(candidate_ids, candidate_texts):
            similarity = self.calculate_similarity(target_text, candidate_text)
            
            if similarity >= threshold:
                similar_items.append((item_id, similarity))
        
        # Sort by similarity score (descending)
        similar_items.sort(key=lambda x: x[1], reverse=True)
        
        return similar_items
    
    def create_search_query_embedding(self, query: str, category: str = None, 
                                    color: str = None, location: str = None) -> List[float]:
        """Create embedding for search query with additional context"""
        query_parts = [query]
        
        if category:
            query_parts.append(f"category {category}")
        if color:
            query_parts.append(f"color {color}")
        if location:
            query_parts.append(f"location {location}")
        
        query_text = ' '.join(query_parts)
        
        # For now, return the query text (we'll use text similarity directly)
        tokens = self.tokenize(query_text)
        word_counts = Counter(tokens)
        
        # Create simple embedding
        vocab_size = 50
        embedding = []
        for i in range(vocab_size):
            if i < len(tokens):
                word = tokens[i] if i < len(tokens) else ""
                embedding.append(word_counts.get(word, 0))
            else:
                embedding.append(0.0)
        
        return embedding

# Global instance to be used across the application
simple_nlp_service = SimpleNLPService()