import csv
import os
from flask import current_app
from app import celery
from backend.models import Application
from datetime import date, timedelta, datetime
from flask_mail import Message
from backend.mail_config import mail
from backend.models import PlacementDrive, Student, Application, Interview, Admin

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

@celery.task
def monthly_report():
    today = datetime.today()
    first_day = today.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    drives_conducted = PlacementDrive.query.filter(
        PlacementDrive.drive_date >= first_day.date(),
        PlacementDrive.drive_date <= today.date()
    ).count()

    students_applied = Application.query.filter(
        Application.application_date >= first_day
    ).count()

    students_selected = Application.query.filter_by(
        status="offer"
    ).count()

    admin = Admin.query.first()

    if not admin:
        return

    html = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            table {{
                border-collapse: collapse;
                width: 60%;
            }}
            th, td {{
                border: 1px solid black;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>

    <body>

    <h2>Monthly Placement Activity Report</h2>

    <p>Hello Admin,</p>

    <p>Please find this month's placement activity summary below.</p>

    <table>
        <tr>
            <th>Metric</th>
            <th>Count</th>
        </tr>

        <tr>
            <td>Placement Drives Conducted</td>
            <td>{drives_conducted}</td>
        </tr>

        <tr>
            <td>Students Applied</td>
            <td>{students_applied}</td>
        </tr>

        <tr>
            <td>Students Selected</td>
            <td>{students_selected}</td>
        </tr>
    </table>

    <br>

    <p>Regards,<br>
    Placement Drive Management System (PDMS)</p>

    </body>
    </html>
    """

    msg = Message(
        subject="Monthly Placement Activity Report",
        recipients=[admin.email]
    )

    msg.html = html

    mail.send(msg)