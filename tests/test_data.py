#!/usr/bin/env python3
"""
Test data script to populate the Lost and Found AI database with sample data
"""

import sys
import os
from datetime import datetime, date, timedelta
import bcrypt

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.app import app
from models.models import db, User, LostItem, FoundItem
from services.simple_matching_service import simple_matching_service as matching_service

def create_test_users():
    """Create test users"""
    users_data = [
        {
            'name': 'John Smith',
            'email': 'john@example.com',
            'password': 'password123',
            'phone': '555-0101'
        },
        {
            'name': 'Sarah Johnson',
            'email': 'sarah@example.com',
            'password': 'password123',
            'phone': '555-0102'
        },
        {
            'name': 'Mike Davis',
            'email': 'mike@example.com',
            'password': 'password123',
            'phone': '555-0103'
        },
        {
            'name': 'Emma Wilson',
            'email': 'emma@example.com',
            'password': 'password123',
            'phone': '555-0104'
        }
    ]
    
    users = []
    for user_data in users_data:
        # Check if user already exists
        existing_user = User.query.filter_by(email=user_data['email']).first()
        if existing_user:
            users.append(existing_user)
            continue
        
        # Hash password
        password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user = User(
            name=user_data['name'],
            email=user_data['email'],
            phone=user_data['phone'],
            password_hash=password_hash
        )
        
        db.session.add(user)
        users.append(user)
    
    db.session.commit()
    print(f"Created {len(users)} test users")
    return users

def create_test_lost_items(users):
    """Create test lost items"""
    lost_items_data = [
        {
            'title': 'iPhone 13 Pro Max',
            'description': 'Black iPhone 13 Pro Max with a blue silicone case. Has a small scratch on the back. Contains important photos and contacts.',
            'category': 'electronics',
            'color': 'black',
            'brand': 'Apple',
            'lost_location': 'Central Park, near the Bethesda Fountain',
            'lost_date': date.today() - timedelta(days=3),
            'reward_amount': 200.0
        },
        {
            'title': 'Gold Wedding Ring',
            'description': 'Gold wedding band with engraved inscription "Forever Yours - M&S 2018". Very sentimental value.',
            'category': 'jewelry',
            'color': 'gold',
            'brand': None,
            'lost_location': 'Times Square subway station',
            'lost_date': date.today() - timedelta(days=7),
            'reward_amount': 500.0
        },
        {
            'title': 'Black Leather Wallet',
            'description': 'Black leather bifold wallet containing driver\'s license, credit cards, and about $80 cash. Has initials J.S. embossed.',
            'category': 'other',
            'color': 'black',
            'brand': 'Coach',
            'lost_location': 'Brooklyn Bridge pedestrian walkway',
            'lost_date': date.today() - timedelta(days=1),
            'reward_amount': 100.0
        },
        {
            'title': 'Blue Backpack',
            'description': 'Navy blue Jansport backpack with laptop compartment. Contains MacBook Pro, textbooks, and notebooks. Student ID inside.',
            'category': 'bag',
            'color': 'blue',
            'brand': 'Jansport',
            'lost_location': 'Columbia University campus library',
            'lost_date': date.today() - timedelta(days=2),
            'reward_amount': 50.0
        },
        {
            'title': 'Car Keys with Remote',
            'description': 'Honda car keys with black key fob and a small flashlight keychain. Has house keys attached.',
            'category': 'keys',
            'color': 'black',
            'brand': 'Honda',
            'lost_location': 'Washington Square Park',
            'lost_date': date.today() - timedelta(days=5),
            'reward_amount': 75.0
        }
    ]
    
    lost_items = []
    for i, item_data in enumerate(lost_items_data):
        user = users[i % len(users)]  # Cycle through users
        
        lost_item = LostItem(
            user_id=user.id,
            title=item_data['title'],
            description=item_data['description'],
            category=item_data['category'],
            color=item_data['color'],
            brand=item_data['brand'],
            lost_location=item_data['lost_location'],
            lost_date=item_data['lost_date'],
            reward_amount=item_data['reward_amount']
        )
        
        db.session.add(lost_item)
        lost_items.append(lost_item)
    
    db.session.commit()
    print(f"Created {len(lost_items)} test lost items")
    return lost_items

