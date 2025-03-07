"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
    const [ticker, setTicker] = useState("");
    const router = useRouter();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!ticker) return alert("Please enter a ticker");

        // Redirect to loading page with the ticker
        router.push(`/loading?ticker=${ticker}`);
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
            <img src="/logo.png" alt="Logo" className="w-32 mb-4" />
            <h1 className="text-3xl font-bold mb-4">AI-Powered Financial Research</h1>
            <form onSubmit={handleSubmit} className="flex space-x-3">
                <input
                    type="text"
                    placeholder="Enter stock ticker"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value.toUpperCase())}
                    className="px-4 py-2 border rounded-md text-lg"
                />
                <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                    Submit
                </button>
            </form>
        </div>
    );
}
