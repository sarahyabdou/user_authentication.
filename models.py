import datetime

import jwt
from flask import current_app

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

            return {'error': 'Invalid credentials'}, 401

        token = jwt.encode(
            {
                'user_id': user.id,
                'role': user.role,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
            },
            current_app.config['SECRET_KEY'],
            algorithm="HS256"
        )

        return {'token': token}, 200
    @classmethod
    def signup(cls,username,password):
        if cls.query.filter_by(username=username).first():
            return {'error':'user already exists'},409
        hashed_password=generate_password_hash(password,method='sha256')
        new_user=cls(username=username,password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return {'message':'success!,sign-up completed'},201

