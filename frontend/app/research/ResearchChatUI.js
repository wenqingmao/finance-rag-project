import { useState } from "react";

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
    <div className="flex flex-col w-full h-full bg-white p-6 rounded-lg shadow-lg">
      <h1 className="text-3xl font-bold text-center mb-4">FinFetch</h1>

      {/* Chat Window */}
      <div className="flex-grow p-4 bg-gray-100 rounded-lg overflow-auto h-[450px]">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`p-3 rounded-lg my-2 max-w-[70%] w-fit ${
              msg.sender === "user"
                ? "bg-blue-500 text-white self-end text-right ml-auto" 
                : "bg-gray-200 text-black self-start text-left mr-auto" 
            }`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault(); 
          handleSend(); 
        }}
        className="flex mt-4"
      >
        <input
          type="text"
          className="flex-grow p-2 border rounded-md"
          placeholder="Write a message..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          type="submit"
          className="ml-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          disabled={loading}
        >
          {loading ? "..." : "➤"}
        </button>
      </form>

    </div>
  );
}
