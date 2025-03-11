import os
import pickle
import requests
import faiss
# import time
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv

# Load API Keys
load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")

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


def retrieve_relevant_chunks(index, processed_chunks, user_query, k=10):
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
    # if not os.path.exists(FAISS_FILE) or not os.path.exists(CHUNKS_FILE):
    #     return {"error": "FAISS index or processed chunks not found. Please build index first."}

    with open(FAISS_FILE, "rb") as f:
        index = pickle.load(f)  # ✅ Load only FAISS index

    with open(CHUNKS_FILE, "rb") as f:
        processed_chunks = pickle.load(f)  # ✅ Load processed chunks separately

    # Retrieve top-k relevant documents
    retrieved_docs = retrieve_relevant_chunks(index, processed_chunks, user_query, k=10)

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
                "You are a financial assistant specializing in stock market analysis."
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
# if __name__ == "__main__":
#     ticker = input("Enter stock ticker: ").upper()
#     user_query = input("\nNow ask a financial question: ")
#     print("\n=== AI Response ===\n")
#     print(query_llm_with_retrieval(ticker, user_query))
