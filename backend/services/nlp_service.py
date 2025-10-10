from sentence_transformers import SentenceTransformer   #the nlp model used to load a pretrained model that produces sentence embeddings.
from sklearn.metrics.pairwise import cosine_similarity  # using this the for the cosine similarity
import numpy as np # numpy lib
import os
from typing import List, Dict, Tuple

class NLPService:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        Initialize the NLP service with a pre-trained sentence transformer model
        all-MiniLM-L6-v2 is a good balance between speed and quality
        """
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', 0.7))
    
    def create_item_text(self, item_data: Dict) -> str:
        """
        Create a comprehensive text representation of an item for embedding
        """
        text_parts = []
        
        # Add title and description (most important)
        if item_data.get('title'):
            text_parts.append(item_data['title'])
        if item_data.get('description'):
            text_parts.append(item_data['description'])
        
        # Add category and brand
        if item_data.get('category'):
            text_parts.append(f"category: {item_data['category']}")
        if item_data.get('brand'):
            text_parts.append(f"brand: {item_data['brand']}")
        
        # Add color information
        if item_data.get('color'):
            text_parts.append(f"color: {item_data['color']}")
        
        # Add condition for found items
        if item_data.get('condition'):
            text_parts.append(f"condition: {item_data['condition']}")
        
        # Add location context
        if item_data.get('lost_location'):
            text_parts.append(f"lost at: {item_data['lost_location']}")
        elif item_data.get('found_location'):
            text_parts.append(f"found at: {item_data['found_location']}")
        
        return ' '.join(text_parts)
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for a given text
        """
        embedding = self.model.encode([text])
        return embedding[0]
    
    def generate_item_embedding(self, item_data: Dict) -> np.ndarray:
        """
        Generate embedding for an item based on its description and metadata
        """
        item_text = self.create_item_text(item_data)
        return self.generate_embedding(item_text)
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        """
        # Reshape to 2D arrays for sklearn
        emb1 = embedding1.reshape(1, -1)
        emb2 = embedding2.reshape(1, -1)
        
        similarity = cosine_similarity(emb1, emb2)[0][0]
        return float(similarity)
    
    def find_similar_items(self, target_embedding: np.ndarray, 
                          candidate_embeddings: List[np.ndarray],
                          candidate_ids: List[int],
                          threshold: float = None) -> List[Tuple[int, float]]:
        """
        Find similar items based on embeddings
        Returns list of (item_id, similarity_score) tuples above threshold
        """
        if threshold is None:
            threshold = self.similarity_threshold
        
        similar_items = []
        
        for item_id, candidate_embedding in zip(candidate_ids, candidate_embeddings):
            similarity = self.calculate_similarity(target_embedding, candidate_embedding)
            
            if similarity >= threshold:
                similar_items.append((item_id, similarity))
        
        # Sort by similarity score (descending)
        similar_items.sort(key=lambda x: x[1], reverse=True)
        
        return similar_items
    
    def preprocess_text(self, text: str) -> str:
        """
        Basic text preprocessing
        """
        # Convert to lowercase and strip whitespace
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Simple keyword extraction (can be enhanced with more sophisticated NLP)
        """
        # Basic implementation - split and filter common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'it', 'he', 'she', 'they', 'we', 'you', 'i', 'me', 'him', 'her', 'them', 'us', 'my', 'your', 'his', 'her', 'their', 'our', 'this', 'that', 'these', 'those'}
        
        words = self.preprocess_text(text).split()
        keywords = [word for word in words if len(word) > 2 and word not in common_words]
        
        return keywords
    
    def create_search_query_embedding(self, query: str, category: str = None, 
                                    color: str = None, location: str = None) -> np.ndarray:
        """
        Create embedding for search query with additional context
        """
        query_parts = [query]
        
        if category:
            query_parts.append(f"category: {category}")
        if color:
            query_parts.append(f"color: {color}")
        if location:
            query_parts.append(f"location: {location}")
        
        query_text = ' '.join(query_parts)
        return self.generate_embedding(query_text)
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently
        """
        embeddings = self.model.encode(texts)
        return [embedding for embedding in embeddings]

# Global instance to be used across the application
nlp_service = NLPService()