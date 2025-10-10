from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    lost_items = db.relationship('LostItem', backref='user', lazy=True)
    found_items = db.relationship('FoundItem', backref='user', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'created_at': self.created_at.isoformat()
        }

class LostItem(db.Model):
    __tablename__ = 'lost_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(50), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    lost_location = db.Column(db.String(255), nullable=False)
    lost_date = db.Column(db.Date, nullable=False)
    reward_amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')  # active, matched, closed
    embedding = db.Column(db.Text, nullable=True)  # JSON string of embedding vector
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_embedding(self, embedding_vector):
        self.embedding = json.dumps(embedding_vector.tolist())
    
    def get_embedding(self):
        if self.embedding:
            return json.loads(self.embedding)
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'color': self.color,
            'brand': self.brand,
            'image_url': self.image_url,
            'lost_location': self.lost_location,
            'lost_date': self.lost_date.isoformat(),
            'reward_amount': self.reward_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class FoundItem(db.Model):
    __tablename__ = 'found_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(50), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    found_location = db.Column(db.String(255), nullable=False)
    found_date = db.Column(db.Date, nullable=False)
    condition = db.Column(db.String(100), nullable=False)  # excellent, good, fair, poor
    status = db.Column(db.String(20), default='available')  # available, matched, returned
    embedding = db.Column(db.Text, nullable=True)  # JSON string of embedding vector
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_embedding(self, embedding_vector):
        self.embedding = json.dumps(embedding_vector.tolist())
    
    def get_embedding(self):
        if self.embedding:
            return json.loads(self.embedding)
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'color': self.color,
            'brand': self.brand,
            'image_url': self.image_url,
            'found_location': self.found_location,
            'found_date': self.found_date.isoformat(),
            'condition': self.condition,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.Integer, primary_key=True)
    lost_item_id = db.Column(db.Integer, db.ForeignKey('lost_items.id'), nullable=False)
    found_item_id = db.Column(db.Integer, db.ForeignKey('found_items.id'), nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    lost_item = db.relationship('LostItem', backref='matches')
    found_item = db.relationship('FoundItem', backref='matches')
    
    def to_dict(self):
        return {
            'id': self.id,
            'lost_item_id': self.lost_item_id,
            'found_item_id': self.found_item_id,
            'similarity_score': self.similarity_score,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'lost_item': self.lost_item.to_dict() if self.lost_item else None,
            'found_item': self.found_item.to_dict() if self.found_item else None
        }

class Claim(db.Model):
    __tablename__ = 'claims'

    id = db.Column(db.Integer, primary_key=True)
    claimant_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_type = db.Column(db.String(10), nullable=False)  # 'lost' or 'found'
    target_item_id = db.Column(db.Integer, nullable=False)
    claimant_description = db.Column(db.Text, nullable=True)
    question_text = db.Column(db.Text, nullable=True)
    options_json = db.Column(db.Text, nullable=True)  # JSON array of {id, label, image_url}
    correct_option_id = db.Column(db.String(64), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, passed, failed
    attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'claimant_user_id': self.claimant_user_id,
            'target_type': self.target_type,
            'target_item_id': self.target_item_id,
            'claimant_description': self.claimant_description,
            'question_text': self.question_text,
            'options': json.loads(self.options_json) if self.options_json else [],
            'status': self.status,
            'attempts': self.attempts,
            'created_at': self.created_at.isoformat()
        }
