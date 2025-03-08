import os
import requests
import pandas as pd
import time
import faiss
import pickle
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load API Key from .env
load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

def get_stock_news(ticker: str) -> list:
    """
    Fetch stock news from Alpha Vantage API.
    """
    ticker = ticker.upper()
    url = "https://www.alphavantage.co/query"
    
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "apikey": API_KEY,
        "sort": "RELEVANCE"
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return {"error": "Failed to fetch data"}

    data = response.json()
    if "feed" not in data:
        return {"error": "No news available"}

    return data["feed"]

def parse_articles(articles: list) -> list:
    """
    Extract article text using LangChain's UnstructuredURLLoader.
    """
    urls = [article['url'] for article in articles]
    loader = UnstructuredURLLoader(urls=urls)
    
    try:
        parsed_docs = loader.load()
        return parsed_docs
    except Exception as e:
        return {"error": f"Failed to parse articles: {str(e)}"}

def split_text(docs: list) -> list:
    """
    Split text into smaller chunks.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', '.', ','],
        chunk_size=1000
    )

    chunks = text_splitter.split_documents(docs)
    # Store chunks with metadata
    processed_chunks = [{"text": chunk.page_content, "source": chunk.metadata.get("source", "Unknown")} for chunk in chunks]

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

def build_stock_index(ticker: str):
    """
    Full pipeline: Fetch news → Parse content → Split text → Build FAISS index.
    """
    # Fetch News
    news = get_stock_news(ticker)
    if "error" in news:
        return news

    # Extract & Process Articles
    parsed_docs = parse_articles(news)
    if "error" in parsed_docs:
        return parsed_docs

    # Text Splitting
    processed_chunks = split_text(parsed_docs)
    if not processed_chunks:
        return {"error": "No text available after splitting"}
    
    # Save the list to a pickle file
    with open("data/chunks.pkl", "wb") as f:
        pickle.dump(processed_chunks, f)

    index = build_index(processed_chunks)
    # Save the FAISS index to a pickle file
    with open("data/faiss_store.pkl", "wb") as f:
        pickle.dump(index, f)

    return {"message": f"Index built for {ticker}", "num_vectors": len(processed_chunks)}
