import os
import pickle
import requests
import faiss
import time
from sentence_transformers import SentenceTransformer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import UnstructuredURLLoader
from openai import OpenAI
from dotenv import load_dotenv

# Load API Keys
load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")

# Ensure 'data/' directory exists
os.makedirs("data", exist_ok=True)

# File paths for storing FAISS index
CHUNKS_FILE = "data/chunks.pkl"
FAISS_FILE = "data/faiss_store.pkl"

### 🔹 Fetch & Store Company Overview ###
def get_company_overview(api_key, ticker):
    """Fetches the company overview from Alpha Vantage and returns as formatted text."""
    url = "https://www.alphavantage.co/query"
    params = {"function": "OVERVIEW", "symbol": ticker, "apikey": api_key}

    response = requests.get(url, params=params)
    data = response.json()

    if "Symbol" not in data:
        return f"Error fetching company overview: {data}"

    # Convert JSON dictionary to formatted text
    overview_text = "\n".join([f"{key}: {val}" for key, val in data.items()])
    return overview_text  # Returns formatted string


### 🔹 Fetch & Process Stock News ###
def get_stock_news(ticker):
    """Fetches stock news from Alpha Vantage API."""
    url = "https://www.alphavantage.co/query"
    params = {"function": "NEWS_SENTIMENT", "tickers": ticker.upper(), "apikey": ALPHA_VANTAGE_API_KEY, "sort": "RELEVANCE"}

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return {"error": "Failed to fetch data"}

    data = response.json()
    if "feed" not in data:
        return {"error": "No news available"}

    return data["feed"]


### 🔹 Parse Articles ###
def parse_articles(articles):
    """Extract article text using LangChain's UnstructuredURLLoader."""
    urls = [article['url'] for article in articles]
    loader = UnstructuredURLLoader(urls=urls)

    try:
        parsed_docs = loader.load()
        return parsed_docs
    except Exception as e:
        return {"error": f"Failed to parse articles: {str(e)}"}


### 🔹 Split Text into Chunks ###
def split_text(docs):
    """Splits text into chunks while retaining metadata (source)."""
    text_splitter = RecursiveCharacterTextSplitter(
        separators=['\n\n', '\n', '.', ','],
        chunk_size=1000
    )

    chunks = text_splitter.split_documents(docs)
    
    # Store chunks with metadata
    processed_chunks = [{"text": chunk.page_content, "source": chunk.metadata.get("source", "Unknown")} for chunk in chunks]

    return processed_chunks  # Returns a list of dictionaries with 'text' and 'source'


### 🔹 Build FAISS Index ###
def build_index(processed_chunks):
    """Builds a FAISS index while using processed_chunks directly."""
    encoder = SentenceTransformer("BAAI/bge-base-en")

    texts = [chunk["text"] for chunk in processed_chunks]  # Only extract text
    vectors = encoder.encode(texts)
    faiss.normalize_L2(vectors)

    dim = vectors.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(vectors)

    return index, processed_chunks  # Keep full processed chunks (text + source)

def build_stock_index(ticker):
    """Fetches company overview & news, parses content, splits text, and builds FAISS index."""
    # Fetch Company Overview
    company_overview = get_company_overview(ALPHA_VANTAGE_API_KEY, ticker)

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

    # Save chunks (No need to extract metadata separately)
    with open(CHUNKS_FILE, "wb") as f:
        pickle.dump(processed_chunks, f)

    # Build FAISS Index
    index, processed_chunks = build_index(processed_chunks)

    # Save FAISS Index (Store processed_chunks directly)
    with open(FAISS_FILE, "wb") as f:
        pickle.dump((index, processed_chunks), f)

    return {"message": f"Index built for {ticker}", "num_vectors": len(processed_chunks), "company_overview": company_overview}


def retrieve_relevant_chunks(index, processed_chunks, user_query, k=3):
    """Retrieves top-k relevant chunks along with their sources."""
    encoder = SentenceTransformer("BAAI/bge-base-en")

    query_vector = encoder.encode([user_query])
    faiss.normalize_L2(query_vector)

    # Perform FAISS search
    _, indices = index.search(query_vector, k=k)

    retrieved_docs = []
    for i in indices[0]:
        if i < len(processed_chunks):  # Ensure index is within range
            retrieved_docs.append({
                "text": processed_chunks[i]["text"],  # ✅ Use processed_chunks directly
                "source": processed_chunks[i]["source"]  # ✅ Keep source information
            })

    return retrieved_docs  # Returns text chunks with sources


def format_retrieved_text(retrieved_docs):
    """Formats retrieved documents into structured text for LLM input."""
    formatted_text = "\n=========\n".join(
        [f"Content: {doc['text']}\nSource: {doc['source']}" for doc in retrieved_docs]
    )
    
    return formatted_text


### 🔹 Query LLM ###
def query_llm_with_retrieval(ticker, user_query):
    """Retrieves relevant news chunks and queries OpenRouter LLM."""
    # Load FAISS Index
    if not os.path.exists(FAISS_FILE) or not os.path.exists(CHUNKS_FILE):
        return {"error": "FAISS index or processed chunks not found. Please build index first."}

    with open(FAISS_FILE, "rb") as f:
        index, _ = pickle.load(f)  # ✅ Load only FAISS index

    with open(CHUNKS_FILE, "rb") as f:
        processed_chunks = pickle.load(f)  # ✅ Load processed chunks separately

    # Retrieve top-k relevant documents
    retrieved_docs = retrieve_relevant_chunks(index, processed_chunks, user_query, k=3)

    # Format Retrieved Docs for Prompt
    retrieved_text = format_retrieved_text(retrieved_docs)

    # Load Company Overview
    company_overview = get_company_overview(ALPHA_VANTAGE_API_KEY, ticker)

    # OpenRouter API Client
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPEN_ROUTER_API_KEY)

    # Construct LLM Prompt
    messages = [
        {
            "role": "system",
            "content": (
                "You are a financial assistant specializing in stock market analysis, with extensive pre-trained knowledge about finance. "
                "The company overview and recent news articles are provided to help you answer the user's question. "
                "If the articles don't address the query, you may rely on your pre-trained knowledge to provide an answer. "
                "If you still don't know the answer, just say 'I don't know.' Don't make up an answer. "
                "If the provided context contradicts your pre-training, favor the provided context.\n\n"

                "=== Company Overview ===\n"
                f"{company_overview}\n\n"
                "=== Relevant News ===\n"
                f"{retrieved_text}\n\n"
                "Provide a well-structured financial response using the above data or your own knowledge, and include source references when using the provided context."
            )
        },
        {
            "role": "user",
            "content": user_query
        }
    ]


    # Call OpenRouter's API
    completion = client.chat.completions.create(
        model="meta-llama/llama-3.3-70b-instruct:free",
        messages=messages
    )

    return completion.choices[0].message.content


### 🔹 Interactive CLI ###
if __name__ == "__main__":
    ticker = input("Enter stock ticker: ").upper()
    print("\nFetching & Indexing Data...")
    build_stock_index(ticker)

    user_query = input("\nNow ask a financial question: ")
    print("\n=== AI Response ===\n")
    print(query_llm_with_retrieval(ticker, user_query))