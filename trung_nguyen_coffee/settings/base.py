import os
from decouple import config

BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

SECRET_KEY = config('SECRET_KEY')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',
    'crispy_bootstrap4',
    'django_countries',
    'integration',
    'paypal.standard.ipn',
    'paypalrestsdk',
    'rest_framework',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'trung_nguyen_coffee.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'trung_nguyen_coffee.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static_in_env')]
STATIC_ROOT = os.path.join(BASE_DIR, 'static_root')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media_root')

# Auth

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend'
)
SITE_ID = 1
LOGIN_REDIRECT_URL = '/'

# CRISPY FORMS

CRISPY_TEMPLATE_PACK = 'bootstrap4'

# settings.py

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'  # e.g., smtp.gmail.com for Gmail
EMAIL_PORT = 25  # Current Local SMTP is listening on port 25 (default)
EMAIL_USE_TLS = False  # or EMAIL_USE_SSL = True
EMAIL_HOST_PASSWORD = ''
EMAIL_HOST_USER = ''  # Leave empty if no authentication is required
EMAIL_HOST_PASSWORD = ''  # Leave empty if no authentication is required
DEFAULT_FROM_EMAIL = 'admin@localhost'  # Default sender email

PAYPAL_TEST = True
PAYPAL_RECEIVER_EMAIL = "sb-4aqtc34262578@business.example.com"         # where cash is paid into   

# PAYPAL_PUBLIC_KEY = config('PAYPAL_TEST_PUBLIC_KEY')
# PAYPAL_SECRET_KEY = config('PAYPAL_TEST_SECRET_KEY')

PAYPAL_CLIENT_ID = 'ARiIB8YoMtuIDxMHE9Khyf-tGskCTx3ZFUX1HcZt0OMfvosArfP8UGeTYWQg825Bc-dlqVI6raRqoaWE'
PAYPAL_CLIENT_SECRET = 'EJvWX4jstlLNwwde1ixX8lHjL7dxESuVwlNvnoiZAKhKeBufcDH5GJ-8nQ7ddCyYlvhPNajTZPy45lB5'
PAYPAL_MODE = 'sandbox'

PAYPAL_BASE_URL= 'https://api-m.sandbox.paypal.com' #if in production use https://api.paypal.com 