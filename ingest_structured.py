import os
import pdfplumber
import google.generativeai as genai
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

# Initialize Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Qdrant Client
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)

# Collection Configuration
COLLECTION_NAME = "ai_structured_collection_v2"
EMBEDDING_MODEL = "models/gemini-embedding-001"
VECTOR_SIZE = 768 
PDF_PATH = "Artificial_Intelligence_Expanded_Detailed_Report.pdf"

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
            # Check if result is valid
            if 'embedding' in result:
                embedding = result['embedding']
                if len(embedding) > VECTOR_SIZE:
                    embedding = embedding[:VECTOR_SIZE]
                return embedding
            else:
                # Handle cases where result might be empty (e.g. safety filter)
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
        
        # Move start forward by (chunk_size - overlap)
        start += (chunk_size - overlap)
    
    return chunks

def extract_text_from_pdf(pdf_path):
    """Extracts raw text from PDF."""
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            try:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            except Exception as e:
                print(f"Error extracting text from page: {e}")
    return full_text

def main():
    print(f"Processing {PDF_PATH} with Chunk Size {CHUNK_SIZE}, Overlap {CHUNK_OVERLAP}...")
    
    # 1. Extract
    print("Extracting text from PDF...")
    raw_text = extract_text_from_pdf(PDF_PATH)
    print(f"Extracted {len(raw_text)} characters.")
    
    # 2. Chunk
    print("Chunking text...")
    text_chunks = chunk_text(raw_text, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"Created {len(text_chunks)} chunks.")
    
    # 3. Re-create Collection
    if client.collection_exists(COLLECTION_NAME):
        print(f"Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(COLLECTION_NAME)

    print(f"Creating collection: {COLLECTION_NAME} with dimension {VECTOR_SIZE}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

    # 4. Generate Embeddings & Upsert
    points = []
    print("Generating embeddings...")
    
    BATCH_SIZE = 20 # Smaller batch size to be safe
    
    for idx, chunk_text_content in enumerate(text_chunks):
        try:
            # Contextualize? Just strict chunking requested.
            # But let's keep it clean.
            embedding = get_embedding(chunk_text_content)
            
            if embedding:
                point = PointStruct(
                    id=idx,
                    vector=embedding,
                    payload={"text": chunk_text_content, "source": PDF_PATH}
                )
                points.append(point)
                
                # Moderate sleep to avoid bursting too hard
                time.sleep(2) 
            else:
                print(f"Skipping chunk {idx} due to embedding failure.")

            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1}/{len(text_chunks)} chunks.")
                
        except Exception as e:
            print(f"Error processing chunk {idx}: {e}")

    # 5. Upsert
    if points:
        print(f"Upserting {len(points)} points to Qdrant...")
        # DEBUG: Check embedding dimension
        if points:
            dim = len(points[0].vector)
            print(f"DEBUG: Embedding dimension: {dim}")
            if dim != VECTOR_SIZE:
                print(f"ERROR: Dimension mismatch! Expected {VECTOR_SIZE}, got {dim}")
        
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
            time.sleep(1) # Sleep between upserts
            
        print("Done! Collection populated.")
    else:
        print("No points to upsert.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR: {e}")
