from typing import List, Dict, Tuple
import numpy as np
from models.models import LostItem, FoundItem, Match, db
from services.nlp_service import nlp_service
from datetime import datetime, timedelta

class MatchingService:
    def __init__(self):
        self.nlp_service = nlp_service
    
    def find_matches_for_lost_item(self, lost_item: LostItem, limit: int = 10) -> List[Tuple[FoundItem, float]]:
        """
        Find potential matches for a lost item among found items
        """
        # Get the embedding for the lost item
        lost_embedding = self._get_or_generate_embedding(lost_item)
        if lost_embedding is None:
            return []
        
        # Get all available found items
        found_items = FoundItem.query.filter_by(status='available').all()
        
        matches = []
        for found_item in found_items:
            # Skip items from the same user
            if found_item.user_id == lost_item.user_id:
                continue
            
            # Get or generate embedding for found item
            found_embedding = self._get_or_generate_embedding(found_item)
            if found_embedding is None:
                continue
            
            # Calculate similarity
            similarity = self.nlp_service.calculate_similarity(lost_embedding, found_embedding)
            
            # Apply additional filtering based on metadata
            if self._passes_metadata_filter(lost_item, found_item, similarity):
                matches.append((found_item, similarity))
        
        # Sort by similarity and return top matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]
    
    def find_matches_for_found_item(self, found_item: FoundItem, limit: int = 10) -> List[Tuple[LostItem, float]]:
        """
        Find potential matches for a found item among lost items
        """
        # Get the embedding for the found item
        found_embedding = self._get_or_generate_embedding(found_item)
        if found_embedding is None:
            return []
        
        # Get all active lost items
        lost_items = LostItem.query.filter_by(status='active').all()
        
        matches = []
        for lost_item in lost_items:
            # Skip items from the same user
            if lost_item.user_id == found_item.user_id:
                continue
            
            # Get or generate embedding for lost item
            lost_embedding = self._get_or_generate_embedding(lost_item)
            if lost_embedding is None:
                continue
            
            # Calculate similarity
            similarity = self.nlp_service.calculate_similarity(found_embedding, lost_embedding)
            
            # Apply additional filtering based on metadata
            if self._passes_metadata_filter(lost_item, found_item, similarity):
                matches.append((lost_item, similarity))
        
        # Sort by similarity and return top matches
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:limit]
    
    def create_matches_for_item(self, item, is_lost_item: bool = True) -> List[Match]:
        """
        Create match records for an item and return them
        """
        matches_created = []
        
        if is_lost_item:
            potential_matches = self.find_matches_for_lost_item(item)
            for found_item, similarity in potential_matches:
                # Check if match already exists
                existing_match = Match.query.filter_by(
                    lost_item_id=item.id,
                    found_item_id=found_item.id
                ).first()
                
                if not existing_match:
                    match = Match(
                        lost_item_id=item.id,
                        found_item_id=found_item.id,
                        similarity_score=similarity
                    )
                    db.session.add(match)
                    matches_created.append(match)
        else:
            potential_matches = self.find_matches_for_found_item(item)
            for lost_item, similarity in potential_matches:
                # Check if match already exists
                existing_match = Match.query.filter_by(
                    lost_item_id=lost_item.id,
                    found_item_id=item.id
                ).first()
                
                if not existing_match:
                    match = Match(
                        lost_item_id=lost_item.id,
                        found_item_id=item.id,
                        similarity_score=similarity
                    )
                    db.session.add(match)
                    matches_created.append(match)
        
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
        
        return matches_created
    
    def _get_or_generate_embedding(self, item) -> np.ndarray:
        """
        Get existing embedding or generate new one for an item
        """
        # Try to get existing embedding
        existing_embedding = item.get_embedding()
        if existing_embedding is not None:
            return np.array(existing_embedding)
        
        # Generate new embedding
        item_data = item.to_dict()
        embedding = self.nlp_service.generate_item_embedding(item_data)
        
        # Store the embedding
        item.set_embedding(embedding)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        
        return embedding
    
    def _passes_metadata_filter(self, lost_item: LostItem, found_item: FoundItem, similarity: float) -> bool:
        """
        Apply additional filtering based on metadata beyond text similarity
        """
        # Check similarity threshold
        if similarity < self.nlp_service.similarity_threshold:
            return False
        
        # Category must match (if both have categories)
        if lost_item.category and found_item.category:
            if lost_item.category.lower() != found_item.category.lower():
                return False
        
        # Color should match (if both have colors)
        if lost_item.color and found_item.color:
            if lost_item.color.lower() != found_item.color.lower():
                # Allow some flexibility for color matching
                color_similarity = self._calculate_color_similarity(lost_item.color, found_item.color)
                if color_similarity < 0.5:  # Adjust threshold as needed
                    return False
        
        # Date range check - found item should be found after lost item
        if lost_item.lost_date and found_item.found_date:
            if found_item.found_date < lost_item.lost_date:
                return False
            
            # Don't match items with too large time gap (optional)
            time_diff = found_item.found_date - lost_item.lost_date
            if time_diff.days > 365:  # 1 year maximum
                return False
        
        # Location proximity check (basic implementation)
        location_similarity = self._calculate_location_similarity(
            lost_item.lost_location, 
            found_item.found_location
        )
        if location_similarity < 0.3:  # Adjust threshold as needed
            return False
        
        return True
    
    def _calculate_color_similarity(self, color1: str, color2: str) -> float:
        """
        Simple color similarity calculation
        """
        color1 = color1.lower().strip()
        color2 = color2.lower().strip()
        
        if color1 == color2:
            return 1.0
        
        # Define color groups for similar colors
        color_groups = [
            ['red', 'burgundy', 'crimson', 'scarlet'],
            ['blue', 'navy', 'azure', 'cyan'],
            ['green', 'emerald', 'lime', 'olive'],
            ['yellow', 'gold', 'amber'],
            ['black', 'dark', 'charcoal'],
            ['white', 'cream', 'ivory'],
            ['gray', 'grey', 'silver'],
            ['brown', 'tan', 'beige', 'khaki'],
            ['purple', 'violet', 'magenta'],
            ['orange', 'coral', 'peach']
        ]
        
        for group in color_groups:
            if color1 in group and color2 in group:
                return 0.8
        
        return 0.0
    
    def _calculate_location_similarity(self, location1: str, location2: str) -> float:
        """
        Simple location similarity calculation
        """
        if not location1 or not location2:
            return 0.5  # Neutral if one location is missing
        
        location1 = location1.lower().strip()
        location2 = location2.lower().strip()
        
        if location1 == location2:
            return 1.0
        
        # Check if one location contains the other
        if location1 in location2 or location2 in location1:
            return 0.8
        
        # Use NLP service to calculate text similarity
        loc1_embedding = self.nlp_service.generate_embedding(location1)
        loc2_embedding = self.nlp_service.generate_embedding(location2)
        
        return self.nlp_service.calculate_similarity(loc1_embedding, loc2_embedding)
    
    def search_items(self, query: str, item_type: str = 'both', 
                    category: str = None, color: str = None, 
                    location: str = None, limit: int = 20) -> List[Dict]:
        """
        Search for items based on query and filters
        """
        # Generate embedding for search query
        query_embedding = self.nlp_service.create_search_query_embedding(
            query, category, color, location
        )
        
        results = []
        
        if item_type in ['lost', 'both']:
            lost_items = LostItem.query.filter_by(status='active').all()
            for item in lost_items:
                item_embedding = self._get_or_generate_embedding(item)
                if item_embedding is not None:
                    similarity = self.nlp_service.calculate_similarity(query_embedding, item_embedding)
                    
                    if similarity > 0.3:  # Lower threshold for search
                        result = item.to_dict()
                        result['similarity'] = similarity
                        result['type'] = 'lost'
                        results.append(result)
        
        if item_type in ['found', 'both']:
            found_items = FoundItem.query.filter_by(status='available').all()
            for item in found_items:
                item_embedding = self._get_or_generate_embedding(item)
                if item_embedding is not None:
                    similarity = self.nlp_service.calculate_similarity(query_embedding, item_embedding)
                    
                    if similarity > 0.3:  # Lower threshold for search
                        result = item.to_dict()
                        result['similarity'] = similarity
                        result['type'] = 'found'
                        results.append(result)
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results[:limit]
    
    def get_user_matches(self, user_id: int) -> List[Dict]:
        """
        Get all matches for a user's items
        """
        # Get matches where user has lost items
        lost_matches = db.session.query(Match).join(LostItem).filter(
            LostItem.user_id == user_id
        ).all()
        
        # Get matches where user has found items
        found_matches = db.session.query(Match).join(FoundItem).filter(
            FoundItem.user_id == user_id
        ).all()
        
        all_matches = lost_matches + found_matches
        
        return [match.to_dict() for match in all_matches]

# Global instance
matching_service = MatchingService()