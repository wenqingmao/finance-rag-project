import os
import requests
import faiss
import pickle
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables if needed
load_dotenv()

# We no longer define get_stock_news(ticker) here,
# because we’ll fetch that in the frontend.

def parse_articles(articles: list) -> list:
    """
    Extract article text using LangChain's UnstructuredURLLoader.
    'articles' is a list of dicts with (at least) 'url'.
    """
    # Each article should at least have a 'url' key
    urls = [article["url"] for article in articles]

    loader = UnstructuredURLLoader(urls=urls)
    try:
        # loads each URL and returns structured docs
        parsed_docs = loader.load()
        return parsed_docs
    except Exception as e:
        return {"error": f"Failed to parse articles: {str(e)}"}

def split_text(docs: list) -> list:
    """
    Split text into smaller chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ".", ","],
        chunk_size=1000
    )
    chunks = text_splitter.split_documents(docs)

    # Convert to a list of dicts with "text" and "source"
    processed_chunks = [
        {
            "text": chunk.page_content,
            "source": chunk.metadata.get("source", "Unknown")
        }
        for chunk in chunks
    ]

    return processed_chunks

def build_index(processed_chunks: list):
    """
    Build a FAISS index from text chunks.
    """
    encoder = SentenceTransformer("BAAI/bge-base-en")
    texts = [chunk["text"] for chunk in processed_chunks]
    vectors = encoder.encode(texts)
    faiss.normalize_L2(vectors)

    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)
    return index

def build_stock_index_from_feed(feed: list, ticker: Optional[str] = None):
    """
    We now receive a feed directly from the frontend.
    'feed' is a list of dictionaries (or Pydantic FeedItem objects)
    that contain at least 'url' for each item.
    """
    if not feed:
        return {"error": "No feed provided"}

    # 1) Parse articles using their URLs
    parsed_docs = parse_articles(feed)
    if isinstance(parsed_docs, dict) and "error" in parsed_docs:
        return parsed_docs  # error happened

    # 2) Split text into chunks
    processed_chunks = split_text(parsed_docs)
    if not processed_chunks:
        return {"error": "No text available after splitting"}

    # 3) Persist the chunks locally (optional)
    os.makedirs("data", exist_ok=True)
    with open("data/chunks.pkl", "wb") as f:
        pickle.dump(processed_chunks, f)

    # 4) Build the FAISS index
    index = build_index(processed_chunks)

    # 5) Persist the index locally (optional)
    with open("data/faiss_store.pkl", "wb") as f:
        pickle.dump(index, f)

    # 6) Return result
    msg = f"Index built for {ticker}" if ticker else "Index built"
    return {"message": msg, "num_vectors": len(processed_chunks)}
