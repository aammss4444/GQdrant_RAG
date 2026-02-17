import os
import google.generativeai as genai
from qdrant_client import QdrantClient
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
COLLECTION_NAME = "ai_pdf_collection"
EMBEDDING_MODEL = "models/gemini-embedding-001"

def get_embedding(text):
    """Generates embedding for the given text using Gemini API."""
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_query"
    )
    return result['embedding']

def search(query, limit=3):
    """Searches the Qdrant collection for the query."""
    print(f"Query: {query}")
    print("Generating embedding...")
    try:
        query_vector = get_embedding(query)
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return

    print("Searching Qdrant...")
    try:
        search_result = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=limit
        )
        hits = search_result.points

        print(f"\nFound {len(hits)} results:")
        for i, hit in enumerate(hits):
            print(f"\n--- Result {i+1} (Score: {hit.score:.4f}) ---")
            print(f"Text: {hit.payload.get('text', 'N/A')}")
            print(f"Source: {hit.payload.get('source', 'N/A')}")
            
    except Exception as e:
        print(f"Error searching Qdrant: {e}")

def main():
    while True:
        query = input("\nEnter your query (or 'quit' to exit): ")
        if query.lower() in ('quit', 'exit', 'q'):
            break
        if not query.strip():
            continue
        
        search(query)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ERROR: {e}")
