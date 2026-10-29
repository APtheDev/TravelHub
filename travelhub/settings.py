
"""
Configuration Django pour TravelHub.
Compatible avec le développement local et Docker/Portainer.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url


# --------------------------------------------------
# Chemins
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# --------------------------------------------------
# Sécurité
# --------------------------------------------------

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

if DEBUG:
    SECRET_KEY = os.environ.get(
        "DJANGO_SECRET_KEY",
        "travelhub-development-only-secret-key"
    )
else:
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost"
    ).split(",")
    if host.strip()
]


# --------------------------------------------------
# Applications
# --------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "rest_framework",
    "rest_framework_simplejwt",
    "drf_spectacular",
    "graphene_django",

    "travel",
]


# --------------------------------------------------
# Middleware
# --------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "travelhub.urls"


# --------------------------------------------------
# Templates
# --------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "travelhub.wsgi.application"


# --------------------------------------------------
# Base de données PostgreSQL
# --------------------------------------------------

if os.environ.get("DATABASE_URL"):

    # Production Docker / Portainer
    DATABASES = {
        "default": dj_database_url.config(
            env="DATABASE_URL",
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

else:

    # Développement local Windows
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "travelhub"),
            "USER": os.environ.get("DB_USER", "travelhub_user"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }


# --------------------------------------------------
# Validation des mots de passe
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# --------------------------------------------------
# Langue et fuseau horaire
# --------------------------------------------------

LANGUAGE_CODE = "fr-ca"

TIME_ZONE = "America/Toronto"

USE_I18N = True
USE_TZ = True


# --------------------------------------------------
# Fichiers statiques
# --------------------------------------------------

STATIC_URL = "static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# --------------------------------------------------
# Email
# --------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# --------------------------------------------------
# Django REST Framework
# --------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],

    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# --------------------------------------------------
# GraphQL
# --------------------------------------------------

GRAPHENE = {
    "SCHEMA": "travel.schemaGraphQL.schema",
}


# --------------------------------------------------
# Swagger / OpenAPI
# --------------------------------------------------

SPECTACULAR_SETTINGS = {
    "TITLE": "TravelHub API",
    "DESCRIPTION": "API REST de planification et gestion de voyages",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}


# --------------------------------------------------
# HTTPS et sécurité en production
# --------------------------------------------------

if not DEBUG:

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    public_url = os.environ["DJANGO_PUBLIC_URL"].rstrip("/")

    if not public_url.startswith("https://"):
        raise ValueError(
            "DJANGO_PUBLIC_URL doit commencer par https://"
        )

    CSRF_TRUSTED_ORIGINS = [public_url]

    # À utiliser uniquement derrière un reverse proxy
    # de confiance qui configure X-Forwarded-Proto.
    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

    # La redirection HTTP vers HTTPS est assurée
    # par Nginx Proxy Manager.
    SECURE_SSL_REDIRECT = False

    SECURE_CONTENT_TYPE_NOSNIFF = True

    X_FRAME_OPTIONS = "DENY"
