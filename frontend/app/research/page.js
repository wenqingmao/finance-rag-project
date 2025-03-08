"use client"; // Ensure this is a client component

import { useSearchParams } from "next/navigation";
import ResearchChatUI from "./ResearchChatUI";

export default function ResearchPage() {
  const searchParams = useSearchParams();
  const ticker = searchParams.get("ticker") || "Unknown"; // Use .get() instead of direct access

  return (
    <div className="flex h-screen">
      {/* Sidebar - 1/4 */}
      <div className="w-1/4 bg-blue-600 text-white p-4">
        <img src="/logo.png" alt="Logo" className="w-16 mb-2" />
        <h2 className="text-xl font-bold">{ticker}</h2>
      </div>

      {/* Chat Window - 3/4 */}
      <div className="w-3/4 flex flex-col">
        <ResearchChatUI ticker={ticker} />
      </div>
    </div>
  );
}
