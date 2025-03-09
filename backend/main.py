from fastapi import FastAPI
import requests
import os
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/news/")
def get_stock_news(symbol: str):
    """Fetch stock news from Alpha Vantage"""
    
    # Ensure symbol is uppercase (Alpha Vantage requires tickers)
    symbol = symbol.upper()

    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={API_KEY}"
    response = requests.get(url)
    
    print("Raw API Response:", response.json())  # Debugging

    if response.status_code == 200:
        data = response.json()

        if "Information" in data:
            return {"error": data["Information"]}  # Return error message

        return {"news": data.get("feed", [])}

    return {"error": "Failed to fetch data"}
