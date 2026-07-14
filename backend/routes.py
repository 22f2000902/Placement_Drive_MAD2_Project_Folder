from flask import Blueprint, app, render_template, request, jsonify, abort, redirect, session, url_for, Response
from backend.models import Admin, Student, Company, PlacementDrive, Application, Interview
from flask_jwt_extended import create_access_token,current_user, get_jwt,jwt_required, get_jwt_identity, JWTManager
from datetime import datetime,timezone
from werkzeug.security import check_password_hash, generate_password_hash
from backend.database import db     
from flask_jwt_extended import verify_jwt_in_request
import os
from werkzeug.utils import secure_filename
from flask import current_app
from celery.result import AsyncResult
from backend.cache_config import cache

auth_bp = Blueprint('auth_bp', __name__)
admin_bp = Blueprint('admin_bp', __name__)
company_bp = Blueprint('company_bp', __name__)
student_bp = Blueprint('student_bp', __name__)

#login api route for all users + the page routing for login page
@auth_bp.route("/login/<role>", methods=["GET", "POST"])
def login(role):

    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if role == "admin":
            user = Admin.query.filter_by(email=email).first()
        elif role == "student":
            user = Student.query.filter_by(email=email).first()
        elif role == "company":
            user = Company.query.filter_by(email=email).first()
        else:
            return jsonify({"error": "Invalid role!"}), 400

        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid email or password."}), 401

        # Student account status check
        if role == "student" and not user.is_active:
            return jsonify({"error": "Your account has been deactivated. Please contact the administrator."}), 403

        # Company account status check
        if role == "company" and user.status in ["pending", "inactive"]:
            return jsonify({"error": "Your company account has been deactivated. Please contact the administrator."}), 403

        display_name = getattr(user, "full_name", getattr(user, "company_name", role.capitalize()))

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                "role": role
            }
        )

        return jsonify({"access_token": access_token, "role": role, "name": display_name}), 200

#sign up api route
@auth_bp.route("/signup/<role>", methods=["GET", "POST"])
def signup(role):
    if request.method == "GET":
        return render_template("signup.html")

    if request.method == "POST": 
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
            cgpa = data.get("cgpa", None)

            if not roll_number or not department or not full_name or not phone_number or not cgpa:
                return jsonify({'error': 'All fields are required for student registration'}), 400
            
            if Student.query.filter_by(email=email).first() or Student.query.filter_by(roll_number=roll_number).first():
                return jsonify({'error': 'Email or roll number already exists'}), 400
            
            new_student = Student(email=email, password_hash=password_hash, roll_number=roll_number, department=department, full_name=full_name, phone_number=phone_number, cgpa=cgpa)

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

