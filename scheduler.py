from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
import database
import email_service
from datetime import datetime
import os

def check_and_send_reminders():
    db = database.SessionLocal()
    now = datetime.now()
    
    # Find reminders that are due and not yet sent
    due_reminders = db.query(database.Reminder).filter(
        database.Reminder.reminder_time <= now,
        database.Reminder.is_sent == False
    ).all()

    for r in due_reminders:
        task = r.task
        print(f"Sending reminder for task: {task.description}")
        
        # In a real app, you'd have the user's email in the task or user model
        # For MVP, we'll use an env variable or a placeholder
        target_email = os.getenv("TARGET_EMAIL", "your_email@example.com")
        
        subject = f"Friendly Reminder: {task.description[:30]}..."
        body = f"Hi!\n\nJust a friendly nudge: {r.message_type}\n\nTask: {task.description}\nDeadline: {task.end_date.strftime('%Y-%m-%d')}\n\nKeep going, you've got this!"
        
        success = email_service.send_reminder_email(target_email, subject, body)
        
        if success:
            r.is_sent = True
            db.commit()
    
    db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Check every minute for MVP purposes (can be hourly later)
    scheduler.add_job(check_and_send_reminders, 'interval', minutes=1)
    scheduler.start()
    print("Scheduler started...")
