from .base import *

DEBUG = config('DEBUG', cast=bool)
ALLOWED_HOSTS = ['ip-address', 'www.tncoffee-website.com']

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': ''
    }
}

# PAYPAL_PUBLIC_KEY = config('PAYPAL_LIVE_PUBLIC_KEY')
# PAYPAL_SECRET_KEY = config('PAYPAL_LIVE_SECRET_KEY')

# PAYPAL_CLIENT_ID = config('YOUR_PAYPAL_CLIENT_ID')
# PAYPAL_CLIENT_SECRET = config('YOUR_PAYPAL_CLIENT_SECRET')