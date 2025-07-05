import os

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("DB_PORT", "7306")),
    "db": os.environ.get("DB_NAME", "siksha"),
    "user": os.environ.get("DB_USER", "siksha"),
    "password": os.environ.get("DB_PASSWORD", "waffle"),
}


REDIS_CONFIG = {
    "host": os.environ.get("REDIS_HOST", "siksha-redis"),
    "port": int(os.environ.get("REDIS_PORT", "6379")),
}

JWT_SECRET = os.environ.get("JWT_SECRET", "secret-local")

S3_BUCKET = os.environ.get("S3_BUCKET", "siksha-local")

SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL")

SITE_ENV = os.environ.get("SITE_ENV", "local")


ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "admin_secret")  # 토큰 시크릿


ADMIN_EXPIRE = os.environ.get("ADMIN_EXPIRE", "300")  # 토큰 만료 시간 (초)
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
