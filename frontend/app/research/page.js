"use client"; // Ensure this is a client component

import { useSearchParams } from "next/navigation";
import ResearchChatUI from "./ResearchChatUI";

export default function ResearchPage() {
  const searchParams = useSearchParams();
  const ticker = searchParams.get("ticker") || "Unknown";

  return (
    <div className="flex h-screen w-screen">
      {/* Sidebar - 1/5 of the page width with gradient background */}
      <div className="w-1/5 h-full bg-gradient-to-r from-blue-500 to-purple-500 text-white p-6 flex flex-col items-center justify-start">
        <img src="/logo.png" alt="Logo" className="w-16 mb-2" />
        <h2 className="text-xl font-bold">{ticker}</h2>
      </div>

      {/* Chat Window - Centered with max width */}
      <div className="flex-grow flex justify-center items-center p-6 bg-gray-100">
        <div className="w-full max-w-3xl">
          <ResearchChatUI ticker={ticker} />
        </div>
      </div>
    </div>
  );
}

export default function ResearchPage() {
  return (
      <Suspense fallback={<div>Loading...</div>}>
          <ResearchComponent />
      </Suspense>
  );
}