#admin dashboard api route
@admin_bp.route('/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if request.method == 'GET':
        return render_template('admin/dashboard.html')
    
    if request.method == 'POST':
            verify_jwt_in_request()
            
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({'error': "Unauthorized administration access"}), 403
    
            active_companies = Company.query.filter_by(status='active').order_by(Company.id.asc()).limit(2).all()
            requested_companies = Company.query.filter(Company.status.in_(['pending', 'inactive'])).order_by(Company.id.asc()).limit(2).all()
            students = Student.query.filter_by(is_active=True).order_by(Student.id.asc()).limit(2).all() 
            placements = PlacementDrive.query.filter_by(status='active').order_by(PlacementDrive.id.asc()).limit(2).all()

            return jsonify({
                'active_companies': [
                    {'id': c.id, 'company_name': c.company_name, 'full_name': c.full_name, 'status': c.status} 
                    for c in active_companies
                ],
                'requested_companies': [
                    {'id': c.id, 'company_name': c.company_name, 'full_name': c.full_name, 'status': c.status} 
                    for c in requested_companies
                ],
                'students': [
                    {'id': s.id, 'full_name': s.full_name, 'email': s.email, 'is_active': s.is_active} 
                    for s in students
                ],
                'placements': [
                    {'id': p.id, 'company_name': p.company.company_name, 'drive_date': str(p.drive_date), 'drive_end_date': str(p.drive_end_date), 'job_title': p.job_title, 'status': p.status} 
                    for p in placements
                ]
            }), 200

#page to view all companies for admin
@admin_bp.route('/companies', methods=['GET', 'POST'])
def admin_companies():

    # Render HTML page
    if request.method == 'GET':
        return render_template('admin/company.html')

    # API data route
    if request.method == 'POST':
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get('role') != 'admin':
            return jsonify({'error': "Unauthorized access"}), 403

        companies = Company.query.order_by(Company.id.asc()).all()
        number_of_drives = PlacementDrive.query.filter_by(company_id=Company.id).count()

        return jsonify({
            'companies': [
                {
                    'id': c.id,
                    'company_name': c.company_name,
                    'full_name': c.full_name,
                    'email': c.email,
                    'status': c.status,
                    'is_blacklisted': c.is_blacklisted,
                    'number_of_drives': number_of_drives
                }
                for c in companies
            ]
        }), 200

@admin_bp.route('/students', methods=['GET', 'POST'])
def admin_students():
    if request.method == 'GET':
        return render_template('admin/students_list.html')
    
    if request.method == 'POST':
        verify_jwt_in_request()

        claims = get_jwt()

        if claims.get('role') != 'admin':
            return jsonify({'error': "Unauthorized access"}), 403
        
        students = Student.query.order_by(Student.id.asc()).all()

        return jsonify({
            'students': [
                {
                   'id': s.id,
                   'full_name': s.full_name,
                   'roll_number': s.roll_number,
                   'department': s.department,
                   'is_active': s.is_active,
                   'resume_path': s.resume_path
                } for s in students
            ]
        }), 200

@admin_bp.route('/change_company_status/<int:company_id>', methods=['GET', 'POST'])
def change_company_status(company_id):
    if request.method == "GET":
        company = Company.query.get(company_id)
        number_of_drives = PlacementDrive.query.filter_by(company_id=company.id).count()

        return render_template(
            'admin/change_company_status.html',
            company_id=company.id,
            company_name=company.company_name,
            company_status=company.status,
            full_name=company.full_name,
            about_company=company.about_company,
            number_of_placement_drives = number_of_drives
        )
    if request.method == "POST":
        verify_jwt_in_request()

        claims = get_jwt()

        if claims.get('role') != 'admin':
            return jsonify({'error': "Unauthorized access"}), 403
        
        company = Company.query.get(company_id)
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        
        data = request.get_json()
        new_status = data.get('status')
        new_status = new_status.lower().strip()

        allowed_statuses = ['active', 'inactive', 'pending', 'blacklisted']
        if new_status not in allowed_statuses:
            return jsonify({'error': f'Status must be one of: {", ".join(allowed_statuses)}'}), 400
        
        company.status = new_status
        db.session.commit()

        return jsonify({
            'message': f'Company status successfully updated to {new_status}!',
            'company_id': company.id,
            'current_status': company.status
        }), 200   

@admin_bp.route('/change_student_status/<int:student_id>', methods=['GET', 'POST'])
def change_student_status(student_id):

    if request.method == "GET":

        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        return render_template(
            'admin/change_student_status.html',
            student_id=student.id,
            student_name=student.full_name,
            roll_number=student.roll_number,
            department=student.department,
            student_status=student.is_active
        )

    if request.method == "POST":

        verify_jwt_in_request()

        claims = get_jwt()

        if claims.get('role') != 'admin':
            return jsonify({'error': "Unauthorized access"}), 403

        student = Student.query.get(student_id)

        if not student:
            return jsonify({'error': 'Student not found'}), 404

        data = request.get_json()

        status = data.get("status")

        if not isinstance(status, bool):
            return jsonify({
                "error": "Status must be a boolean."
            }), 400

        student.is_active = status

        db.session.commit()

        return jsonify({
            "message": "Student status updated successfully.",
            "student_id": student.id,
            "current_status": student.is_active
        }), 200

@admin_bp.route('/view_company_drives/<int:company_id>', methods=['GET', 'POST'])
def view_company_drives(company_id):
    if request.method == "GET":
        return render_template('admin/admin_view_company_drive.html', company_id=company_id)
    
    if request.method == "POST":
        verify_jwt_in_request()

        claims = get_jwt()

        if claims.get('role') != 'admin':
            return jsonify({'error': "Unauthorized access"}), 403
        
        drives = PlacementDrive.query.filter_by(company_id=company_id).order_by(PlacementDrive.id.asc()).all()

        return jsonify({
            'placement_drives': [{
                    'id': d.id,
                    'job_title': d.job_title,
                    'drive_date': str(d.drive_date),
                    'drive_end_date': str(d.drive_end_date),
                    'job_description': d.job_description,
                    'salary_range': d.salary_range,
                    'key_skills': d.key_skills,
                    'status': d.status,
                    'is_approved': d.is_approved} for d in drives]}), 200

@admin_bp.route('/change_placement_drive_status/<int:drive_id>', methods=['GET', 'POST'])
@company_bp.route('/change_placement_drive_status/<int:drive_id>', methods=['GET', 'POST'])
def change_placement_drive_status(drive_id):
    if request.method == "GET":
        drive = PlacementDrive.query.get(drive_id)
        if not drive:
            return jsonify({'error': 'Placement drive not found'}), 404
        
        return render_template(
            'company/change_drive_status.html',
            drive_id=drive.id,
            company_name=drive.company.company_name,
            job_title=drive.job_title,
            job_description=drive.job_description,
            drive_date=str(drive.drive_date),
            drive_end_date=str(drive.drive_end_date),
            key_skills=drive.key_skills,
            salary_range=drive.salary_range,
            current_status=drive.status,
            is_approved=drive.is_approved
        )

    if request.method == "POST":
        verify_jwt_in_request()

        claims = get_jwt()
        role = claims.get('role')
        user_id = get_jwt_identity()

        if role not in ['admin', 'company']:
            return jsonify({'error': 'Unauthorized access'}), 403

        drive = PlacementDrive.query.get(drive_id)

        if not drive:
            return jsonify({'error': 'Placement drive not found'}), 404

        # Company can edit only its own drives
        if role == "company" and str(drive.company_id) != str(user_id):
            return jsonify({'error': 'Unauthorized access'}), 403

        data = request.get_json()

        if role == "company":
            new_status = data.get("status", "").lower().strip()
            allowed_statuses = ["active", "inactive"]

            if new_status not in allowed_statuses:
                return jsonify({
                    "error": f"Status must be one of: {', '.join(allowed_statuses)}"
                }), 400
            drive.status = new_status

        elif role == "admin":
            is_approved = data.get("is_approved")

            if is_approved is None:
                return jsonify({
                    "error": "Approval status is required."
                }), 400

            drive.is_approved = bool(is_approved)

        db.session.commit()

        return jsonify({
            "message": "Placement drive updated successfully.",
            "placement_drive_id": drive.id,
            "current_status": drive.status,
            "is_approved": drive.is_approved
        }), 200

#change student application status api route for admin and company 
@company_bp.route('/student_application_status/<int:id>', methods=['GET', 'POST'])
@admin_bp.route('/student_application_status/<int:id>', methods=['GET', 'POST'])
def student_application_status(id):
    if request.method == "GET":
        application = Application.query.get(id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        return render_template(
                                'admin/change_student_application_status.html',
                                application_id=application.id,
                                student_id=application.student_id,
                                placement_drive_id=application.placement_drive_id,
                                current_status=application.status,
                                student_name=application.student.name,
                                roll_number=application.student.roll_number,
                                department=application.student.department,
                                company=application.placement_drive.company.company_name,
                                job_title=application.placement_drive.job_title
                            )
    
    if request.method == "POST":
        verify_jwt_in_request()

        claims = get_jwt()

        if claims.get('role') not in ['admin', 'company']:
            return jsonify({'error': "Unauthorized access"}), 403
        
        application = Application.query.get(id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        data = request.get_json()
        new_status = data.get('status')
        new_status = new_status.lower().strip()

        allowed_statuses = ['shortlisted', 'interview complete', 'offer', 'rejected', 'inactive', 'placed']
        if new_status not in allowed_statuses:
            return jsonify({'error': f'Status must be one of: {", ".join(allowed_statuses)}'}), 400
        
        application.status = new_status
        db.session.commit()
        cache.delete(f"student_dashboard_{application.student_id}")

        return jsonify({
            'message': f'Application status successfully updated to {new_status}!',
            'application_id': application.id,
            'current_status': application.status
        }), 200

#admin views all the current placement drives api route
@admin_bp.route('/placement_drives', methods=['GET', 'POST'])
@company_bp.route('/placement_drives', methods=['GET', 'POST'])
def placement_drives_list():
    if request.method == 'GET':
        return render_template('admin/placement_list.html')
    
    if request.method == 'POST':
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get('role') not in ['admin', 'company']:
            return jsonify({'error': "Unauthorized access"}), 403
        
        placements = PlacementDrive.query.order_by(PlacementDrive.id.asc()).all()

        return jsonify({
            'placements': [
                {
                    'id': p.id,
                    'company_name': p.company.company_name,
                    'job_title': p.job_title,
                    'drive_date': str(p.drive_date),
                    'drive_end_date': str(p.drive_end_date),
                    'status': p.status,
                    'is_approved': p.is_approved
                } for p in placements
            ]
        }), 200

#api for student applications 
@admin_bp.route('/student_applications/<int:student_id>', methods=["GET", "POST"])
def student_applications(student_id):
    if request.method == "GET":
        return render_template("admin/view_student_applications.html", student_id = student_id)

    if request.method == "POST":
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get('role') not in ['admin']:
            return jsonify({'error': "Unauthorized access"}), 403
        
        student_applications = Application.query.filter_by(student_id=student_id).order_by(Application.id.asc()).all()

        return jsonify({
            'applications': [{
                'id': (a.id),
                'student_name': a.student.full_name,
                'job_title': a.placement_drive.job_title,
                'drive_date': a.placement_drive.drive_date.isoformat() if a.placement_drive.drive_date else None,
                'status': a.status
            } for a in student_applications]
        }), 200

#company dashboard api route
@company_bp.route('/dashboard', methods=['GET', 'POST'])
def company_dashboard():
    if request.method == 'GET':        
        return render_template('company/dashboard.html')
    
    if request.method == "POST":

        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get("role") != "company":
            return jsonify({"error": "Unauthorized access"}), 403

        company_id = get_jwt_identity()
        active_placements = PlacementDrive.query.filter_by(company_id=company_id, is_approved=True).order_by(PlacementDrive.id.asc()).all()
        inactive_placements = PlacementDrive.query.filter_by(company_id=company_id, is_approved=False).order_by(PlacementDrive.id.asc()).all()

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

@company_bp.route('/create_drive', methods=['GET', 'POST'])
def create_drive():
    if request.method == 'GET':
        return render_template('company/create_drive.html')
    
    if request.method == 'POST':
        verify_jwt_in_request()

        claims = get_jwt()

        if claims.get('role') != 'company':
            return jsonify({'error': "Unauthorized access"}), 403
        
        company_id = get_jwt_identity()
        data = request.get_json()

        job_title = data.get('job_title')
        job_description = data.get('job_description')
        salary_range = data.get('salary_range')
        key_skills = data.get('key_skills')
        drive_date_str = data.get('drive_date')
        drive_end_date_str = data.get('drive_end_date')
        required_cgpa=data.get("required_cgpa")

        try:
            drive_date = datetime.fromisoformat(drive_date_str) if drive_date_str else None
            drive_end_date = datetime.fromisoformat(drive_end_date_str) if drive_end_date_str else None
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

        new_drive = PlacementDrive(
            company_id=company_id,
            job_title=job_title,
            job_description=job_description,
            salary_range=salary_range,
            key_skills=key_skills,
            drive_date=drive_date,
            drive_end_date=drive_end_date,
            required_cgpa=required_cgpa,
            status='active',
            is_approved=False
        )

        db.session.add(new_drive)
        db.session.commit()

        return jsonify({
            'message': 'Placement drive created successfully!',
            'placement_drive_id': new_drive.id
        }), 201

#common view drive page api route for companies, admin and student 
@admin_bp.route('/view_drive/<int:drive_id>', methods=['GET', 'POST'])
@company_bp.route('/view_drive/<int:drive_id>', methods=['GET', 'POST'])
@student_bp.route('/view_drive/<int:drive_id>', methods=['GET', 'POST'])
def view_drive(drive_id):

    if request.method == 'GET':
        return render_template('company/view_drive.html', drive_id=drive_id)

    if request.method == 'POST':
        verify_jwt_in_request()

        claims = get_jwt()
        role = claims.get('role')
        user_id = int(get_jwt_identity())

        if role not in ['admin', 'company', 'student']:
            return jsonify({'error': 'Unauthorized access'}), 403

        drive = PlacementDrive.query.get(drive_id)
        if role == "student":
            student = Student.query.get(user_id)

            if not student:
                return jsonify({'error': 'Student not found'}), 404

        if not drive:
            return jsonify({'error': 'Placement drive not found'}), 404

        # Company can only view its own drives
        if role == "company" and drive.company_id != user_id:
            return jsonify({
                "error": "You are not authorized to view this placement drive."
            }), 403

        response = {
            'id': drive.id,
            'company_id': drive.company.id,
            'company_name': drive.company.company_name,
            'about_company': drive.company.about_company,
            'job_title': drive.job_title,
            'job_description': drive.job_description,
            'salary_range': drive.salary_range,
            'key_skills': drive.key_skills,
            'drive_date': drive.drive_date.isoformat() if drive.drive_date else None,
            'drive_end_date': drive.drive_end_date.isoformat() if drive.drive_end_date else None,
            'status': drive.status,
            'is_approved': drive.is_approved,
            'required_cgpa': drive.required_cgpa
        }

        if role == "student":
            response["student_cgpa"] = student.cgpa
            response["is_eligible"] = student.cgpa >= drive.required_cgpa

        # Only admin and company should receive applicant details
        if role in ['admin', 'company']:

            applications = Application.query.filter_by(
                placement_drive_id=drive_id
            ).order_by(Application.id.asc()).all()

            response['application_count'] = len(applications)

            response['applications'] = [{
                'id': a.id,
                'student_id': a.student_id,
                'student_name': a.student.full_name,
                'department': a.student.department,
                'roll_number': a.student.roll_number,
                'status': a.status
            } for a in applications]

        return jsonify(response), 200

#api route for companies and admin to view student applications for drives 
@admin_bp.route('/view_student_applications/<int:drive_id>', methods=['GET', 'POST'])
@company_bp.route('/view_student_applications/<int:drive_id>', methods=['GET', 'POST'])
def view_student_applications(drive_id):
    if request.method == 'GET':
        return render_template('company/view_student_application.html', drive_id=drive_id)

    if request.method == 'POST':
        verify_jwt_in_request()
        claims = get_jwt()
        role = claims.get('role')
        user_id = get_jwt_identity()

        if role not in ['admin', 'company']:
            return jsonify({'error': "Unauthorized access"}), 403
        
        drive = PlacementDrive.query.get(drive_id)
        if not drive:
            return jsonify({'error': 'Placement drive not found'}), 404

        if role == "company" and str(drive.company_id) != user_id:
            return jsonify({"error": "You are not authorized to view this placement drive."}), 403
        
        applications = Application.query.filter_by(placement_drive_id=drive_id).order_by(Application.id.asc()).all()

        return jsonify({
            'placement_drive': {
                'id': drive.id,
                'job_title': drive.job_title,
                'job_description': drive.job_description,
                'salary_range': drive.salary_range,
                'key_skills': drive.key_skills,
                'drive_date': drive.drive_date.isoformat() if drive.drive_date else None,
                'drive_end_date': drive.drive_end_date.isoformat() if drive.drive_end_date else None,
                'status': drive.status,
                'is_approved': drive.is_approved
            },
            'applications': [{
                'id': a.id,
                'student_id': a.student_id,
                'student_name': a.student.full_name,
                'department': a.student.department,
                'roll_number': a.student.roll_number,
                'status': a.status
            } for a in applications]
        }), 200

#api route for companies and admin to change student status for a placement drive 
@company_bp.route('/change_student_application_status/<int:id>', methods=["GET",'POST'])
@admin_bp.route('/change_student_application_status/<int:id>', methods=['GET', 'POST'])
def change_student_application_status(id):
    if request.method == "GET":
        return render_template('company/change_student_application_status.html', application_id=id)

    if request.method == "POST":
        verify_jwt_in_request()

        current_user_id = int(get_jwt_identity())
        claims = get_jwt()
        role = claims.get('role')

        if role == "student":
            return jsonify({'error': 'Unauthorized access.'}), 403
        
        application = db.session.get(Application, id)
        data = request.get_json()
        new_status = data.get('status')
        new_status = new_status.lower().strip()

        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        if role == "company":
            drive = db.session.get(PlacementDrive, application.placement_drive_id)
            if not drive:
                return jsonify({'error': 'Placement drive not found'}), 404
                    
            company_allowed_options = ['shortlisted', 'interview scheduled', 'offer', 'rejected']

            if new_status not in company_allowed_options:
                return jsonify({'error': f'Companies can only transition status to: {", ".join(company_allowed_options)}'}), 400
            
            if new_status == 'interview complete' and application.status.lower() != 'shortlisted':
                return jsonify({'error': 'Cannot mark as Interview Complete unless the student is first Shortlisted.'}), 400

        elif role == 'admin':

            admin_allowed_options = ['shortlisted', 'interview scheduled', 'offer', 'rejected', 'inactive', 'placed']
            if new_status not in admin_allowed_options:
                return jsonify({'error': f'Admin can only transition status to: {", ".join(admin_allowed_options)}'}), 400

        application.status = new_status
        db.session.commit()

        return jsonify({
            'message': f'Application status successfully updated to {new_status}!',
            'application_id': application.id,
            'current_status': application.status
        }), 200

#api helper route to get student application details for companies and admin
@company_bp.route('/get_student_application/<int:id>', methods=['GET'])
@admin_bp.route('/get_student_application/<int:id>', methods=['GET'])
def get_student_application(id):

    verify_jwt_in_request()

    claims = get_jwt()
    role = claims.get('role')

    if role not in ['admin', 'company']:
        return jsonify({'error': 'Unauthorized access'}), 403

    application = db.session.get(Application, id)

    if not application:
        return jsonify({'error': 'Application not found'}), 404

    drive = application.placement_drive
    student = application.student

    return jsonify({
        'id': application.id,
        'status': application.status,
        'student': {
            'id': student.id,
            'full_name': student.full_name,
            'department': student.department,
            'roll_number': student.roll_number,
            'resume_path': student.resume_path
        },
        'placement_drive': {
            'id': drive.id,
            'job_title': drive.job_title
        }
    }), 200

#api route for company to schedule interviews 
@company_bp.route('/schedule_interview/<int:application_id>', methods=['GET', 'POST'])
def schedule_interview(application_id):
    if request.method == "GET":
        return render_template(
            'company/schedule_interview.html',
            application_id=application_id
        )

    verify_jwt_in_request()
    claims = get_jwt()

    if claims.get("role") != "company":
        return jsonify({"error": "Unauthorized access"}), 403

    company_id = int(get_jwt_identity())
    application = Application.query.get(application_id)

    if not application:
        return jsonify({"error": "Application not found"}), 404

    drive = application.placement_drive

    if drive.company_id != company_id:
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.get_json(silent=True) or {}

    if "interview_slot" not in data:
        if application.status.lower() != "shortlisted":
            return jsonify({
                "error": "Only shortlisted students can be scheduled for interviews."
            }), 400

        return jsonify({
            "application": {
                "id": application.id,
                "status": application.status,
                "student_id": application.student.id,
                "full_name": application.student.full_name,
                "department": application.student.department,
                "roll_number": application.student.roll_number,
                "email": application.student.email,
                "resume_path": application.student.resume_path,
                "drive_id": drive.id,
                "job_title": drive.job_title,
                "company_id": drive.company.id,
                "company_name": drive.company.company_name}
                }), 200

    interview_slot = data.get("interview_slot")
    application.status = "Interview Scheduled"
    db.session.commit()

    return jsonify({
        "message": "Interview scheduled successfully!",
        "application_id": application.id,
        "interview_slot": interview_slot,
        "current_status": application.status
    }), 200

#api route to post the intervew schedule in db
@company_bp.route('/create_interview/<int:application_id>', methods=['POST'])
def create_interview(application_id):
    verify_jwt_in_request()
    claims = get_jwt()

    if claims.get("role") != "company":
        return jsonify({"error": "Unauthorized access"}), 403

    company_id = int(get_jwt_identity())
    application = Application.query.get(application_id)

    if not application:
        return jsonify({"error": "Application not found"}), 404

    drive = application.placement_drive

    if drive.company_id != company_id:
        return jsonify({"error": "Unauthorized"}), 403

    existing = Interview.query.filter_by(
        application_id=application.id
    ).first()

    if existing:
        return jsonify({
            "error": "Interview already scheduled."
        }), 400

    data = request.get_json()

    interview = Interview(
        application_id=application.id,
        interview_date=datetime.strptime(
            data["interview_date"],
            "%Y-%m-%d"
        ).date(),
        interview_time=datetime.strptime(
            data["interview_time"],
            "%H:%M"
        ).time())

    db.session.add(interview)
    application.status = "Interview Scheduled"
    cache.delete(f"student_dashboard_{application.student_id}")
    db.session.commit()

    return jsonify({
        "message": "Interview scheduled successfully!"
    }), 201

#api route for student dashboard
@student_bp.route('/dashboard', methods=['GET', 'POST'])
def student_dashboard():
    if request.method == 'GET':
        return render_template('student/dashboard.html')
    
    if request.method == 'POST':
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get('role') != 'student':
            return jsonify({'error': "Unauthorized access"}), 403
        
        student_id = get_jwt_identity()
        cache_key = f"student_dashboard_{student_id}"
        cached_response = cache.get(cache_key)

        if cached_response:
            return jsonify(cached_response), 200
        applications = Application.query.filter_by(student_id=student_id).order_by(Application.id.asc()).all()
        ongoing_drives = PlacementDrive.query.filter(PlacementDrive.drive_date <= datetime.utcnow().date(), PlacementDrive.drive_end_date >= datetime.utcnow().date(), PlacementDrive.status == 'active', PlacementDrive.is_approved == True).all()
        upcoming_drives = PlacementDrive.query.filter(PlacementDrive.drive_date > datetime.utcnow().date(), PlacementDrive.status == 'active', PlacementDrive.is_approved == True).all()
        interviews = Interview.query.join(Application).filter(Application.student_id == student_id).order_by(Interview.interview_date.asc()).all()

        response = {'user_id': student_id,
                'applications': [{
                    'id': a.id,
                    'placement_drive_id': a.placement_drive_id,
                    'company_name': a.placement_drive.company.company_name,
                    'job_title': a.placement_drive.job_title,
                    'drive_date': a.placement_drive.drive_date.isoformat() if a.placement_drive.drive_date else None,
                    'drive_end_date': a.placement_drive.drive_end_date.isoformat() if a.placement_drive.drive_end_date else None,
                    'status': a.status,
                    'application_date': (a.application_date.isoformat() if a.application_date else None)
                } for a in applications], 
                'ongoing_drives': [{
                    'id': d.id,
                    'company_name': d.company.company_name,
                    'job_title': d.job_title,
                    'drive_date': d.drive_date.isoformat() if d.drive_date else None,
                    'drive_end_date': d.drive_end_date.isoformat() if d.drive_end_date else None,
                    'status': d.status
                } for d in ongoing_drives],
                'upcoming_drives': [{
                    'id': d.id,
                    'company_name': d.company.company_name,
                    'job_title': d.job_title,
                    'drive_date': d.drive_date.isoformat() if d.drive_date else None,
                    'drive_end_date': d.drive_end_date.isoformat() if d.drive_end_date else None,
                    'status': d.status
                } for d in upcoming_drives],
                'interviews': [{
                    'id': i.id,
                    'company_name': i.application.placement_drive.company.company_name,
                    'job_title': i.application.placement_drive.job_title,
                    'interview_date': i.interview_date.isoformat() if i.interview_date else None,
                    'interview_time': i.interview_time.strftime('%H:%M') if i.interview_time else None,
                    'interview_mode': i.interview_mode
                } for i in interviews]}

        cache.set(
                cache_key,
                response,
                timeout=300
            )

        return jsonify(response), 200

#api route for student to apply to a placement drive
@student_bp.route('/apply_to_drive/<int:drive_id>', methods=['GET', 'POST'])
def apply_to_drive(drive_id):

    drive = PlacementDrive.query.get(drive_id)

    if not drive:
        return jsonify({'error': 'Placement drive not found'}), 404

    if request.method == "GET":
        return render_template(
            'student/apply_to_drive.html',
            drive_id=drive.id,
            company_name=drive.company.company_name,
            about_company=drive.company.about_company,
            job_title=drive.job_title,
            job_description=drive.job_description,
            key_skills=drive.key_skills,
            salary_range=drive.salary_range,
            drive_date=drive.drive_date.isoformat() if drive.drive_date else '',
            drive_end_date=drive.drive_end_date.isoformat() if drive.drive_end_date else ''
        )

    verify_jwt_in_request()
    claims = get_jwt()

    if claims.get('role') != 'student':
        return jsonify({'error': 'Unauthorized access'}), 403

    student_id = get_jwt_identity()
    student = Student.query.get(student_id)

    if not student:
        return jsonify({'error': 'Student not found'}), 404

    if student.cgpa < drive.required_cgpa:
        return jsonify({
            'error': f'You are not eligible. Minimum CGPA required is {drive.required_cgpa}.'
        }), 403

    existing_application = Application.query.filter_by(
        student_id=student_id,
        placement_drive_id=drive_id
    ).first()

    if existing_application:
        return jsonify({
            'error': 'You have already applied to this placement drive.'
        }), 400

    new_application = Application(
        student_id=student_id,
        placement_drive_id=drive_id,
        status='applied'
    )

    db.session.add(new_application)
    db.session.commit()
    cache.delete(f"student_dashboard_{student_id}")

    return jsonify({
        'message': 'Application submitted successfully!',
        'application_id': new_application.id
    }), 201

#api route for student to view their application details
@student_bp.route('/view_application/<int:application_id>', methods=['GET', 'POST'])
def view_application(application_id):
    if request.method == 'GET':
        return render_template('student/view_application.html', application_id=application_id)

    if request.method == 'POST':
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get('role') != 'student':
            return jsonify({'error': "Unauthorized access"}), 403
        
        student_id = int(get_jwt_identity())
        application = Application.query.get(application_id)

        if not application or application.student_id != student_id:
            return jsonify({'error': 'Application not found or access denied'}), 404

        drive = application.placement_drive
        company = drive.company

        return jsonify({
            'id': application.id,
            'application_date': application.application_date.isoformat() if application.application_date else None,
            'status': application.status,
            'resume_path': application.student.resume_path,
            'student': {
                'id': application.student.id,
                'full_name': application.student.full_name,
                'department': application.student.department,
                'roll_number': application.student.roll_number,
                'resume': application.student.resume_path
            },
            'placement_drive': {
                'id': drive.id,
                'job_title': drive.job_title,
                'job_description': drive.job_description,
                'salary_range': drive.salary_range,
                'key_skills': drive.key_skills,
                'drive_date': drive.drive_date.isoformat() if drive.drive_date else None,
                'drive_end_date': drive.drive_end_date.isoformat() if drive.drive_end_date else None,
                'status': drive.status,
                'is_approved': drive.is_approved
            },
            'company': {
                'id': company.id,
                'company_name': company.company_name,
                'about_company': company.about_company
            }
            }), 200
    
# Common Edit Profile Route
@company_bp.route('/edit_profile/<int:id>', methods=['GET', 'POST', 'PUT'])
@student_bp.route('/edit_profile/<int:id>', methods=['GET', 'POST', 'PUT'])
def edit_profile(id):
    if request.method == "GET":
        return render_template(
            "student/edit_profile.html",
            user_id=id
        )

    verify_jwt_in_request()

    claims = get_jwt()
    role = claims.get("role")
    user_id = int(get_jwt_identity())

    if user_id != id:
        return jsonify({
            "error": "Unauthorized access."
        }), 403

    if request.method == "POST":
        if role == "student":
            student = Student.query.get(id)
            if not student:
                return jsonify({
                    "error": "Student not found."
                }), 404

            return jsonify({
                "id": student.id,
                "full_name": student.full_name,
                "email": student.email,
                "phone_number": student.phone_number,
                "roll_number": student.roll_number,
                "department": student.department,
                "cgpa": student.cgpa,
                "resume_path": student.resume_path
            }), 200


        elif role == "company":
            company = Company.query.get(id)
            if not company:
                return jsonify({
                    "error": "Company not found."
                }), 404

            return jsonify({
                "id": company.id,
                "company_name": company.company_name,
                "full_name": company.full_name,
                "email": company.email,
                "phone_number": company.phone_number,
                "about_company": company.about_company
            }), 200

        return jsonify({
            "error": "Invalid role."
        }), 403

    if request.method == "PUT":
        data = request.form
        if role == "student":
            student = Student.query.get(id)
            if not student:
                return jsonify({
                    "error": "Student not found."
                }), 404

            student.full_name = data.get("full_name")
            student.email = data.get("email")
            student.phone_number = data.get("phone_number")
            student.cgpa = float(data.get("cgpa"))
            resume = request.files.get("resume")

            if resume:
                filename = secure_filename(
                    f"student_{student.id}.pdf"
                )

                upload_folder = os.path.join(
                    current_app.static_folder,
                    "uploads",
                    "resumes"
                )

                os.makedirs(upload_folder, exist_ok=True)
                
                file_path = os.path.join(
                    upload_folder,
                    filename
                )

                # overwrite previous resume
                resume.save(file_path)
                student.resume_path = filename
            db.session.commit()
            cache.delete(f"student_dashboard_{student.id}")

            return jsonify({
                "message": "Profile updated successfully."
            }), 200


        elif role == "company":
            company = Company.query.get(id)
            if not company:
                return jsonify({
                    "error": "Company not found."
                }), 404

            company.full_name = data.get("full_name")
            company.email = data.get("email")
            company.phone_number = data.get("phone_number")
            company.about_company = data.get("about_company")

            db.session.commit()

            return jsonify({
                "message": "Profile updated successfully."
            }), 200

        return jsonify({
            "error": "Invalid role."
        }), 403
    
#api route for admin to view student profile
@admin_bp.route('/student_profile/<int:id>', methods=['GET', 'POST'])
def student_profile(id):
    if request.method == "GET":
        return render_template("admin/view_student_profile.html", student_id=id)

    if request.method == "POST":
        verify_jwt_in_request()
        claims = get_jwt()

        if claims.get("role") != "admin":
            return jsonify({"error": "Unauthorized access."}), 403

        student = Student.query.get(id)

        if not student:
            return jsonify({"error": "Student not found."}), 404

        applications = Application.query.filter_by(student_id=id).order_by(Application.id.asc()).all()

        return jsonify({
            "id": student.id,
            "full_name": student.full_name,
            "email": student.email,
            "phone_number": student.phone_number,
            "department": student.department,
            "roll_number": student.roll_number,
            "cgpa": student.cgpa,
            "resume_path": student.resume_path,
            "applications": [{
                "application_id": a.id,
                "company_name": a.placement_drive.company.company_name,
                "job_title": a.placement_drive.job_title,
                "status": a.status,
                "application_date": a.application_date.isoformat() if a.application_date else None
            } for a in applications]
        }), 200
    
#common search api for students and admin    
@auth_bp.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "GET":
        return render_template("search_result.html")
    
    verify_jwt_in_request()
    claims = get_jwt()
    role = claims.get("role")
    user_id = int(get_jwt_identity())

    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({
            "students": [],
            "companies": [],
            "drives": [],
            "applications": []
        }), 200

    students = []
    companies = []
    drives = []
    applications = []

    if role == "student":
        companies = Company.query.filter(Company.company_name.ilike(f"%{query}%")).all()

        drives = PlacementDrive.query.filter(db.or_(PlacementDrive.job_title.ilike(f"%{query}%"), 
                                                    PlacementDrive.key_skills.ilike(f"%{query}%"),
                                                    PlacementDrive.status.ilike(f"%{query}%")),PlacementDrive.is_approved == True).all()

    elif role == "company":
        drives = PlacementDrive.query.filter(PlacementDrive.company_id == user_id, db.or_(PlacementDrive.job_title.ilike(f"%{query}%"), PlacementDrive.key_skills.ilike(f"%{query}%"), PlacementDrive.status.ilike(f"%{query}%"))).all()

        applications = Application.query.join(Student).join(PlacementDrive).filter(PlacementDrive.company_id == user_id,
            db.or_(Student.full_name.ilike(f"%{query}%"), Student.department.ilike(f"%{query}%"), Student.roll_number.ilike(f"%{query}%"), Application.status.ilike(f"%{query}%"))).all()

    elif role == "admin":
        students = Student.query.filter(
            db.or_(Student.full_name.ilike(f"%{query}%"),Student.department.ilike(f"%{query}%"),
                   Student.roll_number.ilike(f"%{query}%"),Student.email.ilike(f"%{query}%"))).all()

        companies = Company.query.filter(db.or_(Company.company_name.ilike(f"%{query}%"),Company.email.ilike(f"%{query}%"))).all()

        drives = PlacementDrive.query.join(Company).filter(
            db.or_(PlacementDrive.job_title.ilike(f"%{query}%"),PlacementDrive.key_skills.ilike(f"%{query}%"),
                   PlacementDrive.status.ilike(f"%{query}%"),
                   Company.company_name.ilike(f"%{query}%"))).all()

        applications = Application.query.join(Student).join(PlacementDrive).join(Company).filter(
            db.or_(Student.full_name.ilike(f"%{query}%"), Company.company_name.ilike(f"%{query}%"), 
                   PlacementDrive.job_title.ilike(f"%{query}%"), 
                   Application.status.ilike(f"%{query}%"))).all()

    else:
        return jsonify({
            "error": "Unauthorized access."
        }), 403

    return jsonify({
        "students": [{
            "id": s.id,
            "full_name": s.full_name,
            "department": s.department,
            "roll_number": s.roll_number,
            "email": s.email
        } for s in students],

        "companies": [{
            "id": c.id,
            "company_name": c.company_name,
            "email": c.email,
            "status": c.status
        } for c in companies],

        "drives": [{
            "id": d.id,
            "company_name": d.company.company_name,
            "job_title": d.job_title,
            "drive_date": d.drive_date.isoformat() if d.drive_date else None,
            "drive_end_date": d.drive_end_date.isoformat() if d.drive_end_date else None,
            "status": d.status
        } for d in drives],

        "applications": [{
            "id": a.id,
            "student_name": a.student.full_name,
            "company_name": a.placement_drive.company.company_name,
            "job_title": a.placement_drive.job_title,
            "status": a.status
        } for a in applications]}), 200

@student_bp.route("/export_csv", methods=["POST"])
def export_csv():
    verify_jwt_in_request()
    claims = get_jwt()

    from task import export_student_applications

    if claims.get("role") != "student":
        return jsonify({
            "error": "Unauthorized access"
        }), 403

    student_id = int(get_jwt_identity())
    task = export_student_applications.delay(student_id)
    print(task.id)

    return jsonify({
        "message": "Export started.",
        "task_id": task.id
    }), 202

@student_bp.route("/export_status/<task_id>", methods=["GET"])
def export_status(task_id):
    verify_jwt_in_request()
    from app import celery

    result = celery.AsyncResult(task_id)

    if result.ready():
        return jsonify({
            "completed": True,
            "filename": result.result["filename"]
        })

    return jsonify({
        "completed": False
    })

@student_bp.route("/test_mail")
def test_mail():

    from flask_mail import Message
    from backend.mail_config import mail

    msg = Message(
        subject="PDMS Test Email",
        recipients=["22f2000902@ds.study.iitm.ac.in"]
    )

    msg.body = "Congratulations! Flask-Mail is working."

    mail.send(msg)

    return "Mail Sent!"