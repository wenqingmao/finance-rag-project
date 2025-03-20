import streamlit as st
import pickle
import time
import os
import requests
import faiss
import pandas as pd
from datetime import datetime
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
from dotenv import load_dotenv
import torch

torch.classes.__path__ = [os.path.join(torch.__path__[0], torch.classes.__file__)] # Fix for TorchScript error

# Load environment variables
load_dotenv()
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
OPEN_ROUTER_API_KEY = os.getenv("OPEN_ROUTER_API_KEY")
FAISS_DIR = "streamlit/data/"
os.makedirs(FAISS_DIR, exist_ok=True)

st.set_page_config(page_title="FinFetch", layout="wide")

# Function to check if index already exists for today
def get_faiss_filename(ticker):
    today = datetime.today().strftime('%Y-%m-%d')
    return os.path.join(FAISS_DIR, f"faiss_{ticker}_{today}.pkl")

def get_chunks_filename(ticker):
    today = datetime.today().strftime('%Y-%m-%d')
    return os.path.join(FAISS_DIR, f"chunks_{ticker}_{today}.pkl")

def is_index_cached(ticker):
    return os.path.exists(get_faiss_filename(ticker)) and os.path.exists(get_chunks_filename(ticker))

########################################
# 2) Utility Functions (News, Overview)
########################################

def get_stock_news(ticker: str) -> list:
    """
    Fetch stock news from Alpha Vantage API.
    """
    ticker = ticker.upper()
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "apikey": ALPHA_VANTAGE_API_KEY,
        "sort": "RELEVANCE"
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return {"error": "Failed to fetch data"}

    data = response.json()
    if "feed" not in data:
        return {"error": "No news available"}
    return data["feed"]

def get_company_overview(ticker):
    url = "https://www.alphavantage.co/query"
    params = {"function": "OVERVIEW", "symbol": ticker, "apikey": ALPHA_VANTAGE_API_KEY}
    response = requests.get(url, params=params)
    data = response.json()
    if "Symbol" not in data:
        return f"Error fetching company overview: {data}"
    return "\n".join([f"{key}: {val}" for key, val in data.items()])

########################################
# 3) Document Parsing & Splitting
########################################
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
    processed_chunks = [
        {
            "text": chunk.page_content,
            "source": chunk.metadata.get("source", "Unknown")
        }
        for chunk in chunks
    ]
    return processed_chunks

########################################
# 4) Building FAISS Index
########################################
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

########################################
# 5) Full Pipeline to Build & Cache Index
########################################
def build_stock_index(ticker: str):
    ticker = ticker.upper()
    
    print(ticker)
    # Load valid stock symbols
    LISTING_FILE = "streamlit/data/listing_status.csv"
    valid_symbols = set()
    if os.path.exists(LISTING_FILE):
        df = pd.read_csv(LISTING_FILE)
        print('Successfully read valid ticker list!')
        if "symbol" in df.columns:
            valid_symbols = set(df["symbol"].str.upper())

    # Validate ticker
    if ticker not in valid_symbols:
        return {"error": "Invalid ticker symbol. Please enter a valid stock ticker."}
    
    # Check if index already exists
    if is_index_cached(ticker):
        return {"message": f"Index already built for {ticker} today. Retrieving cached index."}
    
    # Fetch news from Alpha Vantage
    news = get_stock_news(ticker)
    if "error" in news:
        return news

    parsed_docs = parse_articles(news)
    if "error" in parsed_docs:
        return parsed_docs

    processed_chunks = split_text(parsed_docs)
    if not processed_chunks:
        return {"error": "No text available after splitting"}

    # Save processed chunks
    os.makedirs(FAISS_DIR, exist_ok=True)
    with open(get_chunks_filename(ticker), "wb") as f:
        pickle.dump(processed_chunks, f)

    # Build and save FAISS index
    index = build_index(processed_chunks)
    with open(get_faiss_filename(ticker), "wb") as f:
        pickle.dump(index, f)

    return {"message": f"Index built for {ticker}", "num_vectors": len(processed_chunks)}

########################################
# 6) Query LLM with Retrieval
########################################
def retrieve_relevant_chunks(index, processed_chunks, user_query, k=10):
    encoder = SentenceTransformer("BAAI/bge-base-en")
    query_vector = encoder.encode([user_query])
    faiss.normalize_L2(query_vector)
    _, indices = index.search(query_vector, k=k)
    return [processed_chunks[i] for i in indices[0] if i < len(processed_chunks)]


def format_retrieved_text(retrieved_docs):
    return "\n========\n".join(
        [f"Content: {doc['text']}\nSource: {doc['source']}" for doc in retrieved_docs]
    )


