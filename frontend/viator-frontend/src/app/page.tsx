"use client";

import { useState, useRef } from "react";

export default function Home() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setResponse("");

    controllerRef.current = new AbortController();

    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ input }),
      signal: controllerRef.current.signal,
    });

    if (!res.body) {
      setIsLoading(false);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let done = false;
    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;
      const chunk = decoder.decode(value);
      setResponse(prev => prev + chunk);
    }

    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-gray-900">
      <h1 className="text-2xl font-bold mb-4 text-white">Travel AI Chat</h1>
      <form onSubmit={handleSubmit} className="w-full max-w-xl flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          className="flex-grow p-2 border border-gray-700 rounded bg-gray-800 text-white"
          placeholder="Ask about your next trip..."
        />
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          {isLoading ? "Loading..." : "Send"}
        </button>
      </form>

      <div className="w-full max-w-xl mt-6 bg-gray-800 p-4 rounded shadow">
        <h2 className="font-semibold mb-2 text-white">Assistant Response:</h2>
        <pre className="whitespace-pre-wrap text-sm text-gray-200">{response}</pre>
      </div>
    </div>
  );
}
