from fastapi import FastAPI, HTTPException, Depends, Form, File, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base, Conversation, Message, User
from . import database
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import sys
import os
import io
import time
import pytesseract
from PIL import Image

# Configure tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

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

# JWT and Security variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-that-should-be-in-env")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

class MessageSchema(BaseModel):
    id: int
    sender: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationSchema(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: List[MessageSchema] = []

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    password: str

MAX_PDF_CHARS = 8000  # Limit PDF text to avoid slow Gemini responses

@app.post("/api/auth/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()  # form_data.username will be the email
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf, truncated to MAX_PDF_CHARS."""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = []
    total_len = 0
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(f"[Page {i+1}]\n{text}")
            total_len += len(text)
            if total_len >= MAX_PDF_CHARS:
                break
    full_text = "\n\n".join(pages_text)
    if len(full_text) > MAX_PDF_CHARS:
        full_text = full_text[:MAX_PDF_CHARS] + "\n\n[... truncated for speed ...]"
    return full_text


@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    conversation_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_message = message
    has_attachment = False
    attachment_name = None
    pdf_context = ""
    image_ocr_text = ""
    image_parts = None

    # Handle uploaded file
    if file and file.filename:
        filename_lower = file.filename.lower()
        if filename_lower.endswith(".pdf"):
            has_attachment = True
            attachment_name = file.filename
            try:
                file_bytes = await file.read()
                pdf_context = extract_pdf_text(file_bytes)
                print(f"Extracted {len(pdf_context)} chars from PDF: {attachment_name}")
            except Exception as e:
                print(f"Error extracting PDF text: {e}")
                pdf_context = f"[Error reading PDF: {e}]"
        elif filename_lower.endswith((".png", ".jpg", ".jpeg", ".webp", ".heic", ".heif")):
            has_attachment = True
            attachment_name = file.filename
            try:
                file_bytes = await file.read()
                
                # Extract text using Tesseract OCR
                try:
                    img = Image.open(io.BytesIO(file_bytes))
                    extracted_text = pytesseract.image_to_string(img)
                    if extracted_text.strip():
                        image_ocr_text = extracted_text.strip()
                        print(f"Extracted {len(image_ocr_text)} chars using OCR")
                except Exception as ocr_err:
                    print(f"Error extracting text from image with OCR: {ocr_err}")
                
                image_parts = [
                    {
                        "mime_type": file.content_type or "image/jpeg",
                        "data": file_bytes
                    }
                ]
                print(f"Loaded image: {attachment_name}")
            except Exception as e:
                print(f"Error reading image: {e}")

    # Create new conversation if not provided
    if not conversation_id:
        conversation = Conversation(title=user_message[:30] + "...", user_id=current_user.id)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id
    else:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # Save user message (include attachment indicator)
    display_content = user_message
    if has_attachment:
        display_content = f"📎 {attachment_name}\n\n{user_message}"
    db_message = Message(conversation_id=conversation_id, sender="user", content=display_content)
    db.add(db_message)
    db.commit()

    # Load conversation history (last 10 messages for context)
    history_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    # Build chat history string (exclude the current message, keep last 10 pairs)
    chat_history = ""
    history_list = history_messages[:-1]  # exclude the message we just added
    if history_list:
        recent = history_list[-20:]  # last 20 messages (~10 pairs)
        history_lines = []
        for msg in recent:
            role = "User" if msg.sender == "user" else "Assistant"
            history_lines.append(f"{role}: {msg.content}")
        chat_history = "\n".join(history_lines)

    # Get RAG response
    try:
        search_results = retrieve.search(user_message)
        # Construct context from search results
        rag_context = "\n\n".join([f"Source: {res['source']}\nContent: {res['text']}" for res in search_results])

        # Build the full prompt
        prompt_parts = []
        prompt_parts.append("You are a helpful assistant. Answer the user query based on the following context.\n")

        if chat_history:
            prompt_parts.append(f"--- Conversation History ---\n{chat_history}\n--- End of History ---\n")

        if pdf_context:
            prompt_parts.append(f"--- Attached PDF Content ---\n{pdf_context}\n--- End of PDF ---\n")
        elif image_ocr_text:
            prompt_parts.append(f"--- Extracted Image Text (OCR) ---\n{image_ocr_text}\n--- End of OCR Text ---\n")
            if rag_context:
                prompt_parts.append(f"--- Knowledge Base Context ---\n{rag_context}\n--- End of Knowledge Base ---\n")
        elif rag_context:
            prompt_parts.append(f"--- Knowledge Base Context ---\n{rag_context}\n--- End of Knowledge Base ---\n")

        prompt_parts.append(f"User: {user_message}")
        prompt = "\n".join(prompt_parts)

        contents = [prompt]
        if image_parts:
            contents.extend(image_parts)

        response = None
        last_error = None
        for model_name in ['gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']:
            try:
                print(f"Generating content with model: {model_name}")
                model = retrieve.genai.GenerativeModel(model_name)
                response = model.generate_content(contents)
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
def get_conversations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversations = db.query(Conversation).filter(Conversation.user_id == current_user.id).order_by(Conversation.created_at.desc()).all()
    return conversations

@app.get("/api/conversations/{conversation_id}", response_model=ConversationSchema)
def get_conversation(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted"}
