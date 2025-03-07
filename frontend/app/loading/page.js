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
            return;
        }

        // Call backend API to build index
        fetch(`/api/build-index?ticker=${ticker}`)
            .then((res) => res.json())
            .then((data) => {
                console.log("Backend request successful");
                router.push(`/research?ticker=${ticker}`); // Redirects to research page
            })
            .catch((err) => {
                console.error("Error:", err);
                alert("Error processing request");
                router.push("/");
            });
    }, [ticker, router]);

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
            <img src="/logo.png" alt="Logo" className="w-32 mb-4" />
            <h1 className="text-2xl font-semibold">Building Index for {ticker}...</h1>
            <div className="mt-4 animate-spin h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
    );
}
