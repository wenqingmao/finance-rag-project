import React from "react";

export default function HomePageUI({ handleSubmit, ticker, setTicker }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen w-screen bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 text-white">
      {/* Logo */}
      <img src="/logo.png" alt="Logo" className="w-32 mb-4 animate-pulse" />

      {/* Title */}
      <h1 className="text-4xl font-extrabold mb-6 drop-shadow-lg text-center">
        AI-Powered Financial Research
      </h1>

      {/* Input Form */}
      <form
        onSubmit={handleSubmit}
        className="flex flex-col items-center bg-white p-6 rounded-lg shadow-lg w-full max-w-md"
      >
        <input
          type="text"
          placeholder="Enter a stock ticker"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          className="px-4 py-2 border rounded-md text-black text-lg text-center w-full"
        />
        <button
          type="submit"
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition duration-300 w-full"
        >
          Submit
        </button>
      </form>
    </div>
  );
}
