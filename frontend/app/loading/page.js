"use client";
import { useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";

export default function LoadingPage() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const ticker = searchParams.get("ticker");

    useEffect(() => {
        if (!ticker) {
            router.push("/");
            return; // ✅ Ensure execution stops here
        }

        // Call backend API to build index
        fetch(`/api/build-index?ticker=${ticker}`)
            .then((res) => res.json())
            .then(() => {
                console.log("Backend request successful");
                router.push(`/research?ticker=${ticker}`); // Redirect to research page
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("Error processing request");
                router.push("/");
            });
    }, [ticker, router]);

    return (
      <div className="flex flex-col items-center justify-center w-screen min-h-screen bg-gradient-to-b from-purple-600 to-indigo-800 text-white">
        {/* ✅ Only render ticker if it's defined to avoid hydration issues */}
        {ticker ? <h1 className="text-3xl font-bold mb-4">Building Index for {ticker}...</h1> : null}
        
        {/* ✅ Added `border-t-transparent` to make the spinner visually better */}
        <div className="w-16 h-16 border-4 border-white border-dashed border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
}
