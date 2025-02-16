import datetime
import os
import  re
from datetime import timedelta

from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename, send_from_directory
from app import Config
import app

UPLOAD_FOLDER = "uploads"

from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, current_user

from datetime import  datetime,timedelta
from flask import Flask, request, jsonify, app, render_template, flash, redirect, url_for, session

from functools import  wraps

import jwt
from werkzeug.security import generate_password_hash

from app.models import User, db
from flask import jsonify
from app.doctors import doctor_blueprint, upload_blueprint


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

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
@upload_blueprint.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    current_user = get_jwt_identity()  # Extract user ID from JWT token

    user_id = request.form.get("user_id")
    phone_number = request.form.get("phone_number")
    country_code = request.form.get("country_code")
    id_of_uploader = request.form.get("id_of_uploader")
    result_date = request.form.get("result_date")
    selected_lab_test = request.form.get("selected_lab_test")
    result_type = request.form.get("result_type")
    file = request.files.get("files")
    if not all(
            [user_id, phone_number, country_code, id_of_uploader, result_date, selected_lab_test, result_type, file]):
            return jsonify({"error": "Missing required fields", "missing_fields": {
            "user_id": user_id,
            "phone_number": phone_number,
            "country_code": country_code,
            "id_of_uploader": id_of_uploader,
            "result_date": result_date,
            "selected_lab_test": selected_lab_test,
            "result_type": result_type,
        }}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file format. Allowed: pdf, jpg, png"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, f"user_{user_id}_{filename}")
    file.save(file_path)

    return jsonify({
        "message": "File uploaded successfully",
        "file_url": file_path
    }), 200
# @upload_blueprint.route("/up", methods=["GET", "POST"])
#
# def upload_file():
#     if request.method == "POST":
#         # Extract data from form
#         user_id = request.form.get("user_id")
#         phone_number = request.form.get("phone_number")
#         country_code = request.form.get("country_code")
#         id_of_uploader = request.form.get("id_of_uploader")
#         result_date = request.form.get("result_date")
#         selected_lab_test = request.form.get("selected_lab_test")
#         result_type = request.form.get("result_type")
#         file = request.files.get("files")
#
#
#         missing_fields = {
#             "user_id": user_id,
#             "phone_number": phone_number,
#             "country_code": country_code,
#             "id_of_uploader": id_of_uploader,
#             "result_date": result_date,
#             "selected_lab_test": selected_lab_test,
#             "result_type": result_type,
#             "files": file
#         }
#
#         missing = [key for key, value in missing_fields.items() if not value]
#
#         if missing:
#             flash(f"Missing required fields: {', '.join(missing)}", "danger")
#             return redirect(url_for("upload_file"))
#
#
#         if not allowed_file(file.filename):
#             flash("Invalid file format. Allowed: pdf, jpg, png", "danger")
#             return redirect(url_for("upload_file"))
#
#         # Save the file
#         filename = secure_filename(f"user_{user_id}_{file.filename}")
#         file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
#         file.save(file_path)
#
#         flash(f"File uploaded successfully for User ID: {user_id}!", "success")
#         return redirect(url_for("upload_file"))
#
#     return render_template("doctors/upload.html")
