import os
from pathlib import Path

# ========================================================
# BASE
# ========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-scholar-ai-v20-master-key'

DEBUG = True

ALLOWED_HOSTS = ['*']

# ========================================================
# APPLICATIONS
# ========================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',

    # Local
    'scholarships_app',
]

# ========================================================
# MIDDLEWARE
# ========================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',       # ← SAXID: link jirin
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ========================================================
# URLS & WSGI
# ========================================================
ROOT_URLCONF = 'scholarships.urls'
WSGI_APPLICATION = 'scholarships.wsgi.application'

# ========================================================
# TEMPLATES
# ========================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# ========================================================
# DATABASE
# ========================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ========================================================
# PASSWORD VALIDATION
# ========================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ========================================================
# LANGUAGE & TIME
# ========================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Mogadishu'
USE_I18N = True
USE_TZ = True

# ========================================================
# STATIC & MEDIA
# ========================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ========================================================
# AUTHENTICATION FLOW
# ========================================================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'home'

# ========================================================
# REST FRAMEWORK - API OPEN (JWT temporarily disabled)
# ========================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        # JWT - mustaqbalka dib u shid:
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Hadda furan - tijaabada
        # Mustaqbalka:
        # 'rest_framework.permissions.IsAuthenticated',
    ],
}

# ========================================================
# EMAIL
# ========================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'                    # ← SAXID: link jirin
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'scholarai@gmail.com'          # ← SAXID: link jirin
EMAIL_HOST_PASSWORD = 'your-app-password'

# ========================================================
# STRIPE PAYMENTS
# ========================================================
STRIPE_PUBLIC_KEY = 'pk_test_...'
STRIPE_SECRET_KEY = 'sk_test_...'
