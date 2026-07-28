from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, ai, courses
from database import engine
from models.models import Base

app = FastAPI(title="EduForge LMS")

# Create tables
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("All database tables created!")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(courses.router)

@app.get("/")
async def root():
    return {"message": "EduForge LMS Backend Running!"}