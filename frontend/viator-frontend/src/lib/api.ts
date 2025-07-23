export async function apiCaller({
    url,
    input,
    signal,
}: {
    url: string;
    input: string;
    signal?: AbortController;
}) {
    if (!signal) {
        signal = new AbortController()
    }
    const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ input }),
    signal: signal.signal,
  });

  if (!res.ok) {
    throw new Error(`Server returned ${res.status}`);
  }

  if (!res.body) {
    throw new Error("No response body received.");
  }

  return res;
}