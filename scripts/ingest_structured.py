import os
import argparse
import pdfplumber
import google.generativeai as genai
import pytesseract
from PIL import Image
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from dotenv import load_dotenv
import time
import random

# Load environment variables
load_dotenv()

# Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing in .env file.")

# Configure tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Initialize Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Qdrant Client
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)

# Collection Configuration
COLLECTION_NAME = "ai_structured_collection_v2"
EMBEDDING_MODEL = "models/gemini-embedding-001"
VECTOR_SIZE = 768 

CHUNK_SIZE = 450
CHUNK_OVERLAP = 80

def get_embedding(text, retries=5):
    """Generates embedding with exponential backoff."""
    for attempt in range(retries):
        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            if 'embedding' in result:
                embedding = result['embedding']
                if len(embedding) > VECTOR_SIZE:
                    embedding = embedding[:VECTOR_SIZE]
                return embedding
            else:
                print(f"Warning: No embedding returned for text: {text[:50]}...")
                return None
        except Exception as e:
            if "429" in str(e) or "Resource exhausted" in str(e):
                unique_wait = (2 ** attempt) + random.uniform(0, 5)
                print(f"Rate limit hit. Waiting {unique_wait:.2f}s... (Attempt {attempt+1}/{retries})")
                time.sleep(unique_wait)
            else:
                print(f"Error generating embedding: {e}")
                time.sleep(5)
    return None

def chunk_text(text, chunk_size, overlap):
    """Splits text into chunks of `chunk_size` characters with `overlap`."""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += (chunk_size - overlap)
    
    return chunks

def extract_text_and_ocr(pdf_path, use_ocr=True):
    """Extracts raw text and performs OCR if needed."""
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"Processing page {i+1}/{len(pdf.pages)}...")
            
            # Try direct text extraction
            text = page.extract_text()
            if text:
                full_text += text + "\n"
            
            # Check for images or low text count to trigger OCR
            if use_ocr and (len(page.images) > 0 or (text and len(text) < 100)):
                print(f"  OCR triggered for page {i+1}...")
                try:
                    # Render page to image
                    with page.to_image(resolution=300) as img:
                        pil_img = img.original
                        ocr_text = pytesseract.image_to_string(pil_img)
                        if ocr_text:
                            print(f"  OCR extracted {len(ocr_text)} characters.")
                            full_text += "\n--- OCR Data ---\n" + ocr_text + "\n"
                except Exception as e:
                    print(f"  OCR failed for page {i+1}: {e}")
            
    return full_text

def main():
    parser = argparse.ArgumentParser(description="Ingest PDF into Qdrant")
    parser.add_argument("pdf_path", nargs="?", default="data/ocr-test-doc.pdf", help="Path to the PDF file")
    parser.add_argument("--append", action="store_true", help="Append to existing collection instead of recreating it")
    parser.add_argument("--no-ocr", action="store_false", dest="ocr", help="Disable OCR even if images found")
    parser.set_defaults(ocr=True)
    args = parser.parse_args()

    pdf_path = args.pdf_path
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        return

    print(f"Processing {pdf_path} (OCR: {args.ocr}) with Chunk Size {CHUNK_SIZE}, Overlap {CHUNK_OVERLAP}...")
    
    # 1. Extract & OCR
    print("Extracting text and performing OCR...")
    raw_text = extract_text_and_ocr(pdf_path, use_ocr=args.ocr)
    print(f"Total extracted {len(raw_text)} characters.")
    
    if len(raw_text) == 0:
        print("Error: No text extracted. Aborting.")
        return

    # 2. Chunk
    print("Chunking text...")
    text_chunks = chunk_text(raw_text, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"Created {len(text_chunks)} chunks.")
    
    # 3. Collection Management
    exists = client.collection_exists(COLLECTION_NAME)
    if exists and not args.append:
        print(f"Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(COLLECTION_NAME)
        exists = False

    if not exists:
        print(f"Creating collection: {COLLECTION_NAME} with dimension {VECTOR_SIZE}")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )

    # 4. Generate Embeddings & Upsert
    points = []
    print("Generating embeddings...")
    
    BATCH_SIZE = 20
    
    current_count = 0
    if args.append:
        try:
            collection_info = client.get_collection(COLLECTION_NAME)
            current_count = collection_info.points_count
            print(f"Starting with index {current_count}")
        except Exception:
            pass

    for idx, chunk_text_content in enumerate(text_chunks):
        try:
            embedding = get_embedding(chunk_text_content)
            
            if embedding:
                point = PointStruct(
                    id=current_count + idx,
                    vector=embedding,
                    payload={"text": chunk_text_content, "source": pdf_path}
                )
                points.append(point)
                
                time.sleep(1)
            else:
                print(f"Skipping chunk {idx} due to embedding failure.")

            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1}/{len(text_chunks)} chunks.")
                
        except Exception as e:
            print(f"Error processing chunk {idx}: {e}")

    # 5. Upsert
    if points:
        print(f"Upserting {len(points)} points to Qdrant...")
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i + BATCH_SIZE]
            try:
                client.upsert(
                    collection_name=COLLECTION_NAME,
                    wait=True,
                    points=batch
                )
                print(f"Upserted batch {i // BATCH_SIZE + 1}")
            except Exception as e:
                print(f"Error upserting batch {i // BATCH_SIZE + 1}: {e}")
            time.sleep(1)
            
        print("Done! Collection updated.")
    else:
        print("No points to upsert.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR: {e}")
