from typing import List, Optional
from pydantic import BaseModel

class Topic(BaseModel):
    topic: str
    relevance_score: str

class TickerSentiment(BaseModel):
    ticker: str
    relevance_score: str
    ticker_sentiment_score: str
    ticker_sentiment_label: str

class FeedItem(BaseModel):
    title: Optional[str] = None
    url: str  # still required for parsing
    time_published: Optional[str] = None
    authors: Optional[List[str]] = None
    summary: Optional[str] = None
    banner_image: Optional[str] = None
    source: Optional[str] = None
    category_within_source: Optional[str] = None
    source_domain: Optional[str] = None

    topics: Optional[List[Topic]] = None
    overall_sentiment_score: Optional[float] = None
    overall_sentiment_label: Optional[str] = None
    ticker_sentiment: Optional[List[TickerSentiment]] = None

class FeedRequest(BaseModel):
    feed: List[FeedItem]
    ticker: Optional[str] = None  # optional if you still want to pass a ticker name
