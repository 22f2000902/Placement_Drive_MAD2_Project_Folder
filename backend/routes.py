from flask import Blueprint, app, render_template, request, jsonify, abort, redirect, session, url_for, Response
from backend.models import Admin, Student, Company, PlacementDrive, Application
from flask_jwt_extended import create_access_token,current_user, get_jwt,jwt_required, get_jwt_identity, JWTManager
from datetime import datetime,timezone
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database import db     

auth_bp = Blueprint('auth_bp', __name__)
admin_bp = Blueprint('admin_bp', __name__)
company_bp = Blueprint('company_bp', __name__)
student_bp = Blueprint('student_bp', __name__)

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

@auth_bp.route("/login")
def login_page():
    return render_template("templates/login.html")

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

@admin_bp.route('/admin/dashboard')
@jwt_required()
def admin_dashboard():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': "Unauthorized access"}), 403
    
    active_companies = Company.query.filter_by(status='active').order_by(Company.id.asc()).limit(2).all()
    requested_companies = Company.query.filter_by(status='inactive').order_by(Company.id.asc()).limit(2).all()
    students = Student.query.filter_by(is_active=True).order_by(Student.id.asc()).limit(2).all() 
    placements = PlacementDrive.query.filter_by(status='active').order_by(PlacementDrive.id.asc()).limit(2).all()

    return jsonify({
        'active_companies': [{'id': c.id, 'company_name': c.company_name} for c in active_companies],
        'requested_companies': [{'id': c.id, 'company_name': c.company_name} for c in requested_companies],
        'students': [{'id': s.id, 'full_name': s.full_name} for s in students],
        'placements': [{'id': p.id, 'job_title': p.job_title} for p in placements]
    }), 200

@admin_bp.route('/admin/companies')
@jwt_required()
def admin_companies():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'error': "Unauthorized access"}), 403
    
    companies = Company.query.order_by(Company.id.asc()).all()
    return jsonify([{
        'id': c.id,
        'company_name': c.company_name,
        'email': c.email,
        'status': c.status,
        'is_blacklisted': c.is_blacklisted
    } for c in companies]), 200

@company_bp.route('/company/dashboard')
@jwt_required()
def company_dashboard():
    claims = get_jwt()
    if claims.get('role') != 'company':
        return jsonify({'error': "Unauthorized access"}), 403
    
    company_id = get_jwt_identity()
    active_placements = PlacementDrive.query.filter_by(company_id=company_id, status='active').order_by(PlacementDrive.id.asc()).all()
    inactive_placements = PlacementDrive.query.filter_by(company_id=company_id, status='inactive').order_by(PlacementDrive.id.asc()).all()

    return jsonify({
        'active_placements': [{
            'id': p.id,
            'company_id': p.company_id,
            'job_title': p.job_title,
            'job_description': p.job_description,
            'salary_range': p.salary_range,
            'key_skills': p.key_skills,
            'drive_date': p.drive_date.isoformat() if p.drive_date else None,
            'drive_end_date': p.drive_end_date.isoformat() if p.drive_end_date else None,
            'status': p.status,
            'is_approved': p.is_approved
        } for p in active_placements],
        
        'inactive_placements': [{
            'id': p.id,
            'company_id': p.company_id,
            'job_title': p.job_title,
            'job_description': p.job_description,
            'salary_range': p.salary_range,
            'key_skills': p.key_skills,
            'drive_date': p.drive_date.isoformat() if p.drive_date else None,
            'drive_end_date': p.drive_end_date.isoformat() if p.drive_end_date else None,
            'status': p.status,
            'is_approved': p.is_approved
        } for p in inactive_placements]
    }), 200

@admin_bp.route('/admin/view-drive/<int:drive_id>')
@company_bp.route('/company/view-drive/<int:drive_id>')
@jwt_required()
def view_drive(drive_id):
    claims = get_jwt()
    role = claims.get('role')

    if role not in ['admin', 'company']:
        return jsonify({'error': "Unauthorized access"}), 403
    
    drive = PlacementDrive.query.get(drive_id)
    if not drive:
        return jsonify({'error': 'Placement drive not found'}), 404
    
    applications = Application.query.filter_by(placement_drive_id=drive_id).order_by(Application.id.asc()).all()

    return jsonify({
        'id': drive.id,
        'company_id': drive.company_id,
        'job_title': drive.job_title,
        'job_description': drive.job_description,
        'salary_range': drive.salary_range,
        'key_skills': drive.key_skills,
        'drive_date': drive.drive_date.isoformat() if drive.drive_date else None,
        'drive_end_date': drive.drive_end_date.isoformat() if drive.drive_end_date else None,
        'status': drive.status,
        'is_approved': drive.is_approved,
        'applications': [{
            'id': a.id,
            'student_id': a.student_id,
            'status': a.status
        } for a in applications]
    }), 200