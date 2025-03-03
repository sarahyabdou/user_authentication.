import os

from flask import app


class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SECRET_KEY = os.urandom(32).hex()
    UPLOAD_FOLDER = "uploads"
    ALLOWED_EXTENSIONS = {"pdf", "jpg", "png"}
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    @staticmethod
    def init_app():
        pass

class DevelopmentConfig(Config):
    """postgresql://username:password@localhost:portnumber/database_name """
    DEBUG=True
    SQLALCHEMY_DATABASE_URI='postgresql://postgres:1181968@localhost:5432/trust'
class ProductionConfig(Config):
    DEBUG=False
    SQLALCHEMY_DATABASE_URI = ''
config_options = {
    "dev": DevelopmentConfig,
    "prd": DevelopmentConfig
}