def create_test_found_items(users):
    """Create test found items"""
    found_items_data = [
        {
            'title': 'iPhone with Blue Case',
            'description': 'Found an iPhone with a blue protective case. Screen is cracked but phone seems to work. Found it on a bench.',
            'category': 'electronics',
            'color': 'blue',
            'brand': 'Apple',
            'found_location': 'Central Park, near Sheep Meadow',
            'found_date': date.today() - timedelta(days=2),
            'condition': 'fair'
        },
        {
            'title': 'Wedding Ring',
            'description': 'Found a gold wedding band with some text engraved inside. Looks like initials and a date. Found near subway entrance.',
            'category': 'jewelry',
            'color': 'gold',
            'brand': None,
            'found_location': 'Times Square, near subway entrance',
            'found_date': date.today() - timedelta(days=6),
            'condition': 'excellent'
        },
        {
            'title': 'Leather Wallet',
            'description': 'Found a black leather wallet with some cards and cash. Has embossed initials on the front. Looks expensive.',
            'category': 'other',
            'color': 'black',
            'brand': None,
            'found_location': 'Brooklyn Bridge, on walkway',
            'found_date': date.today(),
            'condition': 'good'
        },
        {
            'title': 'Student Backpack',
            'description': 'Navy blue backpack found in library. Contains laptop, books, and school supplies. Has student materials inside.',
            'category': 'bag',
            'color': 'navy',
            'brand': None,
            'found_location': 'Columbia University library, 3rd floor',
            'found_date': date.today() - timedelta(days=1),
            'condition': 'good'
        },
        {
            'title': 'Honda Keys',
            'description': 'Set of car keys with Honda remote and several other keys. Has a small flashlight attached.',
            'category': 'keys',
            'color': 'black',
            'brand': 'Honda',
            'found_location': 'Washington Square Park, near fountain',
            'found_date': date.today() - timedelta(days=4),
            'condition': 'excellent'
        },
        {
            'title': 'Red Scarf',
            'description': 'Woolen red scarf, very soft and warm. Looks hand-knitted. Found wrapped around a park bench.',
            'category': 'clothing',
            'color': 'red',
            'brand': None,
            'found_location': 'Madison Square Park',
            'found_date': date.today() - timedelta(days=8),
            'condition': 'excellent'
        }
    ]
    
    found_items = []
    for i, item_data in enumerate(found_items_data):
        user = users[(i + 1) % len(users)]  # Different users than lost items
        
        found_item = FoundItem(
            user_id=user.id,
            title=item_data['title'],
            description=item_data['description'],
            category=item_data['category'],
            color=item_data['color'],
            brand=item_data['brand'],
            found_location=item_data['found_location'],
            found_date=item_data['found_date'],
            condition=item_data['condition']
        )
        
        db.session.add(found_item)
        found_items.append(found_item)
    
    db.session.commit()
    print(f"Created {len(found_items)} test found items")
    return found_items

def generate_test_matches(lost_items, found_items):
    """Generate matches between lost and found items"""
    print("Generating matches...")
    
    matches_count = 0
    for lost_item in lost_items:
        try:
            matches = matching_service.create_matches_for_item(lost_item, is_lost_item=True)
            matches_count += len(matches)
            print(f"  Found {len(matches)} matches for lost item: {lost_item.title}")
        except Exception as e:
            print(f"  Error generating matches for {lost_item.title}: {e}")
    
    print(f"Generated {matches_count} total matches")

def main():
    """Main function to create all test data"""
    with app.app_context():
        # Create tables
        print("Creating database tables...")
        db.create_all()
        
        # Create test data
        print("Creating test users...")
        users = create_test_users()
        
        print("Creating test lost items...")
        lost_items = create_test_lost_items(users)
        
        print("Creating test found items...")
        found_items = create_test_found_items(users)
        
        print("Generating test matches...")
        generate_test_matches(lost_items, found_items)
        
        print("\\nTest data creation completed!")
        print(f"Created {len(users)} users, {len(lost_items)} lost items, {len(found_items)} found items")
        print("\\nTest user credentials:")
        for user in users:
            print(f"  Email: {user.email}, Password: password123")

if __name__ == '__main__':
    main()