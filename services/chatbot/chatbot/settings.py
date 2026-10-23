"""Configuración del microservicio Chatbot IA. Todo secreto viene del entorno."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-only-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [
    h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h
]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "chatbot_api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "chatbot.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "chatbot.wsgi.application"

# Este servicio persiste en MongoDB (ver chatbot/mongo.py); Django no usa base SQL.
DATABASES = {}

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "chatbot")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# JWT: el servicio auth firma; los demás solo validan con el mismo secreto (HS256).
JWT_SIGNING_KEY = os.environ.get("JWT_SIGNING_KEY", "dev-only-jwt-key-change-me-0123456789")
JWT_ALGORITHM = "HS256"

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,  # sin django.contrib.auth en este servicio
    "DEFAULT_AUTHENTICATION_CLASSES": ["chatbot_api.authentication.JWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "paqueteria-ia — Chatbot IA",
    "DESCRIPTION": "API del microservicio Chatbot IA.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# IA: "mock" (reglas locales, sin red) o "gemini". La clave solo se lee del entorno.
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "mock")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
LLM_MAX_TOOL_ROUNDS = 4

# Servicios de los que el chatbot obtiene los datos (el LLM nunca los inventa).
PEDIDOS_URL = os.environ.get("PEDIDOS_URL", "http://localhost:8002")
TRACKING_URL = os.environ.get("TRACKING_URL", "http://localhost:8003")
SERVICE_TIMEOUT = 5
