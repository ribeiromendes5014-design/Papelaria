import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-!c8&7g7$6m+2bq$zy1u#z%r1+41n4=v-82!wjn0x4q2x-2u7pb"
)
DEBUG = os.getenv("DEBUG", "True") == "True"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 60  # 60 dias para PWA manter sessao

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "pedidos",
    "produtos",
    "catalogo",
    "tenants",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "papelaria_multi.middleware.TenantMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "papelaria_multi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tenants.context_processors.current_tenant",
                "catalogo.context_processors.cart_summary",
            ],
        },
    },
]

WSGI_APPLICATION = "papelaria_multi.wsgi.application"

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=True,
    )
}
if not DATABASES["default"]:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "papelariadata",
        "USER": "papelariadata_user",
        "PASSWORD": "oCmSJU3JxytGdDyKyeXOkVoBp39jFWxs",
        "HOST": "dpg-d4se5afpm1nc73c0fi30-a.virginia-postgres.render.com",
        "PORT": "5432",
    }

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

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_L10N = True
USE_TZ = True

AUTHENTICATION_BACKENDS = [
    "tenants.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "192.168.3.3",
    ".onrender.com",
    "papelariaribeiro.top",
    ".papelariaribeiro.top",
]
CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com", "https://papelariaribeiro.top", "https://*.papelariaribeiro.top"]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
IMGBB_API_KEY = os.environ.get(
    "IMGBB_API_KEY", "a351d106aae17d2ea4c334d798162573"
)
LOGIN_URL = "login"
LOGOUT_REDIRECT_URL = "login"
