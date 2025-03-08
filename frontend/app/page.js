"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import HomePageUI from "./HomePageUI"; 

export default function Home() {
    const [ticker, setTicker] = useState("");
    const router = useRouter();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!ticker) return alert("Please enter a ticker");

        // Redirect to loading page with the ticker
        router.push(`/loading?ticker=${ticker}`);
    };

    return <HomePageUI ticker={ticker} setTicker={setTicker} handleSubmit={handleSubmit} />;
}
