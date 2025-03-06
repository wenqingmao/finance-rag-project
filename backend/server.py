from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import index_builder

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
