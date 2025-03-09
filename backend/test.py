import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

def get_alpha_vantage_news(api_key, ticker, topic=None):
    """
    Fetches news articles about `ticker` from the Alpha Vantage News API.
    Optionally filters by `topic` (e.g., "technology", "finance", etc.).
    Returns a list of dicts with article info (title, summary, sentiment, etc.).
    """

    # Alpha Vantage 'NEWS_SENTIMENT' endpoint
    url = "https://www.alphavantage.co/query"

    # Base params
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": ticker,
        "apikey": api_key
    }

    # If a topic was provided, include it in the params
    # NOTE: The Alpha Vantage parameter for filtering by topic is "topics".
    # E.g., topics=technology,ipo
    if topic:
        params["topics"] = topic

    response = requests.get(url, params=params)
    print("Request URL:", response.url)  # Debugging: see the final request
    data = response.json()

    # Check for errors
    if "feed" not in data:
        print(f"Error fetching news from Alpha Vantage: {data}")
        return []

    articles = data["feed"]
    return articles

ticker = "AAPL"
articles = get_alpha_vantage_news(API_KEY, ticker)
limit = 5
articles = articles[:limit]

print(f"\n=== Top {limit} News Articles for {ticker} ===")
for i, article in enumerate(articles, start=1):
    title = article.get("title", "No Title")
    summary = article.get("summary", "No Summary")

    print(f"\nArticle {i}:")
    print(f"Title: {title}")
    print(f"Summary: {summary[:200]}...")  # limit summary preview