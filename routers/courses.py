from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.models import Course, User, Enrollment
from schemas.schemas import CourseBase, CourseResponse
from routers.auth import oauth2_scheme, get_current_user
import requests
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from pydantic import EmailStr

router = APIRouter(prefix="/courses", tags=["Courses"])

# Free Courses API (Example)
FREE_COURSES_API = "https://www.udemy.com/api-2.0/courses/?page_size=12&price=free"

# Email Config (Neon ke saath .env mein add karo)
conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("EMAIL_USER"),
    MAIL_PASSWORD = os.getenv("EMAIL_PASS"),
    MAIL_FROM = os.getenv("EMAIL_USER"),
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

@router.get("/my")
async def get_my_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can view their courses")
    courses = db.query(Course).filter(Course.instructor_id == current_user.id).all()
    return courses

@router.get("/{course_id}")
async def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    instructor = db.query(User).filter(User.id == course.instructor_id).first()
    return {
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "thumbnail": course.thumbnail,
        "instructor_id": course.instructor_id,
        "instructor_name": instructor.name if instructor else "Unknown",
        "created_at": course.created_at.isoformat() if course.created_at else None
    }

@router.post("/{course_id}/enroll")
async def enroll_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    existing = db.query(Enrollment).filter(
        Enrollment.user_id == current_user.id,
        Enrollment.course_id == course_id
    ).first()
    
    if existing:
        return {"message": "Already enrolled"}

    enrollment = Enrollment(user_id=current_user.id, course_id=course_id)
    db.add(enrollment)
    db.commit()

    # Send Email Notification
    try:
        html = f"""
        <h2>Congratulations {current_user.name}!</h2>
        <p>You have successfully enrolled in: <strong>{course.title}</strong></p>
        <br>
        <a href="#" 
           style="background:#3b82f6;color:white;padding:12px 24px;text-decoration:none;border-radius:8px;">
           Start Learning Now
        </a>
        """
        message = MessageSchema(
            subject=f"Enrollment Confirmed: {course.title}",
            recipients=[current_user.email],
            body=html,
            subtype="html"
        )
        fm = FastMail(conf)
        await fm.send_message(message)
    except:
        pass  # Agar email fail ho to bhi enrollment success rahe

    return {"message": "Successfully enrolled! Check your email."}

@router.get("/")
async def get_all_courses(db: Session = Depends(get_db)):
    # Pehle database se courses lo
    db_courses = db.query(Course).all()
    
    if not db_courses:
        # Agar database khali hai to free API se fetch karke save kar do
        try:
            response = requests.get(FREE_COURSES_API)
            data = response.json()
            
            for item in data.get("results", [])[:8]:  # Sirf 8 courses
                existing = db.query(Course).filter(Course.title == item["title"]).first()
                if not existing:
                    new_course = Course(
                        title=item["title"],
                        description=item.get("headline", "No description available"),
                        thumbnail=item.get("image_480x270"),
                        instructor_id=1
                    )
                    db.add(new_course)
            db.commit()
            db_courses = db.query(Course).all()
        except:
            pass  # Agar API fail ho to dummy courses use karo

    return db_courses

@router.post("/", response_model=CourseResponse)
async def create_course(
    course: CourseBase, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "instructor":
        raise HTTPException(status_code=403, detail="Only instructors can create courses")
    
    new_course = Course(
        title=course.title,
        description=course.description,
        thumbnail=course.thumbnail or "https://picsum.photos/id/1015/400/300",
        instructor_id=current_user.id
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return new_course