import os


class Config:
    SECRET_KEY = os.urandom(32).hex()
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