def query_llm_with_retrieval(ticker, user_query):
    """Retrieves relevant news chunks and queries OpenRouter LLM."""
    ticker = ticker.upper()
    faiss_file = get_faiss_filename(ticker)
    chunks_file = get_chunks_filename(ticker)

    # Check if the index exists
    if not os.path.exists(faiss_file) or not os.path.exists(chunks_file):
        return {"error": f"No index found for {ticker} today. Please build the index first."}

    # Load FAISS Index
    with open(faiss_file, "rb") as f:
        index = pickle.load(f)

    # Load Processed Chunks
    with open(chunks_file, "rb") as f:
        processed_chunks = pickle.load(f)

    # Retrieve top-k relevant documents
    retrieved_docs = retrieve_relevant_chunks(index, processed_chunks, user_query, k=10)

    # Format retrieved docs
    retrieved_text = format_retrieved_text(retrieved_docs)

    # Load Company Overview
    company_overview = get_company_overview(ticker)

    # OpenRouter API client
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPEN_ROUTER_API_KEY)

    # Construct prompt
    messages = [
        {
            "role": "system",
            "content": (
                "You are a financial assistant specializing in stock market analysis. "
                "The company overview and recent news articles are provided to help you answer the user's question. "
                "If the articles don't address the query, you may rely on your pre-trained knowledge to provide an answer. "
                "If you still don't know the answer, just say 'I don't know.' Don't make up an answer. "
                "If the provided context contradicts your pre-training, favor the provided context.\n\n"
                "You must include references in your final answer if you use any of the provided articles.\n"
                "Use the following format strictly:\n\n"
                "Answer Body (with in-text citations like [1], [2], etc.)\n\n"
                "References:\n"
                "[1] <url>\n"
                "[2] <url>\n\n"

                "=== Company Overview ===\n"
                f"{company_overview}\n\n"
                "=== Relevant News ===\n"
                f"{retrieved_text}\n\n"
                "Provide a well-structured financial response using the above data or your own knowledge, "
                "and include source references when using the provided context."
                "In your response, add space, new line, or any other separator when necessary."
                
            )
        },
        {
            "role": "assistant",
            "content": (
                "Understood. I will provide references as specified."
            )
        },
        {
            "role": "user",
            "content": user_query
        }
    ]

    # Call LLM
    completion = client.chat.completions.create(
        model="meta-llama/llama-3.3-70b-instruct:free",
        messages=messages
    )

    return completion.choices[0].message.content

########################################
# 7) Streamlit UI
########################################

# # Sidebar settings
# with st.sidebar:
#     st.header("Settings")
#     ticker = st.text_input("Enter Stock Ticker:")
#     if st.button("Build Index"):
#         with st.spinner("Fetching stock news and building index..."):
#             response = build_stock_index(ticker)
#             if "error" in response:
#                 st.error(response["error"])
#             else:
#                 st.success(f"Index built for {ticker}!")

# # Main UI Chatbot Interface
# st.title("📈 FinFetch")
# st.caption("🚀 Get financial insights powered by RAG")

# st.markdown( """ <style> .st-emotion-cache-janbn0 { flex-direction: row-reverse; text-align: right; } </style> """, unsafe_allow_html=True, )

# if "messages" not in st.session_state:
#     st.session_state["messages"] = [{"role": "assistant", "content": "How can I assist you with financial insights?"}]

# for msg in st.session_state.messages:
#     st.chat_message(msg["role"]).write(msg["content"])

# if user_query := st.chat_input("Ask a financial question..."):
#     if not os.path.exists(FAISS_FILE) or not os.path.exists(CHUNKS_FILE):
#         st.error("Please build the index first!")
#     else:
#         with st.spinner("Generating answer..."):
#             response = query_llm_with_retrieval(ticker, user_query)
#             st.session_state.messages.append({"role": "user", "content": user_query})
#             st.chat_message("user").write(user_query)
#             st.session_state.messages.append({"role": "assistant", "content": response})
#             st.chat_message("assistant").write(response)

def response_generator(text: str, delay: float = 0.05):
    """
    Yields chunks of text while preserving newlines and spacing,
    sleeping 'delay' seconds between each chunk.
    """
    buffer = ""
    i = 0
    while i < len(text):
        char = text[i]
        buffer += char
        
        # Yield when we hit a space, newline, or end of text
        if char in [' ', '\n'] or i == len(text) - 1:
            yield buffer
            buffer = ""
            time.sleep(delay)
        i += 1
    
    # Ensure any remaining buffer is yielded
    if buffer:
        yield buffer

# Sidebar settings
with st.sidebar:
    # st.image("logo.png", width=60)
    st.header("Build Index")
    ticker = st.text_input("Enter Stock Ticker:")
    if st.button("Submit"):
        with st.spinner("Fetching stock news and building index..."):
            response = build_stock_index(ticker)
            if "error" in response:
                st.error(response["error"])
            else:
                st.success(f"Index built for {ticker}!")

# Main UI Chatbot Interface
st.title("📈 FinFetch")
st.caption("🚀 Get financial insights powered by RAG")

# Simple CSS override for reversing user messages (optional)
st.markdown(
    """ 
    <style> 
    .st-emotion-cache-janbn0 { 
        flex-direction: row-reverse; 
        text-align: right; 
    } 
    </style> 
    """,
    unsafe_allow_html=True,
)

# Initialize message history
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "How can I assist you with financial insights?"}
    ]

# Display existing messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# User query input
if user_query := st.chat_input("Ask a financial question..."):
    ticker = ticker.upper()
    faiss_file = get_faiss_filename(ticker)
    chunks_file = get_chunks_filename(ticker)

    # Validate if the FAISS index exists for the given ticker and today's date
    if not os.path.exists(faiss_file) or not os.path.exists(chunks_file):
        st.error(f"No index found for {ticker} today. Please build the index first.")
    else:
        # 1) Add user message to conversation & display
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)

        with st.spinner("Generating answer..."):
            # 2) Retrieve entire answer from your LLM or RAG pipeline
            full_answer = query_llm_with_retrieval(ticker, user_query)
            print(full_answer)

            # 3) Stream it word by word using a generator
            with st.chat_message("assistant"):
                streamed_text = st.write_stream(response_generator(full_answer))
                # 'streamed_text' is the final string returned by write_stream,
                # which accumulates all tokens from the generator.

            # 4) Add assistant message to conversation
            st.session_state.messages.append({"role": "assistant", "content": streamed_text})
