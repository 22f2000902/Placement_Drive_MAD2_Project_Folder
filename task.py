import csv
import os
from flask import current_app
from app import celery
from backend.models import Application
from datetime import date, timedelta
from flask_mail import Message
from backend.mail_config import mail
from backend.models import PlacementDrive, Student, Application, Interview

@celery.task
def export_student_applications(student_id):

    applications = Application.query.filter_by(
        student_id=student_id
    ).order_by(Application.id.asc()).all()

    export_folder = os.path.join(
        current_app.static_folder,
        "exports"
    )

    os.makedirs(export_folder, exist_ok=True)

    filename = f"student_{student_id}_applications.csv"

    file_path = os.path.join(
        export_folder,
        filename
    )

    with open(file_path, "w", newline="", encoding="utf-8") as csv_file:

        writer = csv.writer(csv_file)

        writer.writerow([
            "Student ID",
            "Company Name",
            "Drive Title",
            "Application Status",
            "Application Date",
            "Drive Date"
        ])

        for application in applications:

            writer.writerow([
                application.student_id,
                application.placement_drive.company.company_name,
                application.placement_drive.job_title,
                application.status,
                application.application_date.strftime("%Y-%m-%d") if application.application_date else "",
                application.placement_drive.drive_date.strftime("%Y-%m-%d") if application.placement_drive.drive_date else ""
            ])

    return {
        "status": "completed",
        "filename": filename
    }

@celery.task
def daily_reminder():
    tomorrow = date.today() + timedelta(days=1)
    drives = PlacementDrive.query.filter(
        PlacementDrive.drive_end_date <= tomorrow,
        PlacementDrive.status == "active",
        PlacementDrive.is_approved == True
    ).all()

    for drive in drives:
        students = Student.query.filter_by(is_active=True).all()
        for student in students:
            already_applied = Application.query.filter_by(
                student_id=student.id,
                placement_drive_id=drive.id
            ).first()
            if already_applied:
                continue
            msg = Message(
                subject="Placement Drive Reminder",
                recipients=[student.email]
            )

            msg.body = f"""
                Hello {student.full_name},
                Reminder!
                Applications for {drive.job_title} at {drive.company.company_name} close on {drive.drive_end_date}.
                Please apply before the deadline.

                Regards,
                PDMS
                """

            mail.send(msg)
    
    interviews = Interview.query.filter(
        Interview.interview_date <= tomorrow).all()

    for interview in interviews:
        application = interview.application
        student = application.student

        msg = Message(
            subject="Interview Reminder",
            recipients=[student.email]
        )

        msg.body = f"""
            Hello {student.full_name},
            This is a reminder that you have an interview.

            Company:
            {application.placement_drive.company.company_name}
            Role:
            {application.placement_drive.job_title}
            Date:
            {interview.interview_date}
            Time:
            {interview.interview_time}
            Mode:
            {interview.interview_mode}

            Best of luck!
            PDMS
            """

        mail.send(msg)