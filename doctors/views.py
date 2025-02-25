import datetime
import json
import os
import  re
from io import BytesIO

from sqlalchemy.dialects.postgresql import psycopg2


from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename, send_from_directory
from app import Config
import app

UPLOAD_FOLDER = "uploads"

from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, current_user

from datetime import  datetime,timedelta
from flask import Flask, request, jsonify, app, render_template, flash, redirect, url_for, session, send_file

from functools import  wraps
from app.config import DevelopmentConfig
import jwt
from werkzeug.security import generate_password_hash
import psycopg2
from app.models import User, db, File
from flask import jsonify
from app.doctors import doctor_blueprint


def get_db_connection():

        conn = psycopg2.connect(DevelopmentConfig.SQLALCHEMY_DATABASE_URI)
        return conn
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
@doctor_blueprint.route("/upload", methods=["GET"])
def upload_form():
    return render_template("doctors/file_upload.html")


## to save in database
@doctor_blueprint.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    current_user = get_jwt_identity()


    user_id = request.form.get("user_id")
    phone_number = request.form.get("phone_number")
    country_code = request.form.get("country_code")
    id_of_uploader = request.form.get("id_of_uploader")
    result_date = request.form.get("result_date")
    selected_lab_test = request.form.get("selected_lab_test")
    result_type = request.form.get("result_type")
    file = request.files.get("files")


    if not all([user_id, phone_number, country_code, id_of_uploader, result_date, selected_lab_test, result_type, file]):
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


    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO files (user_id, file_name, upload_date, status)
            VALUES (%s, %s, %s, %s)
        """, (user_id, filename, result_date, 'pending'))  # Default status is 'pending'
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Failed to insert file metadata into database: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({"message": "File uploaded and metadata stored successfully!"}), 200

@doctor_blueprint.route('/get-all-files-users', methods=['GET'])
@jwt_required()
def get_all_files_users():
    current_user = get_jwt_identity()

    try:
        current_user = json.loads(current_user)
    except json.JSONDecodeError:
        return jsonify({"message": "Invalid token format"}), 401


    if current_user.get('role') != 'admin':
        return jsonify({"message": "You are not authorized to access this resource."}), 403


    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT files.file_id, files.file_name, files.status, doctors.username
        FROM files
        JOIN doctors ON files.user_id = doctors.id
        WHERE files.status = 'pending'
    """)


    pending_files = cursor.fetchall()

    cursor.close()
    conn.close()


    files_data = [{"file_id": file[0], "filename": file[1], "status": file[2], "username": file[3]} for file in
                  pending_files]

    return jsonify(files_data), 200

@doctor_blueprint.route('/update-file-status', methods=['POST'])
@jwt_required()
def update_file_status():

    current_user = get_jwt_identity()

    try:
        current_user = json.loads(current_user)
    except json.JSONDecodeError:
        return jsonify({"message": "Invalid token format"}), 401

    if current_user.get("role") != "admin":
        return jsonify({"message": "You are not authorized to update the file status."}), 403


    data = request.get_json()
    accept_file = data.get('accept_file')
    file_id = data.get('id_file')


    if accept_file not in ['accept', 'reject']:
        return jsonify({"message": "Invalid value for 'accept_file'. It must be 'accept' or 'reject'."}), 400


    new_status = 'approved' if accept_file == 'accept' else 'rejected'


    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("SELECT status FROM files WHERE file_id = %s", (file_id,))
    file = cursor.fetchone()

    if not file:
        cursor.close()
        conn.close()
        return jsonify({"message": "File not found."}), 404


    cursor.execute("UPDATE files SET status = %s WHERE file_id = %s", (new_status, file_id))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": f"File {new_status} successfully!"}), 200


@doctor_blueprint.route("/get-user-by-phone", methods=["GET"])
@jwt_required()
def get_user_by_phone():


    phone_number = request.args.get("phone_number")
    country_code = request.args.get("country_code", "").strip()
    if not country_code.startswith("+"):
        country_code = f"+{country_code}" # +20 problem
    if not phone_number or not country_code:
        return jsonify({"error": "Missing required parameters: phone_number and country_code"}), 400


    print(f"Querying user with phone_number={phone_number}, country_code={country_code}")


    current_user = get_jwt_identity()
    try:
        current_user = json.loads(current_user)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid token format"}), 401

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # Use to return dictionary

    try:

        cursor.execute("""
            SELECT * FROM doctors
            WHERE phone_number = %s AND country_code = %s
        """, (phone_number, country_code))
        user = cursor.fetchone()


        if not user:
            return jsonify({"error": "User not found"}), 404

        cursor.execute("""
            SELECT * FROM files
            WHERE user_id = %s
        """, (user["id"],))
        files = cursor.fetchall()


        response = {
            "user": {
                "id": user["id"],
                "phone_number": user["phone_number"],
                "country_code": user["country_code"],
                "name": user["username"],

            },
            "files": [
                {
                    "file_id": file["file_id"],
                    "file_name": file["file_name"],
                    "upload_date": file["upload_date"].isoformat() if file["upload_date"] else None,
                    "status": file["status"]
                }
                for file in files
            ]
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()
@doctor_blueprint.route("/userinfo", methods=["GET"])
def user_info():
    return render_template("doctors/userinfo.html")
@doctor_blueprint.route('/down', methods=['GET'])
def download_page():
    return render_template('doctors/download.html')

@doctor_blueprint.route('/download-file/<int:file_id>', methods=['GET'])
@jwt_required()
def download_file(file_id):
    current_user = get_jwt_identity()


    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("SELECT file_name, file_path FROM files WHERE file_id = %s", (file_id,))
    file_record = cursor.fetchone()

    cursor.close()
    conn.close()

    if not file_record:
        return jsonify({"message": "File not found"}), 404

    filename, file_path = file_record

    if not file_path:
        return jsonify({"message": "File path is missing in the database"}), 500


    if not os.path.exists(file_path):
        return jsonify({"message": "File does not exist on the server"}), 404

    return send_file(file_path, as_attachment=True, download_name=filename)

import logging

@doctor_blueprint.route('/file-info/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file_info(file_id):
    try:
        current_user = get_jwt_identity()


        conn = get_db_connection()
        cursor = conn.cursor()


        cursor.execute("SELECT file_name, file_path FROM files WHERE file_id = %s", (file_id,))
        file_record = cursor.fetchone()

        cursor.close()
        conn.close()

        if not file_record:
            logging.error(f"File not found for file_id: {file_id}")
            return jsonify({"message": "File not found"}), 404

        filename, file_path = file_record


        if not file_path:
            logging.error(f"File path missing for file_id: {file_id}")
            return jsonify({"message": "File path is missing in the database"}), 500


        if not os.path.exists(file_path):
            logging.error(f"File does not exist on server for file_id: {file_id}")
            return jsonify({"message": "File does not exist on the server"}), 404


        return jsonify({
            "file_id": file_id,
            "file_name": filename,
            "file_path": file_path
        })
    except Exception as e:
        logging.error(f"Error in get_file_info: {str(e)}")
        return jsonify({"message": "Internal server error"}), 500