from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base, Conversation, Message
from . import database
import sys
import os

# Add parent directory to sys.path to import retrieve.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import retrieve

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

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None

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

@app.post("/api/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    user_message = request.message
    conversation_id = request.conversation_id

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

    # Save user message
    db_message = Message(conversation_id=conversation_id, sender="user", content=user_message)
    db.add(db_message)
    db.commit()

    # Get RAG response
    # Use retrieve.search to get relevant documents
    try:
        search_results = retrieve.search(user_message)
        # Construct context from search results
        context = "\n\n".join([f"Source: {res['source']}\nContent: {res['text']}" for res in search_results])
        
        # In a real scenario, we would send this context to Gemini to generate an answer.
        # For now, let's just return the top result or a summary.
        # The original code just printed results. We need retrieve.py to return them.
        # Assuming retrieve.py is modified to return a list of dicts.
        
        # Let's actually generate a response using Gemini if possible, but retrieve.py currently only retrieves.
        # Implementation plan said: "Handles user messages, performs RAG using retrieve.py, and returns bot response."
        # We need to add generation logic here or in `retrieve.py`.
        # `retrieve.py` has `genai` configured.
        
        try:
           model = retrieve.genai.GenerativeModel('gemini-2.5-pro')
        except:
           try:
               model = retrieve.genai.GenerativeModel('gemini-1.5-pro')
           except:
               model = retrieve.genai.GenerativeModel('gemini-1.5-flash')
           
        prompt = f"Answer the user query based on the following context:\n\n{context}\n\nQuery: {user_message}"
        response = model.generate_content(prompt)
        bot_response = response.text
        
    except Exception as e:
        print(f"Error during RAG/Generation: {e}")
        bot_response = "I'm sorry, I encountered an error processing your request."

    # Save bot message
    db_bot_message = Message(conversation_id=conversation_id, sender="bot", content=bot_response)
    db.add(db_bot_message)
    db.commit()

    return {
        "response": bot_response,
        "conversation_id": conversation_id,
        "search_results": search_results
    }

@app.get("/api/conversations", response_model=List[ConversationSchema])
def get_conversations(db: Session = Depends(get_db)):
    conversations = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
    # Simple serialization to avoid huge payloads if messages are joined
    # Actually schema includes messages by default? No, we should probably exclude messages for list view.
    # But for now, let's keep it simple.
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
