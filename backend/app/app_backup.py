from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, date
import os
from dotenv import load_dotenv
import bcrypt
import jwt
from functools import wraps

# Load environment variables
load_dotenv()

# Add parent directories to Python path
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Import models and services
from models.models import db, User, LostItem, FoundItem, Match
from services.simple_matching_service import simple_matching_service as matching_service
from services.simple_nlp_service import simple_nlp_service as nlp_service
from services.notification_service import notification_service

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database/lost_and_found.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
CORS(app)

# JWT utility functions
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Authentication decorator
def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Add user_id to request context
        request.current_user_id = user_id
        return f(*args, **kwargs)
    
    return decorated

# Routes

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User already exists'}), 400
    
    # Hash password
    password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create user
    user = User(
        name=data['name'],
        email=data['email'],
        phone=data.get('phone'),
        password_hash=password_hash
    )
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = generate_token(user.id)
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user.to_dict()
    })

@app.route('/api/lost-items', methods=['POST'])
@require_auth
def create_lost_item():
    """Create a new lost item"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'description', 'category', 'lost_location', 'lost_date']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        # Parse date
        lost_date = datetime.strptime(data['lost_date'], '%Y-%m-%d').date()
        
        # Create lost item
        lost_item = LostItem(
            user_id=request.current_user_id,
            title=data['title'],
            description=data['description'],
            category=data['category'],
            color=data.get('color'),
            brand=data.get('brand'),
            lost_location=data['lost_location'],
            lost_date=lost_date,
            reward_amount=data.get('reward_amount', 0.0)
        )
        
        db.session.add(lost_item)
        db.session.commit()
        
        # Find potential matches
        matches = matching_service.create_matches_for_item(lost_item, is_lost_item=True)
        
        # Send notifications for matches
        for match in matches:
            notification_service.send_match_notification(match)
        
        return jsonify({
            'message': 'Lost item created successfully',
            'item': lost_item.to_dict(),
            'potential_matches': len(matches)
        }), 201
    
    except ValueError as e:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create lost item'}), 500

@app.route('/api/found-items', methods=['POST'])
@require_auth
def create_found_item():
    """Create a new found item"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'description', 'category', 'found_location', 'found_date', 'condition']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        # Parse date
        found_date = datetime.strptime(data['found_date'], '%Y-%m-%d').date()
        
        # Create found item
        found_item = FoundItem(
            user_id=request.current_user_id,
            title=data['title'],
            description=data['description'],
            category=data['category'],
            color=data.get('color'),
            brand=data.get('brand'),
            found_location=data['found_location'],
            found_date=found_date,
            condition=data['condition']
        )
        
        db.session.add(found_item)
        db.session.commit()
        
        # Find potential matches
        matches = matching_service.create_matches_for_item(found_item, is_lost_item=False)
        
        # Send notifications for matches
        for match in matches:
            notification_service.send_match_notification(match)
        
        return jsonify({
            'message': 'Found item created successfully',
            'item': found_item.to_dict(),
            'potential_matches': len(matches)
        }), 201
    
    except ValueError as e:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create found item'}), 500

@app.route('/api/lost-items', methods=['GET'])
def get_lost_items():
    \"\"\"Get all active lost items\"\"\"
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    lost_items = LostItem.query.filter_by(status='active').paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'items': [item.to_dict() for item in lost_items.items],
        'total': lost_items.total,
        'page': page,
        'per_page': per_page
    })

@app.route('/api/found-items', methods=['GET'])
def get_found_items():
    \"\"\"Get all available found items\"\"\"
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    found_items = FoundItem.query.filter_by(status='available').paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'items': [item.to_dict() for item in found_items.items],
        'total': found_items.total,
        'page': page,
        'per_page': per_page
    })

@app.route('/api/search', methods=['GET'])
def search_items():
    \"\"\"Search for items\"\"\"
    query = request.args.get('query', '')
    item_type = request.args.get('type', 'both')  # lost, found, both
    category = request.args.get('category')
    color = request.args.get('color')
    location = request.args.get('location')
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    try:
        results = matching_service.search_items(
            query=query,
            item_type=item_type,
            category=category,
            color=color,
            location=location,
            limit=limit
        )
        
        return jsonify({
            'results': results,
            'total': len(results)
        })
    
    except Exception as e:
        return jsonify({'error': 'Search failed'}), 500

@app.route('/api/matches', methods=['GET'])
@require_auth
def get_user_matches():
    \"\"\"Get matches for the current user\"\"\"
    try:
        matches = matching_service.get_user_matches(request.current_user_id)
        
        return jsonify({
            'matches': matches,
            'total': len(matches)
        })
    
    except Exception as e:
        return jsonify({'error': 'Failed to fetch matches'}), 500

@app.route('/api/matches/<int:match_id>/confirm', methods=['POST'])
@require_auth
def confirm_match(match_id):
    \"\"\"Confirm a match\"\"\"
    match = Match.query.get_or_404(match_id)
    
    # Check if user owns either the lost or found item
    if (match.lost_item.user_id != request.current_user_id and 
        match.found_item.user_id != request.current_user_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        match.status = 'confirmed'
        match.lost_item.status = 'matched'
        match.found_item.status = 'matched'
        
        db.session.commit()
        
        # Send confirmation notification
        current_user = User.query.get(request.current_user_id)
        notification_service.send_match_confirmation_notification(match, current_user)
        
        return jsonify({
            'message': 'Match confirmed successfully',
            'match': match.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to confirm match'}), 500

@app.route('/api/matches/<int:match_id>/reject', methods=['POST'])
@require_auth
def reject_match(match_id):
    \"\"\"Reject a match\"\"\"
    match = Match.query.get_or_404(match_id)
    
    # Check if user owns either the lost or found item
    if (match.lost_item.user_id != request.current_user_id and 
        match.found_item.user_id != request.current_user_id):
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        match.status = 'rejected'
        db.session.commit()
        
        return jsonify({
            'message': 'Match rejected successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to reject match'}), 500

@app.route('/api/user/profile', methods=['GET'])
@require_auth
def get_user_profile():
    \"\"\"Get current user's profile\"\"\"
    user = User.query.get_or_404(request.current_user_id)
    return jsonify({'user': user.to_dict()})

@app.route('/api/user/items', methods=['GET'])
@require_auth
def get_user_items():
    \"\"\"Get current user's lost and found items\"\"\"
    user = User.query.get_or_404(request.current_user_id)
    
    lost_items = [item.to_dict() for item in user.lost_items]
    found_items = [item.to_dict() for item in user.found_items]
    
    return jsonify({
        'lost_items': lost_items,
        'found_items': found_items
    })

# Initialize database
@app.before_first_request
def create_tables():
    db.create_all()

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)