"use client";
import { useState, useEffect } from "react";

export default function ResearchChatUI({ ticker }) {
  const [messages, setMessages] = useState([
    { sender: "bot", text: "Hi there 👋 How can I help you today?" },
  ]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!query.trim()) return;
    setMessages((prev) => [...prev, { sender: "user", text: query }]);
    setQuery("");
    setLoading(true);

    try {
      const response = await fetch(`/api/ask?ticker=${ticker}&question=${query}`);
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const reader = response.body.getReader();
      let receivedText = "";
      const decoder = new TextDecoder();

      setMessages((prev) => [...prev, { sender: "bot", text: "" }]); // Placeholder

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        receivedText += decoder.decode(value, { stream: true });
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { sender: "bot", text: receivedText },
        ]);
      }
    } catch (error) {
      console.error("Error fetching response:", error);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Sorry, an error occurred." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full p-6 bg-gray-100">
      <h1 className="text-3xl font-bold text-center mb-4">Chatbot</h1>
      {/* Chat Window */}
      <div className="flex-grow p-4 bg-white rounded-lg shadow-md overflow-auto h-96">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`p-3 rounded-lg my-2 ${
              msg.sender === "user"
                ? "bg-blue-500 text-white self-end"
                : "bg-gray-200 text-black self-start"
            }`}
            style={{ maxWidth: "70%" }}
          >
            {msg.text}
          </div>
        ))}
      </div>

      {/* Input Box */}
      <div className="flex mt-4">
        <input
          type="text"
          className="flex-grow p-2 border rounded-md"
          placeholder="Write a message..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          onClick={handleSend}
          className="ml-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          disabled={loading}
        >
          {loading ? "..." : "➤"}
        </button>
      </div>
    </div>
  );
}
