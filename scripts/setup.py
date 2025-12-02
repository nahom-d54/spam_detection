"""Setup script to verify environment and generate security keys."""
import os
import secrets
from cryptography.fernet import Fernet


def generate_keys():
    """Generate security keys for the application."""
    print("🔐 Generating Security Keys\n")
    
    # Generate JWT secret
    jwt_secret = secrets.token_urlsafe(32)
    print(f"JWT_SECRET_KEY={jwt_secret}")
    
    # Generate Fernet key
    fernet_key = Fernet.generate_key().decode()
    print(f"FERNET_KEY={fernet_key}")
    
    print("\n⚠️  Copy these keys to your .env file!")
    print("   Never commit these keys to version control!")


def check_models():
    """Check if ML model files exist."""
    print("\n📊 Checking ML Models\n")
    
    model_path = "models/spam_classifier_model.joblib"
    vectorizer_path = "models/tfidf_vectorizer.joblib"
    
    if os.path.exists(model_path):
        print(f"✓ Found: {model_path}")
    else:
        print(f"✗ Missing: {model_path}")
        print("  Download from your Google Drive and place in models/")
    
    if os.path.exists(vectorizer_path):
        print(f"✓ Found: {vectorizer_path}")
    else:
        print(f"✗ Missing: {vectorizer_path}")
        print("  Download from your Google Drive and place in models/")


def check_env_file():
    """Check if .env file exists."""
    print("\n⚙️  Checking Environment Configuration\n")
    
    if os.path.exists(".env"):
        print("✓ Found: .env file")
        print("  Make sure to update IMAP_HOST, SMTP_HOST, and security keys")
    else:
        print("✗ Missing: .env file")
        print("  Copy .env.example to .env and configure it")
        print("  $ cp .env.example .env")


def main():
    """Run setup checks."""
    print("=" * 60)
    print("Spam Detection API - Setup Verification")
    print("=" * 60)
    
    generate_keys()
    check_models()
    check_env_file()
    
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. Copy generated keys to .env file")
    print("2. Download ML models to models/ directory")
    print("3. Update IMAP_HOST and SMTP_HOST in .env")
    print("4. Run: docker-compose up -d")
    print("5. Visit: http://localhost:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    main()
