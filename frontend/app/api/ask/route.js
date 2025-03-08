export async function GET(req) {
    const url = new URL(req.url);
    const ticker = url.searchParams.get("ticker");
    const question = url.searchParams.get("question");
  
    if (!ticker || !question) {
      return new Response(JSON.stringify({ error: "Missing parameters" }), { status: 400 });
    }
  
    try {
      const response = await fetch(`http://localhost:8000/ask?ticker=${ticker}&question=${question}`);
      return new Response(response.body, { status: 200 });
    } catch (error) {
      return new Response(JSON.stringify({ error: "Backend request failed" }), { status: 500 });
    }
  }
  