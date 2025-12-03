# IMAP-Integrated ML Spam Detection API

A FastAPI-based email spam detection service that integrates with IMAP servers to automatically classify and filter spam emails using machine learning. Users can login with their email credentials, and the system monitors their inbox in real-time, moving spam to a dedicated folder while providing full email client functionality.

## Architecture

```
User → FastAPI Service → Spam ML Model
         ↓
    IMAP Client (Read emails)
         ↓
    Spam Classification
         ↓
    Move spam to folder
         ↓
    SSE Real-time notifications → Next.js UI
```

## Features

- 🔐 **JWT Authentication** - Secure user authentication with access and refresh tokens
- 📧 **Full Email Client** - Read, send, reply, and manage emails via API
- 🤖 **ML Spam Detection** - Pre-trained TF-IDF + classifier for accurate spam detection
- ⚡ **Real-time Updates** - Server-Sent Events (SSE) for instant notifications
- 🔄 **Background Processing** - Celery workers for automated email monitoring
- 🔒 **Encrypted Credentials** - Fernet encryption for secure password storage
- 📊 **PostgreSQL Database** - Robust user and session management
- 🚀 **Docker Support** - Easy deployment with Docker Compose

## Tech Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Database ORM
- **Celery** - Distributed task queue
- **Redis** - Message broker and caching
- **PostgreSQL** - Primary database
- **IMAPClient** - IMAP protocol implementation
- **aiosmtplib** - Async SMTP for sending emails
- **scikit-learn** - ML model framework
- **NLTK** - Natural language processing

## Project Structure

```
spam_detection/
├── app/
│   ├── api/               # API endpoints
│   │   ├── auth.py        # Authentication routes
│   │   ├── emails.py      # Email management routes
│   │   └── monitoring.py  # SSE monitoring endpoint
│   ├── core/              # Core functionality
│   │   ├── config.py      # Application settings
│   │   ├── security.py    # Security utilities
│   │   └── deps.py        # Dependencies
│   ├── models/            # Database models
│   │   └── user.py        # User model
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   │   ├── spam_classifier.py  # ML spam detection
│   │   ├── imap_service.py     # IMAP operations
│   │   └── smtp_service.py     # SMTP operations
│   ├── workers/           # Celery tasks
│   │   ├── __init__.py    # Celery app configuration
│   │   └── tasks.py       # Background tasks
│   ├── database.py        # Database connection
│   └── main.py            # FastAPI application
├── models/                # ML model files
│   ├── spam_classifier_model.joblib
│   └── tfidf_vectorizer.joblib
├── docker-compose.yml     # Docker services
├── Dockerfile             # Application container
├── pyproject.toml         # Python dependencies
└── .env.example           # Environment variables template
```

## Setup

### Prerequisites

- Python 3.12+
- Docker and Docker Compose (recommended)
- ML model files (spam_classifier_model.joblib, tfidf_vectorizer.joblib)

### Installation

1. **Clone the repository**

   ```bash
   cd spam_detection
   ```

2. **Place ML model files**

   ```bash
   # Copy your trained model files to the models/ directory
   # - models/spam_classifier_model.joblib
   # - models/tfidf_vectorizer.joblib
   ```

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and update:

   - `IMAP_HOST` and `IMAP_PORT` - Your IMAP server details
   - `SMTP_HOST` and `SMTP_PORT` - Your SMTP server details
   - `JWT_SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - `FERNET_KEY` - Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

### Running with Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

The API will be available at `http://localhost:8000`

### Running Locally

1. **Install dependencies**

   ```bash
   pip install -e .
   ```

2. **Start PostgreSQL and Redis**

   ```bash
   docker-compose up -d postgres redis
   ```

3. **Run database migrations** (after setting up Alembic)

   ```bash
   alembic upgrade head
   ```

4. **Start FastAPI server**

   ```bash
   uvicorn app.main:app --reload
   ```

5. **Start Celery worker** (in another terminal)

   ```bash
   celery -A app.workers worker --loglevel=info
   ```

6. **Start Celery beat** (in another terminal)
   ```bash
   celery -A app.workers beat --loglevel=info
   ```

## API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT tokens
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout and stop monitoring

#### Email Management

- `GET /emails` - List emails with pagination
- `GET /emails/{email_id}` - Get email details
- `PUT /emails/{email_id}/read` - Mark as read/unread
- `POST /emails/{email_id}/move` - Move to folder
- `DELETE /emails/{email_id}` - Delete email
- `POST /emails/send` - Send new email
- `POST /emails/{email_id}/reply` - Reply to email
- `GET /emails/folders/list` - List all folders

