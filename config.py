import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = "drawinghall-secret-key"
DEBUG = True

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "sua_senha_aqui"
DB_NAME = "drawinghall"
