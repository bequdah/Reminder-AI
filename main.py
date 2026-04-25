from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import database
import ai_service
import scheduler
import os
from datetime import datetime

app = FastAPI(title="AI Smart Deadline Reminder")

# Mount static files
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize database and scheduler on startup
@app.on_event("startup")
def startup():
    database.init_db()
    scheduler.start_scheduler()

@app.get("/")
def serve_home():
    return FileResponse("static/index.html")

@app.get("/tasks-page")
def tasks_page():
    return FileResponse("static/tasks.html")

# Dependency to get the DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Pydantic Models ---
class ReminderUpdate(BaseModel):
    date: str
    friendly_message: str

# --- TASK ENDPOINTS ---

@app.post("/tasks/")
def create_task(
    user_input: str = Body(..., embed=True), 
    chat_history: list = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    parsed_data = ai_service.parse_task_description(user_input, chat_history)
    
    if not parsed_data:
        raise HTTPException(status_code=400, detail="AI could not understand the task. Please be more specific with dates.")

    try:
        s_date_str = parsed_data['start_date'].split(' ')[0]
        e_date_str = parsed_data['end_date'].split(' ')[0]
        start_date = datetime.strptime(s_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(e_date_str, "%Y-%m-%d")
        duration = (end_date - start_date).days
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format from AI: {parsed_data.get('start_date')} | {e}")

    new_task = database.Task(
        description=user_input,
        start_date=start_date,
        end_date=end_date,
        duration_days=duration,
        effort_level=parsed_data['effort_level']
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {
        "status": "Task Analyzed",
        "ai_summary": parsed_data['brief_summary'],
        "suggested_reminders": parsed_data['suggested_reminders'],
        "task_details": {
            "id": new_task.id,
            "start": new_task.start_date,
            "end": new_task.end_date,
            "duration": new_task.duration_days,
            "effort": new_task.effort_level
        }
    }

@app.get("/api/tasks-full")
def get_tasks_full(db: Session = Depends(get_db)):
    tasks = db.query(database.Task).all()
    result = []
    for task in tasks:
        reminders = db.query(database.Reminder).filter(database.Reminder.task_id == task.id).all()
        result.append({
            "id": task.id,
            "description": task.description,
            "start_date": task.start_date.isoformat() if task.start_date else None,
            "end_date": task.end_date.isoformat() if task.end_date else None,
            "duration_days": task.duration_days,
            "effort_level": task.effort_level,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "reminders": [{
                "id": r.id,
                "reminder_time": r.reminder_time.isoformat() if r.reminder_time else None,
                "message_type": r.message_type,
                "is_sent": r.is_sent
            } for r in reminders]
        })
    return result

@app.post("/tasks/{task_id}/confirm")
def confirm_reminders(task_id: int, reminders: list = Body(...), db: Session = Depends(get_db)):
    task = db.query(database.Task).filter(database.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.query(database.Reminder).filter(database.Reminder.task_id == task_id).delete()
    for r in reminders:
        new_reminder = database.Reminder(
            task_id=task_id,
            reminder_time=datetime.strptime(r['date'], "%Y-%m-%d"),
            message_type=r['friendly_message'],
            is_sent=False
        )
        db.add(new_reminder)
    db.commit()
    return {"status": "success", "message": f"{len(reminders)} reminders scheduled."}

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(database.Task).filter(database.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.query(database.Reminder).filter(database.Reminder.task_id == task_id).delete()
    db.delete(task)
    db.commit()
    return {"status": "success", "message": "Task and reminders deleted."}

# --- REMINDER ENDPOINTS ---

@app.post("/tasks/{task_id}/reminders")
def add_reminder(task_id: int, reminder: ReminderUpdate, db: Session = Depends(get_db)):
    task = db.query(database.Task).filter(database.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    new_reminder = database.Reminder(
        task_id=task_id,
        reminder_time=datetime.strptime(reminder.date, "%Y-%m-%d"),
        message_type=reminder.friendly_message,
        is_sent=False
    )
    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)
    return {"status": "success", "id": new_reminder.id}

@app.put("/reminders/{reminder_id}")
def update_reminder(reminder_id: int, reminder: ReminderUpdate, db: Session = Depends(get_db)):
    r = db.query(database.Reminder).filter(database.Reminder.id == reminder_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found")
    r.reminder_time = datetime.strptime(reminder.date, "%Y-%m-%d")
    r.message_type = reminder.friendly_message
    r.is_sent = False  # Reset sent status after edit
    db.commit()
    return {"status": "success"}

@app.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    r = db.query(database.Reminder).filter(database.Reminder.id == reminder_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(r)
    db.commit()
    return {"status": "success"}
