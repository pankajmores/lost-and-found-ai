# Lost & Found AI

An intelligent lost and found system that uses Natural Language Processing (NLP) and cosine similarity to match lost items with found items based on their descriptions.

## Features

- **AI-Powered Matching**: Uses sentence transformers to create embeddings from item descriptions and calculates similarity using cosine similarity
- **Smart Filtering**: Combines text similarity with metadata matching (category, color, location, dates)
- **User Authentication**: Secure user registration and login system
- **Email Notifications**: Automatic notifications when potential matches are found
- **Real-time Search**: Search through lost and found items with similarity scoring
- **Web Interface**: Clean, responsive web interface for easy interaction

## Technology Stack

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Sentence Transformers** - For text embeddings (`all-MiniLM-L6-v2` model)
- **Scikit-learn** - For cosine similarity calculations
- **bcrypt** - Password hashing
- **JWT** - Authentication tokens
- **SQLite** - Database (easily replaceable with PostgreSQL/MySQL)

### Frontend
- **HTML5/CSS3/JavaScript** - Clean, responsive web interface
- **Fetch API** - For REST API communication

### AI/ML Components
- **Text Embeddings**: Convert item descriptions to numerical vectors
- **Cosine Similarity**: Calculate similarity between item descriptions
- **Multi-factor Matching**: Combine text similarity with category, color, location, and date filters

## Project Structure and Responsibilities

- backend/app/app.py
  - Purpose: Main Flask application entry. Loads configuration and env vars, initializes SQLAlchemy and CORS, sets DB path, registers routes.
  - Key endpoints:
    - POST /api/register, POST /api/login
    - POST /api/lost-items, GET /api/lost-items
    - POST /api/found-items, GET /api/found-items
    - GET /api/search
    - POST /api/claims/initiate, POST /api/claims/verify
    - GET /api/uploads/<filename>
    - GET /api/health
  - Utilities: JWT generation/verification, simple SQLite "migration" to add new columns, image upload handling with validation.

- backend/models/models.py
  - Purpose: Database models (SQLAlchemy) and serialization helpers.
  - Models:
    - User: authentication and profile fields
    - LostItem: lost item details, image_url, optional embedding storage
    - FoundItem: found item details, image_url, optional embedding storage
    - Match: potential match records between lost/found items
    - Claim: image-based verification challenges for claimants
  - Each model exposes to_dict() for API responses.

- backend/services/
  - simple_matching_service.py: Default matching service used by the app; builds simple text representations via simple_nlp_service and applies metadata filters (category, color similarity, date and location checks).
  - matching_service.py: Advanced embedding-based matching (optional) via nlp_service; keeps/stores embeddings on models.
  - simple_nlp_service.py: Lightweight text representation + similarity scoring without heavy ML dependencies.
  - nlp_service.py: Advanced NLP/embedding hooks (use when adding sentence-transformers or similar libraries).
  - notification_service.py: Email notification utilities (stubs/placeholders unless configured).

- backend/instance/uploads
  - Purpose: Local storage for uploaded images. Files are served through GET /api/uploads/<filename>.

- backend/routes/
  - Placeholder for future Flask Blueprints (currently unused).

- backend/utils/
  - Placeholder for helper utilities (if/when added).

- frontend/index.html
  - Purpose: Web UI with modals for login, registration, reporting lost/found items (with image upload), and the claim challenge flow.

- frontend/app.js
  - Purpose: Client-side logic. Manages auth, sends requests, handles multipart/form-data uploads, renders search results, opens claim modals, initiates/validates claim challenges.

- database/lost_and_found.db
  - Purpose: SQLite database file (created automatically). You can replace with another RDBMS by changing SQLALCHEMY_DATABASE_URI.

- docs/
  - Purpose: Documentation and design notes (if present).

- tests/
  - Purpose: Test scaffolding and any sample scripts (if present).

- requirements.txt
  - Purpose: Python dependencies.

- .env
  - Purpose: Environment configuration (secrets, DB path, thresholds). Do not commit sensitive values.

- README.md
  - Purpose: Project documentation (you are here).

## Modules and What They’re Used For

Backend runtime dependencies (from requirements.txt):
- flask: Web framework for building the API server
- flask-sqlalchemy: ORM for modeling and DB access
- flask-cors: Cross-Origin Resource Sharing for the frontend to reach the API
- python-dotenv: Load configuration from .env files
- bcrypt: Hash and verify user passwords securely
- pyjwt: Issue and verify JWT access tokens for auth

Notes:
- The default matching path uses simple_matching_service + simple_nlp_service, which do not require heavy ML packages.
- The matching_service + nlp_service layer is designed for embedding-based matching if you later add ML dependencies (e.g., sentence-transformers, numpy, scikit-learn). These are not required by default and are not listed in requirements.txt.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd lost-and-found-ai
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up Environment Variables
Copy the `.env` file and update it with your settings:
```bash
cp .env .env.local
```

