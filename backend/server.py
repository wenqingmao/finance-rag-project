from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import index_builder
from call_llm import query_llm_with_retrieval
import time
import uvicorn

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/build-index/")
async def build_index(ticker: str = Query(..., description="Stock ticker symbol")):
    """
    API to fetch stock news and build an index.
    """
    response = index_builder.build_stock_index(ticker)
    return response

@app.get("/ask/")
async def ask_question(ticker: str = Query(..., description="Stock ticker symbol"),
                       question: str = Query(..., description="User research question")):
    """
    API to process financial research queries.
    Calls LLM retrieval function and streams back the response.
    """

    async def generate_response():
        yield f"Retrieving data for {ticker}...\n\n"

        # Call LLM function
        llm_response = query_llm_with_retrieval(ticker, question)

        # Stream response word by word
        for word in llm_response.split():
            yield word + " "
            time.sleep(0.05)  # Simulate streaming delay

    return StreamingResponse(generate_response(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
