# GeminiQ-RAG

## Overview
GeminiQ-RAG is a robust Retrieval-Augmented Generation (RAG) system that leverages **Google's Gemini** models for embeddings and **Qdrant** for vector storage. It is designed to ingest structured PDF documents, generate semantically rich embeddings, and provide accurate retrieval capabilities.

## Features
- **Structured Ingestion**: `ingest_structured.py` intelligently chunks text by preserving headers and paragraphs, ensuring better context for retrieval.
- **Gemini Embeddings**: Uses `models/gemini-embedding-001` for high-quality vector representations (3072 dimensions).
- **Qdrant Integration**: Efficient vector similarity search using Qdrant.
- **Evaluation Suite**: `evaluate.py` provides Hit Rate and MRR metrics to benchmark retrieval performance.

## Prerequisites
- Python 3.x
- Qdrant (Docker or Cloud)
- Google AI Studio API Key

## Setup
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set up `.env` file:
    ```
    QDRANT_URL=...
    QDRANT_API_KEY=...
    GOOGLE_API_KEY=...
    ```

## Usage
1.  **Ingest Data**:
    ```bash
    python ingest_structured.py
    ```
2.  **Evaluate Performance**:
    ```bash
    python evaluate.py
    ```