#### Monitoring

- `GET /monitoring/sse` - SSE endpoint for real-time updates
- `GET /monitoring/status` - Get monitoring status

## Usage Example

### 1. Register User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password",
    "imap_password": "email_password"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure_password"
  }'
```

Response:

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 3. List Emails

```bash
curl -X GET http://localhost:8000/emails?folder=INBOX&limit=10 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4. Connect to SSE for Real-time Updates

```javascript
const eventSource = new EventSource("http://localhost:8000/monitoring/sse", {
  headers: {
    Authorization: "Bearer YOUR_ACCESS_TOKEN",
  },
});

eventSource.addEventListener("email_event", (event) => {
  const data = JSON.parse(event.data);
  console.log("New email event:", data);
});
```

## How It Works

1. **User Registration**: User registers with their email and IMAP password (encrypted with Fernet)
2. **Login**: User logs in, receives JWT tokens, and monitoring starts
3. **Background Monitoring**: Celery worker checks for new emails every 2 minutes (configurable)
4. **Spam Classification**: Each new email is classified using the pre-trained ML model
5. **Auto-filtering**: Spam emails are automatically moved to the Spam folder
6. **Real-time Notifications**: SSE pushes events to connected clients
7. **Email Management**: Users can read, reply, compose, and manage emails through the API

## ML Model

The spam classifier uses:

- **TF-IDF Vectorization** - Text feature extraction
- **Preprocessing** - Lowercase, remove numbers/punctuation, lemmatization, stop word removal
- **Classification** - Pre-trained scikit-learn model

Place these files in `models/`:

- `spam_classifier_model.joblib`
- `tfidf_vectorizer.joblib`

## Configuration

Key environment variables (`.env`):

```env
# Email Servers (hardcoded for all users)
IMAP_HOST=imap.yourdomain.com
IMAP_PORT=993
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587

# Security Keys (CHANGE IN PRODUCTION!)
JWT_SECRET_KEY=your-secret-key
FERNET_KEY=your-fernet-key

# Monitoring
EMAIL_CHECK_INTERVAL_SECONDS=120  # Check every 2 minutes
```

## Security Considerations

- ✅ JWT-based authentication with token expiration
- ✅ Fernet encryption for IMAP passwords in database
- ✅ bcrypt password hashing for API authentication
- ✅ HTTPS recommended for production
- ✅ CORS configuration for trusted origins
- ⚠️ Generate strong secret keys in production
- ⚠️ Use environment variables for sensitive data
- ⚠️ Implement rate limiting for production

## Development

### Adding New Features

1. Create new route in `app/api/`
2. Add Pydantic schemas in `app/schemas/`
3. Implement business logic in `app/services/`
4. Update router includes in `app/main.py`

### Running Tests

```bash
pytest
```

## Production Deployment

1. **Generate secure keys**:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **Update `.env`** with production values

3. **Set up reverse proxy** (nginx, Caddy, etc.)

4. **Enable HTTPS**

5. **Deploy with Docker Compose** or Kubernetes

6. **Monitor with logging and metrics**

## Troubleshooting

### Model files not found

- Ensure `spam_classifier_model.joblib` and `tfidf_vectorizer.joblib` are in `models/` directory

### IMAP connection failed

- Verify `IMAP_HOST` and `IMAP_PORT` in `.env`
- Check if your email provider requires app-specific passwords (Gmail, Outlook)

### Celery worker not processing tasks

- Ensure Redis is running: `docker-compose ps redis`
- Check worker logs: `docker-compose logs celery_worker`

### SSE connection issues

- Verify Redis pub/sub is working
- Check CORS configuration in `.env`

## Next.js Integration

Connect your Next.js frontend:

```typescript
// Connect to SSE
const eventSource = new EventSource(`http://localhost:8000/monitoring/sse`, {
  headers: { Authorization: `Bearer ${accessToken}` },
});

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle new email or spam detection
};
```

## License

MIT

## GROUP MEMBERS

---

| Name         | ID           |
| ------------ | ------------ |
| Nahom Dereje | UGR/26395/14 |
| Nebil Rahmeto | UGR/25275/14 |
| Muluken Ageri | UGR/25993/14 |

---

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
