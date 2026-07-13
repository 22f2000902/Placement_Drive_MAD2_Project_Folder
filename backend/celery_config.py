from celery import Celery
from celery.schedules import crontab

def make_celery(app):

    celery = Celery(
        app.import_name,
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0"
    )

    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask

    celery.conf.beat_schedule = {
        "daily-placement-reminders": {
            "task": "task.daily_reminder",
            "schedule": crontab(hour=2, minute=50)
        },
        "monthly-placement-report": {
            "task": "task.monthly_report",
            "schedule": crontab(hour=2, minute=50)
        }
    }
    celery.conf.timezone = "Asia/Kolkata"
    return celery