export async function GET(req) {
  // Extract query parameters from the request URL
  const url = new URL(req.url);
  const ticker = url.searchParams.get("ticker");

  if (!ticker) {
      return new Response(JSON.stringify({ error: "No ticker provided" }), {
          status: 400,
      });
  }

  try {
      // Call Python backend with user-provided ticker
      const response = await fetch(`http://localhost:8000/build-index?ticker=${ticker}`);
      const data = await response.json();

      return new Response(JSON.stringify(data), { status: 200 });
  } catch (error) {
      return new Response(JSON.stringify({ error: "Backend request failed" }), {
          status: 500,
      });
  }
}
