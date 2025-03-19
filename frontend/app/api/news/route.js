// app/api/some-route/route.js
export async function GET(req) {
  const url = new URL(req.url);
  const ticker = url.searchParams.get("ticker");

  if (!ticker) {
      return Response.json({ error: "No ticker provided" }, { status: 400 });
  }

  const apiKey = process.env.ALPHA_VANTAGE_API_KEY;
  const alphaUrl = `https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=${ticker}&apikey=${apiKey}&sort=RELEVANCE`;

  
  try {
      const alphaRes = await fetch(alphaUrl);
      const alphaData = await alphaRes.json();
      console.log(alphaData);

      // Forward alphaData.feed AND ticker to the FastAPI backend
      const backendRes = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/build-index`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({alphaData, ticker }) // Include ticker in the payload
      });

      const backendData = await backendRes.json();

      return new Response(JSON.stringify(backendData), {
          status: 200,
          headers: { "Content-Type": "application/json" }
      });
  } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
          status: 500,
          headers: { "Content-Type": "application/json" }
      });
  }
}