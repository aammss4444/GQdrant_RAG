from fastapi import FastAPI, HTTPException, Depends, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base, Conversation, Message
from . import database
import sys
import os
import io
import time

# Add parent directory to sys.path to import retrieve.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import retrieve

from pypdf import PdfReader
from pydantic import BaseModel
from typing import List, Optional

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class MessageSchema(BaseModel):
    id: int
    sender: str
    content: str
    created_at: str

    class Config:
        orm_mode = True

class ConversationSchema(BaseModel):
    id: int
    title: str
    created_at: str
    messages: List[MessageSchema] = []

    class Config:
        orm_mode = True


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(f"[Page {i+1}]\n{text}")
    return "\n\n".join(pages_text)


@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    conversation_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    user_message = message
    has_attachment = False
    attachment_name = None
    pdf_context = ""

    # Extract PDF text if a file was uploaded
    if file and file.filename and file.filename.lower().endswith(".pdf"):
        has_attachment = True
        attachment_name = file.filename
        try:
            file_bytes = await file.read()
            pdf_context = extract_pdf_text(file_bytes)
            print(f"Extracted {len(pdf_context)} chars from PDF: {attachment_name}")
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            pdf_context = f"[Error reading PDF: {e}]"

    # Create new conversation if not provided
    if not conversation_id:
        conversation = Conversation(title=user_message[:30] + "...")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id
    else:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message (include attachment indicator)
    display_content = user_message
    if has_attachment:
        display_content = f"📎 {attachment_name}\n\n{user_message}"
    db_message = Message(conversation_id=conversation_id, sender="user", content=display_content)
    db.add(db_message)
    db.commit()

    # Get RAG response
    try:
        search_results = retrieve.search(user_message)
        # Construct context from search results
        rag_context = "\n\n".join([f"Source: {res['source']}\nContent: {res['text']}" for res in search_results])

        # Build the full prompt with both RAG context and PDF context
        prompt_parts = []
        prompt_parts.append("Answer the user query based on the following context:\n")

        if pdf_context:
            prompt_parts.append(f"--- Attached PDF Content ---\n{pdf_context}\n--- End of PDF ---\n")

        if rag_context:
            prompt_parts.append(f"--- Knowledge Base Context ---\n{rag_context}\n--- End of Knowledge Base ---\n")

        prompt_parts.append(f"Query: {user_message}")
        prompt = "\n".join(prompt_parts)

        response = None
        last_error = None
        for model_name in ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']:
            try:
                print(f"Generating content with model: {model_name}")
                model = retrieve.genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response:
                    break
            except Exception as e:
                print(f"Error generating with {model_name}: {e}")
                last_error = e
                time.sleep(1)

        if not response:
            raise last_error if last_error else Exception("Failed to generate content with any model")

        bot_response = response.text

    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        print(f"Error during RAG/Generation: {e}")
        print(tb_str)
        bot_response = f"I'm sorry, I encountered an error: {str(e)}\n\nTraceback:\n{tb_str}"

    # Save bot message
    db_bot_message = Message(conversation_id=conversation_id, sender="bot", content=bot_response)
    db.add(db_bot_message)
    db.commit()

    return {
        "response": bot_response,
        "conversation_id": conversation_id,
        "search_results": search_results if 'search_results' in dir() else [],
        "has_attachment": has_attachment,
        "attachment_name": attachment_name,
    }

@app.get("/api/conversations", response_model=List[ConversationSchema])
def get_conversations(db: Session = Depends(get_db)):
    conversations = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
    return conversations

@app.get("/api/conversations/{conversation_id}", response_model=ConversationSchema)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted"}
