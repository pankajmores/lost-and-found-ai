from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, date
import os
import uuid
import random
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import bcrypt
import jwt
from functools import wraps

# Load environment variables
load_dotenv()

# Add parent directories to Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Import models and services
from models.models import db, User, LostItem, FoundItem, Match, Claim
from services.simple_matching_service import simple_matching_service as matching_service

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
# Use absolute path for database
db_path = '/Users/pankajmore/Desktop/lost-and-found-ai/database/lost_and_found.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# File uploads configuration
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), '../instance/uploads'))
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
# Ensure upload folder exists
os.makedirs(os.path.abspath(app.config['UPLOAD_FOLDER']), exist_ok=True)

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

def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def _save_image(file_storage) -> str:
    if not file_storage or file_storage.filename == '':
        return None
    if not _allowed_file(file_storage.filename):
        return None
    filename = secure_filename(file_storage.filename)
    # Ensure unique filename
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    abs_upload_dir = os.path.abspath(app.config['UPLOAD_FOLDER'])
    file_path = os.path.join(abs_upload_dir, unique_name)
    file_storage.save(file_path)
    # Return a URL path to access the uploaded file
    return f"/api/uploads/{unique_name}"

# Simple SQLite migration helpers
import sqlite3

def _ensure_column(table: str, column: str, col_type: str):
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute(f"PRAGMA table_info({table})")
            cols = [row[1] for row in cur.fetchall()]
            if column not in cols:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                conn.commit()
    except Exception as e:
        print(f"Migration check/add column failed for {table}.{column}: {e}")

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
    """Create a new lost item (supports JSON or multipart/form-data with optional image)"""
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        form = request.form
        files = request.files
        data = {k: form.get(k) for k in form.keys()}
        image_file = files.get('image')
    else:
        data = request.get_json() or {}
        image_file = None
    
    # Validate required fields
    required_fields = ['title', 'description', 'category', 'lost_location', 'lost_date']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        # Parse date
        lost_date = datetime.strptime(data['lost_date'], '%Y-%m-%d').date()
        
        # Save image if provided
        image_url = None
        if image_file:
            saved = _save_image(image_file)
            if not saved:
                return jsonify({'error': 'Invalid image file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
            image_url = saved
        
        # Create lost item
        lost_item = LostItem(
            user_id=request.current_user_id,
            title=data['title'],
            description=data['description'],
            category=data['category'],
            color=data.get('color'),
            brand=data.get('brand'),
            image_url=image_url,
            lost_location=data['lost_location'],
            lost_date=lost_date,
            reward_amount=float(data.get('reward_amount', 0.0) or 0.0)
        )
        
        db.session.add(lost_item)
        db.session.commit()
        
        # Find potential matches
        matches = matching_service.create_matches_for_item(lost_item, is_lost_item=True)
        
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
    """Create a new found item (supports JSON or multipart/form-data with optional image)"""
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        form = request.form
        files = request.files
        data = {k: form.get(k) for k in form.keys()}
        image_file = files.get('image')
    else:
        data = request.get_json() or {}
        image_file = None
    
    # Validate required fields
    required_fields = ['title', 'description', 'category', 'found_location', 'found_date', 'condition']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        # Parse date
        found_date = datetime.strptime(data['found_date'], '%Y-%m-%d').date()
        
        # Save image if provided
        image_url = None
        if image_file:
            saved = _save_image(image_file)
            if not saved:
                return jsonify({'error': 'Invalid image file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
            image_url = saved
        
        # Create found item
        found_item = FoundItem(
            user_id=request.current_user_id,
            title=data['title'],
            description=data['description'],
            category=data['category'],
            color=data.get('color'),
            brand=data.get('brand'),
            image_url=image_url,
            found_location=data['found_location'],
            found_date=found_date,
            condition=data['condition']
        )
        
        db.session.add(found_item)
        db.session.commit()
        
        # Find potential matches
        matches = matching_service.create_matches_for_item(found_item, is_lost_item=False)
        
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

@app.route('/api/search', methods=['GET'])
def search_items():
    """Search for items"""
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

@app.route('/api/lost-items', methods=['GET'])
def get_lost_items():
    """Get all active lost items"""
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

@app.route('/api/claims/initiate', methods=['POST'])
@require_auth
def initiate_claim():
    """Initiate a claim with an image-based challenge."""
    data = request.get_json() or {}
    target_type = data.get('target_type')  # 'lost' or 'found'
    target_item_id = data.get('target_item_id')
    claimant_description = data.get('claimant_description')

    if target_type not in ['lost', 'found'] or not target_item_id:
        return jsonify({'error': 'target_type (lost|found) and target_item_id are required'}), 400

    # Fetch target item
    if target_type == 'lost':
        target_item = LostItem.query.get(target_item_id)
    else:
        target_item = FoundItem.query.get(target_item_id)

    if not target_item:
        return jsonify({'error': 'Target item not found'}), 404

    if not target_item.image_url:
        return jsonify({'error': 'No image available for the target item to generate a challenge'}), 400

    # Build options: include the correct image and distractors from same category
    options = []
    correct_id = uuid.uuid4().hex
    options.append({'id': correct_id, 'label': 'Option A', 'image_url': target_item.image_url})

    # Collect distractor pool
    distractor_pool = []
    if target_type == 'lost':
        distractor_pool = FoundItem.query.filter(FoundItem.image_url.isnot(None), FoundItem.id != target_item_id, FoundItem.category == target_item.category).all()
    else:
        distractor_pool = LostItem.query.filter(LostItem.image_url.isnot(None), LostItem.id != target_item_id, LostItem.category == target_item.category).all()

    # Fallback to any items with images if not enough
    if len(distractor_pool) < 3:
        extra_lost = LostItem.query.filter(LostItem.image_url.isnot(None), LostItem.id != target_item_id).all()
        extra_found = FoundItem.query.filter(FoundItem.image_url.isnot(None), FoundItem.id != target_item_id).all()
        distractor_pool = list({*distractor_pool, *extra_lost, *extra_found})

    random.shuffle(distractor_pool)
    distractor_pool = distractor_pool[:3]

    labels = ['Option B', 'Option C', 'Option D']
    for i, item in enumerate(distractor_pool):
        options.append({'id': uuid.uuid4().hex, 'label': labels[i], 'image_url': item.image_url})

    # Shuffle options so correct is not always first
    random.shuffle(options)

    question_text = "Based on your description, select the image that best matches your item."

    claim = Claim(
        claimant_user_id=request.current_user_id,
        target_type=target_type,
        target_item_id=target_item_id,
        claimant_description=claimant_description,
        question_text=question_text,
        options_json=json.dumps(options),
        # Store correct option id by finding the option with target image
    )
    # Determine correct option id after shuffle
    for opt in options:
        if opt['image_url'] == target_item.image_url:
            claim.correct_option_id = opt['id']
            break

    try:
        db.session.add(claim)
        db.session.commit()
        return jsonify({'message': 'Claim initiated', 'claim': claim.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to initiate claim'}), 500


@app.route('/api/claims/verify', methods=['POST'])
@require_auth
def verify_claim():
    data = request.get_json() or {}
    claim_id = data.get('claim_id')
    selected_option_id = data.get('selected_option_id')

    if not claim_id or not selected_option_id:
        return jsonify({'error': 'claim_id and selected_option_id are required'}), 400

    claim = Claim.query.get(claim_id)
    if not claim:
        return jsonify({'error': 'Claim not found'}), 404

    if claim.claimant_user_id != request.current_user_id:
        return jsonify({'error': 'Not authorized to verify this claim'}), 403

    claim.attempts += 1
    if selected_option_id == claim.correct_option_id:
        claim.status = 'passed'
        result = 'correct'
    else:
        claim.status = 'failed'
        result = 'incorrect'

    try:
        db.session.commit()
        return jsonify({'message': 'Verification recorded', 'result': result, 'claim': claim.to_dict()}), 200
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Failed to verify claim'}), 500
    """Get all available found items"""
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

@app.route('/api/uploads/<path:filename>', methods=['GET'])
def get_uploaded_file(filename):
    uploads_dir = os.path.abspath(app.config['UPLOAD_FOLDER'])
    return send_from_directory(uploads_dir, filename)

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

# Initialize database tables
def init_db():
    with app.app_context():
        try:
            print(f"Current working directory: {os.getcwd()}")
            print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            print(f"Database path exists: {os.path.exists(db_path)}")
            print(f"Database directory exists: {os.path.exists(os.path.dirname(db_path))}")
            print(f"Database directory permissions: {oct(os.stat(os.path.dirname(db_path)).st_mode)}")
            db.create_all()
            # Lightweight migrations for new columns
            _ensure_column('lost_items', 'image_url', 'VARCHAR(255)')
            _ensure_column('found_items', 'image_url', 'VARCHAR(255)')
            print("Database tables created/migrated successfully!")
        except Exception as e:
            print(f"Database initialization error: {e}")

if __name__ == '__main__':
    # Initialize database on startup
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)