import os
from pathlib import Path
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from the project root (one level above BASE_DIR) or current directory
load_dotenv(os.path.join(BASE_DIR.parent, '.env'))
load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-swiftbuy-key-secret-2026')
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

ALLOWED_HOSTS = ['*']
allowed_hosts_env = os.environ.get('ALLOWED_HOSTS')
if allowed_hosts_env and allowed_hosts_env != '*':
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(',') if h.strip()]

CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
csrf_env = os.environ.get('CSRF_TRUSTED_ORIGINS')
if csrf_env:
    for origin in csrf_env.split(','):
        origin = origin.strip()
        if origin and origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)

railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN')
if railway_domain:
    origin = f"https://{railway_domain}"
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- STATIC & STORAGE CONFIGURATION ---
# Use Django 4.2+ STORAGES setting
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# WhiteNoise configuration
WHITENOISE_USE_FINDERS = True  # Serve from STATICFILES_DIRS even without collectstatic
WHITENOISE_AUTOREFRESH = True  # Auto-discover files

# --------------------------------------------------------------------------



INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'model_utils',  # For model tracking
    'shop.apps.ShopConfig',  # Use AppConfig for signal registration
    'accounts'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
   
]

ROOT_URLCONF = 'ecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'shop.context_processors.cart',
                'shop.context_processors.categories',

            ],
        },
    },
]

# Database configuration for Railway PostgreSQL
database_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_PUBLIC_URL')

if database_url:
    DATABASES = {
        'default': dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
elif os.environ.get('DB_NAME') or os.environ.get('PGDATABASE'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME') or os.environ.get('PGDATABASE'),
            'USER': os.environ.get('DB_USER') or os.environ.get('PGUSER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD') or os.environ.get('PGPASSWORD', ''),
            'HOST': os.environ.get('DB_HOST') or os.environ.get('PGHOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT') or os.environ.get('PGPORT', '5432'),
            'CONN_MAX_AGE': 600,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Media files configuration (stored on Railway container/volume)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cart settings
CART_SESSION_ID = 'cart'

# Email settings
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
if (DEBUG or not os.environ.get('EMAIL_HOST_PASSWORD')) and not os.environ.get('EMAIL_BACKEND'):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'krishnananbu99@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', f'Swiftbuy <{EMAIL_HOST_USER}>')
EMAIL_TIMEOUT = 30  # Increased timeout
EMAIL_USE_SSL = False

# Additional email settings
EMAIL_USE_LOCALTIME = True
EMAIL_SUBJECT_PREFIX = '[Swiftbuy] '  # Prefix for email subjects
ADMIN_EMAIL = 'krishnananbu99@gmail.com'  # Email for admin notifications

# Email notification settings
EMAIL_NOTIFICATIONS = {
    'ORDER_STATUS_CHANGE': True,  # Send emails when order status changes
    'LOW_STOCK_ALERT': True,      # Send emails when product stock is low
    'NEW_ORDER': True,            # Send emails when new orders are placed
    'ORDER_CONFIRMATION': True,   # Send order confirmation emails
    'FAILED_PAYMENT': True,       # Send emails when payments fail
}

# Low stock threshold for notifications
LOW_STOCK_THRESHOLD = 5  # Send alert when stock falls below this number

# Site URL for email links
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')  # Change in production

# Store name and contact info for emails
STORE_NAME = 'Swiftbuy'
STORE_ADDRESS = 'Your Store Address'
STORE_PHONE = 'Your Store Phone'
STORE_SUPPORT_EMAIL = 'krishnananbu99@gmail.com'

# Ensure logs directory exists
(BASE_DIR / 'logs').mkdir(parents=True, exist_ok=True)

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'debug.log',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'shop': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'accounts': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

