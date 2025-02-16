import datetime
import json
from functools import wraps
import jwt
from flask import request,jsonify
from flask import current_app
from flask_jwt_extended import JWTManager, verify_jwt_in_request, get_jwt_identity, create_access_token, \
    create_refresh_token
import  os
from app.config import  Config
from werkzeug.utils import redirect

SECRET_KEY = os.urandom(32).hex()
from flask_sqlalchemy import  SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db=SQLAlchemy()

class User(db.Model):
    __tablename__ = 'doctors'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(80),unique=True,nullable=False)
    password=db.Column(db.String(200),nullable=False)
    role = db.Column(db.String(20), default='user')


    phone_number=db.Column(db.String(15),unique=True)
    first_name=db.Column(db.String(50))
    last_name=db.Column(db.String(50))

    def __str__(self):
        return {self.username},{self.password},self.last_name


    @classmethod
    def user_exists(cls, username):
        user = db.session.query(cls.id).filter_by(username=username).first()
        return user is not None

    @classmethod
    def login(cls, username, password):
        user = cls.query.filter_by(username=username).first()

        if not user:
            return {'error': 'User not found'}, 404

        if not check_password_hash(user.password, password):
            return {'error': 'password uncorrect'}, 401

        # ✅ Ensure identity is a string or JSON-serializable
        identity = json.dumps({
            "user_id": user.id,
            "role": user.role,
            "username": user.username
        })

        access_token = create_access_token(identity=identity, expires_delta=datetime.timedelta(hours=1))
        refresh_token = create_refresh_token(identity={"user_id": user.id})
        # Keep this if it works fine

        return {
            "message": "Logged in",
            "token": {
                "access": access_token,
                "refresh": refresh_token
            }
        }, 200
    @classmethod
    def signup(cls,username,password):
        if cls.query.filter_by(username=username).first():
            return {'error':'user already exists'},409
        hashed_password=generate_password_hash(password,method='sha256')
        new_user=cls(username=username,password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return {'message':'success!,sign-up completed'},201


# point3