Edit `.env.local` with your configurations:
```
DATABASE_URL=sqlite:///database/lost_and_found.db
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
SIMILARITY_THRESHOLD=0.7
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

### 5. Create Database Directory
```bash
mkdir -p database
```

### 6. Initialize Database and Create Test Data
```bash
cd /Users/pankajmore/lost-and-found-ai
python tests/test_data.py
```

### 7. Start the Backend Server
```bash
cd backend
python app/app.py
```

The API server will start at `http://localhost:5001`

### 8. Serve the Frontend
Open `frontend/index.html` in a web browser, or use a simple HTTP server:

```bash
cd frontend
python -m http.server 8000
```

Then open `http://localhost:8000` in your browser.

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - User login
- `GET /api/user/profile` - Get user profile (auth required)

### Items
- `POST /api/lost-items` - Report lost item (auth required)
  - Supports `multipart/form-data` with optional `image` file field
- `POST /api/found-items` - Report found item (auth required)
  - Supports `multipart/form-data` with optional `image` file field
- `GET /api/lost-items` - Get all lost items
- `GET /api/found-items` - Get all found items
- `GET /api/search` - Search items with query

### Matching
- `GET /api/matches` - Get user's matches (auth required)
- `POST /api/matches/{id}/confirm` - Confirm match (auth required)
- `POST /api/matches/{id}/reject` - Reject match (auth required)

### Claims and Verification
- `POST /api/claims/initiate` - Start a claim for an item and receive an image-based verification challenge (auth required)
  - Body: `{ target_type: 'lost'|'found', target_item_id: number, claimant_description?: string }`
  - Response: challenge question and image options to select from
- `POST /api/claims/verify` - Submit your answer to the challenge (auth required)
  - Body: `{ claim_id: number, selected_option_id: string }`

### Uploads
- `GET /api/uploads/<filename>` - Serve uploaded images

### Utility
- `GET /api/health` - Health check

## How the AI Matching Works

1. **Text Preprocessing**: Item descriptions are cleaned and preprocessed
2. **Embedding Generation**: Using sentence transformers (`all-MiniLM-L6-v2`), convert descriptions to 384-dimensional vectors
3. **Similarity Calculation**: Use cosine similarity to compare embeddings
4. **Multi-factor Filtering**: Apply additional filters:
   - Category matching (exact)
   - Color similarity (with color groups)
   - Location proximity (using text similarity)
   - Date range validation
5. **Threshold Application**: Only matches above the similarity threshold (default: 0.7) are considered
6. **Ranking**: Results are sorted by similarity score

### Example Matching Process

**Lost Item**: "Black iPhone 13 with cracked screen, lost in Central Park"
**Found Item**: "Found iPhone with broken screen, black color, near park bench"

1. Generate embeddings for both descriptions
2. Calculate cosine similarity: 0.85 (high similarity)
3. Check category: both "electronics" ✓
4. Check color: both "black" ✓  
5. Check location similarity: "Central Park" vs "park" = 0.6 ✓
6. **Result**: Strong match (85% confidence)

## Test Data

The system comes with pre-populated test data including:

### Test Users
- john@example.com / password123
- sarah@example.com / password123
- mike@example.com / password123
- emma@example.com / password123

### Sample Items
- iPhone with blue case (lost/found pair)
- Gold wedding ring (lost/found pair)
- Black leather wallet (lost/found pair)
- Student backpack (lost/found pair)
- Car keys with Honda remote (lost/found pair)

## Email Notifications

When enabled, the system sends HTML email notifications for:
- **Match Found**: When a potential match is discovered
- **Match Confirmed**: When a user confirms a match

Configure email settings in the `.env` file. For Gmail, use an app-specific password.

## Deployment

### Production Considerations

1. **Database**: Replace SQLite with PostgreSQL or MySQL
2. **Environment Variables**: Use proper secret management
3. **HTTPS**: Enable SSL/TLS
4. **Error Handling**: Add comprehensive error logging
5. **Rate Limiting**: Add API rate limiting
6. **Caching**: Add Redis for caching embeddings
7. **File Uploads**: Image upload functionality with local storage (configurable)
8. **Mobile App**: Develop mobile applications

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "backend.app.app:app"]
```

## Image Uploads

- Default upload directory: `backend/instance/uploads`
- Max file size: 10 MB
- Allowed types: png, jpg, jpeg, gif, webp
- Configure path via `UPLOAD_FOLDER` env or Flask config

## Performance Optimization

- **Embedding Caching**: Embeddings are stored in the database to avoid recalculation
- **Batch Processing**: Use batch embedding generation for multiple items
- **Indexing**: Add database indexes on frequently queried fields
- **Vector Databases**: Consider using specialized vector databases like Pinecone or Weaviate for large-scale deployments

## Future Enhancements

1. **Image Recognition**: Add computer vision for image-based matching
2. **Geolocation**: Implement GPS-based location matching
3. **Real-time Chat**: Add messaging between users
4. **Mobile Apps**: Native iOS/Android applications
5. **Advanced NLP**: Use larger language models for better understanding
6. **Machine Learning**: Implement learning from user feedback
7. **Multi-language Support**: Add support for multiple languages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For questions or support, please create an issue in the GitHub repository.