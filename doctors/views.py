import datetime
import os
import  re
from datetime import timedelta

import app


from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, current_user
from sqlalchemy import except_, True_

from datetime import  datetime,timedelta
from flask import Flask, request, jsonify, app, render_template, flash, redirect, url_for, session

from functools import  wraps

import jwt
from werkzeug.security import generate_password_hash

from app.models import User, db
from flask import jsonify
from app.doctors import doctor_blueprint
@doctor_blueprint.route('/login', methods=['GET', 'POST'], endpoint="login")

def login():
    if request.method == 'GET':
        return render_template('doctors/login.html')  # ✅ Show login page on GET request

    # Handle API JSON request (e.g., from Postman)
    if request.is_json:
        data = request.get_json(silent=True)
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing username or password'}), 400

        response, status_code = User.login(data['username'], data['password'])
        return jsonify(response), status_code

    # Handle form submission (from browser)
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Missing username or password', 'danger')
        return redirect(url_for('doctor.login'))

    response, status_code = User.login(username, password)


    if status_code == 200:
        # ✅ Store access token in session (Temporary)
        session['access_token'] = response['token']['access']
        session['refresh_token'] = response['token']['refresh']
        session['username'] = username
        flash("login successful!", "success")

        return render_template('doctors/login.html', user=response)
    else:
        flash(response['error'], 'danger')
        return redirect(url_for('doctor.login'))

@doctor_blueprint.route('/signup', methods=['GET', 'POST'],endpoint='signup')
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists!", "danger")
            return redirect(url_for('doctor.signup'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        flash("Signup successful!", "success")
        return redirect(url_for('doctor.login'))

    return render_template('doctors/signup.html')




# @doctor_blueprint.route('/profile/<int:user_id>', methods=['GET'])
# @jwt_required()
# def get_user_profile(user_id):
#
#     current_user = get_jwt_identity()
#
#     user = User.query.get(user_id)
#     if not user:
#         return jsonify({"error": "User not found"}), 404
#
#     return jsonify({
#         "message": "User profile retrieved successfully",
#         "user": {
#             "id": user.id,
#             "username": user.username,
#             "role": user.role,
#
#         }
#     }), 200
from flask import render_template

@doctor_blueprint.route('/profile/<int:user_id>', methods=['GET'],endpoint='profile')
def get_user_profile(user_id):


    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    # Render the HTML template with user data
    return render_template('doctors/user_profile.html', user=user)
@doctor_blueprint.route('/refresh')
@jwt_required(refresh=True)
def refresh_access():

    identity = get_jwt_identity()

    new_access_token = create_access_token(identity=identity)



    return jsonify({"access_token": new_access_token})


