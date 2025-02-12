import datetime
import os
import  re


from sqlalchemy import except_


from datetime import  datetime,timedelta
from flask import Flask, request, jsonify, app, render_template, flash, redirect, url_for

from functools import  wraps

import jwt
from werkzeug.security import generate_password_hash

from app.models import User, db
from flask import jsonify
from app.doctors import doctor_blueprint
@doctor_blueprint.route('/login', methods=['GET', 'POST'], endpoint="login")
def login():
    if request.method == 'GET':
        return render_template('doctors/login.html')

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
        flash('Login successful!', 'success')
        return redirect(url_for('doctor.dashboard'))
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


