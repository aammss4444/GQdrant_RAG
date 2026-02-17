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
COLLECTION_NAME = "ai_structured_collection"
EMBEDDING_MODEL = "models/gemini-embedding-001"

# --- Golden Dataset ---
# A list of queries and expected keywords that MUST be present in the retrieved chunks/source.
# Keywords are case-insensitive for matching.
# This assumes general knowledge about what's likely in an "AI PDF".
TEST_DATASET = [
    {
        "query": "What is Deep Learning?",
        "expected_keywords": ["deep learning", "neural networks", "representation learning", "layers"]
    },
    {
        "query": "Define NLP",
        "expected_keywords": ["natural language processing", "nlp", "linguistics", "text"]
    },
    {
        "query": "How do Transformers work?",
        "expected_keywords": ["transformer", "attention", "self-attention", "bert", "gpt"]
    },
    {
        "query": "What are vector databases?",
        "expected_keywords": ["vector database", "similarity search", "embeddings", "high-dimensional"]
    },
    {
        "query": "Explain Generative AI",
        "expected_keywords": ["generative ai", "generate", "content", "fake", "creation"]
    }
]

def get_embedding(text):
    """Generates embedding for the given text using Gemini API."""
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=text,
        task_type="retrieval_query"
    )
    return result['embedding']

def evaluate(k=3):
    """Evaluates retrieval accuracy (Hit Rate & MRR) @ K."""
    print(f"Evaluating Retrieval Accuracy @ {k}...\n")
    
    total_hits = 0
    total_reciprocal_rank = 0
    total_queries = len(TEST_DATASET)

    for case in TEST_DATASET:
        query = case["query"]
        expected = case["expected_keywords"]
        print(f"Query: '{query}'")
        
        # 1. Retrieve
        try:
            query_vector = get_embedding(query)
            search_result = client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                limit=k
            )
            hits = search_result.points
        except Exception as e:
            print(f"  Error retrieving: {e}")
            continue

        # 2. Check for Hits
        hit_rank = 0 # 0 means no hit
        found_keywords = []

        for i, hit in enumerate(hits):
            text = hit.payload.get('text', '').lower()
            # Check if ANY expected keyword is in the retrieved text
            matched = [kw for kw in expected if kw.lower() in text]
            
            if matched:
                if hit_rank == 0:
                    hit_rank = i + 1 # 1-indexed rank
                found_keywords.extend(matched)
                # We count the first relevant result for MRR
                break 
        
        # 3. Update Metrics
        if hit_rank > 0:
            total_hits += 1
            total_reciprocal_rank += 1.0 / hit_rank
            print(f"  [HIT] Rank: {hit_rank} (Matched: {found_keywords})")
        else:
            print(f"  [MISS] Expected: {expected}")
        
        print("-" * 30)

    # 4. Final Calculation
    hit_rate = total_hits / total_queries
    mrr = total_reciprocal_rank / total_queries

    print("\n" + "=" * 30)
    print(f"Final Results (K={k}):")
    print(f"Queries Evaluated: {total_queries}")
    print(f"Hit Rate: {hit_rate:.2%}")
    print(f"MRR:      {mrr:.4f}")
    print("=" * 30)

if __name__ == "__main__":
    evaluate(k=3)
