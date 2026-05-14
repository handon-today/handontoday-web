"""
한돈투데이 Django 설정 (config/settings.py)

[환경별 동작]
- 로컬 개발: .env의 DB_PASSWORD를 직접 사용 (Cloud SQL Python Connector)
- Cloud Run: 환경변수 + Cloud SQL Unix socket 자동 감지
"""

import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# ──────────────────────────────────────────────
# Security
# ──────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-only-change-me')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS', default='localhost,127.0.0.1'
).split(',')

# Cloud Run은 자체 도메인 + 매핑된 도메인 자동 허용 필요

# ──────────────────────────────────────────────
# Applications
# ──────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 외부
    'widget_tweaks',
    
    # 우리 앱
    'articles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 정적 파일 (Cloud Run)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # 프로젝트 공통 템플릿
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

WSGI_APPLICATION = 'config.wsgi.application'

# ──────────────────────────────────────────────
# Database (Cloud SQL Python Connector)
# ──────────────────────────────────────────────
DB_USER = config('DB_USER', default='postgres')
DB_PASSWORD = config('DB_PASSWORD', default='')
DB_NAME = config('DB_NAME', default='handontoday_db')
CLOUD_SQL_CONNECTION_NAME = config(
    'CLOUD_SQL_CONNECTION_NAME',
    default='handontoday:asia-northeast3:handontoday-db'
)

# Cloud Run 환경 감지: /cloudsql/<instance> 소켓이 있으면 production 모드
CLOUD_SQL_SOCKET = f'/cloudsql/{CLOUD_SQL_CONNECTION_NAME}'
IS_CLOUD_RUN = os.path.exists(CLOUD_SQL_SOCKET)

if IS_CLOUD_RUN:
    # Cloud Run: Unix socket 경유
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': CLOUD_SQL_SOCKET,
            'PORT': '5432',
        }
    }
else:
    # 로컬 (Cloud Shell): Cloud SQL Python Connector 사용
    # connections.py에서 동적 연결 처리
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }
    # 로컬 개발 시: cloud-sql-proxy를 백그라운드로 실행하거나
    # 별도 셸에서 띄워둬야 함 (안내는 README에)

# ──────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ──────────────────────────────────────────────
# Localization
# ──────────────────────────────────────────────
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────────────
# Static / Media
# ──────────────────────────────────────────────
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # collectstatic 결과
STATICFILES_DIRS = [BASE_DIR / 'static']  # 개발 시 소스
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# ──────────────────────────────────────────────
# Default
# ──────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 로그인/로그아웃 리다이렉트
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# CSRF 설정 (Cloud Shell 동적 URL)

# 로그인/로그아웃 리다이렉트

# CSRF 설정 (Cloud Shell 동적 URL)
CSRF_TRUSTED_ORIGINS = [
    "https://*.cloudshell.dev",  # 모든 Cloud Shell URL 허용
]
