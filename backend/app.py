from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class CourseRequest(BaseModel):
    url:str

@app.get("/")
def home():
    return {"message":"Coursemind backend is running!"}


@app.post("/course")
def add_course(course:CourseRequest):
    return{
        "massage":"course URL received",
        "url":course.url
    }