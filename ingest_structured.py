import os
import pdfplumber
import google.generativeai as genai
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from dotenv import load_dotenv

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
COLLECTION_NAME = "ai_structured_collection"
EMBEDDING_MODEL = "models/gemini-embedding-001"
VECTOR_SIZE = 3072 
PDF_PATH = "ai.pdf"

import time

def get_embedding(text, retries=3):
    """Generates embedding for the given text using Gemini API with retry logic."""
    for attempt in range(retries):
        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            if "429" in str(e):
                print(f"Rate limit exceeded. Waiting 60s... (Attempt {attempt+1}/{retries})")
                time.sleep(60)
            else:
                print(f"Error generating embedding: {e}")
                time.sleep(5)
    return None

def extract_structured_content(pdf_path):
    """Extracts text preserving structure (Headers vs Paragraphs)."""
    structured_chunks = []
    
    with pdfplumber.open(pdf_path) as pdf:
        current_section = "Introduction" # Default section
        
        for page_num, page in enumerate(pdf.pages):
            # Extract words with their font sizes
            words = page.extract_words(keep_blank_chars=True, use_text_flow=True)
            
            # Simple Heuristic: 
            # 1. Calculate average font size of the page (roughly)
            # 2. Anything significantly larger is a Header
            if not words:
                continue
                
            font_sizes = [w['bottom'] - w['top'] for w in words]
            avg_size = sum(font_sizes) / len(font_sizes)
            header_threshold = avg_size * 1.2  # 20% larger than average
            
            current_block_text = []
            
            # Iterate through words and group them
            # This is a simplified approach. A more robust one might group by absolute Y position.
            # Here we iterate line by line approximately.
            
            # Better approach: Extract text lines directly? 
            # pdfplumber doesn't give line objects with font info directly easily without processing words.
            # Let's use a simpler block iteration.
            
            text_lines = page.extract_text().split('\n')
            # But extract_text loses font info.
            
            # Let's stick to word iteration or check characters.
            # Actually, pdfplumber's `extract_table` is great for tables.
            # For general text, let's just inspect lines.
            
            # Revised approach: Iterate chars to find line breaks and font sizes? Too slow.
            # Let's use the 'top' coordinate to group words into lines.
            
            lines = {} # Y-coord -> [words]
            for w in words:
                top = round(w['top']) # Group by roughly same Y
                if top not in lines:
                    lines[top] = []
                lines[top].append(w)
            
            sorted_y = sorted(lines.keys())
            
            for y in sorted_y:
                line_words = lines[y]
                # Reconstruct line text
                line_text = " ".join([w['text'] for w in line_words])
                
                # Check max font size in this line
                line_font_size = max([w['bottom'] - w['top'] for w in line_words])
                
                if line_font_size > header_threshold:
                    # It's a Header!
                    # 1. Save previous block if exists
                    if current_block_text:
                        chunk_text = " ".join(current_block_text)
                        structured_chunks.append({
                            "text": chunk_text,
                            "type": "paragraph",
                            "section": current_section,
                            "page": page_num + 1
                        })
                        current_block_text = []
                    
                    # 2. Update current section
                    current_section = line_text
                    # We also add the header itself as a chunk? Or just metadata?
                    # Let's add it as a chunk too, helpful for matching "Introduction".
                    structured_chunks.append({
                        "text": line_text,
                        "type": "header",
                        "section": current_section,
                        "page": page_num + 1
                    })
                    
                else:
                    # It's a Paragraph line
                    current_block_text.append(line_text)
            
            # End of page, save remaining block
            if current_block_text:
                 chunk_text = " ".join(current_block_text)
                 structured_chunks.append({
                    "text": chunk_text,
                    "type": "paragraph",
                    "section": current_section,
                    "page": page_num + 1
                })
                
    return structured_chunks

def main():
    print(f"Processing {PDF_PATH} with structure detection...")
    
    # 1. Extract
    chunks = extract_structured_content(PDF_PATH)
    print(f"Extracted {len(chunks)} structured chunks.")
    
    # 2. Re-create Collection
    if client.collection_exists(COLLECTION_NAME):
        print(f"Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(COLLECTION_NAME)

    print(f"Creating collection: {COLLECTION_NAME} with dimension {VECTOR_SIZE}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )

    # 3. Generate Embeddings & Upsert
    points = []
    print("Generating embeddings...")
    
    BATCH_SIZE = 50
    for idx, chunk in enumerate(chunks):
        try:
            # Contextualize text for embedding: "Section: Introduction. Content: ..."
            embedding_text = f"Section: {chunk['section']}. {chunk['text']}"
            
            embedding = get_embedding(embedding_text)
            
            if embedding:
                point = PointStruct(
                    id=idx,
                    vector=embedding,
                    payload=chunk
                )
                points.append(point)
                
                # Rate limit: Sleep to avoid hitting API limits
                time.sleep(2) 
            else:
                print(f"Skipping chunk {idx} due to embedding failure.")

            if (idx + 1) % 10 == 0:
                print(f"Processed {idx + 1}/{len(chunks)} chunks.")
                
        except Exception as e:
            print(f"Error processing chunk {idx}: {e}")

    # 4. Upsert
    if points:
        print(f"Upserting {len(points)} points to Qdrant...")
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i:i + BATCH_SIZE]
            client.upsert(
                collection_name=COLLECTION_NAME,
                wait=True,
                points=batch
            )
            print(f"Upserted batch {i // BATCH_SIZE + 1}")
            
        print("Done! Collection 'ai_structured_collection' is ready.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR: {e}")
