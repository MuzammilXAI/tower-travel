# At the top of settings.py
from django.contrib.messages import constants as messages
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Django settings for Tower Travel Project

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# ================= BASIC SETTINGS =================
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key-for-dev')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ================= INSTALLED APPS =================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Your app
    'travel_app',
]

# ================= MIDDLEWARE =================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # ✅ Must be before AuthenticationMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # ✅ Required for admin
    'django.contrib.messages.middleware.MessageMiddleware',  # ✅ Required for admin
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ================= URLS =================
ROOT_URLCONF = 'DjangoProject.urls'

# ================= TEMPLATES =================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'travel_app', 'templates')],  # Look in app templates folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ================= WSGI =================
WSGI_APPLICATION = 'DjangoProject.wsgi.application'

# ================= DATABASE =================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # SQLite DB file
    }
}

# ================= PASSWORD VALIDATION =================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ================= INTERNATIONALIZATION =================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ================= STATIC & MEDIA FILES =================
STATIC_URL = '/static/'

# Look for static files in both app-level and project-level static folders
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'travel_app', 'static'),  # App-level static folder
    os.path.join(BASE_DIR, 'static'),  # Project-level static folder (if exists)
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # For collectstatic

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # For uploaded images

# ================= PAYMENT SETTINGS (STRIPE) =================
# Get your actual keys from environment variables
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')

# ================= EMAIL SETTINGS (CONFIGURED FOR GMAIL SMTP) =================
# Email configuration for user verification and notifications
# Using Gmail SMTP with App Password

# SMTP Configuration (Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# Your Gmail credentials (using app password)
EMAIL_HOST_USER = 'nmuzammil690@gmail.com'
EMAIL_HOST_PASSWORD = 'kichfvnpssekecuy'  # Your app password (no spaces)

# Default from email
DEFAULT_FROM_EMAIL = 'Tower Travel <noreply@towertravel.com>'

# Optional: Override with environment variables if needed
# Uncomment these lines if you want to use .env file instead
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'nmuzammil690@gmail.com')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
# DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Tower Travel <nmuzammil690@gmail.com>')

# Email verification settings
VERIFICATION_TOKEN_EXPIRY_HOURS = int(os.environ.get('VERIFICATION_TOKEN_EXPIRY_HOURS', 24))
VERIFICATION_EMAIL_SUBJECT = 'Verify Your Tower Travel Account'
VERIFICATION_EMAIL_TEMPLATE = 'emails/verification_email.html'

# ================= AUTHENTICATION SETTINGS =================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'user_login'  # Updated to user login URL
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'user_login'

# Admin login specific settings
ADMIN_LOGIN_URL = 'admin_login'  # Separate admin login URL

# User account settings
ACCOUNT_ACTIVATION_DAYS = 7  # Days until verification token expires

# ================= MESSAGE TAGS =================
MESSAGE_TAGS = {
    messages.ERROR: 'error',
    messages.SUCCESS: 'success',
    messages.INFO: 'info',
    messages.WARNING: 'warning',
}

# ================= CUSTOM USER MODEL SETTINGS =================
# Note: Using Django's default User model
# Email is required for verification but username is used for login

# ================= SECURITY SETTINGS =================
# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# CSRF settings
CSRF_COOKIE_SECURE = not DEBUG  # Only secure in production
CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000').split(',')

# Password reset settings
PASSWORD_RESET_TIMEOUT = 86400  # 24 hours in seconds
PASSWORD_RESET_EMAIL_SUBJECT = 'Reset Your Tower Travel Password'

# ================= API & CHATBOT SETTINGS =================
# For AI recommendations and chatbot
AI_API_ENABLED = DEBUG  # Enable in development, configure for production
CHATBOT_MAX_MESSAGE_LENGTH = 500
RECOMMENDATIONS_CACHE_TIMEOUT = 3600  # 1 hour

# ================= LOGGING (for debugging email issues) =================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'travel_app': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',  # This will show email sending details
        },
    },
}