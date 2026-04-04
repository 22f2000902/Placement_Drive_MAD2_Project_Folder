from flask import Blueprint, app, request, jsonify, abort, redirect, url_for, Response
from backend.models import Admin, Student, Company, PlacementDrive, Application
from flask_jwt_extended import create_access_token,current_user, get_jwt,jwt_required, get_jwt_identity, JWTManager
from datetime import datetime,timezone
from werkzeug.security import check_password_hash, generate_password_hash
from app import db

auth_bp = Blueprint('auth_bp', __name__)


@auth_bp.route("/login/<role>", methods=["POST"])
def login(role):

    data = request.get_json()
    email = data.get("email", None)
    password = data.get("password", None)

    if role == "admin":
        user = Admin.query.filter_by(email=email).first()
    elif role == "student":
        user = Student.query.filter_by(email=email).first()
    elif role == "company":
        user = Company.query.filter_by(email=email).first()
    else:
        return jsonify("Invalid role!"), 400

    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=str(user.id), additional_claims={'role': role})
        return jsonify(access_token=access_token), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route("/signup/<role>", methods=["POST"])
def signup(role):
    if role == "admin":
        return jsonify({'error': 'Admin registration is not allowed'}), 403
    
    data = request.get_json()
    
    email = data.get("email", None)
    password = data.get("password", None)
    confirm_password = data.get("confirm_password", None)

    if not email or not password or not confirm_password:
        return jsonify({'error': 'Email, password and confirm password are required'}), 400
    
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    password_hash = generate_password_hash(password)
    
    if role == "student": 
        roll_number = data.get("roll_number", None)
        department = data.get("department", None)
        full_name = data.get("full_name", None)
        phone_number = data.get("phone_number", None)

        if not roll_number or not department or not full_name or not phone_number:
            return jsonify({'error': 'All fields are required for student registration'}), 400
        
        if Student.query.filter_by(email=email).first() or Student.query.filter_by(roll_number=roll_number).first():
            return jsonify({'error': 'Email or roll number already exists'}), 400
        
        new_student = Student(email=email, password_hash=password_hash, roll_number=roll_number, department=department, full_name=full_name, phone_number=phone_number)

        db.session.add(new_student)
        db.session.commit()

    if role == "company":
        full_name = data.get("full_name", None)
        phone_number = data.get("phone_number", None)
        company_name = data.get("company_name", None)
        about_company = data.get("about_company", None)

        if not full_name or not phone_number or not company_name or not about_company:
            return jsonify({'error': 'All fields are required for company registration'}), 400
        
        if Company.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        new_company = Company(email=email, password_hash=password_hash, full_name=full_name, phone_number=phone_number, company_name=company_name, about_company=about_company)

        db.session.add(new_company)
        db.session.commit()

    return jsonify({'message': f'{role.capitalize()} registered successfully'}), 201


@auth_bp.route("/profile/<int:user_id>", methods=["GET", "PUT"])
@jwt_required()
def profile(user_id):
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    role = claims.get('role')

    if role == "admin":
        user = Admin.query.get(current_user_id)
    elif role == "student":
        user = Student.query.get(current_user_id)
    elif role == "company":
        user = Company.query.get(current_user_id)
    else:
        return jsonify("Invalid role!"), 400

    if not user:
        return jsonify({'error': 'User not found'}), 404

    user_data = {
        'id': user.id,
        'email': user.email,
        'role': role
    }

    if role == "student":
        user_data.update({
            'roll_number': user.roll_number,
            'department': user.department,
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'is_active': user.is_active,
            'resume_path': user.resume_path
        })
    
    if role == "company":
        user_data.update({
            'full_name': user.full_name,
            'phone_number': user.phone_number,
            'company_name': user.company_name,
            'about_company': user.about_company,
            'status': user.status,
            'is_blacklisted': user.is_blacklisted
        })

    return jsonify(user_data), 200