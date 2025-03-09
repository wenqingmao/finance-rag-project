// export async function GET(req) {
//   // Extract query parameters from the request URL
//   const url = new URL(req.url);
//   const ticker = url.searchParams.get("ticker");

//   if (!ticker) {
//       return new Response(JSON.stringify({ error: "No ticker provided" }), {
//           status: 400,
//       });
//   }

//   try {
//       // Call Python backend with user-provided ticker
//       const response = await fetch(`http://localhost:8000/build-index?ticker=${ticker}`);
//       const data = await response.json();

//       return new Response(JSON.stringify(data), { status: 200 });
//   } catch (error) {
//       return new Response(JSON.stringify({ error: "Backend request failed" }), {
//           status: 500,
//       });
//   }
// }

export async function GET(req) {
    const url = new URL(req.url);
    const ticker = url.searchParams.get("ticker");

    if (!ticker) {
        return Response.json({ error: "No ticker provided" }, { status: 400 });
    }

    try {
        // Call Python backend
        const response = await fetch(`http://localhost:8000/build-index?ticker=${ticker}`);
        const jsonData = await response.json();  // ✅ Proper JSON response handling

        return Response.json(jsonData, { status: 200 }); // ✅ Ensures JSON response is correctly formatted
    } catch (error) {
        return Response.json({ error: "Backend request failed" }, { status: 500 });
    }
}
