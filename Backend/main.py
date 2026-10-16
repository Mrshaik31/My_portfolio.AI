from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag import generate_answer
from dotenv import load_dotenv

load_dotenv()


# ==========================================
# CREATE FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="Farhan's Portfolio AI Assistant",
    description="RAG-powered chatbot for my personal portfolio",
    version="1.0.0"
)


# ==========================================
# CORS CONFIGURATION
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ==========================================
# REQUEST MODEL
# ==========================================

class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Question about Farhan's portfolio"
    )


# ==========================================
# ROOT ENDPOINT
# ==========================================

@app.get("/")
def home():
    return {
        "message": "Farhan's Portfolio AI Assistant API is running",
        "status": "active"
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "portfolio-chatbot"
    }


# ==========================================
# CHAT ENDPOINT
# ==========================================

@app.post("/chat")
def chat(request: ChatRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    try:
        answer = generate_answer(question)

        return {
            "question": question,
            "answer": answer
        }
    except Exception:
        import logging
        logging.exception("Chatbot answer generation failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to generate an answer. Please try again later."
        )