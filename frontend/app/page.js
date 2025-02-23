"use client"; // Required for event handling in App Router

import { useState } from "react";
import axios from "axios";

export default function Home() {
  const [symbol, setSymbol] = useState("");
  const [news, setNews] = useState([]); // Ensure news is always an array
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchNews = async () => {
    if (!symbol) {
      setError("Please enter a valid stock ticker (e.g., AAPL, TSLA).");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const ticker = symbol.toUpperCase();  // Convert to uppercase
      const response = await axios.get(`${process.env.NEXT_PUBLIC_BACKEND_URL}/news/`, {
        params: { symbol: ticker },
      });

      console.log("Final API Response:", response.data);

      // Ensure response data is correctly formatted
      if (response.data.error) {
        setError(response.data.error);
        setNews([]);
      } else {
        setNews(response.data.news || []);
      }
    } catch (err) {
      console.error("Error fetching news", err);
      setError("Failed to fetch news. Try again later.");
      setNews([]);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-4">
      <h1 className="text-3xl font-bold mb-4">Stock News Fetcher</h1>
      <input
        type="text"
        placeholder="Enter Stock Ticker (e.g., AAPL)"
        value={symbol}
        onChange={(e) => setSymbol(e.target.value)}
        className="p-2 border border-gray-300 rounded-md w-64"
      />
      <button
        onClick={fetchNews}
        className="mt-2 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-700"
      >
        Get News
      </button>

      {loading && <p className="mt-4">Loading...</p>}
      {error && <p className="text-red-500 mt-4">{error}</p>}

      <div className="mt-6 w-full max-w-lg">
        {Array.isArray(news) && news.length > 0 ? (
          news.map((item, index) => (
            <div key={index} className="bg-white p-4 mb-2 rounded-md shadow">
              <h3 className="font-bold">{item.title}</h3>
              <p className="text-gray-600">{item.summary}</p>
              <a href={item.url} target="_blank" rel="noopener noreferrer" className="text-blue-500">
                Read More
              </a>
            </div>
          ))
        ) : (
          <p className="text-gray-500">No news available.</p>
        )}
      </div>
    </div>
  );
}
