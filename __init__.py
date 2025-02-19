import os
from datetime import timedelta

import psycopg2
from flask import Flask, app
from app.config import config_options as AppConfig
from app.models import  db
from app.config import Config
from flask_migrate import Migrate
from flask_restful import Api
from app.models import User
from app.doctors import doctor_blueprint
from app.doctors.views import doctor_blueprint  #
from flask_jwt_extended import JWTManager

from app.models import jwt

api = Api()
def create_app(config_name='dev'):
    app =Flask(__name__)

    #define configrations
    current_config=AppConfig[config_name]
    app.config['SQLALCHEMY_DATABASE_URI']=current_config.SQLALCHEMY_DATABASE_URI

    app.config.from_object(current_config)



    jwt = JWTManager(app)
    app.config['JWT_SECRET_KEY'] = os.urandom(24).hex()
    app.config['UPLOAD_DIRECTORY'] = 'uploads/'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['ALLOWED_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif']
    print("✅ SECRET_KEY:", app.config["SECRET_KEY"])

    db .init_app(app)
    migrate=Migrate(app,db, render_as_batch=True)
    api.init_app(app)
    jwt.init_app(app)
    # generate apis for this project
    # add the class student resource to the api


    app.register_blueprint(doctor_blueprint, url_prefix='/api')



    return app