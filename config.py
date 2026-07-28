import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
from dotenv import load_dotenv

class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "x9@L2!pQ7#tV8mR4$kN6zY1&wF5uH3"
    )

    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )

    SQLALCHEMY_DATABASE_URI = (
        DATABASE_URL
        if DATABASE_URL
        else "sqlite:///" + os.path.join(BASE_DIR, "restaurant.db")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    }

    # ---------------- MAIL ---------------- #

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False

    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        MAIL_USERNAME
    )

    MAIL_MAX_EMAILS = 10
    MAIL_ASCII_ATTACHMENTS = False
    MAIL_SUPPRESS_SEND = False

    # ---------------- SESSION ---------------- #

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Render HTTPS
    SESSION_COOKIE_SECURE = True


load_dotenv()


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:

    # ==============================
    # Security
    # ==============================

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "76f02782d656c7366e6f2085d35bc34002a79bfdaed9934c7d20b010c731db54"
    )

    # ==============================
    # Database
    # ==============================

    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )

    SQLALCHEMY_DATABASE_URI = (
        DATABASE_URL
        if DATABASE_URL
        else "sqlite:///" + os.path.join(
            BASE_DIR,
            "restaurant.db"
        )
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    }

    # ==============================
    # Email Configuration
    # ==============================

    MAIL_SERVER = os.environ.get(
        "MAIL_SERVER",
        "smtp.gmail.com"
    )

    MAIL_PORT = int(
        os.environ.get("MAIL_PORT", 587)
    )

    MAIL_USE_TLS = os.environ.get(
        "MAIL_USE_TLS",
        "True"
    ).strip().lower() == "true"

    MAIL_USE_SSL = os.environ.get(
        "MAIL_USE_SSL",
        "False"
    ).strip().lower() == "true"

    MAIL_USERNAME = os.environ.get(
        "MAIL_USERNAME"
    )

    MAIL_PASSWORD = os.environ.get(
        "MAIL_PASSWORD"
    )

    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        MAIL_USERNAME
    )

    MAIL_MAX_EMAILS = 10
    MAIL_ASCII_ATTACHMENTS = False
    MAIL_SUPPRESS_SEND = False

    # ==============================
    # Session Configuration
    # ==============================

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Localhost par False
    # Render HTTPS par True
    SESSION_COOKIE_SECURE = os.environ.get(
        "SESSION_COOKIE_SECURE",
        "False"
    ).strip().lower() == "true"