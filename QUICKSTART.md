# Quick Start Commands

## Setup

### 1. Generate Security Keys
```bash
python scripts/setup.py
```

### 2. Create Environment File
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Place ML Models
Download from Google Colab and place in `models/`:
- `spam_classifier_model.joblib`
- `tfidf_vectorizer.joblib`

## Running with Docker

### Start all services
```bash
docker-compose up -d
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

### Stop services
```bash
docker-compose down
```

### Rebuild after code changes
```bash
docker-compose up -d --build
```

## Running Locally

### Install dependencies
```bash
pip install -e .
```

### Start infrastructure
```bash
docker-compose up -d postgres redis
```

### Run API server
```bash
uvicorn app.main:app --reload --port 8000
```

### Run Celery worker (separate terminal)
```bash
celery -A app.workers worker --loglevel=info
```

### Run Celery beat (separate terminal)
```bash
celery -A app.workers beat --loglevel=info
```

## Testing

### Test API endpoints
```bash
# Health check
curl http://localhost:8000/health

# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","imap_password":"email_pass"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### Access API documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Database

### Access PostgreSQL
```bash
docker-compose exec postgres psql -U spam_user -d spam_detection
```

### Run migrations (after setting up Alembic)
```bash
alembic upgrade head
```

### Create new migration
```bash
alembic revision --autogenerate -m "description"
```

## Redis

### Access Redis CLI
```bash
docker-compose exec redis redis-cli
```

### Monitor Redis events
```bash
docker-compose exec redis redis-cli MONITOR
```

## Troubleshooting

### View container status
```bash
docker-compose ps
```

### Restart specific service
```bash
docker-compose restart api
docker-compose restart celery_worker
```

### Clear database and start fresh
```bash
docker-compose down -v
docker-compose up -d
```

### Check Celery tasks
```bash
# In Python shell
from app.workers.tasks import monitor_user_emails
monitor_user_emails.delay(1)  # Test task for user_id=1
```

## Production Deployment

### Build for production
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Generate secure keys
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Update environment
- Set `DEBUG=False`
- Use strong `JWT_SECRET_KEY`
- Use strong `FERNET_KEY`
- Configure proper `CORS_ORIGINS`
- Use HTTPS in production
