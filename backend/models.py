from backend.database import db 
from datetime import datetime

class Admin(db.Model): 
    __tablename__ = 'College Admin'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(250), nullable=False)
    role = db.Column(db.String(20), default='admin')

class Student(db.Model): 
    __tablename__ = 'Students'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(250), nullable=False)
    phone_number = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    resume_path = db.Column(db.String(250), nullable=True)
    cgpa = db.Column(db.Float, nullable=False)

    applications = db.relationship('Application', backref='student', lazy=True)

class Company(db.Model): 
    __tablename__ = 'Companies'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    password_hash = db.Column(db.String(250), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    about_company = db.Column(db.String(1050), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')
    is_blacklisted = db.Column(db.Boolean, default=False)

    placementdrive = db.relationship('PlacementDrive', backref='company', lazy=True)

class PlacementDrive(db.Model): 
    __tablename__ = 'Placement Drives'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey(Company.id), nullable=False)
    drive_date = db.Column(db.Date, nullable=False)
    drive_end_date = db.Column(db.Date, nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.String(1050), nullable=False)
    salary_range = db.Column(db.String(100), nullable=False)
    key_skills = db.Column(db.String(250), nullable=False)
    required_cgpa = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='inactive')
    is_approved = db.Column(db.Boolean, default=False)

    application = db.relationship('Application', backref='placement_drive', lazy=True)

class Application(db.Model): 
    __tablename__ ='Student Applications' 
    __table_args__ = (db.UniqueConstraint('student_id', 'placement_drive_id', name='unique_application'),)

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey(Student.id), nullable=False)
    placement_drive_id = db.Column(db.Integer, db.ForeignKey(PlacementDrive.id), nullable=False)
    application_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Submitted')
    application_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow) 
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

class Interview(db.Model):
    __tablename__ = "Interviews"

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey(Application.id), nullable=False, unique=True)
    interview_date = db.Column(db.Date, nullable=False)
    interview_time = db.Column(db.Time, nullable=False)
    interview_mode = db.Column(db.String(30),default='Online', nullable=False)
    meeting_link = db.Column(db.String(500))
    venue = db.Column(db.String(250))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    application = db.relationship("Application", backref="interview")

